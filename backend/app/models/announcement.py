from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.db.database import Base

# Emoji a reaction can be (a fixed set keeps reactions tidy and the column small)
REACTIONS = ("👍", "❤️", "🎉", "😂", "😮", "🙏")


class Announcement(Base):
    """A club update for its working team (owner, editors, faculty coordinators, working members).
    Posted by the team; working members react and comment."""
    __tablename__ = "club_announcements"

    id:         Mapped[int]        = mapped_column(primary_key=True)
    club_id:    Mapped[int]        = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    author_id:  Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    body:       Mapped[str]        = mapped_column(Text)
    created_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnnouncementComment(Base):
    __tablename__ = "announcement_comments"

    id:              Mapped[int]        = mapped_column(primary_key=True)
    announcement_id: Mapped[int]        = mapped_column(ForeignKey("club_announcements.id", ondelete="CASCADE"), index=True)
    author_id:       Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    body:            Mapped[str]        = mapped_column(Text)
    created_at:      Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnnouncementReaction(Base):
    __tablename__ = "announcement_reactions"
    __table_args__ = (UniqueConstraint("announcement_id", "user_id", "emoji", name="uq_announcement_reaction"),)

    id:              Mapped[int] = mapped_column(primary_key=True)
    announcement_id: Mapped[int] = mapped_column(ForeignKey("club_announcements.id", ondelete="CASCADE"), index=True)
    user_id:         Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    emoji:           Mapped[str] = mapped_column(String(8))
