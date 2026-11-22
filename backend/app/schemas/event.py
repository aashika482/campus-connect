from pydantic import BaseModel, Field, StringConstraints
from typing import Optional, List, Annotated, Generic, Literal, TypeVar
from datetime import date, datetime

from app.models.membership import ClubRoleKind, ClubRoleStatus, ApplicationStatus, LeaveScope, LeaveStatus
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
    is_private: bool = False
    recruiting: bool = False
    working_multi_club: bool = False
    fee_member: int = 500
    fee_working: int = 1000

    model_config = {"from_attributes": True}


ClubPage = Page[ClubOut]


class ClubSettingsUpdate(BaseModel):
    """The club team's settings. Only the fields sent are changed. (The DSW may change is_private only.)"""
    is_private: Optional[bool] = None
    recruiting: Optional[bool] = None
    working_multi_club: Optional[bool] = None
    fee_member: Optional[Annotated[int, Field(ge=0, le=100000)]] = None
    fee_working: Optional[Annotated[int, Field(ge=0, le=100000)]] = None


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
    is_working: bool = False             # on the working team (else a non-working member)
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


# ── Working-team applications ────────────────────────────
class ApplicationOut(PersonOut):
    id: int
    club_id: int
    status: ApplicationStatus
    is_renewal: bool
    reviewed_by_name: Optional[str] = None   # last owner/editor to move it along
    decided_by_name: Optional[str] = None    # the coordinator who approved / declined
    created_at: datetime
    updated_at: datetime


ApplicationPage = Page[ApplicationOut]


class MyApplication(BaseModel):
    """The signed-in student's latest application to this club (null fields: none yet)."""
    status: Optional[ApplicationStatus] = None
    is_renewal: bool = False                 # the open application (or the next one) renews last year's place
    can_apply: bool = False
    reason: Optional[str] = None             # why they can't apply right now


class ApplicationAction(BaseModel):
    """Owner/editors: shortlist, recommend or decline. Faculty coordinator: approve or decline a recommendation."""
    action: Literal["shortlist", "recommend", "approve", "decline"]


# ── New club requests ────────────────────────────────────
Text3000 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]


class ClubRequestIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=150)]
    abbr: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
    description: Text3000
    tags: Annotated[List[str], Field(min_length=1, max_length=4)]
    instagram: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]] = None
    linkedin: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]] = None
    affiliation: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]] = None
    purpose: Text3000
    plans: Text3000
    founding_emails: Annotated[List[LowerEmail], Field(min_length=2, max_length=4)]
    coordinator_email: LowerEmail
    contact_phone: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=20)]


class ClubRequestOut(BaseModel):
    id: int
    status: str
    name: str
    abbr: str
    description: str
    tags: str
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    affiliation: Optional[str] = None
    purpose: str
    plans: str
    founding_emails: str
    coordinator_email: str
    coordinator_signed_up: bool = False      # false: waiting for them to join the portal
    contact_phone: Optional[str] = None      # the DSW (and the requester) only
    requester_name: str
    requester_email: str
    decision_note: Optional[str] = None
    club_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


ClubRequestPage = Page[ClubRequestOut]


class ClubRequestDecision(BaseModel):
    action: Literal["confirm", "decline", "approve", "reject"]
    note: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]] = None


class ClubRequestResult(BaseModel):
    """After the DSW approves: the new club and anyone from the founding team who couldn't be made an editor."""
    club_id: Optional[int] = None
    skipped: List[str] = []


# ── Member benefits ──────────────────────────────────────
class BenefitIn(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    details: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]] = None
    audience: Literal["members", "working"] = "members"
    valid_until: Optional[date] = None


class BenefitOut(BenefitIn):
    id: int
    club_id: int

    model_config = {"from_attributes": True}


# ── Leaving a club (the DSW approves) ────────────────────
class LeaveIn(BaseModel):
    scope: LeaveScope
    reason: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)]] = None


class MyLeaveRequest(BaseModel):
    """The signed-in user's latest leave request for this club (status null: none)."""
    status: Optional[LeaveStatus] = None
    scope: Optional[LeaveScope] = None


class LeaveRequestOut(PersonOut):
    id: int
    club_id: int
    club_name: str
    scope: LeaveScope
    reason: Optional[str] = None
    status: LeaveStatus
    created_at: datetime
    reviewed_at: Optional[datetime] = None


LeaveRequestPage = Page[LeaveRequestOut]


class LeaveReview(BaseModel):
    action: Literal["approve", "reject"]


# ── Roster ───────────────────────────────────────────────
class RosterEntry(BaseModel):
    user_id: int
    name: str
    # Detailed view only (the club's working team); everyone else sees names
    course: Optional[str] = None
    interests: Optional[str] = None
    roles: List[ClubRoleKind] = []
    title: Optional[str] = None


class Roster(BaseModel):
    detailed: bool
    items: List[RosterEntry]


# ── Announcements ────────────────────────────────────────
AnnouncementText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]


class AnnouncementIn(BaseModel):
    body: AnnouncementText


class AnnouncementCommentOut(BaseModel):
    id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    body: str
    created_at: datetime


class ReactionCount(BaseModel):
    emoji: str
    count: int
    mine: bool


class AnnouncementOut(BaseModel):
    id: int
    club_id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_title: Optional[str] = None       # e.g. "President" / "Editor"
    body: str
    created_at: datetime
    reactions: List[ReactionCount]
    comments: List[AnnouncementCommentOut]


AnnouncementPage = Page[AnnouncementOut]


class ReactionIn(BaseModel):
    emoji: str


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
    event_id: Optional[int] = None
    club_id: Optional[int] = None
    discussion_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    items: List[NotificationOut]
    unread: int
