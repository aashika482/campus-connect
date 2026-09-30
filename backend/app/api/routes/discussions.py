import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import get_db
from app.models.discussion import Discussion
from app.models.event import Event
from app.models.notification import Notification
from app.models.user import User, UserRole
from app.core.deps import get_current_active_user, require_club_member
from app.schemas.event import (
    DiscussionOut, DiscussionPage, DiscussionCreate, DiscussionReply, DiscussionUpdate,
)

router = APIRouter()

# Authors can edit a comment/reply for this long after posting.
# The frontend mirrors this value in EventDetailPage.tsx (EDIT_WINDOW_MINUTES).
EDIT_WINDOW_MINUTES = 15


# ── Helpers ──────────────────────────────────────────────
async def _get_event_or_404(db: AsyncSession, event_id: int) -> Event:
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def _attach_replies(db: AsyncSession, comments: list[Discussion]) -> None:
    """Load replies for the given top-level comments in ONE query and attach them.

    Replies use lazy="noload", so we fill .replies by hand. Every reply also gets
    .replies = [] so Pydantic never tries to lazy-load (MissingGreenlet error).
    """
    if not comments:
        return
    result = await db.execute(
        select(Discussion)
        .where(Discussion.parent_id.in_([c.id for c in comments]))
        .order_by(Discussion.created_at.asc())
    )
    reply_map: dict[int, list[Discussion]] = {}
    for r in result.scalars().all():
        r.replies = []
        reply_map.setdefault(r.parent_id, []).append(r)
    for c in comments:
        c.replies = reply_map.get(c.id, [])


async def _paginate_top_level(db: AsyncSession, base_filter, before_id: Optional[int], limit: int) -> DiscussionPage:
    """Newest-first page of top-level comments matching base_filter.

    Uses the last seen id as a cursor (before_id) instead of an offset, so comments
    posted while someone is reading don't shift the pages and cause duplicates.
    """
    total = (await db.execute(
        select(func.count()).select_from(Discussion).join(Event, Discussion.event_id == Event.id)
        .where(base_filter, Discussion.parent_id == None)
    )).scalar()

    q = (
        select(Discussion)
        .join(Event, Discussion.event_id == Event.id)
        .where(base_filter, Discussion.parent_id == None)
        .order_by(Discussion.id.desc())
        .limit(limit)
    )
    if before_id is not None:
        q = q.where(Discussion.id < before_id)
    comments = list((await db.execute(q)).scalars().all())

    await _attach_replies(db, comments)
    return DiscussionPage(items=[DiscussionOut.model_validate(c) for c in comments], total=total)


def _is_club_admin_of(user: User, event: Event) -> bool:
    return user.role == UserRole.member and user.club_name == event.club_name


def _short(text: str, n: int = 80) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


async def _mentioned_user_ids(db: AsyncSession, event_id: int, content: str) -> set[int]:
    """Find who is @mentioned in `content`.

    Only people who have already posted in this event's discussion can be mentioned
    (that's where the UI's "@Name " prefill comes from), so @Jacob here never pings
    an unrelated Jacob elsewhere in the app. Names can contain spaces ("@John Kurian"),
    so we check each participant's name instead of splitting on whitespace.
    """
    rows = (await db.execute(
        select(Discussion.user_id, Discussion.user_name)
        .where(Discussion.event_id == event_id)
        .distinct()
    )).all()

    ids_by_name: dict[str, set[int]] = {}
    for user_id, user_name in rows:
        name = user_name.strip()
        if name:
            ids_by_name.setdefault(name.lower(), set()).add(user_id)

    found: set[int] = set()
    text = content
    # Longest names first, and cut each match out, so "@John Kurian" doesn't also match "@John"
    for name in sorted(ids_by_name, key=len, reverse=True):
        pattern = re.compile("@" + re.escape(name) + r"(?!\w)", re.IGNORECASE)
        if pattern.search(text):
            found |= ids_by_name[name]
            text = pattern.sub(" ", text)
    return found


def _add_mention_notifications(
    db: AsyncSession, user_ids: set[int], author: User, event: Event, discussion_id: int,
) -> None:
    for uid in user_ids:
        db.add(Notification(
            user_id=uid,
            kind="mention",
            message=f"{_short(author.name, 40)} mentioned you on {_short(event.title)}",
            event_id=event.id,
            discussion_id=discussion_id,
        ))


