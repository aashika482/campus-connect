import React, { useState, useEffect } from 'react'
import { useAuthStore } from '@/context/authStore'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useEventsWhere, useUserEvents } from '@/hooks/useData'
import { getEventColor, splitTags, getTimeAgo, ALL_TAGS, TAG_COLORS } from '@/types'
import type { Event, Discussion } from '@/types'
import { eventsApi, clubsApi, discussionsApi, usersApi } from '@/api/client'
import { ImageUpload } from '@/components/ui/ImageUpload'
import { useToastStore } from '@/context/toastStore'
import { MembersTab, RegistrationsTab } from './AdminPeople'

// ── SavedPage ─────────────────────────────────────────────
export function SavedPage({ onViewEvent }: { onViewEvent: (ev: Event) => void }) {
  const { saved, toggleSave, registered } = useUserEvents()
  // Fetch just the saved events; the filter also hides one the moment it's un-saved
  const { events } = useEventsWhere(saved.length ? { ids: saved.join(',') } : null)
  const savedEvents = events.filter(e => saved.includes(e.id))

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Bookmarked</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 42, fontWeight: 800, letterSpacing: '-2px' }}>
            Saved<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>{savedEvents.length} saved events</p>
        </div>
      </div>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 40px' }}>
        {savedEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <div style={{ fontSize: 32, marginBottom: 16 }}>☆</div>
            <div style={{ fontFamily: 'var(--head)', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Nothing saved yet</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>Bookmark events to find them here</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 18 }}>
            {savedEvents.map(ev => (
              <div key={ev.id} className="pcard au" onClick={() => onViewEvent(ev)}>
                {ev.poster_url
                  ? <img src={ev.poster_url} alt={ev.title} onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
                  : <div style={{ width: '100%', height: '100%', background: `linear-gradient(155deg, ${getEventColor(ev)}22 0%, var(--dark2) 65%)` }} />
                }
                <div className="pcard-grad" />
                <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 2 }}>
                  <button onClick={e => { e.stopPropagation(); toggleSave(ev) }}
                    style={{ width: 28, height: 28, background: 'rgba(9,9,9,0.6)', border: '1px solid rgba(242,234,220,0.14)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--orange)', fontSize: 13 }}>★</button>
                </div>
                <div className="pcard-body" style={{ zIndex: 2 }}>
                  <h3 style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 700, lineHeight: 1.25, marginBottom: 5 }}>{ev.title}</h3>
                  <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'rgba(242,234,220,0.45)' }}>{ev.date_display}</div>
                  {registered.includes(ev.id) && <div style={{ marginTop: 4, fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981' }}>✓ Registered</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── ProfilePage ───────────────────────────────────────────
export function ProfilePage() {
  const { user, logout, setUser } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToastStore()
  const { registered, saved } = useUserEvents()
  const { events: registeredEvents } = useEventsWhere(registered.length ? { ids: registered.join(',') } : null)

  // Phone editing ("0000000000" is the placeholder given to older accounts)
  const hasPhone = !!user?.phone && user.phone !== '0000000000'
  const [editingPhone, setEditingPhone] = useState(false)
  const [phoneInput, setPhoneInput] = useState('')
  const [savingPhone, setSavingPhone] = useState(false)
  const savePhone = async () => {
    setSavingPhone(true)
    try {
      const r = await usersApi.update({ phone: phoneInput })
      setUser(r.data)
      setEditingPhone(false)
      toast('Phone number updated', 'success')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      toast(Array.isArray(detail) ? 'Enter a valid 10-digit phone number' : 'Failed to update phone', 'error')
    } finally {
      setSavingPhone(false)
    }
  }

  const handleLogout = () => { logout(); navigate('/login') }
  const userTags = user?.interests?.split(',').filter(Boolean) ?? []

  const stats = [
    { label: 'Registered',  val: registered.length },
    { label: 'Saved',       val: saved.length },
    { label: 'Interests',   val: userTags.length },
  ]

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 900, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 24 }}>
          <div style={{ width: 72, height: 72, background: 'var(--orange)', color: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 28, fontFamily: 'var(--head)', flexShrink: 0 }}>
            {(user?.name ?? 'U')[0].toUpperCase()}
          </div>
          <div>
            <h1 style={{ fontFamily: 'var(--head)', fontSize: 32, fontWeight: 800, letterSpacing: '-1px' }}>{user?.name}</h1>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 4 }}>
              {user?.email} · <span style={{ color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 1 }}>{user?.role}</span>
            </div>
            {user?.reg_no && <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 3 }}>{user.reg_no} · {user.course}</div>}
            {user?.club_name && <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 3 }}>{user.club_name} · {user.position}</div>}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>
              {editingPhone ? (
                <>
                  <input className="inp" type="tel" value={phoneInput} onChange={e => setPhoneInput(e.target.value)} autoFocus
                    onKeyDown={e => { if (e.key === 'Enter') savePhone(); if (e.key === 'Escape') setEditingPhone(false) }}
                    placeholder="98765 43210" style={{ width: 160, padding: '5px 9px', fontSize: 11 }} />
                  <button onClick={savePhone} disabled={savingPhone || !phoneInput.trim()} style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)' }}>{savingPhone ? 'Saving…' : 'Save'}</button>
                  <button onClick={() => setEditingPhone(false)} style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>Cancel</button>
                </>
              ) : (
                <>
                  <span>📞 {hasPhone ? user!.phone : <span style={{ color: 'var(--orange)' }}>No phone number added</span>}</span>
                  <button onClick={() => { setPhoneInput(hasPhone ? user!.phone! : ''); setEditingPhone(true) }}
                    style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textDecoration: 'underline', textUnderlineOffset: 3 }}>
                    {hasPhone ? 'Edit' : 'Add'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 40px' }}>
        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 36 }}>
          {stats.map(s => (
            <div key={s.label} className="stat-card">
              <div style={{ fontFamily: 'var(--head)', fontSize: 34, fontWeight: 800, color: 'var(--orange)' }}>{s.val}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 2, marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Interests */}
        {userTags.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Your Interests</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {userTags.map(t => <span key={t} className="tag" style={{ color: 'var(--orange)', borderColor: 'rgba(212,86,26,0.35)' }}>{t}</span>)}
            </div>
          </div>
        )}

        {/* Registered events */}
        {registered.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Registered Events</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {registeredEvents.map(ev => (
                <button
                  key={ev.id}
                  onClick={() => navigate(`/events/${ev.id}`)}
                  style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: `3px solid ${getEventColor(ev)}`, cursor: 'pointer', textAlign: 'left', width: '100%', transition: 'background 0.15s' }}
                  onMouseOver={e => (e.currentTarget.style.background = 'var(--dark3)')}
                  onMouseOut={e => (e.currentTarget.style.background = 'var(--dark2)')}
                >
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: getEventColor(ev), minWidth: 56 }}>{ev.date_display}</span>
                  <span style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 600, flex: 1 }}>{ev.title}</span>
                  <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 7px', flexShrink: 0 }}>✓ Going</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
          {user?.role === 'member' && (
            <button onClick={() => navigate('/admin')} className="btn-p">
              Club Dashboard →
            </button>
          )}
          <button onClick={handleLogout} className="btn-g">Sign Out</button>
        </div>
      </div>
    </div>
  )
}

