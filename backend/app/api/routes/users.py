from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.user import User
from app.core.deps import get_current_active_user
from app.schemas.user import UserOut, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_active_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    data = payload.model_dump(exclude_unset=True)
    if "interests" in data and data["interests"] is not None:
        data["interests"] = ",".join(data["interests"])
    for k, v in data.items():
        setattr(user, k, v)
    await db.flush()
    return user
