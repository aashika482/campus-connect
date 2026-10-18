# Club team rules, shared by the club routes (requests, proposals) and the DSW routes
# (reviews, faculty assignment, account-type changes). Every rule lives here once:
#   - only students hold owner / editor roles; only faculty are faculty coordinators
#   - a club has one owner and at most settings.MAX_EDITORS_PER_CLUB editors
#   - a student is on one club's team at a time unless the DSW grants an exception
#   - a person has at most one pending owner/editor request at a time
#   - ending a role keeps the row (status "ended") as the club's history

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.club import Club
from app.models.membership import (
    ClubRole, ClubRoleKind, ClubRoleStatus, OPEN_STATUSES, STUDENT_TEAM_ROLES,
)
from app.models.user import User, AccountType
from app.schemas.event import ClubRoleDetailOut, ClubRolePage


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Reading ──────────────────────────────────────────────
async def role_page(db: AsyncSession, *filters, limit: int = 100, offset: int = 0) -> ClubRolePage:
    """Club roles with the people holding them (and who proposed them), newest first."""
    proposer = aliased(User)
    total = (await db.execute(select(func.count()).select_from(ClubRole).where(*filters))).scalar()
    rows = (await db.execute(
        select(ClubRole, User, proposer.name)
        .join(User, User.id == ClubRole.user_id)
        .outerjoin(proposer, proposer.id == ClubRole.proposed_by)
        .where(*filters)
        .order_by(ClubRole.created_at.desc(), ClubRole.id.desc())
        .limit(limit).offset(offset)
    )).all()
    return ClubRolePage(items=[role_detail(r, u, p) for r, u, p in rows], total=total)


def role_detail(r: ClubRole, u: User, proposer_name: str | None = None) -> ClubRoleDetailOut:
    return ClubRoleDetailOut(
        id=r.id, club_id=r.club_id, club_name=r.club_name, role=r.role, status=r.status,
        title=r.title, proposed_by_name=proposer_name, multi_club_exception=r.multi_club_exception,
        created_at=r.created_at, reviewed_at=r.reviewed_at,
        user_id=u.id, name=u.name, email=u.email, phone=u.phone, reg_no=u.reg_no, course=u.course,
    )


async def _count(db: AsyncSession, *filters) -> int:
    return (await db.execute(select(func.count()).select_from(ClubRole).where(*filters))).scalar()


async def sync_member_count(db: AsyncSession, club: Club) -> int:
    """Set clubs.member_count to the real number of active members (a recount never drifts)."""
    club.member_count = await _count(
        db, ClubRole.club_id == club.id, ClubRole.role == ClubRoleKind.member,
        ClubRole.status == ClubRoleStatus.active,
    )
    return club.member_count


# ── Creating requests ────────────────────────────────────
async def request_team_role(
    db: AsyncSession, target: User, club: Club, role: ClubRoleKind, actor: User, title: str | None,
) -> ClubRole:
    """A pending owner/editor role for `target`, waiting for the DSW."""
    if target.account_type != AccountType.student or not target.is_active:
        raise HTTPException(status_code=400, detail="Only active student accounts can join a club's team")
    if any(r.club_id == club.id and r.role in STUDENT_TEAM_ROLES
           for status in OPEN_STATUSES for r in target.roles(status=status)):
        raise HTTPException(status_code=400, detail=f"{target.name} is already on {club.name}'s team or waiting for approval")
    if target.roles(*STUDENT_TEAM_ROLES, status=ClubRoleStatus.pending):
        raise HTTPException(status_code=400, detail=f"{target.name} already has a request waiting for the DSW")
    if role == ClubRoleKind.owner and await _count(
        db, ClubRole.club_id == club.id, ClubRole.role == ClubRoleKind.owner, ClubRole.status == ClubRoleStatus.active,
    ):
        raise HTTPException(status_code=400, detail=f"{club.name} already has an owner. Ask the DSW to hand it over.")

    row = ClubRole(user_id=target.id, club=club, role=role, status=ClubRoleStatus.pending,
                   title=title, proposed_by=actor.id)
    db.add(row)
    await db.flush()
    AuditLog.record(db, actor, f"club_role.request_{role.value}", "club_role", row.id,
                    club=club.name, user=target.email, title=title)
    return row


