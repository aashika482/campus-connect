import { useState } from 'react'
import { useEvents, useUserEvents } from '@/hooks/useData'
import { splitTags, getEventColor, ALL_TAGS } from '@/types'
import type { Event } from '@/types'

interface Props { onViewEvent: (ev: Event) => void }

export function EventsPage({ onViewEvent }: Props) {
  const [activeTag, setActiveTag] = useState<string | null>(null)
  const { events, loading } = useEvents(activeTag ? { tag: activeTag } : undefined)
  const { registered, saved, toggleSave } = useUserEvents()

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      {/* Header */}
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>All Events</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 42, fontWeight: 800, letterSpacing: '-2px' }}>
            Discover<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>
            {loading ? '…' : `${events.length} events`}
          </p>
        </div>
      </div>

      {/* Tag filter */}
      <div style={{ borderBottom: '1px solid var(--dark3)', overflowX: 'auto', scrollbarWidth: 'none' }}>
        <div style={{ display: 'flex', gap: 0, padding: '0 40px', maxWidth: 1200, margin: '0 auto', width: 'max-content' }}>
          {[{ id: null, label: 'All' }, ...ALL_TAGS].map(t => {
            const active = activeTag === t.id
            return (
              <button key={String(t.id)} onClick={() => setActiveTag(t.id)}
                style={{ padding: '12px 16px', fontSize: 11, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 1, color: active ? 'var(--orange)' : 'var(--gray2)', borderBottom: active ? '2px solid var(--orange)' : '2px solid transparent', marginBottom: -1, whiteSpace: 'nowrap', transition: 'all 0.15s' }}>
                {t.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Grid */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 40px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: 'var(--gray2)', fontFamily: 'var(--mono)', fontSize: 12, padding: '60px 0' }}>Loading…</div>
        ) : events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <div style={{ fontFamily: 'var(--head)', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>No events found</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>Try a different filter</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 18 }}>
            {events.map((ev, i) => (
              <EventCard key={ev.id} ev={ev} delay={i * 40} onView={onViewEvent}
                isSaved={saved.includes(ev.id)} isRegistered={registered.includes(ev.id)}
                onSave={toggleSave} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function EventCard({ ev, delay, onView, isSaved, isRegistered, onSave }: {
  ev: Event; delay: number; onView: (e: Event) => void;
  isSaved: boolean; isRegistered: boolean; onSave: (e: Event) => void;
}) {
  return (
    <div className="pcard au" style={{ animationDelay: `${delay}ms`, ...(isRegistered ? { boxShadow: '0 0 0 2px rgba(16,185,129,0.35)' } : {}) }}
      onClick={() => onView(ev)}>
      {ev.poster_url
        ? <img src={ev.poster_url} alt={ev.title} onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
        : <div style={{ width: '100%', height: '100%', background: `linear-gradient(155deg, ${getEventColor(ev)}22 0%, var(--dark2) 65%)` }} />
      }
      <div className="pcard-grad" />
      <div style={{ position: 'absolute', top: 10, left: 10, right: 10, display: 'flex', justifyContent: 'space-between', zIndex: 2 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {ev.is_hot     && <span style={{ padding: '3px 8px', fontSize: 9, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 1.5, background: 'var(--orange)', color: 'var(--bg)', fontWeight: 600 }}>Hot</span>}
          {isRegistered  && <span style={{ padding: '3px 8px', fontSize: 9, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 1, background: 'rgba(16,185,129,0.85)', color: '#fff', fontWeight: 600 }}>✓ Reg</span>}
        </div>
        <button onClick={e => { e.stopPropagation(); onSave(ev) }}
          style={{ width: 28, height: 28, background: 'rgba(9,9,9,0.6)', backdropFilter: 'blur(8px)', border: '1px solid rgba(242,234,220,0.14)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: isSaved ? 'var(--orange)' : 'var(--cream)', fontSize: 12 }}>
          {isSaved ? '★' : '☆'}
        </button>
      </div>
      <div className="pcard-body" style={{ zIndex: 2 }}>
        <div style={{ display: 'flex', gap: 4, marginBottom: 6, flexWrap: 'wrap' }}>
          {splitTags(ev.tags).slice(0, 2).map(tg => (
            <span key={tg} style={{ padding: '2px 7px', fontSize: 9, fontFamily: 'var(--mono)', background: 'rgba(9,9,9,0.6)', border: '1px solid rgba(242,234,220,0.13)', color: 'rgba(242,234,220,0.65)', textTransform: 'capitalize' }}>{tg}</span>
          ))}
        </div>
        <h3 style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 700, lineHeight: 1.25, marginBottom: 5 }}>{ev.title}</h3>
        <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'rgba(242,234,220,0.45)' }}>{ev.date_display}</div>
      </div>
    </div>
  )
}
