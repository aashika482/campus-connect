from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import aliased

from app.core.config import today
from app.db.database import get_db
from app.models.club import Club, ClubBenefit
from app.models.event import Event
from app.models.audit import AuditLog
from app.models.membership import (
    ClubRole, ClubRoleKind, ClubRoleStatus, Registration, OPEN_STATUSES, TEAM_ROLES, STUDENT_TEAM_ROLES,
    CURRENT, ClubApplication, ApplicationStatus, OPEN_APPLICATION_STATUSES, LeaveRequest, LeaveStatus,
)
from app.models.user import User, AccountType
from app.core.deps import get_or_404, get_current_active_user, get_optional_user, ensure_can_manage
from app.core.governance import (
    role_page, role_detail, request_team_role, membership_end, close_lapsed, lapsed, lapsed_working_member,
    application_block, act_on_application, leave_block,
)
from app.schemas.event import (
    ClubOut, ClubPage, ClubMembershipStatus, MemberOut, EventRef,
    ClubRoleDetailOut, ClubRolePage, OwnerRequest, EditorProposal, ClubSettingsUpdate,
    ApplicationOut, ApplicationPage, MyApplication, ApplicationAction, Roster, RosterEntry,
    BenefitIn, BenefitOut, LeaveIn, MyLeaveRequest,
)

router = APIRouter()


