// "Load more" control shared by the paginated Events and Clubs pages.

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
