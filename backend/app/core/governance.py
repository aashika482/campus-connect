# Club team rules, shared by the club routes (requests, proposals) and the DSW routes
# (reviews, faculty assignment, account-type changes). Every rule lives here once:
#   - only students hold owner / editor roles; only faculty are faculty coordinators
#   - a club has one owner and at most settings.MAX_EDITORS_PER_CLUB editors
#   - a student is on one club's team at a time unless the DSW grants an exception
#   - a person has at most one pending owner/editor request at a time
#   - ending a role keeps the row (status "ended") as the club's history
#   - memberships are yearly: they end on the academic year's last day (31 July)
#   - working-team applications: owner/editors shortlist and recommend, the faculty coordinator approves;
#     a club's working_multi_club setting decides whether its working members may work for other clubs too

from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.club import Club, ClubRequest, ClubRequestStatus
from app.models.membership import (
    ClubRole, ClubRoleKind, ClubRoleStatus, OPEN_STATUSES, STUDENT_TEAM_ROLES,
    ClubApplication, ApplicationStatus, OPEN_APPLICATION_STATUSES, LeaveRequest, LeaveScope, LeaveStatus,
)
from app.models.notification import Notification
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


async def end_roles(db: AsyncSession, user: User, kinds: tuple[ClubRoleKind, ...], actor: User, reason: str,
                    club_id: int | None = None) -> None:
    """End this user's active roles of these kinds (and reject pending ones), e.g. on graduation;
    only in one club when club_id is given."""
    for r in [r for status in OPEN_STATUSES for r in user.roles(*kinds, status=status)
              if club_id is None or r.club_id == club_id]:
        was_active = r.status == ClubRoleStatus.active
        r.status = ClubRoleStatus.ended if was_active else ClubRoleStatus.rejected
        r.ended_at = _now() if was_active else None
        r.reviewed_by, r.reviewed_at = actor.id, _now()
        AuditLog.record(db, actor, "club_role.end" if was_active else "club_role.reject", "club_role", r.id,
                        club=r.club_name, user=user.email, role=r.role.value, reason=reason)


# ── Yearly memberships ───────────────────────────────────
ACADEMIC_YEAR_END = (7, 31)   # month, day: memberships run until 31 July


def membership_end(today: date | None = None) -> date:
    """The last day of the academic year that `today` falls in."""
    today = today or date.today()
    end = date(today.year, *ACADEMIC_YEAR_END)
    return end if today <= end else date(today.year + 1, *ACADEMIC_YEAR_END)


def close_lapsed(user: User, club_id: int, kind: ClubRoleKind) -> bool:
    """Mark this user's lapsed yearly role in the club as ended (it ended with its academic year), so a
    new year's row can be opened. Returns whether there was one, i.e. this is a renewal."""
    lapsed = [r for r in user.club_roles if r.club_id == club_id and r.role == kind
              and r.status == ClubRoleStatus.active and r.is_expired]
    for r in lapsed:
        r.status = ClubRoleStatus.ended
        r.ended_at = datetime.combine(r.expires_on + timedelta(days=1), datetime.min.time(), timezone.utc)
    return bool(lapsed)


# ── Working-team applications ────────────────────────────
def working_conflict(user: User, club: Club) -> str | None:
    """Why `user` can't be on `club`'s working team because of working teams elsewhere, if they can't."""
    others = [r for r in user.roles(ClubRoleKind.working_member) if r.club_id != club.id]
    if not others:
        return None
    if not club.working_multi_club:
        return (f"{club.name}'s working members can't be on other clubs' working teams, "
                f"and {user.name} is on {', '.join(r.club_name for r in others)}'s")
    strict = [r.club_name for r in others if not r.club.working_multi_club]
    if strict:
        return f"{', '.join(strict)} doesn't let its working members join other clubs' working teams"
    return None


def lapsed_working_member(user: User, club_id: int) -> bool:
    """Was on this club's working team in a past academic year (and not ended for another reason)."""
    return any(r.club_id == club_id and r.role == ClubRoleKind.working_member
               and r.status == ClubRoleStatus.active and r.is_expired for r in user.club_roles)


def application_block(user: User, club: Club, open_app: ClubApplication | None) -> str | None:
    """Why this user can't apply to the club's working team right now (None: they can)."""
    if user.account_type != AccountType.student or not user.is_active:
        return "Only students can apply to a club's working team"
    if user.is_working_member_of(club.id):
        return "You're already on the working team"
    if open_app is not None:
        return "Your application is being reviewed"
    if not user.is_member_of(club.id):
        return "Join the club for this academic year first"
    if not club.recruiting and not lapsed_working_member(user, club.id):
        return f"{club.name} isn't recruiting right now"
    return working_conflict(user, club)


