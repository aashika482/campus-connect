from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, or_

from app.db.database import get_db
from app.models.club import Club
from app.models.event import Event
from app.models.membership import Membership, Registration
from app.models.user import User
from app.core.deps import get_current_active_user, require_club_member
from app.schemas.event import ClubOut, ClubPage, ClubCreate, ClubMembershipStatus, MemberOut, EventRef

router = APIRouter()


async def _sync_member_count(db: AsyncSession, club: Club) -> int:
    """Set clubs.member_count to the real number of memberships and return it.

    Recounting (instead of +1/-1) means the stored number can never drift.
    """
    count = (await db.execute(
        select(func.count()).select_from(Membership).where(Membership.club_id == club.id)
    )).scalar()
    club.member_count = count
    return count


@router.get("", response_model=ClubPage)
async def list_clubs(
    q: Optional[str] = Query(None, description="Search name, abbreviation, description and tags"),
    name: Optional[str] = Query(None, description="Exact club name"),
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
    if name is not None:
        filters.append(Club.name == name)

    total = (await db.execute(select(func.count()).select_from(Club).where(*filters))).scalar()
    result = await db.execute(
        select(Club).where(*filters).order_by(Club.name, Club.id).limit(limit).offset(offset)
    )
    return ClubPage(items=[ClubOut.model_validate(c) for c in result.scalars().all()], total=total)


@router.get("/{club_id}", response_model=ClubOut)
async def get_club(club_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@router.post("", response_model=ClubOut, status_code=201)
async def create_club(
    payload: ClubCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    club = Club(**payload.model_dump(exclude={"tags"}), tags=",".join(payload.tags))
    db.add(club)
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
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    existing = await db.execute(
        select(Membership).where(Membership.user_id == user.id, Membership.club_id == club_id)
    )
    if not existing.scalar_one_or_none():
        db.add(Membership(user_id=user.id, club_id=club_id))
        await db.flush()  # so the recount below includes the new membership

    count = await _sync_member_count(db, club)
    await db.commit()
    return ClubMembershipStatus(club_id=club_id, is_member=True, member_count=count)


@router.delete("/{club_id}/join", response_model=ClubMembershipStatus)
async def leave_club(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    await db.execute(
        delete(Membership).where(Membership.user_id == user.id, Membership.club_id == club_id)
    )
    count = await _sync_member_count(db, club)
    await db.commit()
    return ClubMembershipStatus(club_id=club_id, is_member=False, member_count=count)


@router.get("/admin/members", response_model=list[MemberOut])
async def list_my_club_members(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    """Members of the admin's own club (newest first), each with the club's events
    they registered for. The club is found by name, like the other admin checks."""
    club = (await db.execute(select(Club).where(Club.name == user.club_name))).scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Your account isn't linked to a club")

    rows = (await db.execute(
        select(User, Membership.joined_at)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.club_id == club.id)
        .order_by(Membership.joined_at.desc())
    )).all()

    # One query for every member's registrations to this club's events
    regs = (await db.execute(
        select(Registration.user_id, Event.id, Event.title)
        .join(Event, Event.id == Registration.event_id)
        .where(Event.club_name == club.name, Registration.user_id.in_([u.id for u, _ in rows]))
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


@router.get("/me/joined", response_model=list[int])
async def my_clubs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Membership.club_id).where(Membership.user_id == user.id)
    )
    return [r for r in result.scalars().all()]
