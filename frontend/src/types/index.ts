// ── Auth / User ──────────────────────────────────────────
// Account type is global (mirrors AccountType in backend/app/models/user.py).
// student / faculty come from the email domain; alumni is set by the DSW;
// dsw (Dean of Student Welfare office) and platform_admin (tech team) are appointed.
export type AccountType = 'student' | 'faculty' | 'alumni' | 'dsw' | 'platform_admin'

// Club roles are per club (mirrors ClubRoleKind / ClubRoleStatus in backend/app/models/membership.py)
export type ClubRoleKind = 'member' | 'editor' | 'owner' | 'faculty_coordinator'
export type ClubRoleStatus = 'pending' | 'active' | 'rejected' | 'ended'

export interface ClubRole {
  id: number
  club_id: number
  club_name: string
  role: ClubRoleKind
  status: ClubRoleStatus
  title: string | null
  created_at: string
}

export interface User {
  id: number
  name: string
  email: string
  account_type: AccountType
  reg_no?: string
  course?: string
  phone?: string       // 10 digits; "0000000000" = placeholder on older accounts
  interests?: string   // comma-separated tag ids
  created_at: string
  club_roles: ClubRole[]   // current roles: pending, active, rejected
}

// ── Admin people lists ───────────────────────────────────
export interface Person {
  user_id: number
  name: string
  email: string
  phone: string | null
  reg_no: string | null
  course: string | null
}

export interface Registrant extends Person {
  registered_at: string
}

// A club role with the person holding it: club team lists and the DSW's review queue
export interface ClubRoleDetail extends Person {
  id: number
  club_id: number
  club_name: string
  role: ClubRoleKind
  status: ClubRoleStatus
  title: string | null
  proposed_by_name: string | null
  multi_club_exception: boolean
  created_at: string
  reviewed_at: string | null
}

export interface Account extends Person {
  account_type: AccountType
  is_active: boolean
  created_at: string
}

export interface AuditEntry {
  id: number
  actor_name: string | null   // null = done from the command line / system
  action: string              // e.g. "club_role.approve"
  entity_type: string
  entity_id: number | null
  details: Record<string, unknown>
  created_at: string
}

export interface ClubMember extends Person {
  joined_at: string
  registered_events: { id: number; title: string }[]   // this club's events they registered for
}

// ── Club ─────────────────────────────────────────────────
export interface Club {
  id: number
  name: string
  abbr: string
  description: string
  color: string
  tags: string        // comma-separated — use splitTags() helper
  member_count: number
  is_open: boolean
  instagram?: string
  linkedin?: string
}

// ── Event ────────────────────────────────────────────────
export interface Event {
  id: number
  title: string
  description: string
  club_id: number
  club_name: string
  start_date: string
  end_date: string
  reg_deadline?: string
  date_display: string
  tags: string        // comma-separated
  team_size?: string
  poster_url?: string
  is_hot: boolean
  created_at: string

  // ── New fields ──
  venue?: string
  time_info?: string
  registration_fee?: string
  prize_pool?: string
  contact_info?: string
}

// ── Paginated listings ───────────────────────────────────
export interface Page<T> {
  items: T[]
  total: number        // matching rows across all pages
}

// Query params of GET /api/events (see list_events in backend/app/api/routes/events.py)
export interface EventFilters {
  tag?: string
  tags?: string        // comma-separated: events with ANY of these tags
  club_id?: number
  hot?: boolean
  q?: string           // search title / club / description / tags
  upcoming?: boolean   // only events that haven't ended
  date_from?: string   // YYYY-MM-DD: still running on/after
  date_to?: string     // YYYY-MM-DD: starting on/before
  ids?: string         // comma-separated event ids
  order?: 'asc' | 'desc'
}

// Query params of GET /api/clubs
export interface ClubFilters {
  q?: string
}

