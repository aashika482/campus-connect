import { useState, useEffect, useCallback, useRef } from 'react'
import { eventsApi, clubsApi } from '@/api/client'
import { useToastStore } from '@/context/toastStore'
import type { Event, Club, Page, EventFilters, ClubFilters } from '@/types'

// The events and clubs listings are paginated: the API returns { items, total }.
// Two ways to use them:
//  - usePagedEvents / usePagedClubs: a "Load more" list (Events page, Clubs page, Home sections)
//  - useEventsWhere / fetchAll*: everything matching a NARROW filter (a month, a club,
//    a user's saved ids), fetched page by page. Never use it for an unfiltered list.

const MAX_PAGE = 100   // the API's largest allowed page

// The value, but only after it stopped changing for `ms` (so typing doesn't fire a request per key)
export function useDebounced<T>(value: T, ms = 300): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return debounced
}

// ── Generic "Load more" list ─────────────────────────────
function usePaged<T>(fetchPage: (params: object) => Promise<{ data: Page<T> }>, filters: object | null, pageSize: number) {
  const [items, setItems] = useState<T[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(filters !== null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)
  // Each request gets a number; a slow, outdated response (e.g. from a previous search)
  // must never overwrite the results of a newer one.
  const requestId = useRef(0)
  const key = JSON.stringify(filters)

  useEffect(() => {
    if (filters === null) { setItems([]); setTotal(0); setLoading(false); return }   // null = don't fetch yet
    const id = ++requestId.current
    setLoading(true)
    setError(null)
    fetchPage({ ...filters, limit: pageSize, offset: 0 })
      .then(r => { if (id === requestId.current) { setItems(r.data.items); setTotal(r.data.total) } })
      .catch(() => { if (id === requestId.current) setError('Failed to load') })
      .finally(() => { if (id === requestId.current) setLoading(false) })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, pageSize, tick])

  const loadMore = useCallback(async () => {
    if (filters === null) return
    const id = requestId.current
    setLoadingMore(true)
    try {
      const r = await fetchPage({ ...filters, limit: pageSize, offset: items.length })
      if (id === requestId.current) { setItems(p => [...p, ...r.data.items]); setTotal(r.data.total) }
    } catch {
      if (id === requestId.current) setError('Failed to load more')
    } finally {
      setLoadingMore(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, pageSize, items.length])

  const refresh = useCallback(() => setTick(t => t + 1), [])

  return { items, setItems, total, loading, loadingMore, error, hasMore: items.length < total, loadMore, refresh }
}

// Fetch every page of a (narrowly filtered) listing
async function fetchAll<T>(fetchPage: (params: object) => Promise<{ data: Page<T> }>, filters: object): Promise<T[]> {
  const all: T[] = []
  for (;;) {
    const { data } = await fetchPage({ ...filters, limit: MAX_PAGE, offset: all.length })
    all.push(...data.items)
    if (data.items.length === 0 || all.length >= data.total) return all
  }
}

export const fetchAllEvents = (filters: EventFilters) => fetchAll<Event>(eventsApi.list, filters)
export const fetchAllClubs  = (filters: ClubFilters = {}) => fetchAll<Club>(clubsApi.list, filters)

// ── Events ───────────────────────────────────────────────
export function usePagedEvents(filters: EventFilters | null, pageSize = 12) {
  const { items, ...rest } = usePaged<Event>(eventsApi.list, filters, pageSize)
  return { events: items, ...rest }
}

// All events matching a narrow filter. Pass null to wait (e.g. until an id is known).
export function useEventsWhere(filters: EventFilters | null) {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(filters !== null)
  const [tick, setTick] = useState(0)
  const requestId = useRef(0)
  const key = JSON.stringify(filters)

  useEffect(() => {
    if (filters === null) { setEvents([]); setLoading(false); return }
    const id = ++requestId.current
    setLoading(true)
    fetchAllEvents(filters)
      .then(evs => { if (id === requestId.current) setEvents(evs) })
      .catch(() => { if (id === requestId.current) setEvents([]) })
      .finally(() => { if (id === requestId.current) setLoading(false) })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick])

  const refresh = useCallback(() => setTick(t => t + 1), [])
  return { events, loading, refresh }
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
export function usePagedClubs(filters: ClubFilters | null, pageSize = 12) {
  const { items, setItems, ...rest } = usePaged<Club>(clubsApi.list, filters, pageSize)

  // After join/leave, show the new member count without refetching the list
  const updateMemberCount = useCallback((clubId: number, count: number) => {
    setItems(p => p.map(c => (c.id === clubId ? { ...c, member_count: count } : c)))
  }, [setItems])

  return { clubs: items, updateMemberCount, ...rest }
}

export function useUserClubs() {
  const [joinedClubs, setJoinedClubs] = useState<number[]>([])
  const { toast } = useToastStore()

  useEffect(() => {
    clubsApi.myClubs()
      .then(r => setJoinedClubs(r.data))
      .catch(() => {})
  }, [])

  // onCount receives the club's new member count from the server
  const toggleMembership = async (club: Club, onCount?: (count: number) => void) => {
    const isMember = joinedClubs.includes(club.id)
    setJoinedClubs(p => isMember ? p.filter(x => x !== club.id) : [...p, club.id])
    try {
      if (isMember) {
        const r = await clubsApi.leave(club.id)
        onCount?.(r.data.member_count)
        toast(`Left ${club.name}`, 'info')
      } else {
        const r = await clubsApi.join(club.id)
        onCount?.(r.data.member_count)
        toast(`Joined ${club.name}!`, 'success')
      }
    } catch {
      setJoinedClubs(p => isMember ? [...p, club.id] : p.filter(x => x !== club.id))
      toast('Something went wrong', 'error')
    }
  }

  return { joinedClubs, toggleMembership }
}
