import { useAuthStore } from '@/context/authStore'
import { useNavigate } from 'react-router-dom'
import { useEvents, useUserEvents } from '@/hooks/useData'
import { getEventColor, splitTags } from '@/types'
import type { Event } from '@/types'

// ── SavedPage ─────────────────────────────────────────────
export function SavedPage({ onViewEvent }: { onViewEvent: (ev: Event) => void }) {
  const { events } = useEvents()
  const { saved, toggleSave, registered } = useUserEvents()
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
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const { events } = useEvents()
  const { registered, saved } = useUserEvents()

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
              {events.filter(e => registered.includes(e.id)).map(ev => (
                <div key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: `3px solid ${getEventColor(ev)}` }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: getEventColor(ev), minWidth: 56 }}>{ev.date_display}</span>
                  <span style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 600, flex: 1 }}>{ev.title}</span>
                  <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 7px' }}>✓ Going</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <button onClick={handleLogout} className="btn-g" style={{ marginTop: 8 }}>Sign Out</button>
      </div>
    </div>
  )
}

// ── CalendarPage ──────────────────────────────────────────
export function CalendarPage({ onViewEvent }: { onViewEvent: (ev: Event) => void }) {
  const { events } = useEvents()
  const { registered } = useUserEvents()
  const now = new Date('2025-10-23')
  const year = now.getFullYear()
  const month = now.getMonth()

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const monthName = now.toLocaleString('default', { month: 'long' })

  // Build date → events map
  const dateMap: Record<string, Event[]> = {}
  events.forEach(ev => {
    const start = new Date(ev.start_date)
    const end   = new Date(ev.end_date)
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const key = d.toISOString().slice(0, 10)
      if (!dateMap[key]) dateMap[key] = []
      dateMap[key].push(ev)
    }
  })

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Schedule</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 42, fontWeight: 800, letterSpacing: '-2px' }}>
            {monthName} {year}<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 40px' }}>
        {/* Day headers */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4, marginBottom: 4 }}>
          {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => (
            <div key={d} style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textAlign: 'center', padding: '8px 0', textTransform: 'uppercase', letterSpacing: 1 }}>{d}</div>
          ))}
        </div>
        {/* Calendar grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4 }}>
          {Array.from({ length: firstDay }).map((_, i) => <div key={`e${i}`} style={{ minHeight: 80 }} />)}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1
            const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
            const dayEvents = dateMap[key] ?? []
            const isToday = day === now.getDate()
            return (
              <div key={day} style={{ minHeight: 80, padding: '7px 6px', border: `1.5px solid ${isToday ? 'var(--orange)' : 'var(--dark3)'}`, background: 'linear-gradient(145deg, var(--dark2) 0%, var(--dark) 100%)', borderRadius: 8, position: 'relative', boxShadow: isToday ? '0 0 0 1px var(--orange), 0 0 16px rgba(212,86,26,0.18)' : undefined }}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: isToday ? 'var(--orange)' : 'var(--gray2)', fontWeight: isToday ? 700 : 400, marginBottom: 4 }}>{day}</div>
                {dayEvents.slice(0, 2).map(ev => (
                  <button key={ev.id} onClick={() => onViewEvent(ev)}
                    style={{ display: 'block', width: '100%', marginBottom: 2, padding: '2px 5px', background: `${getEventColor(ev)}22`, border: `1px solid ${getEventColor(ev)}44`, borderRadius: 3, textAlign: 'left', cursor: 'pointer' }}>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 8.5, color: getEventColor(ev), overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{ev.title}</div>
                  </button>
                ))}
                {dayEvents.length > 2 && <div style={{ fontFamily: 'var(--mono)', fontSize: 8, color: 'var(--gray2)', marginTop: 1 }}>+{dayEvents.length - 2} more</div>}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── AdminPage ─────────────────────────────────────────────
export function AdminPage() {
  const { user } = useAuthStore()
  const { events } = useEvents()
  const myEvents = events.filter(e => e.club_name === user?.club_name)

  if (user?.role !== 'member') {
    return (
      <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--gray2)' }}>Admin access only</div>
      </div>
    )
  }

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>{user.club_name}</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 38, fontWeight: 800, letterSpacing: '-2px' }}>
            Club Dashboard<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>{user.position} · {user.name}</p>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 40px' }}>
        {/* Quick stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 36 }}>
          {[
            { label: 'Your Events', val: myEvents.length },
            { label: 'Hot Events',  val: myEvents.filter(e => e.is_hot).length },
            { label: 'Upcoming',    val: myEvents.filter(e => new Date(e.start_date) >= new Date('2025-10-23')).length },
          ].map(s => (
            <div key={s.label} className="stat-card">
              <div style={{ fontFamily: 'var(--head)', fontSize: 36, fontWeight: 800, color: 'var(--orange)' }}>{s.val}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 2, marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Event list */}
        <div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 14 }}>Your Events</div>
          {myEvents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', border: '1.5px dashed var(--dark4)', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>
              No events yet — create one via the API or ask your dev to wire up the form.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {myEvents.map(ev => (
                <div key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '14px 18px', background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: `3px solid ${getEventColor(ev)}` }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: getEventColor(ev), minWidth: 60 }}>{ev.date_display}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 600 }}>{ev.title}</div>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 2 }}>{splitTags(ev.tags).join(' · ')}</div>
                  </div>
                  {ev.is_hot && <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '2px 7px' }}>Hot</span>}
                  <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 7px' }}>Published</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
