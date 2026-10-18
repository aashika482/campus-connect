from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.database import get_db
from app.models.club import Club
from app.models.event import Event
from app.models.audit import AuditLog
from app.models.membership import (
    ClubRole, ClubRoleKind, ClubRoleStatus, Registration, OPEN_STATUSES, TEAM_ROLES, STUDENT_TEAM_ROLES,
)
from app.models.user import User, AccountType
from app.core.deps import get_or_404, get_current_active_user, require_dsw, ensure_can_manage
from app.core.governance import role_page, role_detail, request_team_role, sync_member_count
from app.schemas.event import (
    ClubOut, ClubPage, ClubCreate, ClubMembershipStatus, MemberOut, EventRef,
    ClubRoleDetailOut, ClubRolePage, OwnerRequest, EditorProposal,
)

router = APIRouter()


@router.get("", response_model=ClubPage)
async def list_clubs(
    q: Optional[str] = Query(None, description="Search name, abbreviation, description and tags"),
    limit: int = Query(12, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Clubs A→Z, one page at a time. `total` counts matches across all pages."""
    filters = []
    if q and q.strip():
        term = q.strip().lower()
        filters.append(or_(*(
            func.lower(col).contains(term, autoescape=True)
            for col in (Club.name, Club.abbr, Club.description, Club.tags)
        )))

    total = (await db.execute(select(func.count()).select_from(Club).where(*filters))).scalar()
    result = await db.execute(
        select(Club).where(*filters).order_by(Club.name, Club.id).limit(limit).offset(offset)
    )
    return ClubPage(items=[ClubOut.model_validate(c) for c in result.scalars().all()], total=total)


@router.get("/{club_id}", response_model=ClubOut)
async def get_club(club_id: int, db: AsyncSession = Depends(get_db)):
    return await get_or_404(db, Club, club_id)


@router.post("", response_model=ClubOut, status_code=201)
async def create_club(
    payload: ClubCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dsw),
):
    """Only the DSW creates clubs; students then request to run them."""
    if (await db.execute(select(Club.id).where(Club.name == payload.name))).first():
        raise HTTPException(status_code=400, detail="A club with this name already exists")
    club = Club(**payload.model_dump(exclude={"tags"}), tags=",".join(payload.tags))
    db.add(club)
    await db.flush()
    AuditLog.record(db, user, "club.create", "club", club.id, name=club.name)
    await db.commit()
    await db.refresh(club)
    return club


# ── Membership ───────────────────────────────────────────
@router.post("/{club_id}/join", response_model=ClubMembershipStatus)
async def join_club(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Students join clubs. There's no leaving from the app (for now): membership is
    ended by the club's governance, not by the member."""
    club = await get_or_404(db, Club, club_id)
    if user.account_type != AccountType.student:
        raise HTTPException(status_code=403, detail="Only students can join clubs")
    if not user.is_member_of(club_id):
        db.add(ClubRole(user_id=user.id, club_id=club_id, role=ClubRoleKind.member, status=ClubRoleStatus.active))
        await db.flush()  # so the recount below includes the new membership
    count = await sync_member_count(db, club)
    await db.commit()
    return ClubMembershipStatus(club_id=club_id, is_member=True, member_count=count)


@router.get("/{club_id}/members", response_model=list[MemberOut])
async def list_club_members(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """The club's members (newest first), each with the club's events they registered for.
    Only for the club's team."""
    ensure_can_manage(user, club_id)
    rows = (await db.execute(
        select(User, ClubRole.created_at)
        .join(ClubRole, ClubRole.user_id == User.id)
        .where(ClubRole.club_id == club_id, ClubRole.role == ClubRoleKind.member,
               ClubRole.status == ClubRoleStatus.active)
        .order_by(ClubRole.created_at.desc())
    )).all()

    # One query for every member's registrations to this club's events
    regs = (await db.execute(
        select(Registration.user_id, Event.id, Event.title)
        .join(Event, Event.id == Registration.event_id)
        .where(Event.club_id == club_id, Registration.user_id.in_([u.id for u, _ in rows]))
        .order_by(Event.start_date)
    )).all() if rows else []
    events_by_user: dict[int, list[EventRef]] = {}
    for user_id, ev_id, title in regs:
        events_by_user.setdefault(user_id, []).append(EventRef(id=ev_id, title=title))

    return [
        MemberOut(
            user_id=u.id, name=u.name, email=u.email, phone=u.phone,
            reg_no=u.reg_no, course=u.course, joined_at=at,
            registered_events=events_by_user.get(u.id, []),
        )
        for u, at in rows
    ]


# ── Team (owner, editors, faculty coordinators) ──────────
@router.get("/{club_id}/team", response_model=ClubRolePage)
async def club_team(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """The club's team, including requests still waiting for the DSW. For the team and the DSW."""
    if not user.can_moderate(club_id):
        raise HTTPException(status_code=403, detail="Only this club's team can see this")
    return await role_page(db, ClubRole.club_id == club_id, ClubRole.role.in_(TEAM_ROLES),
                           ClubRole.status.in_(OPEN_STATUSES))


@router.post("/{club_id}/owner-request", response_model=ClubRoleDetailOut, status_code=201)
async def request_ownership(
    club_id: int,
    payload: OwnerRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """A student asks the DSW to make them this club's owner."""
    club = await get_or_404(db, Club, club_id)
    row = await request_team_role(db, user, club, ClubRoleKind.owner, user, payload.title)
    await db.commit()
    return role_detail(row, user)


@router.post("/{club_id}/editors", response_model=ClubRoleDetailOut, status_code=201)
async def propose_editor(
    club_id: int,
    payload: EditorProposal,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """The club's owner or an editor proposes a student as editor; the DSW approves."""
    if not any(r.club_id == club_id for r in user.roles(*STUDENT_TEAM_ROLES)):
        raise HTTPException(status_code=403, detail="Only the club's owner or editors can propose editors")
    club = await get_or_404(db, Club, club_id)
    target = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="No account with that email. They need to sign up first.")
    row = await request_team_role(db, target, club, ClubRoleKind.editor, user, payload.title)
    await db.commit()
    return role_detail(row, target, user.name)
