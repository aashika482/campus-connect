import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import { GlobalSearch } from './GlobalSearch'
import type { Event, Club } from '@/types'

const lp = { fill: 'none', stroke: 'currentColor', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }

const HomeIco  = () => <svg width={15} height={15} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
const EvIco    = () => <svg width={15} height={15} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><rect x="3" y="3" width="7" height="5" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="3" y="12" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="5" rx="1"/></svg>
const CalIco   = () => <svg width={15} height={15} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
const PplIco   = () => <svg width={15} height={15} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
const BkIco    = () => <svg width={15} height={15} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>
const DashIco  = () => <svg width={15} height={15} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
const SrcIco   = () => <svg width={13} height={13} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
const BellIco  = () => <svg width={15} height={15} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>

const SparkStar = () => (
  <svg width={9} height={13} viewBox="0 0 14 20" fill="var(--orange)" style={{ flexShrink: 0 }}>
    <path d="M7 0 C7.18 5.6 9.8 8.2 14 10 C9.8 11.8 7.18 14.4 7 20 C6.82 14.4 4.2 11.8 0 10 C4.2 8.2 6.82 5.6 7 0 Z"/>
  </svg>
)

const NAV_ITEMS = [
  { path: '/',         label: 'Home',     Icon: HomeIco },
  { path: '/events',   label: 'Events',   Icon: EvIco },
  { path: '/calendar', label: 'Calendar', Icon: CalIco },
  { path: '/clubs',    label: 'Clubs',    Icon: PplIco },
  { path: '/saved',    label: 'Saved',    Icon: BkIco },
]

const NOTIFS = [
  { id: 1, text: 'HackX 3.0 registration closes in 3 days', time: '2h ago', read: false },
  { id: 2, text: "TechnoUtsav '25 just dropped — check it out!", time: '5h ago', read: false },
  { id: 3, text: "You're registered for MUN 2025 on Oct 25–26", time: '1d ago', read: true },
  { id: 4, text: 'Startup Pitch Day is now open for applications', time: '1d ago', read: false },
  { id: 5, text: 'Groove Nation team formation deadline this Sunday', time: '2d ago', read: true },
]

interface Props {
  onViewEvent: (ev: Event) => void
  onViewClub:  (cl: Club)  => void
}