// ── Discussion ───────────────────────────────────────────
export interface Discussion {
  id: number
  event_id: number
  user_id: number
  user_name: string
  user_role: AccountType
  content: string
  parent_id: number | null
  is_official: boolean    // author is an admin of the event's club → show "Admin" badge
  created_at: string
  edited_at: string | null
  replies: Discussion[]
}

export type DiscussionPage = Page<Discussion>   // total = top-level comments only

// ── Notification ─────────────────────────────────────────
export interface Notification {
  id: number
  kind: string            // "reply" | "comment" | "mention"
  message: string
  event_id: number
  discussion_id: number | null
  is_read: boolean
  created_at: string
}

export interface NotificationList {
  items: Notification[]
  unread: number
}

// ── Permissions (mirror the User methods in backend/app/models/user.py) ──
export const TEAM_ROLES: ClubRoleKind[] = ['owner', 'editor', 'faculty_coordinator']

export const ACCOUNT_LABELS: Record<AccountType, string> = {
  student: 'Student', faculty: 'Faculty', alumni: 'Alumni', dsw: 'DSW', platform_admin: 'Tech team',
}

export const ROLE_LABELS: Record<ClubRoleKind, string> = {
  member: 'Member', editor: 'Editor', owner: 'Owner', faculty_coordinator: 'Faculty coordinator',
}

export const activeRoles = (user: User | null, ...kinds: ClubRoleKind[]): ClubRole[] =>
  (user?.club_roles ?? []).filter(r => r.status === 'active' && (kinds.length === 0 || kinds.includes(r.role)))

// The clubs this user helps run (one entry per club)
export const teamClubs = (user: User | null): { id: number; name: string }[] =>
  [...new Map(activeRoles(user, ...TEAM_ROLES).map(r => [r.club_id, { id: r.club_id, name: r.club_name }])).values()]

export const canManage = (user: User | null, clubId: number): boolean =>
  activeRoles(user, ...TEAM_ROLES).some(r => r.club_id === clubId)

// May delete any comment on this club's events
export const canModerate = (user: User | null, clubId: number): boolean =>
  user?.account_type === 'dsw' || canManage(user, clubId)

// ── UI helpers ───────────────────────────────────────────
export const TAG_COLORS: Record<string, string> = {
  hackathon: '#D4561A', tech: '#3B82F6', coding: '#06B6D4',
  music: '#EF4444',     dance: '#F59E0B', photography: '#E879F9',
  art: '#8B5CF6',       robotics: '#06B6D4', film: '#A855F7',
  literature: '#10B981', sports: '#22C55E', social: '#F43F5E',
}

export const ALL_TAGS = [
  { id: 'tech',        label: 'Technology' },
  { id: 'hackathon',  label: 'Hackathon' },
  { id: 'photography',label: 'Photography' },
  { id: 'dance',      label: 'Dance' },
  { id: 'music',      label: 'Music' },
  { id: 'coding',     label: 'Competitive Coding' },
  { id: 'art',        label: 'Art & Design' },
  { id: 'robotics',   label: 'Robotics' },
  { id: 'film',       label: 'Film & Media' },
  { id: 'literature', label: 'Literature' },
  { id: 'sports',     label: 'Sports' },
  { id: 'social',     label: 'Social Impact' },
]

// "Dr. Meenakshi Rao" -> "Meenakshi" (titles like Dr. / Prof. are skipped); initialOf -> "M"
export const firstName = (name: string | undefined): string =>
  name?.split(' ').find(w => w && !w.endsWith('.')) ?? name ?? ''
export const initialOf = (name: string | undefined): string => (firstName(name)[0] ?? 'U').toUpperCase()

export const splitTags = (tags: string): string[] =>
  tags.split(',').map(t => t.trim()).filter(Boolean)

export const getEventColor = (event: Event): string => {
  const tags = splitTags(event.tags)
  for (const t of tags) if (TAG_COLORS[t]) return TAG_COLORS[t]
  return '#D4561A'
}

export const getTimeAgo = (dateStr: string): string => {
  const then = new Date(dateStr)
  const mins = Math.floor((Date.now() - then.getTime()) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return then.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}
