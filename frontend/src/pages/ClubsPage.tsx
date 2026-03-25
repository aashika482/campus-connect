// ClubsPage.tsx
import { useClubs, useUserClubs } from '@/hooks/useData'
import { splitTags } from '@/types'
import type { Club } from '@/types'

interface Props { onViewClub: (cl: Club) => void }

export function ClubsPage({ onViewClub }: Props) {
  const { clubs, loading } = useClubs()
  const { joinedClubs, toggleMembership } = useUserClubs()

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Campus Clubs</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 42, fontWeight: 800, letterSpacing: '-2px' }}>
            Find Your People<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>
            {loading ? '…' : `${clubs.length} clubs across every interest`}
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 40px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', color: 'var(--gray2)', fontFamily: 'var(--mono)', fontSize: 12, padding: '60px 0' }}>Loading…</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
            {clubs.map((cl, i) => (
              <ClubCard key={cl.id} club={cl} delay={i * 30}
                isMember={joinedClubs.includes(cl.id)}
                onView={onViewClub}
                onToggle={toggleMembership} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ClubCard({ club, delay, isMember, onView, onToggle }: {
  club: Club; delay: number; isMember: boolean;
  onView: (c: Club) => void; onToggle: (c: Club) => void;
}) {
  const tags = splitTags(club.tags)
  return (
    <div className="ccard au" style={{ '--cc': club.color, animationDelay: `${delay}ms` } as any}
      onClick={() => onView(club)}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
        <div style={{ width: 48, height: 48, background: `${club.color}18`, border: `1.5px solid ${club.color}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 10, fontWeight: 700, color: club.color }}>{club.abbr.slice(0, 4)}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {club.is_open
            ? <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 7px' }}>Open</span>
            : <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--gray2)', border: '1px solid var(--dark4)', padding: '2px 7px' }}>Closed</span>
          }
        </div>
      </div>

      <h3 style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 6 }}>{club.name}</h3>
      <p style={{ fontFamily: 'var(--body)', fontSize: 12.5, color: 'var(--gray)', lineHeight: 1.5, marginBottom: 14, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {club.description}
      </p>

      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 16 }}>
        {tags.map(t => <span key={t} className="tag">{t}</span>)}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>{club.member_count} members</span>
        <button onClick={e => { e.stopPropagation(); onToggle(club) }}
          style={{ padding: '7px 14px', fontSize: 11, fontFamily: 'var(--mono)', fontWeight: 600, letterSpacing: 0.5, border: `1.5px solid ${isMember ? club.color : 'var(--dark4)'}`, background: isMember ? `${club.color}18` : 'transparent', color: isMember ? club.color : 'var(--gray2)', transition: 'all 0.15s' }}>
          {isMember ? 'Joined ✓' : '+ Join'}
        </button>
      </div>
    </div>
  )
}
