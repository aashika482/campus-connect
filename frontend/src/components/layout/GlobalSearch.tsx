import { useState, useEffect, useRef } from 'react'
import { useEvents, useClubs } from '@/hooks/useData'
import type { Event, Club } from '@/types'
import { splitTags } from '@/types'

const HINTS = ['HackX', 'Music', 'Dance', 'Coding', 'Photography', 'Robotics']

interface Props {
  onClose: () => void
  onViewEvent: (ev: Event) => void
  onViewClub:  (cl: Club)  => void
}

export function GlobalSearch({ onClose, onViewEvent, onViewClub }: Props) {
  const [q, setQ] = useState('')
  const ref = useRef<HTMLInputElement>(null)
  const { events } = useEvents()
  const { clubs }  = useClubs()

  useEffect(() => { ref.current?.focus() }, [])
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])

  const ql = q.toLowerCase().trim()
  const evResults = ql.length < 2 ? [] : events.filter(e =>
    e.title.toLowerCase().includes(ql) ||
    e.club_name.toLowerCase().includes(ql) ||
    splitTags(e.tags).some(t => t.includes(ql)) ||
    e.description.toLowerCase().includes(ql)
  ).slice(0, 5)

  const clResults = ql.length < 2 ? [] : clubs.filter(c =>
    c.name.toLowerCase().includes(ql) ||
    c.abbr.toLowerCase().includes(ql) ||
    splitTags(c.tags).some(t => t.includes(ql)) ||
    c.description.toLowerCase().includes(ql)
  ).slice(0, 4)

  const hasResults = evResults.length > 0 || clResults.length > 0

  return (
    <div
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
      style={{ position: 'fixed', inset: 0, zIndex: 8000, display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 80, background: 'rgba(9,9,9,0.78)', backdropFilter: 'blur(20px)' }}>
      <div style={{ width: '100%', maxWidth: 640, margin: '0 16px', animation: 'searchIn 0.28s cubic-bezier(0.22,1,0.36,1) both' }}>
        {/* Input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'rgba(20,14,10,0.98)', border: '1.5px solid rgba(212,86,26,0.35)', padding: '14px 18px', boxShadow: '0 0 40px rgba(212,86,26,0.12), 0 24px 60px rgba(0,0,0,0.7)' }}>
          <svg width={17} height={17} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input ref={ref} value={q} onChange={e => setQ(e.target.value)} placeholder="Search events, clubs, tags…"
            style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: 'var(--cream)', fontSize: 16, fontFamily: 'var(--body)' }} />
          <button onClick={onClose} style={{ color: 'var(--gray2)', padding: 4, fontSize: 9, fontFamily: 'var(--mono)', border: '1px solid var(--dark4)', padding: '3px 7px', letterSpacing: 1 }}>ESC</button>
        </div>

        {/* Results */}
        {ql.length >= 2 && (
          <div style={{ background: 'rgba(15,11,8,0.99)', border: '1.5px solid rgba(242,234,220,0.07)', borderTop: 'none', maxHeight: 420, overflowY: 'auto' }}>
            {!hasResults && (
              <div style={{ padding: '28px 20px', textAlign: 'center', color: 'var(--gray2)', fontFamily: 'var(--mono)', fontSize: 12 }}>
                No results for "<span style={{ color: 'var(--cream)' }}>{q}</span>"
              </div>
            )}
            {evResults.length > 0 && (
              <>
                <div style={{ padding: '10px 18px 6px', fontSize: 9, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--orange)', borderBottom: '1px solid var(--dark3)' }}>Events</div>
                {evResults.map(ev => (
                  <button key={ev.id} onClick={() => onViewEvent(ev)}
                    style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%', padding: '12px 18px', borderBottom: '1px solid var(--dark2)', textAlign: 'left' }}
                    onMouseOver={e => (e.currentTarget.style.background = 'rgba(242,234,220,0.03)')}
                    onMouseOut={e  => (e.currentTarget.style.background = 'transparent')}>
                    <div style={{ width: 36, height: 36, flexShrink: 0, overflow: 'hidden', borderRadius: 4 }}>
                      {ev.poster_url ? <img src={ev.poster_url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="" /> : <div style={{ width: '100%', height: '100%', background: 'var(--dark3)' }} />}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'var(--head)', fontSize: 13, fontWeight: 600, color: 'var(--cream)', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ev.title}</div>
                      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>{ev.club_name} · {ev.date_display}</div>
                    </div>
                    {ev.is_hot && <span style={{ fontSize: 9, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 1, color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '2px 6px' }}>Hot</span>}
                  </button>
                ))}
              </>
            )}
            {clResults.length > 0 && (
              <>
                <div style={{ padding: '10px 18px 6px', fontSize: 9, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--orange)', borderBottom: '1px solid var(--dark3)' }}>Clubs</div>
                {clResults.map(cl => (
                  <button key={cl.id} onClick={() => onViewClub(cl)}
                    style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%', padding: '12px 18px', borderBottom: '1px solid var(--dark2)', textAlign: 'left' }}
                    onMouseOver={e => (e.currentTarget.style.background = 'rgba(242,234,220,0.03)')}
                    onMouseOut={e  => (e.currentTarget.style.background = 'transparent')}>
                    <div style={{ width: 36, height: 36, flexShrink: 0, background: 'var(--dark3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ color: cl.color, fontFamily: 'var(--mono)', fontSize: 11, fontWeight: 700 }}>{cl.abbr.slice(0, 3)}</span>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'var(--head)', fontSize: 13, fontWeight: 600, color: 'var(--cream)', marginBottom: 2 }}>{cl.name}</div>
                      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>{cl.member_count} members · {splitTags(cl.tags).join(', ')}</div>
                    </div>
                    {cl.is_open && <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 6px' }}>Open</span>}
                  </button>
                ))}
              </>
            )}
          </div>
        )}

        {/* Hint chips */}
        {ql.length < 2 && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12, padding: '0 4px' }}>
            {HINTS.map(h => (
              <button key={h} onClick={() => setQ(h)}
                style={{ padding: '5px 12px', fontSize: 11, fontFamily: 'var(--mono)', color: 'var(--gray2)', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--dark4)', letterSpacing: 0.5, transition: 'all 0.15s' }}
                onMouseOver={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,86,26,0.4)'; (e.currentTarget as HTMLElement).style.color = 'var(--orange)' }}
                onMouseOut={e  => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--dark4)';          (e.currentTarget as HTMLElement).style.color = 'var(--gray2)' }}>
                {h}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
