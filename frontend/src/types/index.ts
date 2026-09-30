// frontend/src/types/index.ts
// REPLACE your existing file with this

// ── Auth / User ──────────────────────────────────────────
export type UserRole = 'student' | 'member'

export interface User {
  id: number
  name: string
  email: string
  role: UserRole
  reg_no?: string
  course?: string
  phone?: string       // 10 digits; "0000000000" = placeholder on older accounts
  club_name?: string
  position?: string
  interests?: string   // comma-separated tag ids
  created_at: string
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

export interface ClubMember extends Person {
  joined_at: string
  registered_events: { id: number; title: string }[]   // this club's events they registered for
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface LoginPayload {
  email: string
  password: string
  role: UserRole
}

export interface RegisterStudentPayload {
  name: string
  email: string
  password: string
  reg_no?: string
  course?: string
  phone?: string
  interests?: string[]
}

export interface RegisterMemberPayload {
  name: string
  email: string
  password: string
  club_name: string
  position?: string
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

// ── Paginated listings (GET /api/events, GET /api/clubs) ──
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
  name?: string        // exact name
}

// ── Discussion ───────────────────────────────────────────
export interface Discussion {
  id: number
  event_id: number
  user_id: number
  user_name: string
  user_role: string       // "student" | "member"
  content: string
  parent_id: number | null
  is_official: boolean    // author is an admin of the event's club → show "Admin" badge
  created_at: string
  edited_at: string | null
  replies: Discussion[]
}

export interface DiscussionPage {
  items: Discussion[]
  total: number           // total top-level comments, across all pages
}

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
