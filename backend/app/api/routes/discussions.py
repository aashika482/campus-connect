from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.discussion import Discussion
from app.models.event import Event
from app.models.user import User
from app.core.deps import get_current_active_user, require_club_member
from app.schemas.event import DiscussionOut, DiscussionCreate, DiscussionReply

router = APIRouter()


# IMPORTANT: /admin/feed must be declared BEFORE /{event_id} so FastAPI
# doesn't try to parse "admin" as an integer event_id.
@router.get("/admin/feed", response_model=list[DiscussionOut])
async def admin_discussion_feed(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_club_member),
):
    """Get all recent top-level discussions across all events for the admin's club."""
    result = await db.execute(
        select(Discussion)
        .join(Event, Discussion.event_id == Event.id)
        .where(Event.club_name == user.club_name, Discussion.parent_id == None)
        .order_by(Discussion.created_at.desc())
        .limit(50)
    )
    discussions = result.scalars().all()

    # Prevent lazy-load on nested .replies during Pydantic serialization
    for d in discussions:
        d.replies = []

    return [DiscussionOut.model_validate(d) for d in discussions]


@router.get("/{event_id}", response_model=list[DiscussionOut])
async def list_discussions(event_id: int, db: AsyncSession = Depends(get_db)):
    """Get all top-level comments for an event, with their replies nested."""
    # Fetch top-level comments
    result = await db.execute(
        select(Discussion)
        .where(Discussion.event_id == event_id, Discussion.parent_id == None)
        .order_by(Discussion.created_at.desc())
    )
    top_level = result.scalars().all()

    # Fetch all replies for this event
    reply_result = await db.execute(
        select(Discussion)
        .where(Discussion.event_id == event_id, Discussion.parent_id != None)
        .order_by(Discussion.created_at.asc())
    )
    all_replies = reply_result.scalars().all()

    # Set replies=[] on every reply object BEFORE model_validate.
    # Without this, Pydantic's from_attributes traversal tries to access
    # r.replies via selectin inside a sync call, causing MissingGreenlet errors.
    for r in all_replies:
        r.replies = []

    # Build parent_id → [replies] map
    reply_map: dict[int, list[Discussion]] = {}
    for r in all_replies:
        reply_map.setdefault(r.parent_id, []).append(r)

    # Attach replies to their parents (overrides the selectin relationship value)
    for comment in top_level:
        comment.replies = reply_map.get(comment.id, [])

    # model_validate is now safe: every .replies is a plain list of ORM objects
    # with their own .replies already set to []
    return [DiscussionOut.model_validate(c) for c in top_level]


@router.post("/{event_id}", response_model=DiscussionOut, status_code=201)
async def create_discussion(
    event_id: int,
    payload: DiscussionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Any logged-in user can post a top-level comment on an event."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")

    discussion = Discussion(
        event_id=event_id,
        user_id=user.id,
        user_name=user.name,
        user_role=user.role.value,
        content=payload.content,
        parent_id=None,
    )
    db.add(discussion)
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
    user: User = Depends(require_club_member),
):
    """Only club members (admins) can reply to comments on their own club's events."""
    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.club_name != user.club_name:
        raise HTTPException(status_code=403, detail="You can only reply to comments on your own club's events")

    result = await db.execute(
        select(Discussion).where(Discussion.id == comment_id, Discussion.event_id == event_id)
    )
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Comment not found")

    reply = Discussion(
        event_id=event_id,
        user_id=user.id,
        user_name=user.name,
        user_role=user.role.value,
        content=payload.content,
        parent_id=comment_id,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    reply.replies = []  # replies are second-level; no sub-replies
    return reply


@router.delete("/{event_id}/{comment_id}", status_code=204)
async def delete_discussion(
    event_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Club admins can delete any comment on their own club's events.
    Students can only delete their own comments.
    Deleting a parent comment cascades to all its replies.
    """
    result = await db.execute(
        select(Discussion).where(Discussion.id == comment_id, Discussion.event_id == event_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    is_own = user.id == comment.user_id
    if user.role == "member":
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
