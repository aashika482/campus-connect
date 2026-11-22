# A club's working-team chat. Mounted under /api/clubs:
#   GET    /{club_id}/chat               history, newest page first (before_id for older, after_id to catch up)
#   POST   /{club_id}/chat               send a message
#   DELETE /{club_id}/chat/{message_id}  its author, or the club's owner/editors
#   WS     /{club_id}/chat/ws            live updates: {"type": "message", "message": {...}} / {"type": "deleted", "id": n}
# Messages are sent over plain HTTP (same auth and validation as everything else); the WebSocket only
# pushes them out. The socket authenticates with its first frame, {"token": "<access token>"}, so the
# token never sits in a URL (or a server log). Who's connected lives in this process's memory, which
# is right for one backend instance; several instances would need a shared channel (e.g. Postgres NOTIFY).

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_or_404, get_current_active_user
from app.core.security import decode_token
from app.db.database import get_db, AsyncSessionLocal
from app.models.announcement import ChatMessage
from app.models.membership import STUDENT_TEAM_ROLES
from app.models.user import User
from app.schemas.event import ChatIn, ChatMessageOut, ChatPage

router = APIRouter()


class ChatHub:
    """The open chat sockets, per club (and whose each one is, to cut someone off)."""
    def __init__(self) -> None:
        self.rooms: dict[int, set[WebSocket]] = {}
        self.owners: dict[WebSocket, int] = {}

    def join(self, club_id: int, ws: WebSocket, user_id: int) -> None:
        self.rooms.setdefault(club_id, set()).add(ws)
        self.owners[ws] = user_id

    def leave(self, club_id: int, ws: WebSocket) -> None:
        self.rooms.get(club_id, set()).discard(ws)
        self.owners.pop(ws, None)

    async def kick(self, user_id: int) -> None:
        """Close every chat socket this person has open (e.g. their account was deactivated)."""
        for ws in [ws for ws, uid in self.owners.items() if uid == user_id]:
            try:
                await ws.close(code=4403)
            except RuntimeError:
                pass   # already closed

    async def broadcast(self, club_id: int, data: dict) -> None:
        sockets = list(self.rooms.get(club_id, ()))
        results = await asyncio.gather(*(ws.send_json(data) for ws in sockets), return_exceptions=True)
        for ws, result in zip(sockets, results):
            if isinstance(result, Exception):   # gone without saying goodbye
                self.leave(club_id, ws)


hub = ChatHub()


def _ensure_working_team(user: User, club_id: int) -> None:
    if not user.on_working_team(club_id):
        raise HTTPException(status_code=403, detail="The chat is for the club's working team")


def _out(m: ChatMessage, author_name: Optional[str]) -> ChatMessageOut:
    return ChatMessageOut(id=m.id, club_id=m.club_id, author_id=m.author_id, author_name=author_name,
                          body=m.body, created_at=m.created_at)


@router.get("/{club_id}/chat", response_model=ChatPage)
async def chat_history(
    club_id: int,
    before_id: Optional[int] = Query(None, description="Older than this message"),
    after_id: Optional[int] = Query(None, description="Newer than this message (catching up after a dropped connection)"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    _ensure_working_team(user, club_id)
    query = select(ChatMessage, User.name).outerjoin(User, User.id == ChatMessage.author_id).where(ChatMessage.club_id == club_id)
    if after_id is not None:
        rows = (await db.execute(query.where(ChatMessage.id > after_id).order_by(ChatMessage.id).limit(limit))).all()
        return ChatPage(items=[_out(m, n) for m, n in rows], has_more=False)
    if before_id is not None:
        query = query.where(ChatMessage.id < before_id)
    rows = (await db.execute(query.order_by(ChatMessage.id.desc()).limit(limit + 1))).all()
    return ChatPage(items=[_out(m, n) for m, n in reversed(rows[:limit])], has_more=len(rows) > limit)


@router.post("/{club_id}/chat", response_model=ChatMessageOut, status_code=201)
async def send_message(
    club_id: int,
    payload: ChatIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    _ensure_working_team(user, club_id)
    m = ChatMessage(club_id=club_id, author_id=user.id, body=payload.body)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    out = _out(m, user.name)
    await hub.broadcast(club_id, {"type": "message", "message": out.model_dump(mode="json")})
    return out


@router.delete("/{club_id}/chat/{message_id}", status_code=204)
async def delete_message(
    club_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    m = await get_or_404(db, ChatMessage, message_id)
    if m.club_id != club_id:
        raise HTTPException(status_code=404, detail="ChatMessage not found")
    if m.author_id != user.id and not any(r.club_id == club_id for r in user.roles(*STUDENT_TEAM_ROLES)):
        raise HTTPException(status_code=403, detail="Only its author or the club's owner and editors can delete a message")
    await db.delete(m)
    await db.commit()
    await hub.broadcast(club_id, {"type": "deleted", "id": message_id})


@router.websocket("/{club_id}/chat/ws")
async def chat_socket(ws: WebSocket, club_id: int):
    """Live updates for one club's chat. Close codes: 4401 bad/expired token, 4403 not on the working team."""
    await ws.accept()
    try:
        first = await asyncio.wait_for(ws.receive_json(), timeout=10)
        user_id = int(decode_token(str(first.get("token", "")), "access")["sub"])
    except Exception:
        await ws.close(code=4401)
        return
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)   # its club roles load with it
        allowed = user is not None and user.is_active and user.on_working_team(club_id)
    if not allowed:
        await ws.close(code=4403)
        return

    hub.join(club_id, ws, user_id)
    try:
        await ws.send_json({"type": "ready"})
        while True:
            await ws.receive_text()   # the client's keep-alive pings; nothing else comes this way
    except WebSocketDisconnect:
        pass
    finally:
        hub.leave(club_id, ws)
