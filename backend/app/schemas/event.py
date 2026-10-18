from pydantic import BaseModel, StringConstraints
from typing import Optional, List, Annotated, Generic, Literal, TypeVar
from datetime import date, datetime

from app.models.membership import ClubRoleKind, ClubRoleStatus
from app.models.user import AccountType
from app.schemas.user import LowerEmail

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """One page of a paginated listing."""
    items: List[T]
    total: int   # matches across all pages (for "Load more" and counts)


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


ClubPage = Page[ClubOut]


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


EventPage = Page[EventOut]


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


# ── Club roles (team requests, DSW review) ───────────────
class ClubRoleDetailOut(PersonOut):
    """A club role with the person holding it: team lists and the DSW's review queue."""
    id: int
    club_id: int
    club_name: str
    role: ClubRoleKind
    status: ClubRoleStatus
    title: Optional[str] = None
    proposed_by_name: Optional[str] = None
    multi_club_exception: bool = False
    created_at: datetime
    reviewed_at: Optional[datetime] = None


ClubRolePage = Page[ClubRoleDetailOut]

Title = Annotated[str, StringConstraints(strip_whitespace=True, max_length=80)]


class OwnerRequest(BaseModel):
    title: Optional[Title] = None          # e.g. "President"


class EditorProposal(BaseModel):
    email: LowerEmail                      # the student being proposed
    title: Optional[Title] = None


class FacultyAssignment(BaseModel):
    email: LowerEmail                      # a faculty account


class RoleReview(BaseModel):
    """approve / reject a pending request, or end an active role (revoke)."""
    action: Literal["approve", "reject", "end"]
    # Approving: let this student hold team roles in more than one club
    multi_club_exception: bool = False


# ── Accounts (DSW / platform admin) ──────────────────────
class AccountOut(PersonOut):
    account_type: AccountType
    is_active: bool
    created_at: datetime


AccountPage = Page[AccountOut]


class AccountTypeUpdate(BaseModel):
    account_type: Literal[AccountType.student, AccountType.faculty, AccountType.alumni]


class DswAccountGrant(BaseModel):
    email: LowerEmail


class AuditLogOut(BaseModel):
    id: int
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: dict
    created_at: datetime


AuditLogPage = Page[AuditLogOut]


class HotUpdate(BaseModel):
    is_hot: bool


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


DiscussionPage = Page[DiscussionOut]   # total = top-level comments only


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
