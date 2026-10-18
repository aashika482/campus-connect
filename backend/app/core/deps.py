from typing import TypeVar

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.database import get_db
from app.models.user import User, AccountType
from sqlalchemy import select

bearer_scheme = HTTPBearer()

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