def coordinator_ids(club_roles: list[ClubRole]) -> list[int]:
    return [r.user_id for r in club_roles if r.role == ClubRoleKind.faculty_coordinator and r.is_current]


async def act_on_application(db: AsyncSession, app: ClubApplication, club: Club, applicant: User,
                             actor: User, action: str) -> None:
    """Owner/editors: shortlist, recommend, decline. A faculty coordinator: approve or decline a
    recommended one. Approving makes the applicant a working member."""
    club_team_rows = (await db.execute(select(ClubRole).where(ClubRole.club_id == club.id))).scalars().all()
    coordinators = coordinator_ids(club_team_rows)
    is_lead = any(r.club_id == club.id for r in actor.roles(*STUDENT_TEAM_ROLES))
    is_approver = actor.id in coordinators

    S = ApplicationStatus
    allowed = {
        "shortlist": is_lead and app.status == S.applied,
        "recommend": is_lead and app.status in (S.applied, S.shortlisted),
        "approve":   is_approver and app.status == S.recommended,
        "decline":   (is_lead and app.status in (S.applied, S.shortlisted))
                     or (is_approver and app.status == S.recommended),
    }[action]
    if not allowed:
        if app.status not in OPEN_APPLICATION_STATUSES:
            raise HTTPException(status_code=400, detail=f"This application is already {app.status.value}")
        who = ("the faculty coordinator" if action == "approve" or app.status == S.recommended
               else "the club's owner or editors")
        raise HTTPException(status_code=403, detail=f"Only {who} can {action} this application now")

    if action == "approve":
        if not applicant.is_active or applicant.account_type != AccountType.student or not applicant.is_member_of(club.id):
            raise HTTPException(status_code=409, detail=f"{applicant.name} is no longer a current student member of {club.name}")
        if conflict := working_conflict(applicant, club):
            raise HTTPException(status_code=409, detail=conflict)
        close_lapsed(applicant, club.id, ClubRoleKind.working_member)
        db.add(ClubRole(user_id=applicant.id, club_id=club.id, role=ClubRoleKind.working_member,
                        status=ClubRoleStatus.active, expires_on=membership_end(),
                        proposed_by=app.reviewed_by, reviewed_by=actor.id, reviewed_at=_now()))

    # The coordinator's call on a recommendation is the decision; everything before it is the review
    if app.status == S.recommended:
        app.decided_by = actor.id
    else:
        app.reviewed_by = actor.id
    app.status = {"shortlist": S.shortlisted, "recommend": S.recommended,
                  "approve": S.accepted, "decline": S.declined}[action]
    AuditLog.record(db, actor, f"application.{action}", "club_application", app.id,
                    club=club.name, user=applicant.email, renewal=app.is_renewal or None)

    if action == "recommend":
        Notification.send(db, coordinators, "app_review",
                          f"{applicant.name} is recommended for {club.name}'s working team. Approve or decline.",
                          club_id=club.id)
    elif app.status in (S.shortlisted, S.accepted, S.declined):
        Notification.send(db, [applicant.id], "application", {
            S.shortlisted: f"{club.name} shortlisted your working-team application. Expect an interview call.",
            S.accepted: f"You're on {club.name}'s working team!",
            S.declined: f"{club.name} didn't take your working-team application this time. You stay a member.",
        }[app.status], club_id=club.id)


# ── Leaving a club (the DSW approves) ────────────────────
LEAVABLE = {
    LeaveScope.working_team: (ClubRoleKind.working_member,),
    LeaveScope.club: (ClubRoleKind.member, ClubRoleKind.working_member, ClubRoleKind.owner, ClubRoleKind.editor),
}


def leave_block(user: User, club_id: int, scope: LeaveScope) -> str | None:
    """Why this user can't ask to leave in this way (None: they can)."""
    if scope == LeaveScope.working_team and not user.is_working_member_of(club_id):
        return "You're not on this club's working team"
    if not any(r.club_id == club_id for r in user.roles(*LEAVABLE[LeaveScope.club])):
        return ("Faculty coordinators are assigned by the DSW; ask the DSW directly"
                if any(r.club_id == club_id for r in user.roles(ClubRoleKind.faculty_coordinator))
                else "You're not in this club")
    return None


