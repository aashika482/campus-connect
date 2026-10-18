import { create } from 'zustand'
import type { User } from '@/types'
import { authApi, usersApi } from '@/api/client'

interface AuthState {
  user: User | null
  isLoading: boolean
  isInitialized: boolean

  login: (email: string, password: string) => Promise<void>
  register: (data: object) => Promise<void>   // the email's domain decides student or faculty
  logout: () => void
  initFromStorage: () => Promise<void>
  setUser: (user: User) => void              // after the profile is edited
  refreshUser: () => Promise<void>           // after anything that changes roles (joining, approvals)
}

export const useAuthStore = create<AuthState>((set) => {
  // Shared by login and sign-up: keep the tokens and the signed-in user
  const startSession = async (request: Promise<{ data: { access_token: string; refresh_token: string; user: User } }>) => {
    set({ isLoading: true })
    try {
      const { data } = await request
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user })
    } finally {
      set({ isLoading: false })
    }
  }

  return {
    user: null,
    isLoading: false,
    isInitialized: false,

    login: (email, password) => startSession(authApi.login({ email, password })),
    register: (payload) => startSession(authApi.register(payload)),

    setUser: (user) => set({ user }),

    refreshUser: async () => {
      try {
        const { data } = await usersApi.me()
        set({ user: data })
      } catch { /* keep the current user; the next request will surface any auth problem */ }
    },

    logout: () => {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null })
    },

    initFromStorage: async () => {
      const token = localStorage.getItem('access_token')
      if (!token) { set({ isInitialized: true }); return }
      try {
        const { data } = await usersApi.me()
        set({ user: data })
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      } finally {
        set({ isInitialized: true })
      }
    },
  }
})
