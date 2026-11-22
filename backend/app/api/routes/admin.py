# Governance consoles. Mounted at /api/admin:
#   /dsw/...       the DSW office: reviews club team requests and leave requests, assigns faculty
#                  coordinators, switches account types (student / faculty / alumni), features events
#   /platform/...  the tech team: grants and removes DSW accounts (no business authority)
#   /audit-log     both: who did what, when
# The team rules themselves live in app.core.governance.

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_or_404, require_account, require_dsw, require_platform_admin
from app.core.governance import assign_faculty, end_roles, review_leave, review_role, role_detail, role_page
from app.db.database import get_db
from app.models.audit import AuditLog
from app.models.club import Club, ClubEvaluation, CoordinatorInvite
from app.models.event import Event
from app.models.membership import (
    ClubRole, ClubRoleKind, ClubRoleStatus, STUDENT_TEAM_ROLES, TEAM_ROLES, LeaveRequest, LeaveStatus,
)
from app.models.user import User, AccountType
from app.schemas.event import (
    AccountOut, AccountPage, AccountTypeUpdate, AuditLogOut, AuditLogPage, ClubRoleDetailOut,
    ClubRolePage, DswAccountGrant, EventOut, FacultyAssignment, HotUpdate, RoleReview,
    LeaveRequestOut, LeaveRequestPage, LeaveReview, EvaluationOut, EvaluationList,
)

router = APIRouter()


async def _user_by_email(db: AsyncSession, email: str) -> User:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="No account with that email. They need to sign up first.")
    return user


def _account_out(u: User) -> AccountOut:
    return AccountOut(user_id=u.id, name=u.name, email=u.email, phone=u.phone, reg_no=u.reg_no,
                      course=u.course, account_type=u.account_type, is_active=u.is_active, created_at=u.created_at)


async def _account_page(db: AsyncSession, filters: list, limit: int, offset: int) -> AccountPage:
    total = (await db.execute(select(func.count()).select_from(User).where(*filters))).scalar()
    users = (await db.execute(
        select(User).where(*filters).order_by(User.name, User.id).limit(limit).offset(offset)
    )).scalars().all()
    return AccountPage(items=[_account_out(u) for u in users], total=total)


# ── DSW: club teams ──────────────────────────────────────
@router.get("/dsw/club-roles", response_model=ClubRolePage)
async def list_club_roles(
    status: ClubRoleStatus = Query(ClubRoleStatus.pending),
    club_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_dsw),
):
    """Team roles (owner / editor / faculty coordinator) with this status: the review queue
    (pending), every club's current team (active), or history (rejected / ended)."""
    filters = [ClubRole.role.in_(TEAM_ROLES), ClubRole.status == status]
    if club_id is not None:
        filters.append(ClubRole.club_id == club_id)
    return await role_page(db, *filters, limit=limit, offset=offset)


@router.patch("/dsw/club-roles/{role_id}", response_model=ClubRoleDetailOut)
async def review_club_role(
    role_id: int,
    payload: RoleReview,
    db: AsyncSession = Depends(get_db),
    dsw: User = Depends(require_dsw),
):
    """Approve or reject a pending request, or end (revoke) an active team role."""
    row = await get_or_404(db, ClubRole, role_id)
    if row.role not in TEAM_ROLES:
        raise HTTPException(status_code=400, detail="Only team roles are reviewed here")
    target = await get_or_404(db, User, row.user_id)
    await review_role(db, row, target, payload.action, dsw, payload.multi_club_exception)
    await db.commit()
    return role_detail(row, target)


