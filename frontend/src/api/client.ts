import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
// The same server over WebSockets (http → ws, https → wss)
export const WS_BASE = `${BASE.replace(/^http/, 'ws')}/api`

export const api = axios.create({
  baseURL: `${BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor — attach access token ────────────
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Response interceptor — auto refresh on 401 ──────────
let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true

      if (isRefreshing) {
        return new Promise(resolve => {
          refreshQueue.push(token => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(api(original))
          })
        })
      }

      isRefreshing = true
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post(`${BASE}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })

        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)

        refreshQueue.forEach(cb => cb(data.access_token))
        refreshQueue = []

        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(err)
  }
)

// The message to show for a failed request: the backend's "detail" (a string, or for a
// 422 validation error a list whose first message is used), else the fallback
export function apiError(err: any, fallback: string): string {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg).replace(/^Value error, /, '')
  return fallback
}

// ── Auth ─────────────────────────────────────────────────
export const authApi = {
  config:          ()             => api.get('/auth/config'),   // { email_domains, microsoft_client_id, microsoft_tenant_id }
  login:           (data: object) => api.post('/auth/login', data),           // session, or { second_step, challenge }
  loginVerify:     (challenge: string, code: string, remember: boolean) => api.post('/auth/login/verify', { challenge, code, remember }),
  loginEmailCode:  (challenge: string) => api.post('/auth/login/email-code', { challenge }),
  microsoft:       (idToken: string) => api.post('/auth/microsoft', { id_token: idToken }),
  registerCode:    (email: string) => api.post('/auth/register/code', { email }),   // emails the sign-up code
  register:        (data: object) => api.post('/auth/register', data),       // details + that code
  refresh:         (data: object) => api.post('/auth/refresh', data),
  logout:          ()             => api.post('/auth/logout'),
}

// ── Events ───────────────────────────────────────────────
export const eventsApi = {
  list:               (params?: object)          => api.get('/events', { params }),   // paginated: { items, total }
  get:                (id: number)               => api.get(`/events/${id}`),
  forYou:             (limit = 6)                => api.get('/events/for-you', { params: { limit } }),   // ranked for the user
  create:             (data: object)             => api.post('/events', data),
  update:             (id: number, data: object) => api.patch(`/events/${id}`, data),
  delete:             (id: number)               => api.delete(`/events/${id}`),
  register:           (id: number)               => api.post(`/events/${id}/register`),
  unregister:         (id: number)               => api.delete(`/events/${id}/register`),
  myRegistered:       ()                         => api.get('/events/me/registered'),
  registrationCount:  (id: number)               => api.get(`/events/${id}/registrations/count`),
  registrations:      (id: number)               => api.get(`/events/${id}/registrations`),   // admin, own club
  save:               (id: number)               => api.post(`/events/${id}/save`),
  unsave:             (id: number)               => api.delete(`/events/${id}/save`),
  mySaved:            ()                         => api.get('/events/me/saved'),
}

// ── Clubs ────────────────────────────────────────────────
export const clubsApi = {
  list:     (params?: object) => api.get('/clubs', { params }),   // paginated: { items, total }
  get:      (id: number) => api.get(`/clubs/${id}`),
  join:     (id: number) => api.post(`/clubs/${id}/join`),
  // The club's team only:
  members:  (id: number) => api.get(`/clubs/${id}/members`),
  team:     (id: number) => api.get(`/clubs/${id}/team`),        // owner, editors, faculty (incl. pending)
  requestOwnership: (id: number, title?: string) => api.post(`/clubs/${id}/owner-request`, { title: title || null }),
  proposeEditor:    (id: number, email: string, title?: string) => api.post(`/clubs/${id}/editors`, { email, title: title || null }),
  updateSettings:   (id: number, data: object) => api.patch(`/clubs/${id}/settings`, data),
  applications:     (id: number, params?: object) => api.get(`/clubs/${id}/applications`, { params }),   // { items, total }
  reviewApplication: (id: number, appId: number, action: 'shortlist' | 'recommend' | 'approve' | 'decline') =>
                      api.patch(`/clubs/${id}/applications/${appId}`, { action }),
  // Any signed-in user:
  roster:        (id: number) => api.get(`/clubs/${id}/roster`),          // { detailed, items }
  myApplication: (id: number) => api.get(`/clubs/${id}/application`),
  apply:         (id: number) => api.post(`/clubs/${id}/application`),
  benefits:      (id: number) => api.get(`/clubs/${id}/benefits`),
  addBenefit:    (id: number, data: object) => api.post(`/clubs/${id}/benefits`, data),       // the club's team
  removeBenefit: (id: number, benefitId: number) => api.delete(`/clubs/${id}/benefits/${benefitId}`),
  myLeave:       (id: number) => api.get(`/clubs/${id}/leave`),
  leave:         (id: number, scope: 'working_team' | 'club', reason?: string) =>
                   api.post(`/clubs/${id}/leave`, { scope, reason: reason || null }),
}

// ── Working-team chat (live updates come over the WebSocket at WS_BASE/clubs/{id}/chat/ws) ──
export const chatApi = {
  history: (clubId: number, params?: { before_id?: number; after_id?: number; limit?: number }) =>
             api.get(`/clubs/${clubId}/chat`, { params }),   // { items (oldest first), has_more }
  send:    (clubId: number, body: string) => api.post(`/clubs/${clubId}/chat`, { body }),
  delete:  (clubId: number, id: number) => api.delete(`/clubs/${clubId}/chat/${id}`),
}

