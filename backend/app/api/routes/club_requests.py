# New club requests. Mounted at /api/club-requests:
#   POST /            a student proposes a club
#   GET  /mine        the student's own requests
#   GET  /for-me      faculty: requests naming them as coordinator (they confirm first)
#   GET  /            the DSW's queue (awaiting_dsw by default)
#   PATCH /{id}       confirm / decline (the named coordinator), approve / reject (the DSW)

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_or_404, get_current_active_user, require_dsw
from app.core.governance import approve_club_request, on_other_team
from app.db.database import get_db
from app.models.audit import AuditLog
from app.models.club import Club, ClubRequest, ClubRequestStatus, OPEN_CLUB_REQUEST_STATUSES
from app.models.notification import Notification
from app.models.user import User, AccountType
from app.schemas.event import (
    ClubRequestIn, ClubRequestOut, ClubRequestPage, ClubRequestDecision, ClubRequestResult,
)

router = APIRouter()
S = ClubRequestStatus


async def _out(db: AsyncSession, rows: list[ClubRequest], show_phone: bool) -> list[ClubRequestOut]:
    """With the requester's name and whether the coordinator has an account yet."""
    people = {u.id: u for u in (await db.execute(
        select(User).where(User.id.in_({r.requested_by for r in rows}))
    )).scalars().all()} if rows else {}
    signed_up = set((await db.execute(
        select(User.email).where(User.email.in_({r.coordinator_email for r in rows}))
    )).scalars().all()) if rows else set()
    return [ClubRequestOut(
        id=r.id, status=r.status.value, name=r.name, abbr=r.abbr, description=r.description, tags=r.tags,
        instagram=r.instagram, linkedin=r.linkedin, affiliation=r.affiliation, purpose=r.purpose, plans=r.plans,
        founding_emails=r.founding_emails, coordinator_email=r.coordinator_email,
        coordinator_signed_up=r.coordinator_email in signed_up,
        contact_phone=r.contact_phone if show_phone else None,
        requester_name=people[r.requested_by].name, requester_email=people[r.requested_by].email,
        decision_note=r.decision_note, club_id=r.club_id, created_at=r.created_at, updated_at=r.updated_at,
    ) for r in rows]


async def _dsw_ids(db: AsyncSession) -> list[int]:
    return list((await db.execute(
        select(User.id).where(User.account_type == AccountType.dsw, User.is_active == True)  # noqa: E712
    )).scalars().all())


