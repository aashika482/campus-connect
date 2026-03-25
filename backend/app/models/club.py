from sqlalchemy import String, Boolean, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.db.database import Base


class Club(Base):
    __tablename__ = "clubs"

    id:          Mapped[int]  = mapped_column(primary_key=True, index=True)
    name:        Mapped[str]  = mapped_column(String(150), unique=True)
    abbr:        Mapped[str]  = mapped_column(String(20))
    description: Mapped[str]  = mapped_column(Text)
    color:       Mapped[str]  = mapped_column(String(10), default="#D4561A")
    tags:        Mapped[str]  = mapped_column(String(300))   # comma-separated
    member_count:Mapped[int]  = mapped_column(Integer, default=0)
    is_open:     Mapped[bool] = mapped_column(Boolean, default=True)

    # Social links
    instagram:   Mapped[str | None] = mapped_column(String(200))
    linkedin:    Mapped[str | None] = mapped_column(String(200))

    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    events:      Mapped[list["Event"]]      = relationship("Event",      back_populates="club")
    memberships: Mapped[list["Membership"]] = relationship("Membership", back_populates="club")
