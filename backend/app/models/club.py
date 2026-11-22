from sqlalchemy import String, Boolean, Integer, Text, DateTime, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
from datetime import datetime

from app.db.database import Base
from app.models.membership import ClubRole, ClubRoleKind, CURRENT


class Club(Base):
    __tablename__ = "clubs"

    id:          Mapped[int]  = mapped_column(primary_key=True, index=True)
    name:        Mapped[str]  = mapped_column(String(150), unique=True)
    abbr:        Mapped[str]  = mapped_column(String(20))
    description: Mapped[str]  = mapped_column(Text)
    color:       Mapped[str]  = mapped_column(String(10), default="#D4561A")
    tags:        Mapped[str]  = mapped_column(String(300))   # comma-separated
    is_open:     Mapped[bool] = mapped_column(Boolean, default=True)

    # Social links
    instagram:   Mapped[str | None] = mapped_column(String(200))
    linkedin:    Mapped[str | None] = mapped_column(String(200))

    # Settings the club's team controls
    recruiting:  Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")   # working-team applications open
    # May this club's working members also be on other clubs' working teams (and vice versa)?
    working_multi_club: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # Yearly fees in rupees (shown to students; collected outside the portal until payments exist).
    # Working members pay fee_member first, then the difference once accepted.
    fee_member:  Mapped[int] = mapped_column(Integer, default=500, server_default="500")
    fee_working: Mapped[int] = mapped_column(Integer, default=1000, server_default="1000")

    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Current (this academic year's) members, counted live so memberships expiring never leave it stale
    member_count: Mapped[int] = column_property(
        select(func.count(ClubRole.id))
        .where(ClubRole.club_id == id, ClubRole.role == ClubRoleKind.member, CURRENT)
        .correlate_except(ClubRole)
        .scalar_subquery()
    )

    # Relationships
    events:      Mapped[list["Event"]]      = relationship("Event",      back_populates="club")
