# backend/app/models/discussion.py
# CREATE this new file in backend/app/models/

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.database import Base


class Discussion(Base):
    __tablename__ = "discussions"

    id:        Mapped[int]      = mapped_column(primary_key=True, index=True)
    event_id:  Mapped[int]      = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id:   Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user_name: Mapped[str]      = mapped_column(String(120))
    user_role: Mapped[str]      = mapped_column(String(20), default="student")  # "student" or "member"
    content:   Mapped[str]      = mapped_column(Text)
    parent_id: Mapped[int|None] = mapped_column(ForeignKey("discussions.id", ondelete="CASCADE"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event:   Mapped["Event"] = relationship("Event", back_populates="discussions")
    user:    Mapped["User"]  = relationship("User")
    replies: Mapped[list["Discussion"]] = relationship(
        "Discussion",
        foreign_keys=[parent_id],
        lazy="noload",
    )