async def review_leave(db: AsyncSession, req: LeaveRequest, leaver: User, club: Club, action: str, dsw: User) -> None:
    """approve: end the roles the request covers (leaving the club also withdraws open applications); or reject."""
    if req.status != LeaveStatus.pending:
        raise HTTPException(status_code=400, detail=f"This request is already {req.status.value}")
    if action == "approve":
        await end_roles(db, leaver, LEAVABLE[req.scope], dsw, reason=f"leave request {req.id}", club_id=club.id)
        if req.scope == LeaveScope.club:
            for app in (await db.execute(select(ClubApplication).where(
                ClubApplication.user_id == leaver.id, ClubApplication.club_id == club.id,
                ClubApplication.status.in_(OPEN_APPLICATION_STATUSES),
            ))).scalars().all():
                app.status, app.decided_by = ApplicationStatus.declined, dsw.id
    req.status = LeaveStatus.approved if action == "approve" else LeaveStatus.rejected
    req.reviewed_by, req.reviewed_at = dsw.id, _now()
    AuditLog.record(db, dsw, f"leave.{action}", "leave_request", req.id, club=club.name, user=leaver.email,
                    scope=req.scope.value)
    what = "the working team of " if req.scope == LeaveScope.working_team else ""
    Notification.send(db, [leaver.id], "leave", (
        f"The DSW approved your request: you've left {what}{club.name}." if action == "approve"
        else f"The DSW didn't approve your request to leave {what}{club.name}."), club_id=club.id)


# ── New club requests ────────────────────────────────────
CLUB_COLORS = ("#3B82F6", "#EF4444", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316", "#22C55E", "#A855F7")


def on_other_team(user: User, club_id: int | None = None) -> list[str]:
    """Clubs where this student is owner or editor (other than club_id)."""
    return [r.club_name for r in user.roles(*STUDENT_TEAM_ROLES) if r.club_id != club_id]


async def approve_club_request(db: AsyncSession, req: ClubRequest, requester: User, dsw: User) -> tuple[Club, list[str]]:
    """Create the club: the requester owns it, the coordinator is assigned, the founding team become editors
    (each one who has a student account and isn't on another club's team, up to the editor limit).
    Returns the club and the founding members who couldn't be added, with why."""
    if (await db.execute(select(Club.id).where(func.lower(Club.name) == req.name.lower()))).first():
        raise HTTPException(status_code=409, detail=f"A club named {req.name} already exists")
    if requester.account_type != AccountType.student or not requester.is_active:
        raise HTTPException(status_code=409, detail=f"{requester.name} is no longer an active student account")
    if elsewhere := on_other_team(requester):
        raise HTTPException(status_code=409, detail=f"{requester.name} already runs {', '.join(elsewhere)}. End that role first.")
    coordinator = (await db.execute(select(User).where(User.email == req.coordinator_email))).scalar_one_or_none()
    if coordinator is None or coordinator.account_type != AccountType.faculty:
        raise HTTPException(status_code=409, detail="The faculty coordinator's account isn't a faculty account any more")

    club = Club(name=req.name, abbr=req.abbr, description=req.description, tags=req.tags,
                instagram=req.instagram, linkedin=req.linkedin,
                color=CLUB_COLORS[sum(map(ord, req.name)) % len(CLUB_COLORS)])
    db.add(club)
    await db.flush()
    year_end, now = membership_end(), _now()

    def grant(user: User, role: ClubRoleKind, **extra) -> None:
        db.add(ClubRole(user_id=user.id, club_id=club.id, role=role, status=ClubRoleStatus.active,
                        proposed_by=requester.id, reviewed_by=dsw.id, reviewed_at=now, **extra))

    grant(requester, ClubRoleKind.owner, title="Founder")
    grant(requester, ClubRoleKind.member, expires_on=year_end)
    grant(coordinator, ClubRoleKind.faculty_coordinator)

    skipped: list[str] = []
    editors = 0
    for email in [e for e in req.founding_emails.split(",") if e and e != requester.email]:
        founder = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        why = ("hasn't signed up yet" if founder is None
               else "isn't a student account" if founder.account_type != AccountType.student or not founder.is_active
               else f"already runs {', '.join(on_other_team(founder))}" if on_other_team(founder)
               else f"the club already has {settings.MAX_EDITORS_PER_CLUB} editors" if editors >= settings.MAX_EDITORS_PER_CLUB
               else None)
        if why:
            skipped.append(f"{email}: {why}")
            continue
        grant(founder, ClubRoleKind.editor, title="Founding member")
        grant(founder, ClubRoleKind.member, expires_on=year_end)
        editors += 1
        Notification.send(db, [founder.id], "club_request", f"{club.name} is approved. You're one of its founding editors.", club_id=club.id)

    req.status, req.club_id, req.reviewed_by = ClubRequestStatus.approved, club.id, dsw.id
    AuditLog.record(db, dsw, "club_request.approve", "club_request", req.id, club=club.name,
                    owner=requester.email, coordinator=coordinator.email, skipped=skipped or None)
    Notification.send(db, [requester.id, coordinator.id], "club_request",
                      f"The DSW approved {club.name}. It's live on the portal.", club_id=club.id)
    return club, skipped
