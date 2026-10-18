// Governance consoles:
//  - DswPage (/dsw): the DSW office. Reviews club team requests, sees and ends active
//    team roles, assigns faculty coordinators, switches account types, reads the activity log
//  - PlatformPage (/platform): the tech team. Grants and removes DSW accounts, reads the log
import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { adminApi, apiError } from '@/api/client'
import { fetchAllClubRoles, useDebounced, usePaged } from '@/hooks/useData'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { TabBar, LoadMore } from '@/components/ui/ListControls'
import { ClubSelect } from '@/components/ui/ClubSelect'
import { PeopleTable, Empty, roleColumns, fmtDate } from './AdminPeople'
import type { Column } from './AdminPeople'
import { ACCOUNT_LABELS } from '@/types'
import type { Account, AccountType, AuditEntry, ClubRoleDetail } from '@/types'

const btn = (color: string): React.CSSProperties => ({
  padding: '4px 10px', fontSize: 10, fontFamily: 'var(--mono)', color, border: `1px solid ${color}55`, borderRadius: 4, whiteSpace: 'nowrap',
})

// Page header + tab bar shared by both consoles; the active tab lives in the URL (?tab=)
function Console<T extends string>({ kicker, title, intro, tabs, children }: {
  kicker: string
  title: string
  intro: string
  tabs: readonly { id: T; label: string }[]
  children: (tab: T) => React.ReactNode
}) {
  const [params, setParams] = useSearchParams()
  const tab = tabs.find(t => t.id === params.get('tab'))?.id ?? tabs[0].id
  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>{kicker}</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 38, fontWeight: 800, letterSpacing: '-2px' }}>
            {title}<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>{intro}</p>
        </div>
      </div>
      <TabBar tabs={tabs} active={tab} onChange={t => setParams(t === tabs[0].id ? {} : { tab: t })} />
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 40px' }}>{children(tab)}</div>
    </div>
  )
}

// ── DSW Console ───────────────────────────────────────────
const DSW_TABS = [
  { id: 'requests', label: 'Requests' },
  { id: 'teams',    label: 'Club teams' },
  { id: 'accounts', label: 'Accounts' },
  { id: 'activity', label: 'Activity' },
] as const

export function DswPage() {
  const { user } = useAuthStore()
  if (user?.account_type !== 'dsw') return <Empty text="DSW access only" />
  return (
    <Console kicker="Dean of Student Welfare" title="DSW Console" tabs={DSW_TABS}
      intro="Everything that needs approval comes here. Only approved team members can run a club.">
      {tab => tab === 'requests' ? <RoleList status="pending" />
        : tab === 'teams' ? <><AssignFaculty /><RoleList status="active" /></>
        : tab === 'accounts' ? <AccountsTab />
        : <ActivityTab />}
    </Console>
  )
}

// Pending requests (approve / reject) or active team roles (end)
function RoleList({ status }: { status: 'pending' | 'active' }) {
  const { toast } = useToastStore()
  const [rows, setRows] = useState<ClubRoleDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchAllClubRoles(status)
      .then(setRows)
      .catch(err => { setRows([]); setError(apiError(err, 'Failed to load')) })
      .finally(() => setLoading(false))
  }, [status])

  const act = async (r: ClubRoleDetail, action: 'approve' | 'reject' | 'end', exception = false) => {
    setBusyId(r.id)
    try {
      await adminApi.reviewRole(r.id, action, exception)
      setRows(p => p.filter(x => x.id !== r.id))
      toast(action === 'approve' ? `${r.name} is now on ${r.club_name}'s team`
        : action === 'reject' ? `Rejected ${r.name}'s request` : `Ended ${r.name}'s role in ${r.club_name}`, 'success')
    } catch (err: any) {
      const message = apiError(err, 'Failed to update')
      // A student already on another club's team needs an explicit exception
      if (action === 'approve' && !exception && err?.response?.status === 409 && message.includes('multi-club exception')
          && window.confirm(`${message}\n\nApprove anyway, allowing a second club?`)) {
        setBusyId(null)
        return act(r, 'approve', true)
      }
      toast(message, 'error')
    } finally {
      setBusyId(null)
    }
  }

  const actions: Column<ClubRoleDetail> = {
    label: 'Action',
    csv: r => r.status,
    cell: r => (
      <div style={{ display: 'flex', gap: 6, opacity: busyId === r.id ? 0.5 : 1, pointerEvents: busyId === r.id ? 'none' : 'auto' }}>
        {status === 'pending' ? <>
          <button onClick={() => act(r, 'approve')} style={btn('#22C55E')}>Approve</button>
          <button onClick={() => act(r, 'reject')} style={btn('#EF4444')}>Reject</button>
        </> : <button onClick={() => window.confirm(`End ${r.name}'s role in ${r.club_name}?`) && act(r, 'end')} style={btn('#EF4444')}>End role</button>}
      </div>
    ),
  }

  return (
    <PeopleTable
      rows={rows}
      rowKey={r => r.id}
      academic={false}
      loading={loading}
      error={error}
      dateOf={r => status === 'pending' ? r.created_at : (r.reviewed_at ?? r.created_at)}
      dateLabel={status === 'pending' ? 'Requested' : 'Since'}
      fileName={`club-teams-${status}`}
      emptyText={status === 'pending' ? 'Nothing waiting for approval.' : 'No active team roles.'}
      columns={[roleColumns.club, roleColumns.role, roleColumns.proposedBy, actions]}
    />
  )
}

