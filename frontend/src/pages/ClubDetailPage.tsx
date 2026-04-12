import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { clubsApi, eventsApi } from '@/api/client'
import { useUserClubs } from '@/hooks/useData'
import { useToastStore } from '@/context/toastStore'
import { splitTags, TAG_COLORS, getEventColor } from '@/types'
import type { Club, Event } from '@/types'

// ── Icons ─────────────────────────────────────────────────
const lp = { fill: 'none', stroke: 'currentColor', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
const IgIco  = () => <svg width={14} height={14} viewBox="0 0 24 24" {...lp} strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="0.5" fill="currentColor" stroke="none"/></svg>
const LiIco  = () => <svg width={14} height={14} viewBox="0 0 24 24" {...lp} strokeWidth="2"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
const ArrIco = () => <svg width={13} height={13} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>

export function ClubDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToastStore()
  const { joinedClubs, toggleMembership } = useUserClubs()

  const [club, setClub] = useState<Club | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [eventsLoading, setEventsLoading] = useState(true)

  const clubId = Number(id)
  const isMember = joinedClubs.includes(clubId)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    clubsApi.get(clubId)
      .then(r => setClub(r.data))
      .catch(() => { toast('Club not found', 'error'); navigate('/clubs') })
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!id) return
    setEventsLoading(true)
    eventsApi.list({ club_id: clubId })
      .then(r => setEvents(r.data))
      .catch(() => {})
      .finally(() => setEventsLoading(false))
  }, [id])

  if (loading || !club) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', letterSpacing: 3, textTransform: 'uppercase' }}>Loading…</div>
      </div>
    )
  }

  const tags = splitTags(club.tags)

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>

      {/* ── Header ─────────────────────────────────────────── */}
      <div className="pg-hdr" style={{ padding: '36px 40px 40px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1100, margin: '0 auto' }}>

          {/* Back */}
          <button
            onClick={() => navigate('/clubs')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 28, transition: 'color 0.15s', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            onMouseOver={e => (e.currentTarget.style.color = 'var(--cream)')}
            onMouseOut={e => (e.currentTarget.style.color = 'var(--gray2)')}
          >
            <ArrIco /> Back to Clubs
          </button>

          {/* Main header row */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 28, flexWrap: 'wrap' }}>

            {/* Club badge */}
            <div style={{
              width: 72, height: 72, flexShrink: 0,
              background: `${club.color}14`,
              border: `2px solid ${club.color}44`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 700, color: club.color, letterSpacing: 1 }}>
                {club.abbr.slice(0, 5)}
              </span>
            </div>

            {/* Title + meta */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Campus Club</div>
              <h1 style={{ fontFamily: 'var(--syne)', fontSize: 40, fontWeight: 800, letterSpacing: '-1.5px', lineHeight: 1.05, marginBottom: 14 }}>
                {club.name}<span style={{ color: 'var(--orange)' }}>.</span>
              </h1>
              <p style={{ fontFamily: 'var(--body)', fontSize: 14, color: 'var(--cream3)', lineHeight: 1.7, maxWidth: 620, marginBottom: 18 }}>
                {club.description}
              </p>

              {/* Tags */}
              {tags.length > 0 && (
                <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginBottom: 20 }}>
                  {tags.map(t => (
                    <span key={t} style={{
                      padding: '4px 12px', borderRadius: 20, fontSize: 10.5,
                      fontFamily: 'var(--mono)', letterSpacing: 0.5,
                      border: `1.5px solid ${(TAG_COLORS[t] ?? 'var(--orange)') + '44'}`,
                      background: `${TAG_COLORS[t] ?? 'var(--orange)'}0f`,
                      color: TAG_COLORS[t] ?? 'var(--orange)',
                      textTransform: 'capitalize',
                    }}>
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Stats + actions row */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
                {/* Member count */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 800, color: club.color }}>{club.member_count}</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.5 }}>Members</span>
                </div>

                {/* Status badge */}
                {club.is_open
                  ? <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '3px 10px', background: 'rgba(16,185,129,0.06)', letterSpacing: 0.5 }}>● Open</span>
                  : <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--gray2)', border: '1px solid var(--dark4)', padding: '3px 10px', letterSpacing: 0.5 }}>Closed</span>
                }

                {/* Divider */}
                <div style={{ width: 1, height: 20, background: 'var(--dark4)' }} />

                {/* Join/Leave button */}
                <button
                  onClick={() => toggleMembership(club)}
                  style={{
                    padding: '9px 22px',
                    fontFamily: 'var(--head)', fontSize: 11, fontWeight: 700,
                    textTransform: 'uppercase', letterSpacing: 2,
                    border: `1.5px solid ${isMember ? club.color : 'var(--dark4)'}`,
                    background: isMember ? `${club.color}18` : 'rgba(242,234,220,0.04)',
                    color: isMember ? club.color : 'var(--cream)',
                    borderRadius: 8, cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {isMember ? '✓ Joined' : '+ Join Club'}
                </button>

                {/* Social links */}
                {club.instagram && (
                  <a href={club.instagram} target="_blank" rel="noopener noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textDecoration: 'none', letterSpacing: 0.5, transition: 'color 0.15s' }}
                    onMouseOver={e => (e.currentTarget.style.color = 'var(--cream)')}
                    onMouseOut={e => (e.currentTarget.style.color = 'var(--gray2)')}>
                    <IgIco /> Instagram
                  </a>
                )}
                {club.linkedin && (
                  <a href={club.linkedin} target="_blank" rel="noopener noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textDecoration: 'none', letterSpacing: 0.5, transition: 'color 0.15s' }}
                    onMouseOver={e => (e.currentTarget.style.color = 'var(--cream)')}
                    onMouseOut={e => (e.currentTarget.style.color = 'var(--gray2)')}>
                    <LiIco /> LinkedIn
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Events Section ──────────────────────────────────── */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 40px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 3, marginBottom: 6 }}>Events</div>
            <div style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>
              Events by {club.name}
            </div>
          </div>
          {!eventsLoading && (
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>
              {events.length} {events.length === 1 ? 'event' : 'events'}
            </span>
          )}
        </div>

        {eventsLoading ? (
          <div style={{ textAlign: 'center', color: 'var(--gray2)', fontFamily: 'var(--mono)', fontSize: 11, padding: '48px 0' }}>Loading…</div>
        ) : events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '56px 0', border: '1.5px dashed var(--dark4)', borderRadius: 12 }}>
            <div style={{ fontSize: 28, marginBottom: 12 }}>◇</div>
            <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 8 }}>No events yet</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>
              {club.name} hasn't posted any events
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 18 }}>
            {events.map((ev, i) => (
              <EventCard key={ev.id} event={ev} delay={i * 30} onClick={() => navigate(`/events/${ev.id}`)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── EventCard ─────────────────────────────────────────────
function EventCard({ event: ev, delay, onClick }: { event: Event; delay: number; onClick: () => void }) {
  const color = getEventColor(ev)
  return (
    <div
      className="pcard au"
      style={{ animationDelay: `${delay}ms`, cursor: 'pointer' }}
      onClick={onClick}
    >
      {ev.poster_url
        ? <img src={ev.poster_url} alt={ev.title} onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
        : <div style={{ width: '100%', height: '100%', background: `linear-gradient(155deg, ${color}22 0%, var(--dark2) 65%)` }} />
      }
      <div className="pcard-grad" />
      <div className="pcard-body" style={{ zIndex: 2 }}>
        <h3 style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 700, lineHeight: 1.25, marginBottom: 5 }}>{ev.title}</h3>
        <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'rgba(242,234,220,0.45)' }}>{ev.date_display}</div>
        {ev.is_hot && (
          <div style={{ marginTop: 5, display: 'inline-block', fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '1px 6px' }}>Hot</div>
        )}
      </div>
    </div>
  )
}