export function Nav({ onViewEvent, onViewClub }: Props) {
  const navigate  = useNavigate()
  const location  = useLocation()
  const { user, logout } = useAuthStore()
  const [showSearch, setShowSearch] = useState(false)
  const [showNotif,  setShowNotif]  = useState(false)
  const [notifs, setNotifs] = useState(NOTIFS)

  const unread = notifs.filter(n => !n.read).length
  const markAll = () => setNotifs(p => p.map(n => ({ ...n, read: true })))

  return (
    <>
      <nav className="nav" style={{ position: 'fixed', top: 0, left: 0, right: 0, height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 28px', zIndex: 100 }}>
        {/* Logo */}
        <button onClick={() => navigate('/')} style={{ display: 'flex', alignItems: 'center', gap: 4, fontFamily: 'var(--syne)', fontSize: 21, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '-0.5px' }}>
          <span style={{ color: 'var(--cream)' }}>Cam</span>
          <SparkStar />
          <span style={{ color: 'var(--orange)' }}>Pulse</span>
        </button>

        {/* Nav links */}
        <div style={{ display: 'flex' }}>
          {NAV_ITEMS.map(({ path, label, Icon }) => {
            const active = location.pathname === path
            return (
              <button key={path} onClick={() => navigate(path)}
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 14px', fontSize: 11, fontWeight: 500, textTransform: 'uppercase', letterSpacing: 0.5, fontFamily: 'var(--mono)', transition: 'all 0.15s', color: active ? 'var(--orange)' : 'var(--gray2)', borderBottom: active ? '2px solid var(--orange)' : '2px solid transparent', marginBottom: -1 }}>
                <Icon />{label}
              </button>
            )
          })}
          {user?.role === 'member' && (
            <button onClick={() => navigate('/admin')}
              style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 14px', fontSize: 11, fontWeight: 500, textTransform: 'uppercase', letterSpacing: 0.5, fontFamily: 'var(--mono)', transition: 'all 0.15s', color: location.pathname === '/admin' ? 'var(--orange)' : 'var(--gray2)', borderBottom: location.pathname === '/admin' ? '2px solid var(--orange)' : '2px solid transparent', marginBottom: -1 }}>
              <DashIco />Dashboard
            </button>
          )}
        </div>

        {/* Right actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={() => setShowSearch(true)}
            style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '7px 12px', border: '1.5px solid var(--dark4)', background: 'rgba(242,234,220,0.03)', color: 'var(--gray2)', fontSize: 11, fontFamily: 'var(--mono)', letterSpacing: 0.5, transition: 'all 0.15s' }}
            onMouseOver={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(212,86,26,0.4)'; (e.currentTarget as HTMLElement).style.color = 'var(--cream)' }}
            onMouseOut={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--dark4)'; (e.currentTarget as HTMLElement).style.color = 'var(--gray2)' }}>
            <SrcIco /> Search
            <span style={{ padding: '1px 5px', background: 'var(--dark3)', fontSize: 9, letterSpacing: 1, color: 'var(--gray2)', marginLeft: 2 }}>⌘K</span>
          </button>

          {/* Notification bell */}
          <div style={{ position: 'relative' }}>
            <button onClick={() => setShowNotif(p => !p)}
              style={{ position: 'relative', width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1.5px solid var(--dark4)', background: 'rgba(242,234,220,0.03)', color: 'var(--cream3)', transition: 'all 0.15s' }}>
              <BellIco />
              {unread > 0 && <div style={{ position: 'absolute', top: 7, right: 7, width: 7, height: 7, background: 'var(--orange)', borderRadius: '50%', border: '1.5px solid var(--bg)', boxShadow: '0 0 6px rgba(212,86,26,0.6)' }} />}
            </button>

            {showNotif && (
              <>
                <div style={{ position: 'fixed', inset: 0, zIndex: 99 }} onClick={() => setShowNotif(false)} />
                <div style={{ position: 'absolute', top: 'calc(100% + 10px)', right: 0, width: 320, background: 'rgba(14,10,8,0.99)', border: '1.5px solid rgba(242,234,220,0.09)', boxShadow: '0 24px 60px rgba(0,0,0,0.75)', zIndex: 200, animation: 'panelIn 0.22s cubic-bezier(0.22,1,0.36,1) both' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '13px 16px 10px', borderBottom: '1px solid var(--dark3)' }}>
                    <div style={{ fontFamily: 'var(--head)', fontSize: 13, fontWeight: 700 }}>Notifications</div>
                    <button onClick={markAll} style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--orange)', letterSpacing: 0.5 }}>Mark all read</button>
                  </div>
                  <div style={{ maxHeight: 360, overflowY: 'auto' }}>
                    {notifs.map(n => (
                      <div key={n.id} onClick={() => setNotifs(p => p.map(x => x.id === n.id ? { ...x, read: true } : x))}
                        style={{ display: 'flex', gap: 10, padding: '11px 16px', borderBottom: '1px solid var(--dark2)', cursor: 'pointer', background: n.read ? 'transparent' : 'rgba(212,86,26,0.03)' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontFamily: 'var(--body)', fontSize: 12.5, color: n.read ? 'var(--gray)' : 'var(--cream)', lineHeight: 1.4, marginBottom: 3 }}>{n.text}</div>
                          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>{n.time}</div>
                        </div>
                        {!n.read && <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--orange)', flexShrink: 0, marginTop: 5 }} />}
                      </div>
                    ))}
                  </div>
                  <div style={{ padding: '10px 16px', borderTop: '1px solid var(--dark3)', textAlign: 'center' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', letterSpacing: 0.5 }}>That's all for now</span>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Profile */}
          <button onClick={() => navigate('/profile')} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {user?.role === 'member' && <span style={{ fontSize: 10, color: 'var(--orange)', fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 1, border: '1px solid rgba(212,86,26,0.3)', padding: '3px 8px', background: 'rgba(212,86,26,0.08)' }}>Admin</span>}
            <span style={{ fontSize: 11, color: 'var(--gray2)', fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 0.5 }}>{user?.name?.split(' ')[0]}</span>
            <div style={{ width: 34, height: 34, background: 'var(--orange)', color: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 14, fontFamily: 'var(--head)', boxShadow: '0 0 18px rgba(212,86,26,0.35)' }}>
              {(user?.name ?? 'U')[0].toUpperCase()}
            </div>
          </button>
        </div>
      </nav>

      {showSearch && (
        <GlobalSearch
          onClose={() => setShowSearch(false)}
          onViewEvent={ev => { onViewEvent(ev); setShowSearch(false) }}
          onViewClub={cl => { onViewClub(cl); setShowSearch(false) }}
        />
      )}
    </>
  )
}
