// Governance consoles:
//  - DswPage (/dsw): the DSW office. Reviews club team requests and leave requests, sees and ends
//    active team roles, assigns faculty coordinators, makes clubs private, switches account types,
//    reads the activity log
//  - PlatformPage (/platform): the tech team. Grants and removes DSW accounts, reads the log
import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { adminApi, clubsApi, apiError } from '@/api/client'
import { fetchAllClubRoles, useDebounced, usePaged } from '@/hooks/useData'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { TabBar, LoadMore } from '@/components/ui/ListControls'
import { ClubSelect } from '@/components/ui/ClubSelect'
import { PeopleTable, Empty, roleColumns, fmtDate } from './AdminPeople'
import { DswClubRequests } from './ClubRequests'
import type { Column } from './AdminPeople'
import { ACCOUNT_LABELS } from '@/types'
import type { Account, AccountType, AuditEntry, ClubRoleDetail, LeaveRequest, Club, Evaluation } from '@/types'

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
  { id: 'clubs',    label: 'New clubs' },
  { id: 'leaving',  label: 'Leave requests' },
  { id: 'teams',    label: 'Club teams' },
  { id: 'evaluations', label: 'Evaluations' },
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
        : tab === 'clubs' ? <DswClubRequests />
        : tab === 'leaving' ? <LeaveRequests />
        : tab === 'teams' ? <><AssignFaculty /><ClubPrivacy /><RoleList status="active" /></>
        : tab === 'evaluations' ? <EvaluationsTab />
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

