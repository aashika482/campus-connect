from sqlalchemy import Boolean, Enum, ForeignKey, DateTime, Index, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.db.database import Base


class ClubRoleKind(str, enum.Enum):
    member = "member"                            # joined the club
    editor = "editor"                            # runs the club's content; proposed by the team, approved by the DSW
    owner = "owner"                              # leads the club (one per club); requested by a student, approved by the DSW
    faculty_coordinator = "faculty_coordinator"  # faculty overseeing the club; assigned by the DSW


# Roles that run a club (dashboard, events, members, moderation)
TEAM_ROLES = (ClubRoleKind.owner, ClubRoleKind.editor, ClubRoleKind.faculty_coordinator)
# Student-held team roles: limited to one club per person unless the DSW grants an exception
STUDENT_TEAM_ROLES = (ClubRoleKind.owner, ClubRoleKind.editor)


class ClubRoleStatus(str, enum.Enum):
    pending = "pending"     # waiting for the DSW (owner / editor requests)
    active = "active"
    rejected = "rejected"   # the DSW said no
    ended = "ended"         # was active: revoked, replaced or graduated. Kept as history


OPEN_STATUSES = (ClubRoleStatus.pending, ClubRoleStatus.active)


class ClubRole(Base):
    """One person's role in one club: member, editor, owner or faculty coordinator.

    A person can hold several roles in a club (e.g. member + owner), one row each.
    Rows are never deleted when a role ends: status moves to `ended` so the club keeps
    its history. At most one open (pending/active) row per user, club and role.
    """
    __tablename__ = "club_roles"
    __table_args__ = (
        Index("uq_club_roles_open", "user_id", "club_id", "role", unique=True,
              postgresql_where=text("status IN ('pending', 'active')")),
    )

    id:      Mapped[int]            = mapped_column(primary_key=True)
    user_id: Mapped[int]            = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    club_id: Mapped[int]            = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    # VARCHARs, not Postgres enum types, so adding a value later needs no ALTER TYPE
    role:    Mapped[ClubRoleKind]   = mapped_column(Enum(ClubRoleKind, native_enum=False, length=30))
    status:  Mapped[ClubRoleStatus] = mapped_column(
        Enum(ClubRoleStatus, native_enum=False, length=20),
        default=ClubRoleStatus.active, server_default=ClubRoleStatus.active.value, index=True,
    )
    title:   Mapped[str | None]     = mapped_column(String(80), nullable=True)   # "President", "Tech Lead"…

    proposed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # The DSW let this person hold team roles in more than one club
    multi_club_exception: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    created_at:  Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at:    Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="club_roles")
    # Loaded with the row (one JOIN) so the club's name is always at hand
    club: Mapped["Club"] = relationship("Club", lazy="joined")

    @property
    def club_name(self) -> str:
        return self.club.name


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