async def assign_faculty(db: AsyncSession, faculty: User, club: Club, dsw: User) -> ClubRole:
    """The DSW makes a faculty account a coordinator of this club (active immediately)."""
    if faculty.account_type != AccountType.faculty or not faculty.is_active:
        raise HTTPException(status_code=400, detail="Only active faculty accounts can coordinate a club")
    if any(r.club_id == club.id for r in faculty.roles(ClubRoleKind.faculty_coordinator)):
        raise HTTPException(status_code=400, detail=f"{faculty.name} already coordinates {club.name}")
    row = ClubRole(user_id=faculty.id, club=club, role=ClubRoleKind.faculty_coordinator,
                   status=ClubRoleStatus.active, proposed_by=dsw.id, reviewed_by=dsw.id, reviewed_at=_now())
    db.add(row)
    await db.flush()
    AuditLog.record(db, dsw, "club_role.assign_faculty", "club_role", row.id, club=club.name, user=faculty.email)
    return row


# ── DSW review ───────────────────────────────────────────
async def review_role(db: AsyncSession, row: ClubRole, target: User, action: str,
                      dsw: User, multi_club_exception: bool = False) -> None:
    """approve / reject a pending request, or end an active role."""
    expected = ClubRoleStatus.active if action == "end" else ClubRoleStatus.pending
    if row.status != expected:
        raise HTTPException(status_code=400, detail=f"This role is {row.status.value}; it can't be {action}d")

    if action == "approve":
        await _check_can_approve(db, row, target, multi_club_exception)
        row.status = ClubRoleStatus.active
        row.multi_club_exception = multi_club_exception
        if row.role == ClubRoleKind.owner:
            await _reject_rival_owner_requests(db, row, dsw)
    elif action == "reject":
        row.status = ClubRoleStatus.rejected
    else:
        row.status = ClubRoleStatus.ended
        row.ended_at = _now()
    row.reviewed_by, row.reviewed_at = dsw.id, _now()
    AuditLog.record(db, dsw, f"club_role.{action}", "club_role", row.id, club=row.club_name,
                    user=target.email, role=row.role.value, multi_club_exception=multi_club_exception or None)


async def _check_can_approve(db: AsyncSession, row: ClubRole, target: User, exception: bool) -> None:
    if target.account_type != AccountType.student or not target.is_active:
        raise HTTPException(status_code=409, detail=f"{target.name} is no longer an active student account")
    # Lock the club row so two approvals at once can't both slip under a limit
    await db.execute(select(Club.id).where(Club.id == row.club_id).with_for_update())
    active_here = (ClubRole.club_id == row.club_id, ClubRole.status == ClubRoleStatus.active)
    if row.role == ClubRoleKind.owner and await _count(db, *active_here, ClubRole.role == ClubRoleKind.owner):
        raise HTTPException(status_code=409, detail=f"{row.club_name} already has an owner. End their role first.")
    if row.role == ClubRoleKind.editor and await _count(db, *active_here, ClubRole.role == ClubRoleKind.editor) >= settings.MAX_EDITORS_PER_CLUB:
        raise HTTPException(status_code=409, detail=f"{row.club_name} already has {settings.MAX_EDITORS_PER_CLUB} editors (the limit). End one first.")
    elsewhere = [r.club_name for r in target.roles(*STUDENT_TEAM_ROLES) if r.club_id != row.club_id]
    if elsewhere and not exception:
        raise HTTPException(
            status_code=409,
            detail=f"{target.name} is already on {', '.join(elsewhere)}'s team. Approve with a multi-club exception to allow it.",
        )


async def _reject_rival_owner_requests(db: AsyncSession, approved: ClubRole, dsw: User) -> None:
    """A club has one owner: once one is approved, the other pending owner requests can't be."""
    rivals = (await db.execute(select(ClubRole).where(
        ClubRole.club_id == approved.club_id, ClubRole.role == ClubRoleKind.owner,
        ClubRole.status == ClubRoleStatus.pending, ClubRole.id != approved.id,
    ))).scalars().all()
    for r in rivals:
        r.status, r.reviewed_by, r.reviewed_at = ClubRoleStatus.rejected, dsw.id, _now()
        AuditLog.record(db, dsw, "club_role.reject", "club_role", r.id, club=r.club_name,
                        role=r.role.value, reason="another owner was approved")


async def end_roles(db: AsyncSession, user: User, kinds: tuple[ClubRoleKind, ...], actor: User, reason: str) -> None:
    """End this user's active roles of these kinds (and reject pending ones), e.g. on graduation."""
    for r in [r for status in OPEN_STATUSES for r in user.roles(*kinds, status=status)]:
        was_active = r.status == ClubRoleStatus.active
        r.status = ClubRoleStatus.ended if was_active else ClubRoleStatus.rejected
        r.ended_at = _now() if was_active else None
        r.reviewed_by, r.reviewed_at = actor.id, _now()
        AuditLog.record(db, actor, "club_role.end" if was_active else "club_role.reject", "club_role", r.id,
                        club=r.club_name, user=user.email, role=r.role.value, reason=reason)
