from sqlalchemy import Boolean, Date, Enum, ForeignKey, DateTime, Index, String, UniqueConstraint, and_, func, or_, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
import enum

from app.db.database import Base


class ClubRoleKind(str, enum.Enum):
    member = "member"                            # joined the club (a non-working member unless also working_member)
    working_member = "working_member"            # on the club's working team: applied, interviewed offline, recommended
                                                 # by the owner/an editor and approved by the faculty coordinator
    editor = "editor"                            # runs the club's content; proposed by the team, approved by the DSW
    owner = "owner"                              # leads the club (one per club); requested by a student, approved by the DSW
    faculty_coordinator = "faculty_coordinator"  # faculty overseeing the club; assigned by the DSW


# Roles that run a club (dashboard, events, members, moderation)
TEAM_ROLES = (ClubRoleKind.owner, ClubRoleKind.editor, ClubRoleKind.faculty_coordinator)
# Student-held team roles: limited to one club per person unless the DSW grants an exception
STUDENT_TEAM_ROLES = (ClubRoleKind.owner, ClubRoleKind.editor)
# How each role reads to people (e.g. an announcement author with no title of their own)
ROLE_TITLES = {
    ClubRoleKind.member: "Member", ClubRoleKind.working_member: "Working member", ClubRoleKind.editor: "Editor",
    ClubRoleKind.owner: "Owner", ClubRoleKind.faculty_coordinator: "Faculty coordinator",
}
# Yearly memberships: these end with the academic year (expires_on) and are renewed by re-joining / re-applying
YEARLY_ROLES = (ClubRoleKind.member, ClubRoleKind.working_member)


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
    # Yearly memberships (YEARLY_ROLES): the last day of the academic year they were taken for.
    # An active row past this date counts as over everywhere (is_current / CURRENT).
    expires_on:  Mapped[date | None]     = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="club_roles")
    # Loaded with the row (one JOIN) so the club's name is always at hand
    club: Mapped["Club"] = relationship("Club", lazy="joined")

    @property
    def club_name(self) -> str:
        return self.club.name

    @property
    def is_expired(self) -> bool:
        return self.expires_on is not None and self.expires_on < date.today()

    @property
    def is_current(self) -> bool:
        """Active and not past its academic year."""
        return self.status == ClubRoleStatus.active and not self.is_expired


# The SQL twin of ClubRole.is_current, for queries
CURRENT = and_(ClubRole.status == ClubRoleStatus.active,
               or_(ClubRole.expires_on.is_(None), ClubRole.expires_on >= func.current_date()))


class ApplicationStatus(str, enum.Enum):
    applied = "applied"            # waiting for the club's owner/editors
    shortlisted = "shortlisted"    # called for the (offline) interview
    recommended = "recommended"    # the owner/an editor says yes; waiting for the faculty coordinator
    accepted = "accepted"          # the coordinator approved: the applicant is now a working member
    declined = "declined"          # stays a non-working member


OPEN_APPLICATION_STATUSES = (ApplicationStatus.applied, ApplicationStatus.shortlisted, ApplicationStatus.recommended)


class ClubApplication(Base):
    """A member applying to a club's working team (or renewing their place for a new academic year).
    The interview happens offline; only the decision trail is kept here."""
    __tablename__ = "club_applications"
    __table_args__ = (
        Index("uq_club_applications_open", "user_id", "club_id", unique=True,
              postgresql_where=text("status IN ('applied', 'shortlisted', 'recommended')")),
    )

    id:         Mapped[int]  = mapped_column(primary_key=True)
    user_id:    Mapped[int]  = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    club_id:    Mapped[int]  = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    status:     Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=20), default=ApplicationStatus.applied, index=True,
    )
    is_renewal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")  # was working last year
    # Last owner/editor to move it along, and the coordinator who approved or declined it
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_by:  Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at:  Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:  Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


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