// Students asking to leave a club's working team, or a club
function LeaveRequests() {
  const { toast } = useToastStore()
  const [rows, setRows] = useState<LeaveRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected'>('pending')   // the queue, or history

  useEffect(() => {
    setLoading(true)
    adminApi.leaveRequests({ status })
      .then(r => { setRows(r.data.items); setError(null) })
      .catch(err => setError(apiError(err, 'Failed to load')))
      .finally(() => setLoading(false))
  }, [status])

  const act = async (r: LeaveRequest, action: 'approve' | 'reject') => {
    setBusyId(r.id)
    try {
      await adminApi.decideLeave(r.id, action)
      setRows(p => p.filter(x => x.id !== r.id))
      toast(action === 'approve' ? `${r.name} has left ${r.scope === 'working_team' ? `${r.club_name}'s working team` : r.club_name}` : 'Request rejected', 'success')
    } catch (err) {
      toast(apiError(err, 'Failed to update'), 'error')
    } finally {
      setBusyId(null)
    }
  }

  return (<>
    <select className="inp" value={status} onChange={e => setStatus(e.target.value as typeof status)}
      style={{ width: 'auto', fontSize: 12, marginBottom: 14 }}>
      <option value="pending">Waiting for you</option>
      <option value="approved">Approved</option>
      <option value="rejected">Rejected</option>
    </select>
    <PeopleTable
      rows={rows}
      rowKey={r => r.id}
      academic={false}
      loading={loading}
      error={error}
      dateOf={r => status === 'pending' ? r.created_at : (r.reviewed_at ?? r.created_at)}
      dateLabel={status === 'pending' ? 'Requested' : 'Decided'}
      fileName={`leave-requests-${status}`}
      emptyText={status === 'pending' ? 'No one is waiting to leave a club.' : `No ${status} requests.`}
      columns={[
        { label: 'Club', csv: r => r.club_name, cell: r => <span style={{ color: 'var(--cream)' }}>{r.club_name}</span> },
        { label: 'Wants to leave', csv: r => r.scope, cell: r => r.scope === 'working_team' ? 'The working team (stays a member)' : 'The club' },
        { label: 'Reason', csv: r => r.reason ?? '', cell: r => r.reason || '—' },
        {
          label: 'Action', csv: r => r.status,
          cell: r => r.status !== 'pending' ? <span style={{ textTransform: 'capitalize' }}>{r.status}</span> : (
            <div style={{ display: 'flex', gap: 6, opacity: busyId === r.id ? 0.5 : 1, pointerEvents: busyId === r.id ? 'none' : 'auto' }}>
              <button onClick={() => act(r, 'approve')} style={btn('#22C55E')}>Approve</button>
              <button onClick={() => act(r, 'reject')} style={btn('#EF4444')}>Reject</button>
            </div>
          ),
        },
      ]}
    />
  </>)
}

// The yearly audit of every club (imported from the DSW's sheet): private to the DSW
const CATEGORY_COLORS: Record<string, string> = {
  Platinum: '#E5E7EB', Gold: '#EAB308', Silver: '#94A3B8', Bronze: '#C2410C', White: '#F8FAFC', Black: '#6B7280',
}

function EvaluationsTab() {
  const [year, setYear] = useState<string | undefined>()
  const [data, setData] = useState<{ years: string[]; items: Evaluation[] } | null>(null)
  const [category, setCategory] = useState('')
  const [query, setQuery] = useState('')
  useEffect(() => { adminApi.evaluations(year).then(r => setData(r.data)).catch(() => setData({ years: [], items: [] })) }, [year])

  if (!data) return <Empty text="Loading…" />
  if (data.years.length === 0) return <Empty text="No evaluations yet. Import the audit sheet: python -m app.db.import_clubs SHEET.xlsx --year 2024-25" />
  const q = query.trim().toLowerCase()
  const rows = data.items.filter(e => (!category || e.category === category) && (!q || e.club_name.toLowerCase().includes(q)))
  const categories = [...new Set(data.items.map(e => e.category))]
  const th: React.CSSProperties = { fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.2, textAlign: 'left', padding: '10px 10px', borderBottom: '1px solid var(--dark3)', whiteSpace: 'nowrap' }
  const td: React.CSSProperties = { fontFamily: 'var(--mono)', fontSize: 11.5, color: 'var(--cream3)', padding: '10px 10px', borderBottom: '1px solid var(--dark3)', verticalAlign: 'top' }
  const n = (v: number) => (Number.isInteger(v) ? v : v.toFixed(1))

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 14 }}>
        <select className="inp" value={year ?? data.years[0]} onChange={e => setYear(e.target.value)} style={{ width: 'auto', fontSize: 12 }}>
          {data.years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <select className="inp" value={category} onChange={e => setCategory(e.target.value)} style={{ width: 'auto', fontSize: 12 }}>
          <option value="">Every category</option>
          {categories.map(c => <option key={c} value={c}>{c} ({data.items.filter(e => e.category === c).length})</option>)}
        </select>
        <input className="inp" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search clubs…" style={{ width: 240, fontSize: 12 }} />
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>{rows.length} clubs · private to the DSW</span>
      </div>
      <div style={{ border: '1px solid var(--dark3)', borderRadius: 12, overflowX: 'auto', background: 'var(--dark2)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 980 }}>
          <thead><tr>
            {['Club', 'Category', 'Events /30', 'Sponsors /20', 'Engagement /20', 'DSW /20', 'Faculty /10', 'Total', 'Coordinators', 'Remarks']
              .map(h => <th key={h} style={th}>{h}</th>)}
          </tr></thead>
          <tbody>
            {rows.map(e => (
              <tr key={e.club_id}>
                <td style={{ ...td, color: 'var(--cream)', maxWidth: 240 }}>{e.club_name}</td>
                <td style={{ ...td, color: CATEGORY_COLORS[e.category] ?? 'var(--cream3)' }}>{e.category}</td>
                <td style={td}>{n(e.quality_of_events)}</td><td style={td}>{n(e.sponsorship)}</td>
                <td style={td}>{n(e.student_engagement)}</td><td style={td}>{n(e.dsw_component)}</td>
                <td style={td}>{n(e.faculty_component)}</td>
                <td style={{ ...td, color: 'var(--cream)', fontWeight: 600 }}>{n(e.total)}</td>
                <td style={{ ...td, maxWidth: 220 }}>
                  {e.coordinators.join(', ')}
                  {e.invited_coordinators.length > 0 && (
                    <div style={{ color: 'var(--gray2)' }} title="Named in the records; becomes coordinator on signing in">
                      Invited: {e.invited_coordinators.join(', ')}
                    </div>
                  )}
                  {!e.coordinators.length && !e.invited_coordinators.length && '—'}
                </td>
                <td style={{ ...td, maxWidth: 320, whiteSpace: 'pre-wrap' }}>{e.remarks || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Make any club private or public
function ClubPrivacy() {
  const { toast } = useToastStore()
  const [clubId, setClubId] = useState('')
  const [club, setClub] = useState<Club | null>(null)
  const [saving, setSaving] = useState(false)
  useEffect(() => {
    setClub(null)
    if (clubId) clubsApi.get(Number(clubId)).then(r => setClub(r.data)).catch(() => {})
  }, [clubId])

  const flip = async () => {
    if (!club) return
    setSaving(true)
    try {
      const r = await clubsApi.updateSettings(club.id, { is_private: !club.is_private })
      setClub(r.data)
      toast(`${r.data.name} is now ${r.data.is_private ? 'private' : 'public'}`, 'success')
    } catch (err) {
      toast(apiError(err, 'Could not change it'), 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 22, padding: 16, border: '1px solid var(--dark3)', borderRadius: 12, background: 'var(--dark2)' }}>
      <div style={{ width: 280 }}><ClubSelect value={clubId} onChange={setClubId} /></div>
      <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', padding: '10px 0' }}>
        {club ? (club.is_private ? 'Private: hidden from outsiders' : 'Public') : 'Pick a club to see whether it\'s private'}
      </span>
      <button className="btn-g" disabled={!club || saving} onClick={flip} style={{ padding: '10px 16px', fontSize: 10, letterSpacing: 1.5 }}>
        {club?.is_private ? 'Make public' : 'Make private'}
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
