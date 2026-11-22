from sqlalchemy import String, Boolean, Date, Enum, Float, Integer, Text, DateTime, ForeignKey, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
from datetime import date, datetime
import enum

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
    is_open:     Mapped[bool] = mapped_column(Boolean, default=True)    # taking new members (the team's switch)

    # Social links
    instagram:   Mapped[str | None] = mapped_column(String(200))
    linkedin:    Mapped[str | None] = mapped_column(String(200))

    # Settings the club's team controls
    # Private: hidden from listings and search for outsiders, who can still open its page and history
    # but don't see its upcoming events and can't join. Its members, team and the DSW see it as usual.
    is_private:  Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
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


class ClubBenefit(Base):
    """A perk for a club's members (e.g. "10% off fest passes"), for every member or only the working team.
    Anyone can see them; only members get them."""
    __tablename__ = "club_benefits"

    id:          Mapped[int]         = mapped_column(primary_key=True)
    club_id:     Mapped[int]         = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    title:       Mapped[str]         = mapped_column(String(80))
    details:     Mapped[str | None]  = mapped_column(String(300), nullable=True)
    audience:    Mapped[str]         = mapped_column(String(10), default="members")   # "members" | "working"
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)            # hidden after this day
    created_at:  Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClubRequestStatus(str, enum.Enum):
    awaiting_coordinator = "awaiting_coordinator"   # the named faculty coordinator confirms first
    awaiting_dsw = "awaiting_dsw"                   # confirmed; the DSW decides
    approved = "approved"                           # the club exists (club_id); the requester owns it
    declined = "declined"                           # the coordinator said no
    rejected = "rejected"                           # the DSW said no


OPEN_CLUB_REQUEST_STATUSES = (ClubRequestStatus.awaiting_coordinator, ClubRequestStatus.awaiting_dsw)


class ClubRequest(Base):
    """A student proposing a new club. The faculty coordinator they name confirms (the request waits
    if that coordinator hasn't signed up yet), then the DSW approves: the club is created with the
    requester as owner, the coordinator assigned and the founding team as editors."""
    __tablename__ = "club_requests"

    id:           Mapped[int]         = mapped_column(primary_key=True)
    requested_by: Mapped[int]         = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status:       Mapped[ClubRequestStatus] = mapped_column(
        Enum(ClubRequestStatus, native_enum=False, length=30), default=ClubRequestStatus.awaiting_coordinator, index=True,
    )
    # The club as proposed
    name:         Mapped[str]         = mapped_column(String(150))
    abbr:         Mapped[str]         = mapped_column(String(20))
    description:  Mapped[str]         = mapped_column(Text)
    tags:         Mapped[str]         = mapped_column(String(300))           # comma-separated
    instagram:    Mapped[str | None]  = mapped_column(String(200), nullable=True)
    linkedin:     Mapped[str | None]  = mapped_column(String(200), nullable=True)
    affiliation:  Mapped[str | None]  = mapped_column(String(120), nullable=True)   # e.g. "IEEE student chapter"
    purpose:      Mapped[str]         = mapped_column(Text)                  # why it's needed, how it differs
    plans:        Mapped[str]         = mapped_column(Text)                  # first semester's activities
    founding_emails:   Mapped[str]    = mapped_column(String(600))           # comma-separated students → editors
    coordinator_email: Mapped[str]    = mapped_column(String(255), index=True)
    contact_phone:     Mapped[str]    = mapped_column(String(20))            # for the DSW only
    # The decision trail
    coordinator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by:    Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_note:  Mapped[str | None] = mapped_column(String(300), nullable=True)
    club_id:        Mapped[int | None] = mapped_column(ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True)
    created_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:     Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ClubEvaluation(Base):
    """The DSW's yearly audit of a club (imported from the audit sheet). Visible to the DSW only."""
    __tablename__ = "club_evaluations"
    __table_args__ = (UniqueConstraint("club_id", "year", name="uq_club_evaluation_year"),)

    id:          Mapped[int]          = mapped_column(primary_key=True)
    club_id:     Mapped[int]          = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    year:        Mapped[str]          = mapped_column(String(9))          # academic year, e.g. "2024-25"
    category:    Mapped[str]          = mapped_column(String(20))         # Platinum / Gold / Silver / Bronze / White / Black
    # Marks out of 30 / 20 / 20 / 20 / 10, and the total out of 100 (blank cells count as 0)
    quality_of_events:   Mapped[float] = mapped_column(Float, default=0)
    sponsorship:         Mapped[float] = mapped_column(Float, default=0)
    student_engagement:  Mapped[float] = mapped_column(Float, default=0)
    dsw_component:       Mapped[float] = mapped_column(Float, default=0)
    faculty_component:   Mapped[float] = mapped_column(Float, default=0)
    total:               Mapped[float] = mapped_column(Float, default=0)
    remarks:     Mapped[str | None]   = mapped_column(Text, nullable=True)
    created_at:  Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())


class CoordinatorInvite(Base):
    """A faculty email the DSW's records name as a club's coordinator. When that person signs in with
    a verified college account, they become the club's faculty coordinator (claimed_at is set)."""
    __tablename__ = "coordinator_invites"
    __table_args__ = (UniqueConstraint("club_id", "email", name="uq_coordinator_invite"),)

    id:         Mapped[int]              = mapped_column(primary_key=True)
    club_id:    Mapped[int]              = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    email:      Mapped[str]              = mapped_column(String(255), index=True)   # lowercase
    created_at: Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    claimed_at: Mapped[datetime | None]  = mapped_column(DateTime(timezone=True), nullable=True)
