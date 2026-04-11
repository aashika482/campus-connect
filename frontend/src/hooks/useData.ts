import { useState, useEffect, useCallback } from 'react'
import { eventsApi, clubsApi } from '@/api/client'
import { useToastStore } from '@/context/toastStore'
import type { Event, Club } from '@/types'

// ── Events ───────────────────────────────────────────────
export function useEvents(params?: object) {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  const refresh = useCallback(() => setTick(t => t + 1), [])

  useEffect(() => {
    setLoading(true)
    eventsApi.list(params)
      .then(r => setEvents(r.data))
      .catch(() => setError('Failed to load events'))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params), tick])

  return { events, loading, error, refresh }
}

export function useUserEvents() {
  const [registered, setRegistered] = useState<number[]>([])
  const [saved, setSaved] = useState<number[]>([])
  const { toast } = useToastStore()

  const load = useCallback(async () => {
    try {
      const [reg, sav] = await Promise.all([
        eventsApi.myRegistered(),
        eventsApi.mySaved(),
      ])
      setRegistered(reg.data)
      setSaved(sav.data)
    } catch { /* not logged in yet */ }
  }, [])

  useEffect(() => { load() }, [load])

  const toggleSave = async (event: Event) => {
    const isSaved = saved.includes(event.id)
    setSaved(p => isSaved ? p.filter(x => x !== event.id) : [...p, event.id])
    try {
      if (isSaved) {
        await eventsApi.unsave(event.id)
        toast(`Removed "${event.title}" from saved`, 'info')
      } else {
        await eventsApi.save(event.id)
        toast(`Saved "${event.title}"`, 'success')
      }
    } catch {
      setSaved(p => isSaved ? [...p, event.id] : p.filter(x => x !== event.id))
      toast('Something went wrong', 'error')
    }
  }

  const register = async (event: Event) => {
    if (registered.includes(event.id)) return
    setRegistered(p => [...p, event.id])
    try {
      await eventsApi.register(event.id)
      toast(`Registered for ${event.title}! 🎉`, 'success')
    } catch (err: any) {
      setRegistered(p => p.filter(x => x !== event.id))
      toast(err?.response?.data?.detail ?? 'Registration failed', 'error')
    }
  }

  return { registered, saved, toggleSave, register }
}

// ── Clubs ────────────────────────────────────────────────
export function useClubs() {
  const [clubs, setClubs] = useState<Club[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    clubsApi.list()
      .then(r => setClubs(r.data))
      .finally(() => setLoading(false))
  }, [])

  return { clubs, loading }
}

export function useUserClubs() {
  const [joinedClubs, setJoinedClubs] = useState<number[]>([])
  const { toast } = useToastStore()

  useEffect(() => {
    clubsApi.myClubs()
      .then(r => setJoinedClubs(r.data))
      .catch(() => {})
  }, [])

  const toggleMembership = async (club: Club) => {
    const isMember = joinedClubs.includes(club.id)
    setJoinedClubs(p => isMember ? p.filter(x => x !== club.id) : [...p, club.id])
    try {
      if (isMember) {
        await clubsApi.leave(club.id)
        toast(`Left ${club.name}`, 'info')
      } else {
        await clubsApi.join(club.id)
        toast(`Joined ${club.name}!`, 'success')
      }
    } catch {
      setJoinedClubs(p => isMember ? [...p, club.id] : p.filter(x => x !== club.id))
      toast('Something went wrong', 'error')
    }
  }

  return { joinedClubs, toggleMembership }
}
