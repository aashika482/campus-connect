# backend/app/schemas/event.py
# REPLACE your existing file with this

from pydantic import BaseModel, StringConstraints
from typing import Optional, List, Annotated
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


class ClubPage(BaseModel):
    items: List[ClubOut]
    total: int   # matching clubs across all pages


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


class EventPage(BaseModel):
    items: List[EventOut]
    total: int   # matching events across all pages


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


# ── Admin people lists (registrants / members) ───────────
class PersonOut(BaseModel):
    user_id: int
    name: str
    email: str
    phone: Optional[str] = None
    reg_no: Optional[str] = None
    course: Optional[str] = None


class RegistrantOut(PersonOut):
    registered_at: datetime


class EventRef(BaseModel):
    id: int
    title: str


class MemberOut(PersonOut):
    joined_at: datetime
    registered_events: List[EventRef]   # this club's events the member registered for


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
    is_official: bool = False
    created_at: datetime
    edited_at: Optional[datetime] = None
    replies: List["DiscussionOut"] = []

    model_config = {"from_attributes": True}


class DiscussionPage(BaseModel):
    items: List[DiscussionOut]
    total: int   # total top-level comments (not just this page)


# Trims whitespace, rejects empty comments and anything over 2000 chars
CommentText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class DiscussionCreate(BaseModel):
    content: CommentText


class DiscussionReply(BaseModel):
    content: CommentText


class DiscussionUpdate(BaseModel):
    content: CommentText


# ── Uploads (signed Cloudinary) ──────────────────────────
class UploadStatus(BaseModel):
    enabled: bool


class UploadSignature(BaseModel):
    cloud_name: str
    api_key: str        # public identifier; the secret never leaves the server
    signature: str
    timestamp: str
    folder: str
    allowed_formats: str


# ── Notification ─────────────────────────────────────────
class NotificationOut(BaseModel):
    id: int
    kind: str
    message: str
    event_id: int
    discussion_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    items: List[NotificationOut]
    unread: int
