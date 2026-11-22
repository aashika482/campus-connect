import re
from pydantic import AfterValidator, BaseModel, EmailStr, StringConstraints, field_validator
from typing import Annotated, Literal, Optional, List
from datetime import date, datetime
from app.models.user import AccountType
from app.models.membership import ClubRoleKind, ClubRoleStatus


# The tags clubs, events and interests use. Mirrored by ALL_TAGS in frontend/src/types/index.ts
TAG_IDS = ("tech", "hackathon", "photography", "dance", "music", "coding", "art", "robotics", "film", "literature",
           "sports", "social", "business", "science", "environment", "wellness", "culture", "gaming", "quizzing")
TagId = Literal[TAG_IDS]


MIN_PASSWORD = 8
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


def check_password(v: str) -> str:
    """The one password rule (sign-up, adding or changing one, the admin bootstrap)."""
    if len(v) < MIN_PASSWORD:
        raise ValueError(f"Password must be at least {MIN_PASSWORD} characters")
    return v


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
    device_token: Optional[str] = None     # "remember this browser" from an earlier second step


class LoginVerify(BaseModel):
    challenge: str                         # from the password step
    code: str                              # emailed code, or the authenticator app's
    remember: bool = False                 # skip the second step on this browser for 30 days


class ChallengeRequest(BaseModel):
    challenge: str


class EmailRequest(BaseModel):
    email: LowerEmail


class MicrosoftLogin(BaseModel):
    id_token: str


class LoginResponse(BaseModel):
    """Either the session (tokens + user), or the second step to do (second_step + challenge)."""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional["UserOut"] = None
    device_token: Optional[str] = None     # when "remember this browser" was ticked
    second_step: Optional[Literal["email", "totp"]] = None
    challenge: Optional[str] = None


class RegisterRequest(BaseModel):
    """One sign-up form for everyone: the email's domain decides student or faculty.
    `code` is the one emailed to that address (POST /auth/register/code): it proves they own it."""
    code: str
    name: Name
    email: LowerEmail
    password: str
    phone: str
    reg_no: Optional[str] = None
    course: Optional[str] = None
    interests: Optional[List[TagId]] = []

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        return check_password(v)

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
    microsoft_client_id: Optional[str] = None   # set when "Sign in with Microsoft" is available
    microsoft_tenant_id: Optional[str] = None


class PasswordUpdate(BaseModel):
    current_password: Optional[str] = None   # not needed when adding a first password
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v):
        return check_password(v)


class TotpSetup(BaseModel):
    secret: str
    uri: str                                 # otpauth://… for authenticator apps


class SecondStepUpdate(BaseModel):
    method: Literal["email", "totp"]
    secret: Optional[str] = None             # totp: from /two-step/totp
    code: Optional[str] = None               # totp: the app's current code, proving it's set up


# ── User ────────────────────────────────────────────────
class ClubRoleOut(BaseModel):
    id: int
    club_id: int
    club_name: str
    role: ClubRoleKind
    status: ClubRoleStatus
    title: Optional[str] = None
    created_at: datetime
    expires_on: Optional[date] = None    # yearly memberships: last day of the academic year

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
    has_password: bool = True
    second_factor: str = "email"
    profile_complete: bool = True
    club_roles: List[ClubRoleOut] = []   # current ones: pending, active and rejected (ended roles are history)

    model_config = {"from_attributes": True}

    @field_validator("club_roles", mode="before")
    @classmethod
    def current_roles_only(cls, v):
        return [r for r in v if getattr(r, "status", None) != ClubRoleStatus.ended and not getattr(r, "is_expired", False)]


class UserUpdate(BaseModel):
    name: Optional[Name] = None
    phone: Optional[str] = None
    reg_no: Optional[str] = None
    course: Optional[str] = None
    interests: Optional[List[TagId]] = None

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v):
        return normalize_phone(v) if v is not None else v


TokenResponse.model_rebuild()
LoginResponse.model_rebuild()
