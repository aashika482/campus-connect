from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole


# ── Auth ────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole


class RegisterStudentRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    reg_no: Optional[str] = None
    course: Optional[str] = None
    phone: Optional[str] = None
    interests: Optional[List[str]] = []

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class RegisterMemberRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    club_name: str
    position: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User ────────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    reg_no: Optional[str] = None
    course: Optional[str] = None
    club_name: Optional[str] = None
    position: Optional[str] = None
    interests: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    interests: Optional[List[str]] = None


TokenResponse.model_rebuild()