// ── CalendarPage ──────────────────────────────────────────
const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December']

// "YYYY-MM-DD" in LOCAL time. (toISOString() converts to UTC, which shifts the
// date by a day in some time zones, so we build the key by hand.)
const dayKey = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

// Parse an API date ("2026-05-14") as local midnight; new Date("2026-05-14") would be UTC midnight
const parseDay = (s: string) => new Date(s + 'T00:00:00')

// Months are counted as year*12 + month so prev/next/jump are simple +/- arithmetic
const toIndex = (year: number, month: number) => year * 12 + month

export function CalendarPage({ onViewEvent }: { onViewEvent: (ev: Event) => void }) {
  const { registered } = useUserEvents()
  const today = new Date()
  const todayKey = dayKey(today)
  const todayIndex = toIndex(today.getFullYear(), today.getMonth())

  const [viewIndex, setViewIndex] = useState(todayIndex)
  const year = Math.floor(viewIndex / 12)
  const month = viewIndex % 12
  const shift = (n: number) => setViewIndex(i => i + n)

  // Only the month on screen is fetched (every event that overlaps it)
  const monthStart = new Date(year, month, 1)
  const monthEnd = new Date(year, month + 1, 0)
  const { events: monthEvents, loading } = useEventsWhere({ date_from: dayKey(monthStart), date_to: dayKey(monthEnd) })

  // Empty month: find the nearest months that do have events (one tiny query each way)
  const [prevEventIndex, setPrevEventIndex] = useState<number | null>(null)
  const [nextEventIndex, setNextEventIndex] = useState<number | null>(null)
  useEffect(() => {
    setPrevEventIndex(null)
    setNextEventIndex(null)
    if (loading || monthEvents.length > 0) return
    const indexOf = (r: { data: { items: Event[] } }) => {
      const ev = r.data.items[0]
      if (!ev) return null
      const d = parseDay(ev.start_date)
      return toIndex(d.getFullYear(), d.getMonth())
    }
    const dayBefore = new Date(year, month, 0)
    const dayAfter = new Date(year, month + 1, 1)
    let stale = false
    eventsApi.list({ date_to: dayKey(dayBefore), order: 'desc', limit: 1 })     // latest event before
      .then(r => { if (!stale) setPrevEventIndex(indexOf(r)) }).catch(() => {})
    eventsApi.list({ date_from: dayKey(dayAfter), order: 'asc', limit: 1 })     // earliest event after
      .then(r => { if (!stale) setNextEventIndex(indexOf(r)) }).catch(() => {})
    return () => { stale = true }
  }, [viewIndex, loading, monthEvents.length])

  // ← / → change month, Shift+← / Shift+→ change year, T jumps to today
  // (ignored while typing in an input, e.g. the search box)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.metaKey || e.ctrlKey || e.altKey) return
      if (e.key === 'ArrowLeft')  shift(e.shiftKey ? -12 : -1)
      else if (e.key === 'ArrowRight') shift(e.shiftKey ? 12 : 1)
      else if (e.key === 't' || e.key === 'T') setViewIndex(todayIndex)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [todayIndex])

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  // Build date → events map (multi-day events appear on every day they run)
  const dateMap: Record<string, Event[]> = {}
  monthEvents.forEach(ev => {
    const end = parseDay(ev.end_date)
    for (let d = parseDay(ev.start_date); d <= end; d.setDate(d.getDate() + 1)) {
      const key = dayKey(d)
      if (!dateMap[key]) dateMap[key] = []
      dateMap[key].push(ev)
    }
  })

  // Year dropdown: a few years around today, plus the year on screen
  const years = new Set<number>()
  for (let y = today.getFullYear() - 3; y <= today.getFullYear() + 3; y++) years.add(y)
  years.add(year)
  const yearOptions = [...years].sort((a, b) => a - b)

  const indexLabel = (i: number) => `${MONTH_NAMES[i % 12].slice(0, 3)} ${Math.floor(i / 12)}`

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1000, margin: '0 auto', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Schedule</div>
            <h1 style={{ fontFamily: 'var(--head)', fontSize: 42, fontWeight: 800, letterSpacing: '-2px' }}>
              {MONTH_NAMES[month]} {year}<span style={{ color: 'var(--orange)' }}>.</span>
            </h1>
            <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>
              {loading ? 'Loading…' : monthEvents.length === 0 ? 'No events this month' : `${monthEvents.length} event${monthEvents.length === 1 ? '' : 's'} this month`}
              {viewIndex !== todayIndex && ` · ${viewIndex < todayIndex ? 'past' : 'upcoming'}`}
            </p>
          </div>

          {/* Navigation controls */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <NavBtn onClick={() => shift(-12)} title="Previous year (Shift+←)">«</NavBtn>
              <NavBtn onClick={() => shift(-1)} title="Previous month (←)">‹</NavBtn>
              <select className="inp" value={month} onChange={e => setViewIndex(toIndex(year, Number(e.target.value)))}
                style={{ width: 'auto', padding: '7px 10px', fontSize: 11, fontFamily: 'var(--mono)', cursor: 'pointer' }} aria-label="Month">
                {MONTH_NAMES.map((m, i) => <option key={m} value={i}>{m}</option>)}
              </select>
              <select className="inp" value={year} onChange={e => setViewIndex(toIndex(Number(e.target.value), month))}
                style={{ width: 'auto', padding: '7px 10px', fontSize: 11, fontFamily: 'var(--mono)', cursor: 'pointer' }} aria-label="Year">
                {yearOptions.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
              <NavBtn onClick={() => shift(1)} title="Next month (→)">›</NavBtn>
              <NavBtn onClick={() => shift(12)} title="Next year (Shift+→)">»</NavBtn>
              <button onClick={() => setViewIndex(todayIndex)} className="btn-g" disabled={viewIndex === todayIndex}
                title="Jump to today (T)" style={{ padding: '7px 14px', fontSize: 10, letterSpacing: 2, marginLeft: 4 }}>
                Today
              </button>
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', letterSpacing: 0.5 }}>
              ← → month · Shift+← → year · T today
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 40px' }}>
        {/* Day headers */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4, marginBottom: 4 }}>
          {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => (
            <div key={d} style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textAlign: 'center', padding: '8px 0', textTransform: 'uppercase', letterSpacing: 1 }}>{d}</div>
          ))}
        </div>
        {/* Calendar grid — keyed by month so the fade-in replays on navigation */}
        <div key={viewIndex} className="au" style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4 }}>
          {Array.from({ length: firstDay }).map((_, i) => <div key={`e${i}`} style={{ minHeight: 80 }} />)}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1
            const key = dayKey(new Date(year, month, day))
            const dayEvents = dateMap[key] ?? []
            const isToday = key === todayKey
            const isPast = key < todayKey
            return (
              <div key={day} style={{ minHeight: 80, minWidth: 0, overflow: 'hidden', padding: '7px 6px', border: `1.5px solid ${isToday ? 'var(--orange)' : 'var(--dark3)'}`, background: 'linear-gradient(145deg, var(--dark2) 0%, var(--dark) 100%)', borderRadius: 8, position: 'relative', boxShadow: isToday ? '0 0 0 1px var(--orange), 0 0 16px rgba(212,86,26,0.18)' : undefined, opacity: isPast ? 0.55 : 1 }}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: isToday ? 'var(--orange)' : 'var(--gray2)', fontWeight: isToday ? 700 : 400, marginBottom: 4 }}>{day}</div>
                {dayEvents.slice(0, 2).map(ev => (
                  <button key={ev.id} onClick={() => onViewEvent(ev)} title={ev.title}
                    style={{ display: 'block', width: '100%', minWidth: 0, marginBottom: 2, padding: '2px 5px', background: `${getEventColor(ev)}22`, border: `1px solid ${getEventColor(ev)}44`, borderRadius: 3, textAlign: 'left', cursor: 'pointer', overflow: 'hidden' }}>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 8.5, color: getEventColor(ev), overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                      {registered.includes(ev.id) && '✓ '}{ev.title}
                    </div>
                  </button>
                ))}
                {dayEvents.length > 2 && <div style={{ fontFamily: 'var(--mono)', fontSize: 8, color: 'var(--gray2)', marginTop: 1 }}>+{dayEvents.length - 2} more</div>}
              </div>
            )
          })}
        </div>

        {/* Empty month: offer a jump to the nearest month that has events */}
        {!loading && monthEvents.length === 0 && (prevEventIndex !== null || nextEventIndex !== null) && (
          <div style={{ marginTop: 20, padding: '16px 20px', border: '1.5px dashed var(--dark4)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>Nothing scheduled in {MONTH_NAMES[month]}.</span>
            <div style={{ display: 'flex', gap: 8 }}>
              {prevEventIndex !== null && (
                <button className="btn-g" onClick={() => setViewIndex(prevEventIndex)} style={{ padding: '7px 14px', fontSize: 10, letterSpacing: 1.5 }}>
                  ← {indexLabel(prevEventIndex)}
                </button>
              )}
              {nextEventIndex !== null && (
                <button className="btn-p" onClick={() => setViewIndex(nextEventIndex)} style={{ padding: '7px 14px', fontSize: 10, letterSpacing: 1.5 }}>
                  {indexLabel(nextEventIndex)} →
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function NavBtn({ children, onClick, title }: { children: React.ReactNode; onClick: () => void; title: string }) {
  return (
    <button onClick={onClick} title={title} aria-label={title}
      style={{ width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1.5px solid var(--dark4)', borderRadius: 6, color: 'var(--cream3)', fontSize: 15, fontFamily: 'var(--mono)', transition: 'all 0.15s' }}
      onMouseOver={e => { e.currentTarget.style.borderColor = 'rgba(212,86,26,0.5)'; e.currentTarget.style.color = 'var(--orange)' }}
      onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--dark4)'; e.currentTarget.style.color = 'var(--cream3)' }}>
      {children}
    </button>
  )
}

// ── EventCreateForm helpers ───────────────────────────────
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

function autoDateDisplay(start: string, end: string): string {
  if (!start || !end) return ''
  const s = new Date(start + 'T00:00:00')
  const e = new Date(end + 'T00:00:00')
  if (start === end) return `${MONTHS[s.getMonth()]} ${s.getDate()}`
  if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear())
    return `${MONTHS[s.getMonth()]} ${s.getDate()}-${e.getDate()}`
  return `${MONTHS[s.getMonth()]} ${s.getDate()} - ${MONTHS[e.getMonth()]} ${e.getDate()}`
}

const LBL: React.CSSProperties = {
  fontFamily: 'var(--mono)',
  fontSize: 10,
  textTransform: 'uppercase',
  letterSpacing: 1.5,
  color: 'var(--gray2)',
  marginBottom: 6,
  display: 'block',
}

function FieldLabel({ text, required }: { text: string; required?: boolean }) {
  return (
    <label style={LBL}>
      {text}
      {required && <span style={{ color: 'var(--orange)', marginLeft: 3 }}>*</span>}
    </label>
  )
}

function ErrMsg({ msg }: { msg?: string }) {
  if (!msg) return null
  return <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#ef4444', marginTop: 5 }}>{msg}</div>
}

// ── EventForm (create, or edit when `event` is passed) ────
interface EventFormProps {
  clubId: number
  event?: Event          // present = editing this event
  onSuccess: () => void
  onCancel: () => void
}

function EventForm({ clubId, event, onSuccess, onCancel }: EventFormProps) {
  const { toast } = useToastStore()
  const isEdit = !!event
  const [submitting, setSubmitting] = useState(false)
  const [showOptional, setShowOptional] = useState(
    !!(event && (event.venue || event.time_info || event.prize_pool || event.team_size))
  )
  // When editing, keep a hand-written date label (e.g. "Oct 29–31 (tentative)") unless it
  // matches the auto-generated one, in which case it keeps following the dates
  const [dateDisplayTouched, setDateDisplayTouched] = useState(
    !!event && event.date_display !== autoDateDisplay(event.start_date, event.end_date)
  )
  const [errors, setErrors] = useState<Record<string, string>>({})

  const [form, setForm] = useState({
    title: event?.title ?? '',
    start_date: event?.start_date ?? '',
    end_date: event?.end_date ?? '',
    date_display: event?.date_display ?? '',
    tags: event ? splitTags(event.tags) : [] as string[],
    reg_deadline: event?.reg_deadline ?? '',
    description: event?.description ?? '',
    poster_url: event?.poster_url ?? '',
    contact_info: event?.contact_info ?? '',
    registration_fee: event?.registration_fee ?? 'Free',
    venue: event?.venue ?? '',
    time_info: event?.time_info ?? '',
    prize_pool: event?.prize_pool ?? '',
    team_size: event?.team_size ?? '',
  })

  // Auto-update date_display when dates change (unless user manually edited it)
  useEffect(() => {
    if (!dateDisplayTouched) {
      const auto = autoDateDisplay(form.start_date, form.end_date)
      if (auto) setForm(f => ({ ...f, date_display: auto }))
    }
  }, [form.start_date, form.end_date, dateDisplayTouched])

  const setField = (key: string, val: string) => {
    setForm(f => ({ ...f, [key]: val }))
    if (errors[key]) setErrors(e => ({ ...e, [key]: '' }))
  }

  const toggleTag = (id: string) => {
    setForm(f => ({
      ...f,
      tags: f.tags.includes(id) ? f.tags.filter(t => t !== id) : [...f.tags, id],
    }))
    if (errors.tags) setErrors(e => ({ ...e, tags: '' }))
  }

  const validate = (): Record<string, string> => {
    const e: Record<string, string> = {}
    if (!form.title.trim())            e.title = 'Required'
    if (!form.start_date)              e.start_date = 'Required'
    if (!form.end_date)                e.end_date = 'Required'
    else if (form.start_date && form.end_date < form.start_date) e.end_date = "Can't be before the start date"
    if (!form.date_display.trim())     e.date_display = 'Required'
    if (form.tags.length === 0)        e.tags = 'Select at least one tag'
    if (!form.reg_deadline)            e.reg_deadline = 'Required'
    if (!form.description.trim())      e.description = 'Required'
    if (!form.poster_url.trim())       e.poster_url = 'Required'
    if (!form.contact_info.trim())     e.contact_info = 'Required'
    if (!form.registration_fee.trim()) e.registration_fee = 'Required'
    return e
  }

  const handleSubmit = async () => {
    const errs = validate()
    if (Object.keys(errs).length > 0) { setErrors(errs); return }
    setSubmitting(true)
    // Empty optional fields: omitted on create; sent as null on edit so clearing a field saves
    const opt = (v: string) => v.trim() || (isEdit ? null : undefined)
    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      start_date: form.start_date,
      end_date: form.end_date,
      reg_deadline: form.reg_deadline || (isEdit ? null : undefined),
      date_display: form.date_display.trim(),
      tags: form.tags,
      poster_url: opt(form.poster_url),
      contact_info: opt(form.contact_info),
      registration_fee: form.registration_fee.trim() || 'Free',
      venue: opt(form.venue),
      time_info: opt(form.time_info),
      prize_pool: opt(form.prize_pool),
      team_size: opt(form.team_size),
    }
    try {
      if (event) {
        await eventsApi.update(event.id, payload)
        toast(`"${payload.title}" updated`, 'success')
      } else {
        await eventsApi.create({ ...payload, club_id: clubId })
        toast(`"${payload.title}" published successfully!`, 'success')
      }
      onSuccess()
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      toast(typeof detail === 'string' ? detail : isEdit ? 'Failed to save changes' : 'Failed to publish event', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      background: 'var(--dark2)',
      border: '1.5px solid var(--dark3)',
      borderRadius: 16,
      padding: 32,
      marginBottom: 32,
      animation: 'panelIn 0.3s cubic-bezier(0.22,1,0.36,1) both',
    }}>
      {/* Form header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 3, marginBottom: 6 }}>{isEdit ? 'Edit Event' : 'New Event'}</div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>{event ? event.title : 'Post an Event'}</div>
        </div>
      </div>

      {/* Required fields */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '22px 28px' }}>

        {/* Title — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Event Title" required />
          <input
            className="inp"
            value={form.title}
            onChange={e => setField('title', e.target.value)}
            placeholder="e.g. HackX 4.0"
          />
          <ErrMsg msg={errors.title} />
        </div>

        {/* Start Date */}
        <div>
          <FieldLabel text="Start Date" required />
          <input
            type="date"
            className="inp"
            value={form.start_date}
            onChange={e => setField('start_date', e.target.value)}
            style={{ colorScheme: 'dark' }}
          />
          <ErrMsg msg={errors.start_date} />
        </div>

        {/* End Date */}
        <div>
          <FieldLabel text="End Date" required />
          <input
            type="date"
            className="inp"
            value={form.end_date}
            onChange={e => setField('end_date', e.target.value)}
            style={{ colorScheme: 'dark' }}
          />
          <ErrMsg msg={errors.end_date} />
        </div>

        {/* Date Display */}
        <div>
          <FieldLabel text="Date Display" required />
          <input
            className="inp"
            value={form.date_display}
            onChange={e => { setDateDisplayTouched(true); setField('date_display', e.target.value) }}
            placeholder="e.g. Oct 29-31"
          />
          <ErrMsg msg={errors.date_display} />
        </div>

        {/* Registration Deadline */}
        <div>
          <FieldLabel text="Registration Deadline" required />
          <input
            type="date"
            className="inp"
            value={form.reg_deadline}
            onChange={e => setField('reg_deadline', e.target.value)}
            style={{ colorScheme: 'dark' }}
          />
          <ErrMsg msg={errors.reg_deadline} />
        </div>

        {/* Tags — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Tags" required />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 2 }}>
            {ALL_TAGS.map(tag => {
              const selected = form.tags.includes(tag.id)
              const color = TAG_COLORS[tag.id] ?? 'var(--orange)'
              return (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 20,
                    fontSize: 11,
                    fontFamily: 'var(--mono)',
                    letterSpacing: 0.5,
                    cursor: 'pointer',
                    border: `1.5px solid ${selected ? color : 'var(--dark4)'}`,
                    background: selected ? `${color}1a` : 'transparent',
                    color: selected ? color : 'var(--gray2)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {tag.label}
                </button>
              )
            })}
          </div>
          <ErrMsg msg={errors.tags} />
        </div>

        {/* Description — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Description" required />
          <textarea
            className="inp"
            value={form.description}
            onChange={e => setField('description', e.target.value)}
            placeholder="Describe your event..."
            style={{ minHeight: 120, resize: 'vertical', lineHeight: 1.65 }}
          />
          <ErrMsg msg={errors.description} />
        </div>

        {/* Poster — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Poster" required />
          <ImageUpload
            value={form.poster_url}
            onChange={url => { setField('poster_url', url) }}
            error={errors.poster_url}
          />
        </div>

        {/* Contact Info */}
        <div>
          <FieldLabel text="Contact Info" required />
          <textarea
            className="inp"
            value={form.contact_info}
            onChange={e => setField('contact_info', e.target.value)}
            placeholder="Email, phone, or social handles for organizers"
            style={{ minHeight: 80, resize: 'vertical', lineHeight: 1.65 }}
          />
          <ErrMsg msg={errors.contact_info} />
        </div>

        {/* Registration Fee */}
        <div>
          <FieldLabel text="Registration Fee" required />
          <input
            className="inp"
            value={form.registration_fee}
            onChange={e => setField('registration_fee', e.target.value)}
            placeholder="e.g. ₹200 per team"
          />
          <ErrMsg msg={errors.registration_fee} />
        </div>

      </div>

      {/* Optional fields toggle */}
      <div style={{ marginTop: 28 }}>
        <button
          onClick={() => setShowOptional(s => !s)}
          style={{
            fontFamily: 'var(--mono)',
            fontSize: 11,
            color: 'var(--orange)',
            letterSpacing: 1,
            textTransform: 'uppercase',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
            marginBottom: showOptional ? 22 : 0,
          }}
        >
          {showOptional ? '▲ Hide Additional Details' : '▼ Additional Details +'}
        </button>

        {showOptional && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '22px 28px' }}>
            <div>
              <FieldLabel text="Venue" />
              <input
                className="inp"
                value={form.venue}
                onChange={e => setField('venue', e.target.value)}
                placeholder="Leave empty for TBA"
              />
            </div>
            <div>
              <FieldLabel text="Time" />
              <input
                className="inp"
                value={form.time_info}
                onChange={e => setField('time_info', e.target.value)}
                placeholder="e.g. 10:00 AM - 5:00 PM"
              />
            </div>
            <div>
              <FieldLabel text="Prize Pool" />
              <input
                className="inp"
                value={form.prize_pool}
                onChange={e => setField('prize_pool', e.target.value)}
                placeholder="e.g. ₹50,000 total"
              />
            </div>
            <div>
              <FieldLabel text="Team Size" />
              <input
                className="inp"
                value={form.team_size}
                onChange={e => setField('team_size', e.target.value)}
                placeholder="e.g. 2-4 or Solo"
              />
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--dark3)' }}>
        <button onClick={handleSubmit} className="btn-p" disabled={submitting}>
          {submitting ? (isEdit ? 'Saving…' : 'Publishing…') : (isEdit ? 'Save Changes →' : 'Publish Event →')}
        </button>
        <button onClick={onCancel} className="btn-g">Cancel</button>
      </div>
    </div>
  )
}

// ── AdminPage ─────────────────────────────────────────────
type AdminTab = 'overview' | 'members' | 'registrations'

export function AdminPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const { toast } = useToastStore()
  const [showForm, setShowForm] = useState(false)
  const [editingEvent, setEditingEvent] = useState<Event | null>(null)
  const [deletingEvent, setDeletingEvent] = useState<Event | null>(null)   // shown in the confirm dialog
  const [deleteSubmitting, setDeleteSubmitting] = useState(false)
  const [clubId, setClubId] = useState<number | null>(null)
  const [memberCount, setMemberCount] = useState<number | null>(null)
  const [regCounts, setRegCounts] = useState<Record<number, number>>({})
  const [discussions, setDiscussions] = useState<Discussion[]>([])

  // Active tab (and event, for Registrations) live in the URL: /admin?tab=registrations&event=12
  const [params, setParams] = useSearchParams()
  const tab = (['members', 'registrations'].includes(params.get('tab') ?? '') ? params.get('tab') : 'overview') as AdminTab
  const tabEventId = Number(params.get('event')) || null
  const goTab = (t: AdminTab, eventId?: number) => {
    const next: Record<string, string> = {}
    if (t !== 'overview') next.tab = t
    if (eventId) next.event = String(eventId)
    setParams(next)
    window.scrollTo({ top: 0 })
  }
  const [discLoading, setDiscLoading] = useState(false)
  const [discHasMore, setDiscHasMore] = useState(false)
  const [discLoadingMore, setDiscLoadingMore] = useState(false)
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [replyContent, setReplyContent] = useState('')
  const [replySubmitting, setReplySubmitting] = useState(false)

  // The admin's club, looked up by its exact name (admins are linked to clubs by name)
  useEffect(() => {
    if (!user?.club_name) return
    clubsApi.list({ name: user.club_name, limit: 1 })
      .then(r => {
        const club = r.data.items[0]
        if (club) { setClubId(club.id); setMemberCount(club.member_count) }
      })
      .catch(() => {})
  }, [user?.club_name])

  // This club's events (one club: small enough to load in full)
  const { events: myEvents, refresh } = useEventsWhere(clubId !== null ? { club_id: clubId } : null)

  // Fetch registration counts for each club event
  useEffect(() => {
    if (myEvents.length === 0) return
    Promise.all(
      myEvents.map(ev =>
        eventsApi.registrationCount(ev.id)
          .then((r: any) => ({ id: ev.id, count: typeof r.data === 'number' ? r.data : (r.data?.count ?? 0) }))
          .catch(() => ({ id: ev.id, count: 0 }))
      )
    ).then(results => {
      const map: Record<number, number> = {}
      results.forEach((r: any) => { map[r.id] = r.count })
      setRegCounts(map)
    })
  }, [myEvents.length])

  // Fetch discussion feed (first page; "Load more" appends older pages)
  const DISC_PAGE_SIZE = 10
  const fetchDiscussions = async () => {
    setDiscLoading(true)
    try {
      const r = await discussionsApi.adminFeed({ limit: DISC_PAGE_SIZE })
      setDiscussions(r.data.items)
      setDiscHasMore(r.data.items.length === DISC_PAGE_SIZE && r.data.items.length < r.data.total)
    } catch {
      setDiscussions([])
    } finally {
      setDiscLoading(false)
    }
  }

  const loadMoreDiscussions = async () => {
    const last = discussions[discussions.length - 1]
    if (!last) return
    setDiscLoadingMore(true)
    try {
      const r = await discussionsApi.adminFeed({ before_id: last.id, limit: DISC_PAGE_SIZE })
      setDiscussions(prev => [...prev, ...r.data.items])
      setDiscHasMore(r.data.items.length === DISC_PAGE_SIZE)
    } catch {
      toast('Failed to load more discussions', 'error')
    } finally {
      setDiscLoadingMore(false)
    }
  }

  useEffect(() => {
    if (user?.role === 'member') fetchDiscussions()
  }, [user?.role])

  if (user?.role !== 'member') {
    return (
      <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--gray2)' }}>Admin access only</div>
      </div>
    )
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const upcomingCount = myEvents.filter(e => new Date(e.start_date) >= today).length

  const getEventTitle = (eventId: number) => {
    const ev = myEvents.find(e => e.id === eventId)
    return ev?.title ?? `Event #${eventId}`
  }

  const handleReply = async (disc: Discussion) => {
    if (!replyContent.trim()) return
    setReplySubmitting(true)
    try {
      const r = await discussionsApi.reply(disc.event_id, disc.id, { content: replyContent.trim() })
      setDiscussions(prev => prev.map(d => (d.id === disc.id ? { ...d, replies: [...d.replies, r.data] } : d)))
      toast('Reply posted', 'success')
      setReplyingTo(null)
      setReplyContent('')
    } catch (err: any) {
      toast(typeof err?.response?.data?.detail === 'string' ? err.response.data.detail : 'Failed to reply', 'error')
    } finally {
      setReplySubmitting(false)
    }
  }

  // Works for both top-level comments and replies (deleting a comment removes its replies too)
  const handleDelete = async (disc: Discussion) => {
    try {
      await discussionsApi.delete(disc.event_id, disc.id)
      setDiscussions(prev => disc.parent_id === null
        ? prev.filter(d => d.id !== disc.id)
        : prev.map(d => (d.id === disc.parent_id ? { ...d, replies: d.replies.filter(r => r.id !== disc.id) } : d)))
      toast('Comment deleted', 'success')
    } catch (err: any) {
      toast(typeof err?.response?.data?.detail === 'string' ? err.response.data.detail : 'Failed to delete', 'error')
    }
  }

  // One form at a time: opening "edit" closes "new", and vice versa. The form lives on Overview.
  const openCreate = () => { setEditingEvent(null); setShowForm(true); if (tab !== 'overview') goTab('overview') }
  const openEdit = (ev: Event) => {
    setShowForm(false)
    setEditingEvent(ev)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  const closeForm = () => { setShowForm(false); setEditingEvent(null) }

  const handleFormSuccess = () => {
    closeForm()
    refresh()
  }

  const handleDeleteEvent = async () => {
    if (!deletingEvent) return
    setDeleteSubmitting(true)
    try {
      await eventsApi.delete(deletingEvent.id)
      toast(`"${deletingEvent.title}" deleted`, 'info')
      if (editingEvent?.id === deletingEvent.id) closeForm()
      setDeletingEvent(null)
      refresh()
      fetchDiscussions()   // the event's comments were deleted with it
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      toast(typeof detail === 'string' ? detail : 'Failed to delete event', 'error')
    } finally {
      setDeleteSubmitting(false)
    }
  }

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      {/* Header */}
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>{user.club_name}</div>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
            <div>
              <h1 style={{ fontFamily: 'var(--head)', fontSize: 38, fontWeight: 800, letterSpacing: '-2px' }}>
                Club Dashboard<span style={{ color: 'var(--orange)' }}>.</span>
              </h1>
              <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>{user.position} · {user.name}</p>
            </div>
            {!showForm && !editingEvent && (
              <button
                onClick={openCreate}
                className="btn-p"
                disabled={!clubId}
                style={{ marginTop: 6, whiteSpace: 'nowrap', flexShrink: 0 }}
              >
                Post New Event +
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: '1px solid var(--dark3)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 40px', display: 'flex', gap: 4 }}>
          {([
            { id: 'overview',      label: 'Overview' },
            { id: 'members',       label: `Members${memberCount !== null ? ` (${memberCount})` : ''}` },
            { id: 'registrations', label: 'Registrations' },
          ] as const).map(t => (
            <button key={t.id} onClick={() => goTab(t.id)}
              style={{ padding: '14px 16px', fontFamily: 'var(--mono)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1.5, color: tab === t.id ? 'var(--orange)' : 'var(--gray2)', borderBottom: `2px solid ${tab === t.id ? 'var(--orange)' : 'transparent'}`, marginBottom: -1, transition: 'color 0.15s' }}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 40px' }}>

        {tab === 'members' && <MembersTab clubName={user.club_name ?? 'club'} />}

        {tab === 'registrations' && (
          <RegistrationsTab
            events={myEvents}
            eventId={tabEventId}
            onPickEvent={id => goTab('registrations', id)}
          />
        )}

        {tab === 'overview' && (<>

        {/* Event creation form */}
        {(showForm || editingEvent) && clubId !== null && (
          <EventForm
            key={editingEvent?.id ?? 'new'}   // fresh form state when switching events
            clubId={clubId}
            event={editingEvent ?? undefined}
            onSuccess={handleFormSuccess}
            onCancel={closeForm}
          />
        )}

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 36 }}>
          {[
            { label: 'Your Events', val: myEvents.length },
            { label: memberCount === 1 ? 'Member' : 'Members', val: memberCount ?? '—', onClick: () => goTab('members') },
            { label: 'Upcoming',    val: upcomingCount },
          ].map(s => (
            <div key={s.label} className="stat-card" onClick={s.onClick}
              title={s.onClick ? 'See all members' : undefined}
              style={s.onClick ? { cursor: 'pointer', position: 'relative' } : undefined}>
              <div style={{ fontFamily: 'var(--head)', fontSize: 36, fontWeight: 800, color: 'var(--orange)' }}>{s.val}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 2, marginTop: 4 }}>{s.label}</div>
              {s.onClick && <span style={{ position: 'absolute', top: 16, right: 18, fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--orange)' }}>→</span>}
            </div>
          ))}
        </div>

        {/* Event list */}
        <div style={{ marginBottom: 44 }}>
          <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 14 }}>Your Events</div>
          {myEvents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', border: '1.5px dashed var(--dark4)', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', borderRadius: 12 }}>
              No events yet — click "Post New Event +" to create your first event.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {myEvents.map(ev => (
                <div key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '14px 18px', background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: `3px solid ${getEventColor(ev)}` }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: getEventColor(ev), minWidth: 60 }}>{ev.date_display}</div>
                  <div style={{ flex: 1 }}>
                    <button
                      onClick={() => navigate(`/events/${ev.id}`)}
                      style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--fg)', padding: 0, textAlign: 'left' }}
                    >
                      {ev.title}
                    </button>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 2 }}>{splitTags(ev.tags).join(' · ')}</div>
                  </div>
                  <button onClick={() => goTab('registrations', ev.id)} title="See who registered"
                    style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--cream3)', border: '1px solid var(--dark4)', padding: '2px 8px', whiteSpace: 'nowrap', cursor: 'pointer', transition: 'all 0.15s' }}
                    onMouseOver={e => { e.currentTarget.style.borderColor = 'rgba(212,86,26,0.5)'; e.currentTarget.style.color = 'var(--orange)' }}
                    onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--dark4)'; e.currentTarget.style.color = 'var(--cream3)' }}>
                    {regCounts[ev.id] ?? '—'} registered →
                  </button>
                  {ev.is_hot && <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '2px 7px' }}>Hot</span>}
                  <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 7px' }}>Published</span>
                  <div style={{ display: 'flex', gap: 6, marginLeft: 6 }}>
                    <button
                      onClick={() => openEdit(ev)}
                      disabled={editingEvent?.id === ev.id}
                      style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--cream3)', background: 'none', border: '1px solid var(--dark4)', padding: '3px 12px', cursor: 'pointer', opacity: editingEvent?.id === ev.id ? 0.4 : 1 }}
                    >
                      {editingEvent?.id === ev.id ? 'Editing' : 'Edit'}
                    </button>
                    <button
                      onClick={() => setDeletingEvent(ev)}
                      style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#ef4444', background: 'none', border: '1px solid rgba(239,68,68,0.3)', padding: '3px 12px', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Discussion feed */}
        <div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 14 }}>Recent Discussions</div>
          {discLoading ? (
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', padding: '20px 0' }}>Loading…</div>
          ) : discussions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', border: '1.5px dashed var(--dark4)', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', borderRadius: 12 }}>
              No discussions yet
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {discussions.map(disc => (
                <div key={disc.id} style={{ background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: '3px solid var(--dark4)', padding: '14px 18px' }}>
                  {/* Meta row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <span style={{ fontFamily: 'var(--head)', fontSize: 13, fontWeight: 600 }}>{disc.user_name}</span>
                    {disc.is_official && <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '1px 6px', textTransform: 'uppercase', letterSpacing: 0.5 }}>Admin</span>}
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', marginLeft: 'auto' }}>{getTimeAgo(disc.created_at)}{disc.edited_at && ' (edited)'}</span>
                  </div>
                  {/* Event reference */}
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', marginBottom: 8 }}>
                    on{' '}
                    <button
                      onClick={() => navigate(`/events/${disc.event_id}`)}
                      style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--orange)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                    >
                      {getEventTitle(disc.event_id)}
                    </button>
                  </div>
                  {/* Content */}
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--fg)', lineHeight: 1.65, marginBottom: 12 }}>
                    {disc.content.length > 200 ? disc.content.slice(0, 200) + '…' : disc.content}
                  </div>
                  {/* Replies */}
                  {disc.replies.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12, paddingLeft: 14, borderLeft: '2px solid var(--dark4)' }}>
                      {disc.replies.map(reply => (
                        <div key={reply.id} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                              <span style={{ fontFamily: 'var(--head)', fontSize: 12, fontWeight: 600, color: reply.is_official ? 'var(--orange)' : 'var(--cream)' }}>{reply.user_name}</span>
                              {reply.is_official && <span style={{ fontFamily: 'var(--mono)', fontSize: 8, color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '0 5px', textTransform: 'uppercase', letterSpacing: 0.5 }}>Admin</span>}
                              <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)' }}>{getTimeAgo(reply.created_at)}{reply.edited_at && ' (edited)'}</span>
                            </div>
                            <div style={{ fontFamily: 'var(--mono)', fontSize: 11.5, color: 'var(--cream3)', lineHeight: 1.6 }}>
                              {reply.content.length > 200 ? reply.content.slice(0, 200) + '…' : reply.content}
                            </div>
                          </div>
                          <button
                            onClick={() => handleDelete(reply)}
                            style={{ fontFamily: 'var(--mono)', fontSize: 9, color: '#ef4444', background: 'none', border: '1px solid rgba(239,68,68,0.3)', padding: '2px 8px', cursor: 'pointer', flexShrink: 0 }}
                          >
                            Delete
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  {/* Actions */}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <button
                      onClick={() => { setReplyingTo(replyingTo === disc.id ? null : disc.id); setReplyContent('') }}
                      style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', background: 'none', border: '1px solid rgba(212,86,26,0.4)', padding: '3px 12px', cursor: 'pointer' }}
                    >
                      {replyingTo === disc.id ? 'Cancel' : 'Reply'}
                    </button>
                    <button
                      onClick={() => handleDelete(disc)}
                      style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#ef4444', background: 'none', border: '1px solid rgba(239,68,68,0.3)', padding: '3px 12px', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </div>
                  {/* Inline reply input */}
                  {replyingTo === disc.id && (
                    <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                      <textarea
                        className="inp"
                        value={replyContent}
                        onChange={e => setReplyContent(e.target.value)}
                        placeholder="Write a reply…"
                        style={{ flex: 1, minHeight: 72, resize: 'vertical', lineHeight: 1.65, fontSize: 12 }}
                        autoFocus
                      />
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <button
                          onClick={() => handleReply(disc)}
                          className="btn-p"
                          disabled={replySubmitting || !replyContent.trim()}
                          style={{ fontSize: 11, padding: '7px 14px', whiteSpace: 'nowrap' }}
                        >
                          {replySubmitting ? '…' : 'Send →'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {discHasMore && (
                <button
                  onClick={loadMoreDiscussions}
                  className="btn-g"
                  disabled={discLoadingMore}
                  style={{ alignSelf: 'center', marginTop: 14, padding: '9px 26px', fontSize: 10, letterSpacing: 2 }}
                >
                  {discLoadingMore ? 'Loading…' : 'Load more'}
                </button>
              )}
            </div>
          )}
        </div>

        </>)}
      </div>

      {/* Delete confirmation */}
      {deletingEvent && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="mbg" style={{ position: 'absolute', inset: 0 }} onClick={() => !deleteSubmitting && setDeletingEvent(null)} />
          <div className="mbox asi" style={{ position: 'relative', padding: '34px 36px', maxWidth: 420, width: '90%' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'linear-gradient(90deg, #ef4444, #ef444444, transparent)', borderRadius: '20px 20px 0 0' }} />
            <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: '#ef4444', textTransform: 'uppercase', letterSpacing: 3, marginBottom: 14 }}>Delete Event</div>
            <h3 style={{ fontFamily: 'var(--syne)', fontSize: 22, fontWeight: 800, letterSpacing: '-0.5px', marginBottom: 14 }}>{deletingEvent.title}</h3>
            <p style={{ fontFamily: 'var(--body)', fontSize: 14, color: 'var(--cream3)', lineHeight: 1.65, marginBottom: 28 }}>
              This permanently removes the event
              {(regCounts[deletingEvent.id] ?? 0) > 0 && <>, its <strong style={{ color: 'var(--cream)' }}>{regCounts[deletingEvent.id]} registration{regCounts[deletingEvent.id] === 1 ? '' : 's'}</strong></>}
              {' '}and its whole discussion. This can't be undone.
            </p>
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setDeletingEvent(null)} className="btn-g" style={{ flex: 1 }} disabled={deleteSubmitting}>Cancel</button>
              <button onClick={handleDeleteEvent} className="btn-p" disabled={deleteSubmitting}
                style={{ flex: 1, background: '#ef4444', borderColor: '#ef4444' }}>
                {deleteSubmitting ? 'Deleting…' : 'Delete →'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
