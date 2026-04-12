// frontend/src/api/client.ts
// REPLACE your existing file with this
// Changes: added discussionsApi section

import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

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

// ── Auth ─────────────────────────────────────────────────
export const authApi = {
  login:           (data: object) => api.post('/auth/login', data),
  registerStudent: (data: object) => api.post('/auth/register/student', data),
  registerMember:  (data: object) => api.post('/auth/register/member', data),
  refresh:         (data: object) => api.post('/auth/refresh', data),
  logout:          ()             => api.post('/auth/logout'),
}

// ── Events ───────────────────────────────────────────────
export const eventsApi = {
  list:               (params?: object)          => api.get('/events', { params }),
  get:                (id: number)               => api.get(`/events/${id}`),
  create:             (data: object)             => api.post('/events', data),
  update:             (id: number, data: object) => api.patch(`/events/${id}`, data),
  delete:             (id: number)               => api.delete(`/events/${id}`),
  register:           (id: number)               => api.post(`/events/${id}/register`),
  unregister:         (id: number)               => api.delete(`/events/${id}/register`),
  myRegistered:       ()                         => api.get('/events/me/registered'),
  registrationCount:  (id: number)               => api.get(`/events/${id}/registrations/count`),
  save:               (id: number)               => api.post(`/events/${id}/save`),
  unsave:             (id: number)               => api.delete(`/events/${id}/save`),
  mySaved:            ()                         => api.get('/events/me/saved'),
}

// ── Clubs ────────────────────────────────────────────────
export const clubsApi = {
  list:     ()           => api.get('/clubs'),
  get:      (id: number) => api.get(`/clubs/${id}`),
  join:     (id: number) => api.post(`/clubs/${id}/join`),
  leave:    (id: number) => api.delete(`/clubs/${id}/join`),
  myClubs:  ()           => api.get('/clubs/me/joined'),
}

// ── Users ────────────────────────────────────────────────
export const usersApi = {
  me:     ()           => api.get('/users/me'),
  update: (data: object) => api.patch('/users/me', data),
}

// ── Discussions ──────────────────────────────────────────
export const discussionsApi = {
  list:       (eventId: number)                          => api.get(`/discussions/${eventId}`),
  create:     (eventId: number, data: { content: string }) => api.post(`/discussions/${eventId}`, data),
  reply:      (eventId: number, commentId: number, data: { content: string }) =>
                api.post(`/discussions/${eventId}/${commentId}/reply`, data),
  delete:     (eventId: number, commentId: number)       => api.delete(`/discussions/${eventId}/${commentId}`),
  adminFeed:  ()                                         => api.get('/discussions/admin/feed'),
}
