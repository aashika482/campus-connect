// ── Auth / User ──────────────────────────────────────────
export type UserRole = 'student' | 'member'

export interface User {
  id: number
  name: string
  email: string
  role: UserRole
  reg_no?: string
  course?: string
  club_name?: string
  position?: string
  interests?: string   // comma-separated tag ids
  created_at: string
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
