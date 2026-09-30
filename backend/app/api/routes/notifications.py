from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.db.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.core.deps import get_current_active_user
from app.schemas.event import NotificationOut, NotificationList

router = APIRouter()


@router.get("", response_model=NotificationList)
async def list_notifications(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """Latest notifications for the current user, plus the total unread count (for the bell dot)."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.id.desc())
        .limit(limit)
    )
    unread = (await db.execute(
        select(func.count()).select_from(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)
    )).scalar()
    return NotificationList(
        items=[NotificationOut.model_validate(n) for n in result.scalars().all()],
        unread=unread,
    )


@router.post("/read-all", status_code=204)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()


@router.post("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    await db.commit()
