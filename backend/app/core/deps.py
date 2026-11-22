from typing import TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import today
from app.core.security import decode_token
from app.db.database import get_db
from app.models.club import Club
from app.models.event import Event
from app.models.user import User, AccountType
from sqlalchemy import or_, select

bearer_scheme = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)

M = TypeVar("M")


async def get_or_404(db: AsyncSession, model: type[M], id: int) -> M:
    """The row with this primary key, or a 404 named after the model ("Event not found")."""
    obj = await db.get(model, id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials, "access")
    user_id = int(payload["sub"])

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """The signed-in user on pages anyone may see (None when signed out). A bad or expired
    token is still a 401, so the frontend refreshes it instead of quietly showing the public view."""
    if credentials is None:
        return None
    user = await get_current_user(credentials, db)
    return user if user.is_active else None


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def require_account(*types: AccountType):
    """Dependency: the signed-in user must have one of these account types."""
    async def dependency(user: User = Depends(get_current_active_user)) -> User:
        if user.account_type not in types:
            raise HTTPException(status_code=403, detail="You don't have access to this")
        return user
    return dependency


require_dsw = require_account(AccountType.dsw)
require_platform_admin = require_account(AccountType.platform_admin)


async def require_club_team(user: User = Depends(get_current_active_user)) -> User:
    """Someone who runs at least one club (owner, editor or faculty coordinator)."""
    if not user.team_club_ids:
        raise HTTPException(status_code=403, detail="Only a club's team can do this")
    return user


def ensure_can_manage(user: User, club_id: int) -> None:
    """403 unless the user is on this club's active team."""
    if not user.can_manage(club_id):
        raise HTTPException(status_code=403, detail="Only this club's team can do this")


# ── Private clubs: what outsiders don't see ──────────────
def visible_events(user: User | None):
    """Filter: a private club's upcoming events are only for the people in it (and the DSW).
    Its past events stay visible to everyone, as the club's history. None: no filter needed."""
    if user and user.account_type == AccountType.dsw:
        return None
    hidden = select(Club.id).where(Club.is_private == True, Club.id.not_in(user.club_ids if user else set()))  # noqa: E712
    return or_(Event.end_date < today(), Event.club_id.not_in(hidden))


async def get_visible_event(db: AsyncSession, event_id: int, user: User | None) -> Event:
    """The event, or a 404 if it's a private club's upcoming event and this user is outside the club.
    Everything about one event (its page, discussion, saving, registering, counts) goes through this."""
    event = await get_or_404(db, Event, event_id)
    if event.end_date >= today() and not (user and user.sees_inside(event.club_id)):
        club = await db.get(Club, event.club_id)
        if club and club.is_private:
            raise HTTPException(status_code=404, detail="Event not found")
    return event
