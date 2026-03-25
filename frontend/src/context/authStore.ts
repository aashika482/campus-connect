import { create } from 'zustand'
import type { User } from '@/types'
import { authApi, usersApi } from '@/api/client'

interface AuthState {
  user: User | null
  isLoading: boolean
  isInitialized: boolean

  login: (email: string, password: string, role: 'student' | 'member') => Promise<void>
  registerStudent: (data: object) => Promise<void>
  registerMember: (data: object) => Promise<void>
  logout: () => void
  initFromStorage: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  isInitialized: false,

  login: async (email, password, role) => {
    set({ isLoading: true })
    try {
      const { data } = await authApi.login({ email, password, role })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user })
    } finally {
      set({ isLoading: false })
    }
  },

  registerStudent: async (payload) => {
    set({ isLoading: true })
    try {
      const { data } = await authApi.registerStudent(payload)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user })
    } finally {
      set({ isLoading: false })
    }
  },

  registerMember: async (payload) => {
    set({ isLoading: true })
    try {
      const { data } = await authApi.registerMember(payload)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ user: data.user })
    } finally {
      set({ isLoading: false })
    }
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
}))
