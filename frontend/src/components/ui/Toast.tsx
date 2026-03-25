import { useToastStore } from '@/context/toastStore'

const ICONS = { success: '✓', error: '✕', info: '·', warn: '!' }
const COLORS = { success: '#10B981', error: '#EF4444', info: 'var(--orange)', warn: '#F59E0B' }

export function ToastContainer() {
  const { toasts, dismiss } = useToastStore()

  return (
    <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 9000, display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'flex-end' }}>
      {toasts.map(t => (
        <div
          key={t.id}
          className={`toast${t.exiting ? ' out' : ''}`}
          onClick={() => dismiss(t.id)}
          style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '11px 16px',
            minWidth: 200, maxWidth: 340,
            background: 'rgba(20,20,20,0.96)', backdropFilter: 'blur(22px)',
            border: `1px solid ${COLORS[t.type]}44`, borderLeft: `3px solid ${COLORS[t.type]}`,
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)', cursor: 'pointer',
          }}
        >
          <span style={{ color: COLORS[t.type], fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
            {ICONS[t.type]}
          </span>
          <span style={{ fontFamily: 'var(--body)', fontSize: 13, color: 'var(--cream)', lineHeight: 1.4 }}>
            {t.msg}
          </span>
        </div>
      ))}
    </div>
  )
}
