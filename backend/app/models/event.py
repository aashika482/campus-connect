from sqlalchemy import String, Boolean, Integer, Text, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date

from app.db.database import Base


class Event(Base):
    __tablename__ = "events"

    id:           Mapped[int]       = mapped_column(primary_key=True, index=True)
    title:        Mapped[str]       = mapped_column(String(200))
    description:  Mapped[str]       = mapped_column(Text)
    club_id:      Mapped[int]       = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    club_name:    Mapped[str]       = mapped_column(String(120))  # denormalized for quick reads

    start_date:   Mapped[date]      = mapped_column(Date)
    end_date:     Mapped[date]      = mapped_column(Date)
    reg_deadline: Mapped[date|None] = mapped_column(Date, nullable=True)
    date_display: Mapped[str]       = mapped_column(String(40))   # "Oct 29–31"

    tags:         Mapped[str]       = mapped_column(String(300))  # comma-separated
    team_size:    Mapped[str|None]  = mapped_column(String(30))   # "2–4", "Solo", null
    poster_url:   Mapped[str|None]  = mapped_column(String(500))
    is_hot:       Mapped[bool]      = mapped_column(Boolean, default=False)
    is_published: Mapped[bool]      = mapped_column(Boolean, default=True)

    created_at:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    club:          Mapped["Club"]            = relationship("Club",         back_populates="events")
    registrations: Mapped[list["Registration"]] = relationship("Registration", back_populates="event", cascade="all, delete-orphan")
    saved_by:      Mapped[list["SavedEvent"]]   = relationship("SavedEvent",   back_populates="event", cascade="all, delete-orphan")