# ── Routes ───────────────────────────────────────────────
# IMPORTANT: /admin/feed must be declared BEFORE /{event_id} so FastAPI
# doesn't try to parse "admin" as an integer event_id.
@router.get("/admin/feed", response_model=DiscussionPage)
async def admin_discussion_feed(
    before_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    """Paginated top-level comments (with their replies) across all of the admin's club events."""
    return await _paginate_top_level(db, Event.club_name == user.club_name, before_id, limit)


@router.get("/{event_id}", response_model=DiscussionPage)
async def list_discussions(
    event_id: int,
    before_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Paginated top-level comments for an event, newest first, with replies nested (oldest first)."""
    return await _paginate_top_level(db, Discussion.event_id == event_id, before_id, limit)


@router.post("/{event_id}", response_model=DiscussionOut, status_code=201)
async def create_discussion(
    event_id: int,
    payload: DiscussionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Any logged-in user can post a top-level comment.
    Anyone @mentioned gets a "mention" notification; the event's other club admins get a "comment" one.
    """
    event = await _get_event_or_404(db, event_id)

    discussion = Discussion(
        event_id=event_id,
        user_id=user.id,
        user_name=user.name,
        user_role=user.role.value,
        is_official=_is_club_admin_of(user, event),
        content=payload.content,
        parent_id=None,
    )
    db.add(discussion)
    await db.flush()  # assigns discussion.id so notifications can point at it

    mentioned = await _mentioned_user_ids(db, event_id, payload.content) - {user.id}
    _add_mention_notifications(db, mentioned, user, event, discussion.id)

    admin_ids = set((await db.execute(
        select(User.id).where(
            User.role == UserRole.member,
            User.club_name == event.club_name,
            User.is_active == True,
            User.id != user.id,
        )
    )).scalars().all())
    for admin_id in admin_ids - mentioned:  # mentioned admins already got a notification
        db.add(Notification(
            user_id=admin_id,
            kind="comment",
            message=f"{_short(user.name, 40)} commented on {_short(event.title)}",
            event_id=event_id,
            discussion_id=discussion.id,
        ))

    await db.commit()
    await db.refresh(discussion)
    discussion.replies = []  # prevent lazy-load during serialization
    return discussion


@router.post("/{event_id}/{comment_id}/reply", response_model=DiscussionOut, status_code=201)
async def reply_to_discussion(
    event_id: int,
    comment_id: int,
    payload: DiscussionReply,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Any logged-in user can reply to a top-level comment (one level deep only).
    The comment's author gets a "reply" notification (unless replying to themselves),
    and anyone else @mentioned gets a "mention" notification.
    """
    event = await _get_event_or_404(db, event_id)

    result = await db.execute(
        select(Discussion).where(Discussion.id == comment_id, Discussion.event_id == event_id)
    )
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Comment not found")
    if parent.parent_id is not None:
        raise HTTPException(status_code=400, detail="Replies can only be one level deep")

    reply = Discussion(
        event_id=event_id,
        user_id=user.id,
        user_name=user.name,
        user_role=user.role.value,
        is_official=_is_club_admin_of(user, event),
        content=payload.content,
        parent_id=comment_id,
    )
    db.add(reply)
    await db.flush()

    if parent.user_id != user.id:
        db.add(Notification(
            user_id=parent.user_id,
            kind="reply",
            message=f"{_short(user.name, 40)} replied to your comment on {_short(event.title)}",
            event_id=event_id,
            discussion_id=reply.id,
        ))

    # The parent's author already got a "reply" notification above
    mentioned = await _mentioned_user_ids(db, event_id, payload.content) - {user.id, parent.user_id}
    _add_mention_notifications(db, mentioned, user, event, reply.id)

    await db.commit()
    await db.refresh(reply)
    reply.replies = []  # replies are second-level; no sub-replies
    return reply


@router.patch("/{event_id}/{comment_id}", response_model=DiscussionOut)
async def edit_discussion(
    event_id: int,
    comment_id: int,
    payload: DiscussionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Authors can edit their own comment or reply within EDIT_WINDOW_MINUTES of posting.
    Admins can't edit other people's comments (they can only delete them).
    Newly added @mentions notify people who haven't been notified about this comment yet.
    """
    result = await db.execute(
        select(Discussion).where(Discussion.id == comment_id, Discussion.event_id == event_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    if datetime.now(timezone.utc) - comment.created_at > timedelta(minutes=EDIT_WINDOW_MINUTES):
        raise HTTPException(status_code=403, detail=f"Comments can only be edited within {EDIT_WINDOW_MINUTES} minutes of posting")

    comment.content = payload.content
    comment.edited_at = datetime.now(timezone.utc)

    # Skip anyone already notified about this comment, so fixing a typo doesn't re-ping people
    already_notified = set((await db.execute(
        select(Notification.user_id).where(Notification.discussion_id == comment.id)
    )).scalars().all())
    mentioned = await _mentioned_user_ids(db, event_id, payload.content) - {user.id} - already_notified
    if mentioned:
        event = await _get_event_or_404(db, event_id)
        _add_mention_notifications(db, mentioned, user, event, comment.id)

    await db.commit()
    await db.refresh(comment)
    comment.replies = []  # frontend keeps its existing replies; this just prevents lazy-load
    return comment


@router.delete("/{event_id}/{comment_id}", status_code=204)
async def delete_discussion(
    event_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Club admins can delete any comment on their own club's events.
    Students can only delete their own comments.
    Deleting a parent comment cascades to all its replies (and their notifications).
    """
    result = await db.execute(
        select(Discussion).where(Discussion.id == comment_id, Discussion.event_id == event_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    is_own = user.id == comment.user_id
    if user.role == UserRole.member:
        # Admins can only moderate events belonging to their own club
        event_result = await db.execute(select(Event).where(Event.id == event_id))
        event = event_result.scalar_one_or_none()
        is_own_club = event is not None and event.club_name == user.club_name
        if not is_own_club and not is_own:
            raise HTTPException(status_code=403, detail="You can only delete comments on your own club's events")
    else:
        # Students can only delete their own comments
        if not is_own:
            raise HTTPException(status_code=403, detail="Not allowed to delete this comment")

    await db.delete(comment)
    await db.commit()