// ── New club requests ────────────────────────────────────
export const clubRequestsApi = {
  submit: (data: object) => api.post('/club-requests', data),             // a student
  mine:   ()             => api.get('/club-requests/mine'),
  forMe:  ()             => api.get('/club-requests/for-me'),             // faculty: requests naming them
  queue:  (params?: object) => api.get('/club-requests', { params }),     // the DSW: { items, total }
  decide: (id: number, action: 'confirm' | 'decline' | 'approve' | 'reject', note?: string) =>
            api.patch(`/club-requests/${id}`, { action, note: note || null }),   // → { club_id, skipped }
}

// ── Club announcements (the club's working team) ─────────
export const announcementsApi = {
  list:          (clubId: number, params?: { before_id?: number; limit?: number }) =>
                   api.get(`/clubs/${clubId}/announcements`, { params }),   // { items, total }
  post:          (clubId: number, body: string) => api.post(`/clubs/${clubId}/announcements`, { body }),
  delete:        (clubId: number, id: number) => api.delete(`/clubs/${clubId}/announcements/${id}`),
  comment:       (clubId: number, id: number, body: string) => api.post(`/clubs/${clubId}/announcements/${id}/comments`, { body }),
  deleteComment: (clubId: number, id: number, commentId: number) =>
                   api.delete(`/clubs/${clubId}/announcements/${id}/comments/${commentId}`),
  react:         (clubId: number, id: number, emoji: string) => api.post(`/clubs/${clubId}/announcements/${id}/reactions`, { emoji }),
}

// ── Users ────────────────────────────────────────────────
export const usersApi = {
  me:     ()           => api.get('/users/me'),
  update: (data: object) => api.patch('/users/me', data),
  setPassword:   (newPassword: string, currentPassword?: string) =>
                   api.post('/users/me/password', { new_password: newPassword, current_password: currentPassword || null }),
  totpSetup:     () => api.post('/users/me/two-step/totp'),               // { secret, uri }
  setSecondStep: (method: 'email' | 'totp', secret?: string, code?: string) => api.put('/users/me/two-step', { method, secret, code }),
}

// ── Admin: DSW office and tech team (paginated lists: { items, total }) ──
export const adminApi = {
  clubRoles:     (params?: object) => api.get('/admin/dsw/club-roles', { params }),   // { status, club_id }
  reviewRole:    (id: number, action: 'approve' | 'reject' | 'end', multiClubException = false) =>
                   api.patch(`/admin/dsw/club-roles/${id}`, { action, multi_club_exception: multiClubException }),
  assignFaculty: (clubId: number, email: string) => api.post(`/admin/dsw/clubs/${clubId}/faculty`, { email }),
  accounts:      (params?: object) => api.get('/admin/dsw/accounts', { params }),     // { q, account_type }
  setAccountType: (userId: number, accountType: 'student' | 'faculty' | 'alumni') =>
                   api.patch(`/admin/dsw/accounts/${userId}`, { account_type: accountType }),
  setHot:        (eventId: number, isHot: boolean) => api.patch(`/admin/dsw/events/${eventId}/hot`, { is_hot: isHot }),
  dswAccounts:   () => api.get('/admin/platform/dsw-accounts'),
  grantDsw:      (email: string) => api.post('/admin/platform/dsw-accounts', { email }),
  removeDsw:     (userId: number) => api.delete(`/admin/platform/dsw-accounts/${userId}`),
  auditLog:      (params?: object) => api.get('/admin/audit-log', { params }),
  leaveRequests: (params?: object) => api.get('/admin/dsw/leave-requests', { params }),   // { status }
  evaluations:   (year?: string) => api.get('/admin/dsw/evaluations', { params: year ? { year } : {} }),   // { years, items }
  decideLeave:   (id: number, action: 'approve' | 'reject') => api.patch(`/admin/dsw/leave-requests/${id}`, { action }),
}

// ── Discussions ──────────────────────────────────────────
// list/adminFeed are paginated: pass before_id = id of the last comment you have to get the next page
type PageParams = { before_id?: number; limit?: number }

export const discussionsApi = {
  list:       (eventId: number, params?: PageParams)     => api.get(`/discussions/${eventId}`, { params }),
  create:     (eventId: number, data: { content: string }) => api.post(`/discussions/${eventId}`, data),
  reply:      (eventId: number, commentId: number, data: { content: string }) =>
                api.post(`/discussions/${eventId}/${commentId}/reply`, data),
  edit:       (eventId: number, commentId: number, data: { content: string }) =>
                api.patch(`/discussions/${eventId}/${commentId}`, data),
  delete:     (eventId: number, commentId: number)       => api.delete(`/discussions/${eventId}/${commentId}`),
  adminFeed:  (clubId: number, params?: PageParams)      => api.get('/discussions/admin/feed', { params: { club_id: clubId, ...params } }),
}

// ── Uploads (signed Cloudinary; admin only) ──────────────
export const uploadsApi = {
  status:    () => api.get('/uploads/status'),       // { enabled }
  signature: () => api.post('/uploads/signature'),   // params to send to Cloudinary with the file
}

// ── Notifications ────────────────────────────────────────
export const notificationsApi = {
  list:        ()           => api.get('/notifications'),
  markRead:    (id: number) => api.post(`/notifications/${id}/read`),
  markAllRead: ()           => api.post('/notifications/read-all'),
}
