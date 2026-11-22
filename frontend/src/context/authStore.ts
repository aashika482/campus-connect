import { create } from 'zustand'
import type { User } from '@/types'
import { authApi, usersApi } from '@/api/client'

// After a correct password: the second step still to do
export interface SecondStep { method: 'email' | 'totp'; challenge: string }

type Session = { access_token: string; refresh_token: string; user: User; device_token?: string | null }

interface AuthState {
  user: User | null
  isLoading: boolean
  isInitialized: boolean

  login: (email: string, password: string) => Promise<SecondStep | null>   // null: signed in (remembered browser)
  verify: (challenge: string, code: string, remember: boolean) => Promise<void>
  microsoft: (idToken: string) => Promise<void>
  register: (data: object) => Promise<void>   // details + the emailed code; the domain decides student or faculty
  logout: () => void
  initFromStorage: () => Promise<void>
  setUser: (user: User) => void              // after the profile is edited
  refreshUser: () => Promise<void>           // after anything that changes roles (joining, approvals)
}

// "Remember this browser" for the second step: one token per account (so two people sharing a
// browser don't replace each other's), kept across logouts
const DEVICE_KEY = 'device_tokens'
const deviceTokens = (): Record<string, string> => {
  try { return JSON.parse(localStorage.getItem(DEVICE_KEY) ?? '{}') } catch { return {} }
}

export const useAuthStore = create<AuthState>((set) => {
  // Every way of signing in ends here: keep the tokens and the signed-in user
  const startSession = (data: Session) => {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    if (data.device_token) localStorage.setItem(DEVICE_KEY, JSON.stringify({ ...deviceTokens(), [data.user.email]: data.device_token }))
    set({ user: data.user })
  }
  const busy = async <T,>(work: () => Promise<T>): Promise<T> => {
    set({ isLoading: true })
    try { return await work() } finally { set({ isLoading: false }) }
  }

  return {
    user: null,
    isLoading: false,
    isInitialized: false,

    login: (email, password) => busy(async () => {
      const { data } = await authApi.login({ email, password, device_token: deviceTokens()[email.trim().toLowerCase()] ?? null })
      if (data.access_token) { startSession(data); return null }
      return { method: data.second_step, challenge: data.challenge }
    }),
    verify: (challenge, code, remember) => busy(async () => startSession((await authApi.loginVerify(challenge, code, remember)).data)),
    microsoft: (idToken) => busy(async () => startSession((await authApi.microsoft(idToken)).data)),
    register: (payload) => busy(async () => startSession((await authApi.register(payload)).data)),

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