@router.post("", response_model=ClubRequestOut, status_code=201)
async def request_club(
    payload: ClubRequestIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    if user.account_type != AccountType.student:
        raise HTTPException(status_code=403, detail="Only students can propose a new club")
    if elsewhere := on_other_team(user):
        raise HTTPException(status_code=400, detail=f"You already run {', '.join(elsewhere)}")
    if settings.account_kind_for(payload.coordinator_email) != "faculty":
        raise HTTPException(status_code=400, detail="The faculty coordinator needs a faculty email "
                            f"({', '.join('@' + d for d in settings.email_domains['faculty'])})")
    founders = list(dict.fromkeys(e for e in payload.founding_emails if e != user.email))
    if any(settings.account_kind_for(e) != "student" for e in founders):
        raise HTTPException(status_code=400, detail="The founding team must be students (college student emails)")
    if len(founders) < 2:
        raise HTTPException(status_code=400, detail="Name at least two other students for the founding team")
    if (await db.execute(select(Club.id).where(func.lower(Club.name) == payload.name.lower()))).first():
        raise HTTPException(status_code=400, detail="A club with this name already exists")
    open_mine = (await db.execute(select(ClubRequest.id).where(
        ClubRequest.requested_by == user.id, ClubRequest.status.in_(OPEN_CLUB_REQUEST_STATUSES)))).first()
    if open_mine:
        raise HTTPException(status_code=400, detail="You already have a club request in progress")

    req = ClubRequest(requested_by=user.id, **payload.model_dump(exclude={"tags", "founding_emails"}),
                      tags=",".join(payload.tags), founding_emails=",".join(founders))
    db.add(req)
    await db.flush()
    AuditLog.record(db, user, "club_request.submit", "club_request", req.id, name=req.name,
                    coordinator=req.coordinator_email)
    coordinator = (await db.execute(select(User).where(User.email == req.coordinator_email))).scalar_one_or_none()
    if coordinator:
        Notification.send(db, [coordinator.id], "club_request",
                          f"{user.name} named you faculty coordinator of a proposed club, {req.name}. Please confirm or decline.")
    await db.commit()
    return (await _out(db, [req], show_phone=True))[0]


@router.get("/mine", response_model=list[ClubRequestOut])
async def my_club_requests(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    rows = (await db.execute(select(ClubRequest).where(ClubRequest.requested_by == user.id)
                             .order_by(ClubRequest.id.desc()))).scalars().all()
    return await _out(db, rows, show_phone=True)


@router.get("/for-me", response_model=list[ClubRequestOut])
async def requests_naming_me(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_active_user)):
    """Faculty: every request that names them as coordinator, newest first."""
    rows = (await db.execute(select(ClubRequest).where(ClubRequest.coordinator_email == user.email)
                             .order_by(ClubRequest.id.desc()))).scalars().all()
    return await _out(db, rows, show_phone=False)


@router.get("", response_model=ClubRequestPage)
async def club_request_queue(
    status: Optional[ClubRequestStatus] = Query(ClubRequestStatus.awaiting_dsw),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_dsw),
):
    filters = [ClubRequest.status == status] if status else []
    total = (await db.execute(select(func.count()).select_from(ClubRequest).where(*filters))).scalar()
    rows = (await db.execute(select(ClubRequest).where(*filters)
                             .order_by(ClubRequest.created_at, ClubRequest.id).limit(limit).offset(offset))).scalars().all()
    return ClubRequestPage(items=await _out(db, rows, show_phone=True), total=total)


@router.patch("/{request_id}", response_model=ClubRequestResult)
async def decide_club_request(
    request_id: int,
    payload: ClubRequestDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    req = await get_or_404(db, ClubRequest, request_id)
    requester = await get_or_404(db, User, req.requested_by)

    if payload.action in ("confirm", "decline"):
        if user.email != req.coordinator_email or user.account_type != AccountType.faculty:
            raise HTTPException(status_code=403, detail="Only the faculty coordinator named in the request can do this")
        if req.status != S.awaiting_coordinator:
            raise HTTPException(status_code=400, detail="This request isn't waiting for the coordinator")
        req.coordinator_id, req.decision_note = user.id, payload.note
        if payload.action == "confirm":
            req.status = S.awaiting_dsw
            Notification.send(db, await _dsw_ids(db), "club_request", f"New club proposed: {req.name}, confirmed by {user.name}.")
            Notification.send(db, [requester.id], "club_request", f"{user.name} confirmed {req.name}. It's with the DSW now.")
        else:
            req.status = S.declined
            Notification.send(db, [requester.id], "club_request", f"{user.name} declined to coordinate {req.name}.")
        AuditLog.record(db, user, f"club_request.{payload.action}", "club_request", req.id, name=req.name)
        await db.commit()
        return ClubRequestResult()

    if user.account_type != AccountType.dsw:
        raise HTTPException(status_code=403, detail="Only the DSW approves new clubs")
    if req.status != S.awaiting_dsw:
        raise HTTPException(status_code=400, detail="This request isn't waiting for the DSW")
    req.decision_note = payload.note
    if payload.action == "approve":
        club, skipped = await approve_club_request(db, req, requester, user)
        await db.commit()
        return ClubRequestResult(club_id=club.id, skipped=skipped)
    req.status, req.reviewed_by = S.rejected, user.id
    AuditLog.record(db, user, "club_request.reject", "club_request", req.id, name=req.name)
    Notification.send(db, [requester.id], "club_request",
                      f"The DSW didn't approve {req.name}." + (f" {payload.note}" if payload.note else ""))
    await db.commit()
    return ClubRequestResult()