function AssignFaculty() {
  const { toast } = useToastStore()
  const [clubId, setClubId] = useState('')
  const [email, setEmail] = useState('')
  const [sending, setSending] = useState(false)

  const assign = async () => {
    setSending(true)
    try {
      const r = await adminApi.assignFaculty(Number(clubId), email.trim())
      toast(`${r.data.name} now coordinates ${r.data.club_name}. Reload to see them in the list.`, 'success')
      setEmail('')
    } catch (err) {
      toast(apiError(err, 'Could not assign'), 'error')
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 22, padding: 16, border: '1px solid var(--dark3)', borderRadius: 12, background: 'var(--dark2)' }}>
      <div style={{ width: 280 }}><ClubSelect value={clubId} onChange={setClubId} /></div>
      <input className="inp" value={email} onChange={e => setEmail(e.target.value)} placeholder="Faculty email" style={{ width: 260, fontSize: 12 }} />
      <button className="btn-p" disabled={sending || !clubId || !email.trim()} onClick={assign} style={{ padding: '10px 16px', fontSize: 10, letterSpacing: 1.5 }}>
        {sending ? 'Assigning…' : 'Assign faculty coordinator'}
      </button>
    </div>
  )
}

// The types the DSW can switch people between (DSW / tech accounts are the platform admin's)
const SWITCHABLE: AccountType[] = ['student', 'faculty', 'alumni']

function AccountsTab() {
  const { toast } = useToastStore()
  const [q, setQ] = useState('')
  const query = useDebounced(q)
  const [rows, setRows] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    adminApi.accounts({ q: query || undefined, limit: 100 })
      .then(r => { setRows(r.data.items); setError(null) })
      .catch(err => setError(apiError(err, 'Failed to load accounts')))
      .finally(() => setLoading(false))
  }, [query])

  const change = async (a: Account, next: AccountType) => {
    const note = next === 'alumni' ? ' Their team roles end; club memberships stay.' : ''
    if (!window.confirm(`Make ${a.name} ${ACCOUNT_LABELS[next].toLowerCase()}?${note}`)) return
    try {
      const r = await adminApi.setAccountType(a.user_id, next as 'student' | 'faculty' | 'alumni')
      setRows(p => p.map(x => (x.user_id === a.user_id ? r.data : x)))
      toast(`${a.name} is now ${ACCOUNT_LABELS[next].toLowerCase()}`, 'success')
    } catch (err) {
      toast(apiError(err, 'Could not change the account type'), 'error')
    }
  }

  return (
    <div>
      <input className="inp" value={q} onChange={e => setQ(e.target.value)} placeholder="Find anyone by name, email or reg no (server search, first 100)"
        style={{ maxWidth: 480, fontSize: 12, marginBottom: 14 }} />
      <PeopleTable
        rows={rows}
        loading={loading}
        error={error}
        dateOf={r => r.created_at}
        dateLabel="Joined"
        fileName="accounts"
        emptyText="No accounts match."
        columns={[{
          label: 'Account type',
          csv: r => r.account_type,
          cell: r => SWITCHABLE.includes(r.account_type)
            ? <select className="inp" value={r.account_type} onChange={e => change(r, e.target.value as AccountType)}
                style={{ width: 'auto', padding: '4px 8px', fontSize: 11 }}>
                {SWITCHABLE.map(t => <option key={t} value={t}>{ACCOUNT_LABELS[t]}</option>)}
              </select>
            : <span style={{ color: 'var(--orange)' }}>{ACCOUNT_LABELS[r.account_type]}</span>,
        }]}
      />
    </div>
  )
}

