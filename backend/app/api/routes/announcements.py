# A club's announcements: private updates for its working team (owner, editors, faculty
# coordinators, working members). The team posts; the whole working team reacts and comments.
# Mounted under /api/clubs, next to the club routes.

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.announcement import Announcement, AnnouncementComment, AnnouncementReaction, REACTIONS
from app.models.club import Club
from app.models.membership import ClubRole, ClubRoleKind, CURRENT, TEAM_ROLES, ROLE_TITLES
from app.models.notification import Notification
from app.models.user import User
from app.core.deps import get_or_404, get_current_active_user, ensure_can_manage
from app.schemas.event import (
    AnnouncementIn, AnnouncementOut, AnnouncementPage, AnnouncementCommentOut, ReactionCount, ReactionIn,
)

router = APIRouter()


def _ensure_working_team(user: User, club_id: int) -> None:
    if not user.on_working_team(club_id):
        raise HTTPException(status_code=403, detail="Announcements are for the club's working team")


async def _own_announcement(db: AsyncSession, club_id: int, announcement_id: int) -> Announcement:
    a = await get_or_404(db, Announcement, announcement_id)
    if a.club_id != club_id:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return a


@router.get("/{club_id}/announcements", response_model=AnnouncementPage)
async def list_announcements(
    club_id: int,
    before_id: Optional[int] = Query(None, description="Older than this announcement (for 'Load more')"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Newest first, each with its reactions and comments."""
    _ensure_working_team(user, club_id)
    filters = [Announcement.club_id == club_id]
    total = (await db.execute(select(func.count()).select_from(Announcement).where(*filters))).scalar()
    if before_id:
        filters.append(Announcement.id < before_id)
    posts = (await db.execute(
        select(Announcement).where(*filters).order_by(Announcement.id.desc()).limit(limit)
    )).scalars().all()
    ids = [a.id for a in posts]

    comments = (await db.execute(
        select(AnnouncementComment).where(AnnouncementComment.announcement_id.in_(ids))
        .order_by(AnnouncementComment.id)
    )).scalars().all() if ids else []
    reactions = (await db.execute(
        select(AnnouncementReaction.announcement_id, AnnouncementReaction.emoji,
               func.count(), func.bool_or(AnnouncementReaction.user_id == user.id))
        .where(AnnouncementReaction.announcement_id.in_(ids))
        .group_by(AnnouncementReaction.announcement_id, AnnouncementReaction.emoji)
    )).all() if ids else []

    # Names of everyone who wrote something here, and the authors' titles in this club
    author_ids = {a.author_id for a in posts} | {c.author_id for c in comments}
    names = dict((await db.execute(select(User.id, User.name).where(User.id.in_(author_ids)))).all()) if author_ids else {}
    titles: dict[int, str] = {}
    for uid, role, title in (await db.execute(
        select(ClubRole.user_id, ClubRole.role, ClubRole.title)
        .where(ClubRole.club_id == club_id, ClubRole.user_id.in_({a.author_id for a in posts}),
               ClubRole.role.in_(TEAM_ROLES), CURRENT)
    )).all() if posts else []:
        titles.setdefault(uid, title or ROLE_TITLES[role])

    by_post_comments: dict[int, list[AnnouncementCommentOut]] = {}
    for c in comments:
        by_post_comments.setdefault(c.announcement_id, []).append(AnnouncementCommentOut(
            id=c.id, author_id=c.author_id, author_name=names.get(c.author_id), body=c.body, created_at=c.created_at))
    by_post_reactions: dict[int, list[ReactionCount]] = {}
    for aid, emoji, count, mine in sorted(reactions, key=lambda r: REACTIONS.index(r[1]) if r[1] in REACTIONS else 99):
        by_post_reactions.setdefault(aid, []).append(ReactionCount(emoji=emoji, count=count, mine=bool(mine)))

    return AnnouncementPage(total=total, items=[
        AnnouncementOut(
            id=a.id, club_id=a.club_id, author_id=a.author_id, author_name=names.get(a.author_id),
            author_title=titles.get(a.author_id), body=a.body, created_at=a.created_at,
            reactions=by_post_reactions.get(a.id, []), comments=by_post_comments.get(a.id, []),
        ) for a in posts
    ])


@router.post("/{club_id}/announcements", status_code=201)
async def post_announcement(
    club_id: int,
    payload: AnnouncementIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """The club's team (owner, editors, faculty coordinators) posts; the rest of the working team is notified."""
    ensure_can_manage(user, club_id)
    club = await get_or_404(db, Club, club_id)
    a = Announcement(club_id=club_id, author_id=user.id, body=payload.body)
    db.add(a)
    await db.flush()
    audience = (await db.execute(
        select(ClubRole.user_id).where(ClubRole.club_id == club_id, CURRENT,
                                       ClubRole.role.in_((*TEAM_ROLES, ClubRoleKind.working_member)),
                                       ClubRole.user_id != user.id)
    )).scalars().all()
    Notification.send(db, audience, "announcement", f"{club.name}: {payload.body}", club_id=club_id)
    await db.commit()
    return {"id": a.id}


@router.delete("/{club_id}/announcements/{announcement_id}", status_code=204)
async def delete_announcement(
    club_id: int,
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Its author, or anyone running the club. Comments and reactions go with it."""
    a = await _own_announcement(db, club_id, announcement_id)
    if a.author_id != user.id:
        ensure_can_manage(user, club_id)
    await db.execute(delete(Announcement).where(Announcement.id == a.id))
    await db.commit()


@router.post("/{club_id}/announcements/{announcement_id}/comments", response_model=AnnouncementCommentOut, status_code=201)
async def comment_on_announcement(
    club_id: int,
    announcement_id: int,
    payload: AnnouncementIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    _ensure_working_team(user, club_id)
    a = await _own_announcement(db, club_id, announcement_id)
    c = AnnouncementComment(announcement_id=a.id, author_id=user.id, body=payload.body)
    db.add(c)
    if a.author_id and a.author_id != user.id:
        Notification.send(db, [a.author_id], "ann_comment",
                          f"{user.name} commented on your announcement: {payload.body}", club_id=club_id)
    await db.commit()
    await db.refresh(c)
    return AnnouncementCommentOut(id=c.id, author_id=user.id, author_name=user.name, body=c.body, created_at=c.created_at)


@router.delete("/{club_id}/announcements/{announcement_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    club_id: int,
    announcement_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Its author, or anyone running the club."""
    await _own_announcement(db, club_id, announcement_id)
    c = await get_or_404(db, AnnouncementComment, comment_id)
    if c.announcement_id != announcement_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    if c.author_id != user.id:
        ensure_can_manage(user, club_id)
    await db.delete(c)
    await db.commit()


@router.post("/{club_id}/announcements/{announcement_id}/reactions", response_model=list[ReactionCount])
async def toggle_reaction(
    club_id: int,
    announcement_id: int,
    payload: ReactionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Add this reaction, or take it back if it's already yours. Returns the announcement's reactions."""
    _ensure_working_team(user, club_id)
    if payload.emoji not in REACTIONS:
        raise HTTPException(status_code=400, detail=f"React with one of {' '.join(REACTIONS)}")
    a = await _own_announcement(db, club_id, announcement_id)
    mine = AnnouncementReaction.announcement_id == a.id, AnnouncementReaction.user_id == user.id, \
        AnnouncementReaction.emoji == payload.emoji
    if (await db.execute(delete(AnnouncementReaction).where(*mine))).rowcount == 0:
        db.add(AnnouncementReaction(announcement_id=a.id, user_id=user.id, emoji=payload.emoji))
    await db.flush()
    rows = (await db.execute(
        select(AnnouncementReaction.emoji, func.count(), func.bool_or(AnnouncementReaction.user_id == user.id))
        .where(AnnouncementReaction.announcement_id == a.id).group_by(AnnouncementReaction.emoji)
    )).all()
    await db.commit()
    return [ReactionCount(emoji=e, count=n, mine=bool(m))
            for e, n, m in sorted(rows, key=lambda r: REACTIONS.index(r[0]) if r[0] in REACTIONS else 99)]
