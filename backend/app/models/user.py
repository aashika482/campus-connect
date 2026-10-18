from sqlalchemy import String, Boolean, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.db.database import Base
from app.models.membership import ClubRoleKind, ClubRoleStatus, TEAM_ROLES


class AccountType(str, enum.Enum):
    student = "student"                 # default for student email domains
    faculty = "faculty"                 # default for staff email domains
    alumni = "alumni"                   # set by the DSW when a student graduates
    dsw = "dsw"                         # Dean of Student Welfare office: approves everything, governs clubs
    platform_admin = "platform_admin"   # tech team: manages DSW accounts and the system, no business authority


# Account types the DSW may switch people between (dsw / platform_admin are managed by the tech team)
DSW_ASSIGNABLE_TYPES = (AccountType.student, AccountType.faculty, AccountType.alumni)


class User(Base):
    __tablename__ = "users"

    id:           Mapped[int]         = mapped_column(primary_key=True, index=True)
    name:         Mapped[str]         = mapped_column(String(120))
    email:        Mapped[str]         = mapped_column(String(255), unique=True, index=True)   # always lowercase
    password:     Mapped[str]         = mapped_column(String(255))
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), default=AccountType.student)

    # Student fields
    reg_no:     Mapped[str | None] = mapped_column(String(30))
    course:     Mapped[str | None] = mapped_column(String(100))
    phone:      Mapped[str | None] = mapped_column(String(20))
    interests:  Mapped[str | None] = mapped_column(String(500))  # comma-separated tag ids

    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    registrations: Mapped[list["Registration"]] = relationship("Registration", back_populates="user", cascade="all, delete-orphan")
    saved_events:  Mapped[list["SavedEvent"]]   = relationship("SavedEvent",   back_populates="user", cascade="all, delete-orphan")
    # Loaded with every user (one extra IN query, not one per user): every permission check needs it
    club_roles:    Mapped[list["ClubRole"]]     = relationship(
        "ClubRole", foreign_keys="ClubRole.user_id", back_populates="user",
        lazy="selectin", cascade="all, delete-orphan",
    )

    # ── Permissions: the one place that decides who may do what ──
    def roles(self, *kinds: ClubRoleKind, status: ClubRoleStatus = ClubRoleStatus.active) -> list["ClubRole"]:
        """This user's club roles with the given status, optionally only of the given kinds."""
        return [r for r in self.club_roles if r.status == status and (not kinds or r.role in kinds)]

    @property
    def team_club_ids(self) -> set[int]:
        """Clubs this user helps run: active owner, editor or faculty coordinator."""
        return {r.club_id for r in self.roles(*TEAM_ROLES)}

    def can_manage(self, club_id: int) -> bool:
        """Run this club: its events, members list, registrants and dashboard."""
        return club_id in self.team_club_ids

    def can_moderate(self, club_id: int) -> bool:
        """Delete any comment on this club's events: the club's team, or the DSW."""
        return self.account_type == AccountType.dsw or self.can_manage(club_id)

    def is_member_of(self, club_id: int) -> bool:
        return any(r.club_id == club_id for r in self.roles(ClubRoleKind.member))
