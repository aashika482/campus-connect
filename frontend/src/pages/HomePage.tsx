import { useEvents, useUserEvents } from '@/hooks/useData'
import { useAuthStore } from '@/context/authStore'
import { splitTags, getEventColor, TAG_COLORS } from '@/types'
import type { Event } from '@/types'

interface Props { onViewEvent: (ev: Event) => void }

export function HomePage({ onViewEvent }: Props) {
  const { user } = useAuthStore()
  const { events, loading } = useEvents()
  const { registered, saved, toggleSave, register } = useUserEvents()

  const hot       = events.filter(e => e.is_hot)
  const userTags  = user?.interests ? user.interests.split(',') : []
  const forYou    = userTags.length > 0
    ? events.filter(e => splitTags(e.tags).some(t => userTags.includes(t))).slice(0, 6)
    : events.slice(0, 6)
  const upcoming  = [...events].sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime()).slice(0, 4)

  if (loading) return <PageLoader />

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      {/* Hero */}
      <div className="pg-hdr" style={{ padding: '56px 40px 48px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 12 }}>
            MUJ · Manipal University Jaipur
          </div>
          <h1 style={{ fontFamily: 'var(--syne)', fontSize: 'clamp(36px,5vw,64px)', fontWeight: 800, letterSpacing: '-2px', lineHeight: 1.05, marginBottom: 16 }}>
            Your campus.<br />
            <span style={{ color: 'var(--orange)' }}>Fully alive.</span>
          </h1>
          <p style={{ fontFamily: 'var(--body)', fontSize: 15, color: 'var(--cream3)', maxWidth: 480, lineHeight: 1.6 }}>
            16 clubs, 25+ events, one place. Find what's happening, register in seconds, and never miss a moment.
          </p>
          <div style={{ display: 'flex', gap: 10, marginTop: 28, flexWrap: 'wrap' }}>
            {[`${events.length} events`, '16 clubs', '3,200 students'].map((t, i) => (
              <div key={i} style={{ padding: '5px 12px', background: i === 0 ? 'var(--orange)' : 'transparent', color: i === 0 ? 'var(--bg)' : 'var(--cream)', border: i === 0 ? 'none' : '1.5px solid rgba(242,234,220,0.14)', fontSize: 9, fontFamily: 'var(--mono)', letterSpacing: 1.2, textTransform: 'uppercase' }}>{t}</div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 40px' }}>

        {/* Hot events */}
        {hot.length > 0 && (
          <Section title="🔥 Hot Right Now" sub={`${hot.length} events everyone's watching`}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 16 }}>
              {hot.map(ev => (
                <EventCard key={ev.id} ev={ev} onView={onViewEvent} onSave={toggleSave} isSaved={saved.includes(ev.id)} isRegistered={registered.includes(ev.id)} />
              ))}
            </div>
          </Section>
        )}

        {/* For You */}
        <Section title="For You" sub={userTags.length > 0 ? `Based on your interests` : "Explore what's on"}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 16 }}>
            {forYou.map(ev => (
              <EventCard key={ev.id} ev={ev} onView={onViewEvent} onSave={toggleSave} isSaved={saved.includes(ev.id)} isRegistered={registered.includes(ev.id)} />
            ))}
          </div>
        </Section>

        {/* Upcoming — horizontal list */}
        <Section title="Coming Up" sub="Sorted by date">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {upcoming.map(ev => (
              <UpcomingRow key={ev.id} ev={ev} onClick={() => onViewEvent(ev)} isRegistered={registered.includes(ev.id)} />
            ))}
          </div>
        </Section>

        {/* Tag filter strip */}
        <Section title="Browse by Category" sub="">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(TAG_COLORS).map(([tag, color]) => (
              <button key={tag}
                style={{ padding: '7px 14px', fontSize: 11, fontFamily: 'var(--mono)', border: `1.5px solid ${color}44`, background: `${color}11`, color, borderRadius: 20, letterSpacing: 0.5, transition: 'all 0.15s', textTransform: 'capitalize' }}
                onMouseOver={e => { (e.currentTarget as HTMLElement).style.background = `${color}22` }}
                onMouseOut={e =>  { (e.currentTarget as HTMLElement).style.background = `${color}11` }}>
                {tag}
              </button>
            ))}
          </div>
        </Section>

      </div>
    </div>
  )
}

