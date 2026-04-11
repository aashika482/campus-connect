# backend/app/schemas/event.py
# REPLACE your existing file with this

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# ── Club ────────────────────────────────────────────────
class ClubOut(BaseModel):
    id: int
    name: str
    abbr: str
    description: str
    color: str
    tags: str
    member_count: int
    is_open: bool
    instagram: Optional[str] = None
    linkedin: Optional[str] = None

    model_config = {"from_attributes": True}


class ClubCreate(BaseModel):
    name: str
    abbr: str
    description: str
    color: str = "#D4561A"
    tags: List[str]
    is_open: bool = True
    instagram: Optional[str] = None
    linkedin: Optional[str] = None


class ClubMembershipStatus(BaseModel):
    club_id: int
    is_member: bool
    member_count: int


# ── Event ────────────────────────────────────────────────
class EventOut(BaseModel):
    id: int
    title: str
    description: str
    club_id: int
    club_name: str
    start_date: date
    end_date: date
    reg_deadline: Optional[date] = None
    date_display: str
    tags: str
    team_size: Optional[str] = None
    poster_url: Optional[str] = None
    is_hot: bool
    created_at: datetime

    # ── New fields ──
    venue: Optional[str] = None
    time_info: Optional[str] = None
    registration_fee: Optional[str] = "Free"
    prize_pool: Optional[str] = None
    contact_info: Optional[str] = None

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    title: str
    description: str
    club_id: int
    start_date: date
    end_date: date
    reg_deadline: Optional[date] = None
    date_display: str
    tags: List[str]
    team_size: Optional[str] = None
    poster_url: Optional[str] = None
    is_hot: bool = False

    # ── New fields ──
    venue: Optional[str] = None
    time_info: Optional[str] = None
    registration_fee: Optional[str] = "Free"
    prize_pool: Optional[str] = None
    contact_info: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reg_deadline: Optional[date] = None
    date_display: Optional[str] = None
    tags: Optional[List[str]] = None
    team_size: Optional[str] = None
    poster_url: Optional[str] = None
    is_hot: Optional[bool] = None
    is_published: Optional[bool] = None

    # ── New fields ──
    venue: Optional[str] = None
    time_info: Optional[str] = None
    registration_fee: Optional[str] = None
    prize_pool: Optional[str] = None
    contact_info: Optional[str] = None


class RegistrationStatus(BaseModel):
    event_id: int
    is_registered: bool


class SaveStatus(BaseModel):
    event_id: int
    is_saved: bool


# ── Discussion ───────────────────────────────────────────
class DiscussionOut(BaseModel):
    id: int
    event_id: int
    user_id: int
    user_name: str
    user_role: str
    content: str
    parent_id: Optional[int] = None
    created_at: datetime
    replies: List["DiscussionOut"] = []

    model_config = {"from_attributes": True}


class DiscussionCreate(BaseModel):
    content: str


class DiscussionReply(BaseModel):
    content: str
