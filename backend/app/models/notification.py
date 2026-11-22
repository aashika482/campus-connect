from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id:            Mapped[int]      = mapped_column(primary_key=True, index=True)
    user_id:       Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)  # recipient
    # Event discussions: "reply" | "comment" | "mention". Clubs: "announcement" | "ann_comment" (on your announcement)
    # | "application" (your application moved) | "app_review" (an application waits for you, the coordinator)
    kind:          Mapped[str]      = mapped_column(String(20))
    message:       Mapped[str]      = mapped_column(String(300))
    # What it's about: an event's discussion, or a club (announcements, applications)
    event_id:      Mapped[int|None] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=True)
    club_id:       Mapped[int|None] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True)
    # The comment/reply that triggered this. Deleting it deletes the notification too.
    discussion_id: Mapped[int|None] = mapped_column(ForeignKey("discussions.id", ondelete="CASCADE"), nullable=True)
    is_read:       Mapped[bool]     = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @classmethod
    def send(cls, db, user_ids, kind: str, message: str, *, event_id: int | None = None,
             club_id: int | None = None) -> None:
        """Queue the same notification for each of these users (added to the session, not committed)."""
        db.add_all([cls(user_id=uid, kind=kind, message=message[:300], event_id=event_id, club_id=club_id)
                    for uid in dict.fromkeys(user_ids)])
