from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, or_
from typing import Optional

from app.db.database import get_db
from app.models.club import Club
from app.models.event import Event
from app.models.membership import Registration, SavedEvent
from app.models.user import User
from app.core.deps import get_current_active_user, require_club_member
from app.schemas.event import (
    EventOut, EventPage, EventCreate, EventUpdate, RegistrationStatus, SaveStatus, RegistrantOut,
)

router = APIRouter()

# Fields that can't be cleared with PATCH {"field": null} (the DB columns are NOT NULL)
REQUIRED_FIELDS = {"title", "description", "start_date", "end_date", "date_display", "tags"}


async def _get_event_or_404(db: AsyncSession, event_id: int) -> Event:
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def _get_own_event(db: AsyncSession, event_id: int, user: User) -> Event:
    """The event, if it belongs to the admin's club (same string match as discussions.py)."""
    event = await _get_event_or_404(db, event_id)
    if event.club_name != user.club_name:
        raise HTTPException(status_code=403, detail="You can only manage your own club's events")
    return event


def _check_dates(start: date, end: date) -> None:
    if end < start:
        raise HTTPException(status_code=400, detail="End date can't be before the start date")


def _has_tag(tag: str):
    """Exact match inside the comma-separated tags column: "art" matches "film,art" but not "smart".
    (",film,art," LIKE "%,art,%"; spaces are ignored in case a list was saved as "film, art".)"""
    wrapped = func.concat(",", func.replace(Event.tags, " ", ""), ",")
    return wrapped.contains(f",{tag.strip()},", autoescape=True)


def _int_list(raw: str, name: str) -> list[int]:
    try:
        return [int(x) for x in raw.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{name} must be a comma-separated list of ids")


@router.get("", response_model=EventPage)
async def list_events(
    tag: Optional[str] = Query(None, description="Events with this tag"),
    tags: Optional[str] = Query(None, description="Events with ANY of these comma-separated tags"),
    club_id: Optional[int] = Query(None),
    hot: Optional[bool] = Query(None),
    q: Optional[str] = Query(None, description="Search title, club, description and tags"),
    upcoming: bool = Query(False, description="Only events that haven't ended yet"),
    date_from: Optional[date] = Query(None, description="Events still running on/after this date"),
    date_to: Optional[date] = Query(None, description="Events starting on/before this date"),
    ids: Optional[str] = Query(None, description="Only these comma-separated event ids"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="By start date: asc = soonest first"),
    limit: int = Query(12, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Published events by start date (soonest first by default), one page at a time.
    `total` is the number of matching events across all pages (for "Load more" and counts)."""
    filters = [Event.is_published == True]
    if tag:
        filters.append(_has_tag(tag))
    if tags:
        wanted = [t for t in tags.split(",") if t.strip()]
        if wanted:
            filters.append(or_(*(_has_tag(t) for t in wanted)))
    if club_id:
        filters.append(Event.club_id == club_id)
    if hot is not None:
        filters.append(Event.is_hot == hot)
    if q and q.strip():
        term = q.strip().lower()
        filters.append(or_(*(
            func.lower(col).contains(term, autoescape=True)   # autoescape: a typed % or _ is literal
            for col in (Event.title, Event.club_name, Event.description, Event.tags)
        )))
    if upcoming:
        filters.append(Event.end_date >= date.today())
    # A date range matches every event that overlaps it (multi-day events included)
    if date_from:
        filters.append(Event.end_date >= date_from)
    if date_to:
        filters.append(Event.start_date <= date_to)
    if ids is not None:
        filters.append(Event.id.in_(_int_list(ids, "ids")))

    total = (await db.execute(select(func.count()).select_from(Event).where(*filters))).scalar()
    result = await db.execute(
        select(Event).where(*filters)
        # id breaks ties so pages never overlap or skip
        .order_by(*((Event.start_date, Event.id) if order == "asc" else (Event.start_date.desc(), Event.id.desc())))
        .limit(limit).offset(offset)
    )
    return EventPage(items=[EventOut.model_validate(e) for e in result.scalars().all()], total=total)


@router.get("/{event_id}", response_model=EventOut)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_event_or_404(db, event_id)


@router.post("", response_model=EventOut, status_code=201)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    """Club admins can post events for their own club only."""
    club = (await db.execute(select(Club).where(Club.id == payload.club_id))).scalar_one_or_none()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    if club.name != user.club_name:
        raise HTTPException(status_code=403, detail="You can only post events for your own club")
    _check_dates(payload.start_date, payload.end_date)

    event = Event(
        title=payload.title,
        description=payload.description,
        club_id=payload.club_id,
        club_name=club.name,
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
    """Club admins can edit their own club's events. Only the fields sent are changed."""
    event = await _get_own_event(db, event_id, user)
    data = payload.model_dump(exclude_unset=True)
    cleared = sorted(k for k in REQUIRED_FIELDS if k in data and data[k] is None)
    if cleared:
        raise HTTPException(status_code=400, detail=f"These fields can't be empty: {', '.join(cleared)}")
    if "tags" in data:
        if not data["tags"]:
            raise HTTPException(status_code=400, detail="Select at least one tag")
        data["tags"] = ",".join(data["tags"])
    _check_dates(data.get("start_date", event.start_date), data.get("end_date", event.end_date))

    for k, v in data.items():
        setattr(event, k, v)
    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    """Club admins can delete their own club's events.
    The DB cascades remove its registrations, saves, discussions and notifications.
    (A bulk delete, not db.delete(event): the ORM version would try to lazy-load
    those relationships, which async SQLAlchemy can't do.)
    """
    await _get_own_event(db, event_id, user)
    await db.execute(delete(Event).where(Event.id == event_id))
    await db.commit()


# ── Registration ─────────────────────────────────────────
@router.post("/{event_id}/register", response_model=RegistrationStatus)
async def register_for_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    event = await _get_event_or_404(db, event_id)
    # Registration stays open through the deadline day itself (matches the event page)
    if event.reg_deadline and event.reg_deadline < date.today():
        raise HTTPException(status_code=400, detail="Registration for this event has closed")
    existing = await db.execute(
        select(Registration).where(Registration.user_id == user.id, Registration.event_id == event_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already registered")
    db.add(Registration(user_id=user.id, event_id=event_id))
    await db.commit()
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


@router.get("/{event_id}/registrations", response_model=list[RegistrantOut])
async def list_registrations(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    """Who registered for one of the admin's own events (newest first; the UI can re-sort)."""
    await _get_own_event(db, event_id, user)
    rows = (await db.execute(
        select(User, Registration.registered_at)
        .join(Registration, Registration.user_id == User.id)
        .where(Registration.event_id == event_id)
        .order_by(Registration.registered_at.desc())
    )).all()
    return [
        RegistrantOut(
            user_id=u.id, name=u.name, email=u.email, phone=u.phone,
            reg_no=u.reg_no, course=u.course, registered_at=at,
        )
        for u, at in rows
    ]


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