# ── DSW: club evaluations ────────────────────────────────
@router.get("/dsw/evaluations", response_model=EvaluationList)
async def club_evaluations(
    year: Optional[str] = Query(None, description="Academic year, e.g. 2024-25 (default: the latest)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_dsw),
):
    """Every club's audit for one academic year, best first, with who coordinates it (or is invited to)."""
    years = list((await db.execute(select(ClubEvaluation.year).distinct().order_by(ClubEvaluation.year.desc()))).scalars().all())
    year = year or (years[0] if years else None)
    if year is None:
        return EvaluationList(years=[], items=[])
    rows = (await db.execute(
        select(ClubEvaluation, Club.name).join(Club, Club.id == ClubEvaluation.club_id)
        .where(ClubEvaluation.year == year).order_by(ClubEvaluation.total.desc(), Club.name)
    )).all()
    coordinators: dict[int, list[str]] = {}
    for club_id, name in (await db.execute(
        select(ClubRole.club_id, User.name).join(User, User.id == ClubRole.user_id)
        .where(ClubRole.role == ClubRoleKind.faculty_coordinator, ClubRole.status == ClubRoleStatus.active)
    )).all():
        coordinators.setdefault(club_id, []).append(name)
    invited: dict[int, list[str]] = {}
    for club_id, email in (await db.execute(
        select(CoordinatorInvite.club_id, CoordinatorInvite.email).where(CoordinatorInvite.claimed_at.is_(None))
    )).all():
        invited.setdefault(club_id, []).append(email)
    return EvaluationList(years=years, items=[
        EvaluationOut(club_id=e.club_id, club_name=name, year=e.year, category=e.category,
                      quality_of_events=e.quality_of_events, sponsorship=e.sponsorship,
                      student_engagement=e.student_engagement, dsw_component=e.dsw_component,
                      faculty_component=e.faculty_component, total=e.total, remarks=e.remarks,
                      coordinators=coordinators.get(e.club_id, []), invited_coordinators=invited.get(e.club_id, []))
        for e, name in rows
    ])


# ── DSW: leave requests ──────────────────────────────────
@router.get("/dsw/leave-requests", response_model=LeaveRequestPage)
async def list_leave_requests(
    status: LeaveStatus = Query(LeaveStatus.pending),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_dsw),
):
    """Students asking to leave a club's working team, or a club. Oldest first: a queue."""
    filters = [LeaveRequest.status == status]
    total = (await db.execute(select(func.count()).select_from(LeaveRequest).where(*filters))).scalar()
    rows = (await db.execute(
        select(LeaveRequest, User, Club.name)
        .join(User, User.id == LeaveRequest.user_id).join(Club, Club.id == LeaveRequest.club_id)
        .where(*filters).order_by(LeaveRequest.created_at, LeaveRequest.id).limit(limit).offset(offset)
    )).all()
    return LeaveRequestPage(total=total, items=[
        LeaveRequestOut(id=r.id, club_id=r.club_id, club_name=club_name, scope=r.scope, reason=r.reason,
                        status=r.status, created_at=r.created_at, reviewed_at=r.reviewed_at,
                        user_id=u.id, name=u.name, email=u.email, phone=u.phone, reg_no=u.reg_no, course=u.course)
        for r, u, club_name in rows
    ])


@router.patch("/dsw/leave-requests/{request_id}", status_code=204)
async def decide_leave_request(
    request_id: int,
    payload: LeaveReview,
    db: AsyncSession = Depends(get_db),
    dsw: User = Depends(require_dsw),
):
    req = await get_or_404(db, LeaveRequest, request_id)
    leaver = await get_or_404(db, User, req.user_id)
    club = await get_or_404(db, Club, req.club_id)
    await review_leave(db, req, leaver, club, payload.action, dsw)
    await db.commit()


@router.post("/dsw/clubs/{club_id}/faculty", response_model=ClubRoleDetailOut, status_code=201)
async def assign_faculty_coordinator(
    club_id: int,
    payload: FacultyAssignment,
    db: AsyncSession = Depends(get_db),
    dsw: User = Depends(require_dsw),
):
    club = await get_or_404(db, Club, club_id)
    faculty = await _user_by_email(db, payload.email)
    row = await assign_faculty(db, faculty, club, dsw)
    await db.commit()
    return role_detail(row, faculty)


# ── DSW: accounts ────────────────────────────────────────
@router.get("/dsw/accounts", response_model=AccountPage)
async def list_accounts(
    q: Optional[str] = Query(None, description="Search name, email or reg no"),
    account_type: Optional[AccountType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_dsw),
):
    filters = []
    if q and q.strip():
        term = q.strip().lower()
        filters.append(or_(*(func.lower(c).contains(term, autoescape=True) for c in (User.name, User.email, User.reg_no))))
    if account_type is not None:
        filters.append(User.account_type == account_type)
    return await _account_page(db, filters, limit, offset)


