import re
from pydantic import AfterValidator, BaseModel, EmailStr, field_validator
from typing import Annotated, Optional, List
from datetime import datetime
from app.models.user import AccountType
from app.models.membership import ClubRoleKind, ClubRoleStatus


def normalize_phone(v: str) -> str:
    """Accept "98765 43210", "+91-9876543210", "09876543210"… and store plain 10 digits."""
    digits = re.sub(r"[\s\-()]", "", v)
    digits = re.sub(r"^(\+91|0)", "", digits)
    if not re.fullmatch(r"\d{10}", digits):
        raise ValueError("Enter a valid 10-digit phone number")
    return digits


# Every email the API accepts is lowercased, so one address can never become two accounts
LowerEmail = Annotated[EmailStr, AfterValidator(str.lower)]


# ── Auth ────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: LowerEmail
    password: str


class RegisterRequest(BaseModel):
    """One sign-up form for everyone: the email's domain decides student or faculty."""
    name: str
    email: LowerEmail
    password: str
    phone: str
    reg_no: Optional[str] = None
    course: Optional[str] = None
    interests: Optional[List[str]] = []

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v):
        return normalize_phone(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthConfig(BaseModel):
    """Public sign-up rules the frontend shows (from env, never hardcoded in the UI)."""
    email_domains: dict[str, List[str]]   # {"student": [...], "faculty": [...]}


# ── User ────────────────────────────────────────────────
class ClubRoleOut(BaseModel):
    id: int
    club_id: int
    club_name: str
    role: ClubRoleKind
    status: ClubRoleStatus
    title: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    account_type: AccountType
    reg_no: Optional[str] = None
    course: Optional[str] = None
    phone: Optional[str] = None
    interests: Optional[str] = None
    created_at: datetime
    club_roles: List[ClubRoleOut] = []   # current ones: pending, active and rejected (ended roles are history)

    model_config = {"from_attributes": True}

    @field_validator("club_roles", mode="before")
    @classmethod
    def current_roles_only(cls, v):
        return [r for r in v if getattr(r, "status", None) != ClubRoleStatus.ended]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    interests: Optional[List[str]] = None

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v):
        return normalize_phone(v) if v is not None else v


TokenResponse.model_rebuild()
