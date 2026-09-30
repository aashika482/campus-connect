from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id:            Mapped[int]      = mapped_column(primary_key=True, index=True)
    user_id:       Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)  # recipient
    kind:          Mapped[str]      = mapped_column(String(20))   # "reply" | "comment" | "mention"
    message:       Mapped[str]      = mapped_column(String(300))
    event_id:      Mapped[int]      = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    # The comment/reply that triggered this. Deleting it deletes the notification too.
    discussion_id: Mapped[int|None] = mapped_column(ForeignKey("discussions.id", ondelete="CASCADE"), nullable=True)
    is_read:       Mapped[bool]     = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
