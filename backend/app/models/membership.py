from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.database import Base


class Membership(Base):
    """User joining a club."""
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "club_id", name="uq_membership"),)

    id:         Mapped[int]      = mapped_column(primary_key=True)
    user_id:    Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    club_id:    Mapped[int]      = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    joined_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    club: Mapped["Club"] = relationship("Club", back_populates="memberships")


class Registration(Base):
    """User registering for an event."""
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_registration"),)

    id:            Mapped[int]      = mapped_column(primary_key=True)
    user_id:       Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_id:      Mapped[int]      = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user:  Mapped["User"]  = relationship("User",  back_populates="registrations")
    event: Mapped["Event"] = relationship("Event", back_populates="registrations")


class SavedEvent(Base):
    """User bookmarking an event."""
    __tablename__ = "saved_events"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_saved"),)

    id:       Mapped[int]      = mapped_column(primary_key=True)
    user_id:  Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int]      = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user:  Mapped["User"]  = relationship("User",  back_populates="saved_events")
    event: Mapped["Event"] = relationship("Event", back_populates="saved_by")
