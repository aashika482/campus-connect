import { create } from 'zustand'

export type ToastType = 'success' | 'error' | 'info' | 'warn'

export interface Toast {
  id: number
  msg: string
  type: ToastType
  exiting: boolean
}

interface ToastState {
  toasts: Toast[]
  toast: (msg: string, type?: ToastType, duration?: number) => void
  dismiss: (id: number) => void
}

let _nextId = 1

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],

  toast: (msg, type = 'info', duration = 3200) => {
    const id = _nextId++
    set(s => ({ toasts: [...s.toasts.slice(-4), { id, msg, type, exiting: false }] }))

    setTimeout(() => {
      set(s => ({ toasts: s.toasts.map(t => t.id === id ? { ...t, exiting: true } : t) }))
      setTimeout(() => get().dismiss(id), 280)
    }, duration)
  },

  dismiss: (id) => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),
}))
