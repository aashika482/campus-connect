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
    tags: str           # comma-separated, split on frontend
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
    tags: str           # comma-separated
    team_size: Optional[str] = None
    poster_url: Optional[str] = None
    is_hot: bool
    created_at: datetime

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


class RegistrationStatus(BaseModel):
    event_id: int
    is_registered: bool


class SaveStatus(BaseModel):
    event_id: int
    is_saved: bool