@router.patch("/dsw/accounts/{user_id}", response_model=AccountOut)
async def set_account_type(
    user_id: int,
    payload: AccountTypeUpdate,
    db: AsyncSession = Depends(get_db),
    dsw: User = Depends(require_dsw),
):
    """Switch someone between student, faculty and alumni (e.g. on graduation). Team roles
    that don't fit the new type end; club memberships stay."""
    user = await get_or_404(db, User, user_id)
    if user.account_type in (AccountType.dsw, AccountType.platform_admin):
        raise HTTPException(status_code=403, detail="DSW and platform admin accounts are managed by the tech team")
    old, new = user.account_type, payload.account_type
    if new != AccountType.student:
        await end_roles(db, user, (*STUDENT_TEAM_ROLES, ClubRoleKind.working_member), dsw, reason=f"account became {new.value}")
    if new != AccountType.faculty:
        await end_roles(db, user, (ClubRoleKind.faculty_coordinator,), dsw, reason=f"account became {new.value}")
    user.account_type = new
    AuditLog.record(db, dsw, "user.account_type", "user", user.id, user=user.email, old=old.value, new=new.value)
    await db.commit()
    return _account_out(user)


# ── DSW: events ──────────────────────────────────────────
@router.patch("/dsw/events/{event_id}/hot", response_model=EventOut)
async def set_event_hot(
    event_id: int,
    payload: HotUpdate,
    db: AsyncSession = Depends(get_db),
    dsw: User = Depends(require_dsw),
):
    """Feature (or stop featuring) an event in "Hot Right Now". Clubs can't flag their own."""
    event = await get_or_404(db, Event, event_id)
    event.is_hot = payload.is_hot
    AuditLog.record(db, dsw, "event.hot", "event", event.id, title=event.title, is_hot=payload.is_hot)
    await db.commit()
    await db.refresh(event)
    return event


# ── Platform admin: DSW accounts ─────────────────────────
@router.get("/platform/dsw-accounts", response_model=AccountPage)
async def list_dsw_accounts(db: AsyncSession = Depends(get_db), _: User = Depends(require_platform_admin)):
    return await _account_page(db, [User.account_type == AccountType.dsw], 100, 0)


@router.post("/platform/dsw-accounts", response_model=AccountOut, status_code=201)
async def grant_dsw(
    payload: DswAccountGrant,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    """Make an existing account a DSW account. Its club team roles end: the DSW governs
    every club rather than running one."""
    user = await _user_by_email(db, payload.email)
    if user.account_type in (AccountType.dsw, AccountType.platform_admin):
        raise HTTPException(status_code=400, detail=f"{user.name} is already a {user.account_type.value} account")
    await end_roles(db, user, TEAM_ROLES, admin, reason="became a DSW account")
    old = user.account_type
    user.account_type = AccountType.dsw
    AuditLog.record(db, admin, "user.grant_dsw", "user", user.id, user=user.email, old=old.value)
    await db.commit()
    return _account_out(user)


@router.delete("/platform/dsw-accounts/{user_id}", response_model=AccountOut)
async def remove_dsw(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_platform_admin),
):
    """Take DSW rights away; the account goes back to what its email domain gives it."""
    user = await get_or_404(db, User, user_id)
    if user.account_type != AccountType.dsw:
        raise HTTPException(status_code=400, detail=f"{user.name} isn't a DSW account")
    user.account_type = AccountType(settings.account_kind_for(user.email) or "student")
    AuditLog.record(db, admin, "user.remove_dsw", "user", user.id, user=user.email, new=user.account_type.value)
    await db.commit()
    return _account_out(user)


# ── Both: audit log ──────────────────────────────────────
@router.get("/audit-log", response_model=AuditLogPage)
async def audit_log(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_account(AccountType.dsw, AccountType.platform_admin)),
):
    """Every governance action, newest first."""
    total = (await db.execute(select(func.count()).select_from(AuditLog))).scalar()
    rows = (await db.execute(
        select(AuditLog).order_by(AuditLog.id.desc()).limit(limit).offset(offset)
    )).scalars().all()
    return AuditLogPage(items=[
        AuditLogOut(id=r.id, actor_name=r.actor.name if r.actor else None, action=r.action,
                    entity_type=r.entity_type, entity_id=r.entity_id, details=r.details, created_at=r.created_at)
        for r in rows
    ], total=total)
