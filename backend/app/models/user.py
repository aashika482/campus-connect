from sqlalchemy import String, Boolean, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    member = "member"   # club admin/member


class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(primary_key=True, index=True)
    name:       Mapped[str]      = mapped_column(String(120))
    email:      Mapped[str]      = mapped_column(String(255), unique=True, index=True)
    password:   Mapped[str]      = mapped_column(String(255))
    role:       Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.student)

    # Student fields
    reg_no:     Mapped[str | None] = mapped_column(String(30))
    course:     Mapped[str | None] = mapped_column(String(100))
    phone:      Mapped[str | None] = mapped_column(String(20))
    interests:  Mapped[str | None] = mapped_column(String(500))  # comma-separated tag ids

    # Club member fields
    club_name:  Mapped[str | None] = mapped_column(String(120))
    position:   Mapped[str | None] = mapped_column(String(80))

    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    memberships:   Mapped[list["Membership"]]   = relationship("Membership",   back_populates="user", cascade="all, delete-orphan")
    registrations: Mapped[list["Registration"]] = relationship("Registration", back_populates="user", cascade="all, delete-orphan")
    saved_events:  Mapped[list["SavedEvent"]]   = relationship("SavedEvent",   back_populates="user", cascade="all, delete-orphan")