// ── Activity log (both consoles) ──────────────────────────
const ACTION_LABELS: Record<string, string> = {
  'club_role.request_owner': 'asked to own a club',
  'club_role.request_editor': 'proposed an editor',
  'club_role.approve': 'approved a team role',
  'club_role.reject': 'rejected a team request',
  'club_role.end': 'ended a team role',
  'club_role.assign_faculty': 'assigned a faculty coordinator',
  'user.account_type': 'changed an account type',
  'user.grant_dsw': 'made a DSW account',
  'user.remove_dsw': 'removed a DSW account',
  'user.grant_platform_admin': 'made a platform admin',
  'user.remove_platform_admin': 'removed a platform admin',
  'club.create': 'created a club',
  'event.hot': 'changed an event\'s "hot" flag',
  'demo.reset': 'reset the demo data',
}

function ActivityTab() {
  const { items, total, loading, loadingMore, loadMore, error } = usePaged<AuditEntry>(adminApi.auditLog, {}, 50)
  if (loading) return <Empty text="Loading…" />
  if (error) return <Empty text={error} />
  if (items.length === 0) return <Empty text="Nothing has happened yet." />
  return (
    <div>
      <div style={{ border: '1px solid var(--dark3)', borderRadius: 12, background: 'var(--dark2)' }}>
        {items.map(e => (
          <div key={e.id} style={{ display: 'flex', gap: 16, padding: '12px 16px', borderBottom: '1px solid var(--dark3)', fontFamily: 'var(--mono)', fontSize: 11.5, color: 'var(--cream3)', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--gray2)', minWidth: 160 }}>{fmtDate(e.created_at)}</span>
            <span style={{ flex: 1, minWidth: 260 }}>
              <span style={{ color: 'var(--cream)' }}>{e.actor_name ?? 'System'}</span> {ACTION_LABELS[e.action] ?? e.action}
              <span style={{ color: 'var(--gray2)' }}>
                {' '}{Object.entries(e.details).filter(([, v]) => v !== null && v !== undefined).map(([k, v]) => `${k}: ${v}`).join(' · ')}
              </span>
            </span>
          </div>
        ))}
      </div>
      <LoadMore shown={items.length} total={total} loading={loadingMore} onClick={loadMore} noun="entries" />
    </div>
  )
}

// ── Platform Console ──────────────────────────────────────
const PLATFORM_TABS = [
  { id: 'dsw',      label: 'DSW accounts' },
  { id: 'activity', label: 'Activity' },
] as const

export function PlatformPage() {
  const { user } = useAuthStore()
  if (user?.account_type !== 'platform_admin') return <Empty text="Tech team access only" />
  return (
    <Console kicker="Tech team" title="Platform Console" tabs={PLATFORM_TABS}
      intro="Appoint the DSW office's accounts. Business decisions (approvals, clubs, roles) belong to the DSW.">
      {tab => tab === 'dsw' ? <DswAccountsTab /> : <ActivityTab />}
    </Console>
  )
}

function DswAccountsTab() {
  const { toast } = useToastStore()
  const [rows, setRows] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [sending, setSending] = useState(false)

  const load = () => {
    setLoading(true)
    adminApi.dswAccounts()
      .then(r => setRows(r.data.items))
      .catch(err => setError(apiError(err, 'Failed to load DSW accounts')))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const grant = async () => {
    setSending(true)
    try {
      const r = await adminApi.grantDsw(email.trim())
      toast(`${r.data.name} is now a DSW account`, 'success')
      setEmail('')
      load()
    } catch (err) {
      toast(apiError(err, 'Could not grant DSW access'), 'error')
    } finally {
      setSending(false)
    }
  }

  const remove = async (a: Account) => {
    if (!window.confirm(`Remove DSW access from ${a.name}?`)) return
    try {
      await adminApi.removeDsw(a.user_id)
      setRows(p => p.filter(x => x.user_id !== a.user_id))
      toast(`${a.name} is no longer a DSW account`, 'success')
    } catch (err) {
      toast(apiError(err, 'Could not remove DSW access'), 'error')
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 18 }}>
        <input className="inp" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email of an existing account" style={{ width: 300, fontSize: 12 }} />
        <button className="btn-p" disabled={sending || !email.trim()} onClick={grant} style={{ padding: '9px 16px', fontSize: 10, letterSpacing: 1.5 }}>
          {sending ? 'Saving…' : 'Make DSW account'}
        </button>
      </div>
      <PeopleTable
        rows={rows}
        academic={false}
        loading={loading}
        error={error}
        dateOf={r => r.created_at}
        dateLabel="Joined"
        fileName="dsw-accounts"
        emptyText="No DSW accounts yet."
        columns={[{ label: 'Action', csv: () => '', cell: r => <button onClick={() => remove(r)} style={btn('#EF4444')}>Remove DSW</button> }]}
      />
    </div>
  )
}