// ── Sub-components ───────────────────────────────────────

function Section({ title, sub, children }: { title: string; sub: string; children: React.ReactNode }) {
  return (
    <div style={{ marginTop: 52 }}>
      <div style={{ marginBottom: 22 }}>
        <h2 style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>{title}</h2>
        {sub && <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 4 }}>{sub}</p>}
      </div>
      {children}
    </div>
  )
}

function EventCard({ ev, onView, onSave, isSaved, isRegistered }: {
  ev: Event; onView: (e: Event) => void; onSave: (e: Event) => void;
  isSaved: boolean; isRegistered: boolean;
}) {
  return (
    <div className="pcard au" onClick={() => onView(ev)}
      style={isRegistered ? { boxShadow: '0 0 0 2px rgba(16,185,129,0.35)' } : {}}>
      {ev.poster_url
        ? <img src={ev.poster_url} alt={ev.title} onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
        : <div style={{ width: '100%', height: '100%', background: `linear-gradient(155deg, ${getEventColor(ev)}22 0%, var(--dark2) 65%)` }} />
      }
      <div className="pcard-grad" />

      {/* Badges */}
      <div style={{ position: 'absolute', top: 10, left: 10, right: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', zIndex: 2 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          {ev.is_hot && <span style={{ padding: '3px 8px', fontSize: 9, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 1.5, background: 'var(--orange)', color: 'var(--bg)', fontWeight: 600 }}>Hot</span>}
          {isRegistered && <span style={{ padding: '3px 8px', fontSize: 9, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 1, background: 'rgba(16,185,129,0.85)', color: '#fff', fontWeight: 600 }}>✓ Registered</span>}
        </div>
        <button onClick={e => { e.stopPropagation(); onSave(ev) }}
          style={{ width: 30, height: 30, background: 'rgba(9,9,9,0.55)', backdropFilter: 'blur(8px)', border: '1px solid rgba(242,234,220,0.14)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: isSaved ? 'var(--orange)' : 'var(--cream)' }}>
          {isSaved ? '★' : '☆'}
        </button>
      </div>

      <div className="pcard-body" style={{ zIndex: 2 }}>
        <div style={{ display: 'flex', gap: 5, marginBottom: 7, flexWrap: 'wrap' }}>
          {splitTags(ev.tags).slice(0, 2).map(tg => (
            <span key={tg} style={{ padding: '2px 7px', fontSize: 9, fontFamily: 'var(--mono)', background: 'rgba(9,9,9,0.6)', backdropFilter: 'blur(4px)', border: '1px solid rgba(242,234,220,0.13)', color: 'rgba(242,234,220,0.65)', textTransform: 'capitalize' }}>{tg}</span>
          ))}
        </div>
        <h3 style={{ fontFamily: 'var(--head)', fontSize: 14.5, fontWeight: 700, lineHeight: 1.25, marginBottom: 6 }}>{ev.title}</h3>
        <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'rgba(242,234,220,0.48)' }}>{ev.club_name}</div>
        <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'rgba(242,234,220,0.38)' }}>{ev.date_display}</div>
      </div>
    </div>
  )
}

function UpcomingRow({ ev, onClick, isRegistered }: { ev: Event; onClick: () => void; isRegistered: boolean }) {
  const color = getEventColor(ev)
  return (
    <button onClick={onClick}
      style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '14px 18px', background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: `3px solid ${color}`, cursor: 'pointer', transition: 'all 0.15s', textAlign: 'left', width: '100%' }}
      onMouseOver={e => (e.currentTarget.style.background = 'var(--dark3)')}
      onMouseOut={e  => (e.currentTarget.style.background = 'var(--dark2)')}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color, minWidth: 60 }}>{ev.date_display}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 600 }}>{ev.title}</div>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 2 }}>{ev.club_name}</div>
      </div>
      {isRegistered && <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 8px', flexShrink: 0 }}>✓ Going</span>}
    </button>
  )
}

function PageLoader() {
  return (
    <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', letterSpacing: 3, textTransform: 'uppercase' }}>Loading…</div>
    </div>
  )
}
