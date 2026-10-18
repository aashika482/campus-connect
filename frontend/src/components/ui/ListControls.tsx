// Controls shared by list pages: "Load more" (Events, Clubs) and a tab bar (Club Dashboard, DSW Console).

export function LoadMore({ shown, total, loading, onClick, noun }: {
  shown: number
  total: number
  loading: boolean
  onClick: () => void
  noun: string           // e.g. "events"
}) {
  if (shown >= total) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, marginTop: 32 }}>
      <button onClick={onClick} className="btn-g" disabled={loading}
        style={{ padding: '11px 30px', fontSize: 10, letterSpacing: 2 }}>
        {loading ? 'Loading…' : 'Load more'}
      </button>
      <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>
        Showing {shown} of {total} {noun}
      </span>
    </div>
  )
}

export function TabBar<T extends string>({ tabs, active, onChange }: {
  tabs: readonly { id: T; label: string }[]
  active: T
  onChange: (id: T) => void
}) {
  return (
    <div style={{ borderBottom: '1px solid var(--dark3)' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 40px', display: 'flex', gap: 4 }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => onChange(t.id)}
            style={{ padding: '14px 16px', fontFamily: 'var(--mono)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1.5, color: active === t.id ? 'var(--orange)' : 'var(--gray2)', borderBottom: `2px solid ${active === t.id ? 'var(--orange)' : 'transparent'}`, marginBottom: -1, transition: 'color 0.15s' }}>
            {t.label}
          </button>
        ))}
      </div>
    </div>
  )
}