@router.get("", response_model=ClubPage)
async def list_clubs(
    q: Optional[str] = Query(None, description="Search name, abbreviation, description and tags"),
    limit: int = Query(12, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Clubs A→Z, one page at a time. `total` counts matches across all pages.
    Private clubs are listed only for the people in them (and the DSW)."""
    filters = []
    if not (user and user.account_type == AccountType.dsw):
        filters.append(or_(Club.is_private == False, Club.id.in_(user.club_ids if user else set())))  # noqa: E712
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


# ── Membership ───────────────────────────────────────────
@router.post("/{club_id}/join", response_model=ClubMembershipStatus)
async def join_club(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Students join a club for the current academic year as non-working members (joining again
    after 31 July renews it). There's no leaving from the app (for now)."""
    club = await get_or_404(db, Club, club_id)
    if user.account_type != AccountType.student:
        raise HTTPException(status_code=403, detail="Only students can join clubs")
    if club.is_private and not user.sees_inside(club_id):
        raise HTTPException(status_code=403, detail=f"{club.name} is private and isn't taking members")
    if not club.is_open and not user.is_member_of(club_id) and not lapsed(user, club_id, ClubRoleKind.member):
        raise HTTPException(status_code=403, detail=f"{club.name} isn't taking new members right now")
    if not user.is_member_of(club_id):
        renewal = close_lapsed(user, club_id, ClubRoleKind.member)
        db.add(ClubRole(user_id=user.id, club_id=club_id, role=ClubRoleKind.member,
                        status=ClubRoleStatus.active, expires_on=membership_end()))
        AuditLog.record(db, user, "club.renew" if renewal else "club.join", "club", club_id, club=club.name)
        await db.flush()
    await db.refresh(club, ["member_count"])
    await db.commit()
    return ClubMembershipStatus(club_id=club_id, is_member=True, member_count=club.member_count)


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
        .where(ClubRole.club_id == club_id, ClubRole.role == ClubRoleKind.member, CURRENT)
        .order_by(ClubRole.created_at.desc())
    )).all()

    # One query for every member's registrations to this club's events
    regs = (await db.execute(
        select(Registration.user_id, Event.id, Event.title)
        .join(Event, Event.id == Registration.event_id)
        .where(Event.club_id == club_id, Registration.user_id.in_([u.id for u, _ in rows]))
        .order_by(Event.start_date)
    )).all() if rows else []
    working = set((await db.execute(
        select(ClubRole.user_id).where(ClubRole.club_id == club_id, ClubRole.role == ClubRoleKind.working_member, CURRENT)
    )).scalars().all())
    events_by_user: dict[int, list[EventRef]] = {}
    for user_id, ev_id, title in regs:
        events_by_user.setdefault(user_id, []).append(EventRef(id=ev_id, title=title))

    return [
        MemberOut(
            user_id=u.id, name=u.name, email=u.email, phone=u.phone,
            reg_no=u.reg_no, course=u.course, joined_at=at, is_working=u.id in working,
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


# ── Settings ─────────────────────────────────────────────
@router.patch("/{club_id}/settings", response_model=ClubOut)
async def update_settings(
    club_id: int,
    payload: ClubSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Private, recruiting, the multi-club rule for working members and the yearly fees: the club's team.
    The DSW can make any club private or public."""
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not (user.account_type == AccountType.dsw and set(changes) <= {"is_private"}):
        ensure_can_manage(user, club_id)
    club = await get_or_404(db, Club, club_id)
    if "tags" in changes:
        changes["tags"] = ",".join(dict.fromkeys(t.strip() for t in changes["tags"] if t.strip()))
    for link in ("instagram", "linkedin"):
        if changes.get(link) == "":
            changes[link] = None
    for k, v in changes.items():
        setattr(club, k, v)
    if club.fee_working < club.fee_member:
        raise HTTPException(status_code=400, detail="The working-member fee can't be lower than the member fee")
    AuditLog.record(db, user, "club.settings", "club", club_id, club=club.name,
                    **{k: v for k, v in changes.items() if k != "description"})
    await db.commit()
    await db.refresh(club)
    return club


# ── Roster ───────────────────────────────────────────────
@router.get("/{club_id}/roster", response_model=Roster)
async def club_roster(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Everyone in the club this academic year. The working team sees course, interests and roles;
    everyone else sees names only. Contact details are never shown here."""
    club = await get_or_404(db, Club, club_id)
    if club.is_private and not user.sees_inside(club_id):
        return Roster(detailed=False, items=[])
    detailed = user.on_working_team(club_id)
    rows = (await db.execute(
        select(User, ClubRole.role, ClubRole.title)
        .join(ClubRole, ClubRole.user_id == User.id)
        .where(ClubRole.club_id == club_id, CURRENT)
        .order_by(User.name, User.id)
    )).all()
    people: dict[int, RosterEntry] = {}
    for u, role, title in rows:
        entry = people.setdefault(u.id, RosterEntry(user_id=u.id, name=u.name))
        if detailed:
            entry.course, entry.interests = u.course, u.interests
            entry.roles.append(role)
            entry.title = entry.title or title
    return Roster(detailed=detailed, items=list(people.values()))


# ── Working-team applications ────────────────────────────
@router.get("/{club_id}/application", response_model=MyApplication)
async def my_application(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """The signed-in student's latest application here, and whether they can apply now."""
    club = await get_or_404(db, Club, club_id)
    latest = (await db.execute(
        select(ClubApplication).where(ClubApplication.club_id == club_id, ClubApplication.user_id == user.id)
        .order_by(ClubApplication.id.desc()).limit(1)
    )).scalar_one_or_none()
    open_app = latest if latest and latest.status in OPEN_APPLICATION_STATUSES else None
    reason = application_block(user, club, open_app)
    return MyApplication(status=latest.status if latest else None, can_apply=reason is None, reason=reason,
                         is_renewal=open_app.is_renewal if open_app else lapsed_working_member(user, club_id))


@router.post("/{club_id}/application", response_model=MyApplication, status_code=201)
async def apply_to_working_team(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """A member applies to the working team (or renews last year's place, even outside recruiting)."""
    club = await get_or_404(db, Club, club_id)
    open_app = (await db.execute(
        select(ClubApplication).where(ClubApplication.club_id == club_id, ClubApplication.user_id == user.id,
                                      ClubApplication.status.in_(OPEN_APPLICATION_STATUSES))
    )).scalar_one_or_none()
    if reason := application_block(user, club, open_app):
        raise HTTPException(status_code=400, detail=reason)
    renewal = lapsed_working_member(user, club_id)
    app = ClubApplication(user_id=user.id, club_id=club_id, is_renewal=renewal)
    db.add(app)
    await db.flush()
    AuditLog.record(db, user, "application.renew" if renewal else "application.apply", "club_application", app.id,
                    club=club.name)
    await db.commit()
    return MyApplication(status=app.status, is_renewal=renewal, can_apply=False,
                         reason="Your application is being reviewed")


@router.get("/{club_id}/applications", response_model=ApplicationPage)
async def list_applications(
    club_id: int,
    status: Optional[ApplicationStatus] = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Every application to this club's working team, newest first. The club's team."""
    ensure_can_manage(user, club_id)
    filters = [ClubApplication.club_id == club_id] + ([ClubApplication.status == status] if status else [])
    reviewer, decider = aliased(User), aliased(User)
    total = (await db.execute(select(func.count()).select_from(ClubApplication).where(*filters))).scalar()
    rows = (await db.execute(
        select(ClubApplication, User, reviewer.name, decider.name)
        .join(User, User.id == ClubApplication.user_id)
        .outerjoin(reviewer, reviewer.id == ClubApplication.reviewed_by)
        .outerjoin(decider, decider.id == ClubApplication.decided_by)
        .where(*filters)
        .order_by(ClubApplication.created_at.desc(), ClubApplication.id.desc())
        .limit(limit).offset(offset)
    )).all()
    return ApplicationPage(total=total, items=[
        ApplicationOut(
            id=a.id, club_id=a.club_id, status=a.status, is_renewal=a.is_renewal,
            reviewed_by_name=rn, decided_by_name=dn, created_at=a.created_at, updated_at=a.updated_at,
            user_id=u.id, name=u.name, email=u.email, phone=u.phone, reg_no=u.reg_no, course=u.course,
        ) for a, u, rn, dn in rows
    ])


@router.patch("/{club_id}/applications/{application_id}", status_code=204)
async def review_application(
    club_id: int,
    application_id: int,
    payload: ApplicationAction,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Move an application along: shortlist / recommend / decline (owner, editors), then
    approve / decline (faculty coordinator)."""
    app = await get_or_404(db, ClubApplication, application_id)
    if app.club_id != club_id:
        raise HTTPException(status_code=404, detail="ClubApplication not found")
    club = await get_or_404(db, Club, club_id)
    applicant = await get_or_404(db, User, app.user_id)
    await act_on_application(db, app, club, applicant, user, payload.action)
    await db.commit()


# ── Member benefits ──────────────────────────────────────
@router.get("/{club_id}/benefits", response_model=list[BenefitOut])
async def list_benefits(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """The club's current perks. Public, except for a private club's outsiders."""
    club = await get_or_404(db, Club, club_id)
    if club.is_private and not (user and user.sees_inside(club_id)):
        return []
    rows = (await db.execute(
        select(ClubBenefit).where(ClubBenefit.club_id == club_id,
                                  or_(ClubBenefit.valid_until.is_(None), ClubBenefit.valid_until >= today()))
        .order_by(ClubBenefit.audience, ClubBenefit.id)
    )).scalars().all()
    return rows


@router.post("/{club_id}/benefits", response_model=BenefitOut, status_code=201)
async def add_benefit(
    club_id: int,
    payload: BenefitIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    ensure_can_manage(user, club_id)
    benefit = ClubBenefit(club_id=club_id, **payload.model_dump())
    db.add(benefit)
    await db.commit()
    await db.refresh(benefit)
    return benefit


@router.delete("/{club_id}/benefits/{benefit_id}", status_code=204)
async def remove_benefit(
    club_id: int,
    benefit_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    ensure_can_manage(user, club_id)
    benefit = await get_or_404(db, ClubBenefit, benefit_id)
    if benefit.club_id != club_id:
        raise HTTPException(status_code=404, detail="ClubBenefit not found")
    await db.delete(benefit)
    await db.commit()


# ── Leaving (the DSW approves) ───────────────────────────
async def _latest_leave(db: AsyncSession, user_id: int, club_id: int) -> LeaveRequest | None:
    return (await db.execute(
        select(LeaveRequest).where(LeaveRequest.user_id == user_id, LeaveRequest.club_id == club_id)
        .order_by(LeaveRequest.id.desc()).limit(1)
    )).scalar_one_or_none()


@router.get("/{club_id}/leave", response_model=MyLeaveRequest)
async def my_leave_request(
    club_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    latest = await _latest_leave(db, user.id, club_id)
    return MyLeaveRequest(status=latest.status, scope=latest.scope) if latest else MyLeaveRequest()


@router.post("/{club_id}/leave", response_model=MyLeaveRequest, status_code=201)
async def request_to_leave(
    club_id: int,
    payload: LeaveIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Ask the DSW to let you leave this club's working team, or the club."""
    club = await get_or_404(db, Club, club_id)
    if reason := leave_block(user, club_id, payload.scope):
        raise HTTPException(status_code=400, detail=reason)
    latest = await _latest_leave(db, user.id, club_id)
    if latest and latest.status == LeaveStatus.pending:
        raise HTTPException(status_code=400, detail="You already have a request waiting for the DSW")
    req = LeaveRequest(user_id=user.id, club_id=club_id, scope=payload.scope, reason=payload.reason)
    db.add(req)
    await db.flush()
    AuditLog.record(db, user, "leave.request", "leave_request", req.id, club=club.name, scope=payload.scope.value)
    await db.commit()
    return MyLeaveRequest(status=req.status, scope=req.scope)
