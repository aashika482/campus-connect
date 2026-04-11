# backend/app/api/routes/events.py
# REPLACE your existing file with this
# Changes: added /{event_id}/registrations/count endpoint, updated create_event for new fields

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.db.database import get_db
from app.models.event import Event
from app.models.membership import Registration, SavedEvent
from app.models.user import User
from app.core.deps import get_current_active_user, require_club_member
from app.schemas.event import EventOut, EventCreate, EventUpdate, RegistrationStatus, SaveStatus

router = APIRouter()


@router.get("", response_model=list[EventOut])
async def list_events(
    tag: Optional[str] = Query(None),
    club_id: Optional[int] = Query(None),
    hot: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Event).where(Event.is_published == True).order_by(Event.start_date)
    if tag:
        q = q.where(Event.tags.contains(tag))
    if club_id:
        q = q.where(Event.club_id == club_id)
    if hot is not None:
        q = q.where(Event.is_hot == hot)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("", response_model=EventOut, status_code=201)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    event = Event(
        title=payload.title,
        description=payload.description,
        club_id=payload.club_id,
        club_name=user.club_name or "",
        start_date=payload.start_date,
        end_date=payload.end_date,
        reg_deadline=payload.reg_deadline,
        date_display=payload.date_display,
        tags=",".join(payload.tags),
        team_size=payload.team_size,
        poster_url=payload.poster_url,
        is_hot=payload.is_hot,
        venue=payload.venue,
        time_info=payload.time_info,
        registration_fee=payload.registration_fee,
        prize_pool=payload.prize_pool,
        contact_info=payload.contact_info,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.patch("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    data = payload.model_dump(exclude_unset=True)
    if "tags" in data:
        data["tags"] = ",".join(data["tags"])
    for k, v in data.items():
        setattr(event, k, v)
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    await db.execute(delete(Event).where(Event.id == event_id))


# ── Registration ─────────────────────────────────────────
@router.post("/{event_id}/register", response_model=RegistrationStatus)
async def register_for_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    existing = await db.execute(
        select(Registration).where(Registration.user_id == user.id, Registration.event_id == event_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already registered")
    db.add(Registration(user_id=user.id, event_id=event_id))
    return RegistrationStatus(event_id=event_id, is_registered=True)


@router.delete("/{event_id}/register", response_model=RegistrationStatus)
async def unregister_from_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await db.execute(
        delete(Registration).where(Registration.user_id == user.id, Registration.event_id == event_id)
    )
    return RegistrationStatus(event_id=event_id, is_registered=False)


@router.get("/me/registered", response_model=list[int])
async def my_registrations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Registration.event_id).where(Registration.user_id == user.id)
    )
    return [r for r in result.scalars().all()]


# ── Registration count (for event detail + admin dashboard) ──
@router.get("/{event_id}/registrations/count")
async def registration_count(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.count()).select_from(Registration).where(Registration.event_id == event_id)
    )
    count = result.scalar()
    return {"event_id": event_id, "count": count}


# ── Saved ────────────────────────────────────────────────
@router.post("/{event_id}/save", response_model=SaveStatus)
async def save_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    existing = await db.execute(
        select(SavedEvent).where(SavedEvent.user_id == user.id, SavedEvent.event_id == event_id)
    )
    if not existing.scalar_one_or_none():
        db.add(SavedEvent(user_id=user.id, event_id=event_id))
    return SaveStatus(event_id=event_id, is_saved=True)


@router.delete("/{event_id}/save", response_model=SaveStatus)
async def unsave_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await db.execute(
        delete(SavedEvent).where(SavedEvent.user_id == user.id, SavedEvent.event_id == event_id)
    )
    return SaveStatus(event_id=event_id, is_saved=False)


@router.get("/me/saved", response_model=list[int])
async def my_saved_events(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(SavedEvent.event_id).where(SavedEvent.user_id == user.id)
    )
    return [r for r in result.scalars().all()]
