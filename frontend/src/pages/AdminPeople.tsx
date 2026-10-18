// People lists, all built on PeopleTable (search + newest/oldest sort + CSV download):
//  - Club Dashboard tabs: members, per-event registrations, the club's team
//  - the DSW and Platform consoles (GovernancePages.tsx) reuse PeopleTable and the role columns
import { useState, useEffect } from 'react'
import { clubsApi, eventsApi, apiError } from '@/api/client'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { activeRoles, ROLE_LABELS } from '@/types'
import type { Event, Person, Registrant, ClubMember, ClubRoleDetail } from '@/types'

const PLACEHOLDER_PHONE = '0000000000'

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' })

// ── Generic table ─────────────────────────────────────────
export interface Column<T> {
  label: string
  cell: (row: T) => React.ReactNode
  csv: (row: T) => string
  width?: string
}

export function PeopleTable<T extends Person>({ rows, columns, dateOf, dateLabel, fileName, emptyText, loading, error, rowKey = r => r.user_id, academic = true }: {
  rows: T[]
  academic?: boolean                  // show Reg No. + Course (lists about clubs' teams don't need them)
  rowKey?: (row: T) => number         // defaults to user_id (lists where a person can appear twice pass their own)
  columns: Column<T>[]
  dateOf: (row: T) => string        // the date the sort arrows order by
  dateLabel: string                 // e.g. "Registered on"
  fileName: string                  // CSV name, without extension
  emptyText: string
  loading: boolean
  error: string | null
}) {
  const [query, setQuery] = useState('')
  const [newestFirst, setNewestFirst] = useState(true)

  const q = query.trim().toLowerCase()
  const visible = rows
    .filter(r => !q || [r.name, r.email, r.phone, r.reg_no, r.course].some(v => v?.toLowerCase().includes(q)))
    .sort((a, b) => (newestFirst ? -1 : 1) * (new Date(dateOf(a)).getTime() - new Date(dateOf(b)).getTime()))

  const downloadCsv = () => {
    const header = ['Name', 'Email', 'Phone', ...(academic ? ['Reg No.', 'Course'] : []), ...columns.map(c => c.label), dateLabel]
    // ="..." makes Excel keep digits as text (no dropped leading zeros / 9.88E+09)
    const asText = (v: string | null) => (v && /^\d+$/.test(v) ? `="${v}"` : safe(v ?? ''))
    // A cell starting with = + - @ would run as a formula in Excel; a leading ' stops that
    const safe = (v: string) => (/^[=+\-@]/.test(v) ? `'${v}` : v)
    const lines = visible.map(r => [
      safe(r.name), safe(r.email),
      r.phone === PLACEHOLDER_PHONE ? '' : asText(r.phone), ...(academic ? [asText(r.reg_no), safe(r.course ?? '')] : []),
      ...columns.map(c => safe(c.csv(r))), fmtDate(dateOf(r)),
    ])
    const quote = (v: string) => (v.startsWith('="') ? v : /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v)
    const csv = [header, ...lines].map(l => l.map(quote).join(',')).join('\r\n')
    // BOM so Excel reads UTF-8 names (e.g. accents) correctly
    const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `${fileName}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const th: React.CSSProperties = { fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.5, textAlign: 'left', padding: '11px 14px', fontWeight: 500, whiteSpace: 'nowrap', borderBottom: '1px solid var(--dark3)' }
  const td: React.CSSProperties = { fontFamily: 'var(--mono)', fontSize: 11.5, color: 'var(--cream3)', padding: '12px 14px', borderBottom: '1px solid var(--dark3)', verticalAlign: 'top' }

  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 260px', maxWidth: 380 }}>
          <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="var(--gray2)" strokeWidth="2.5" strokeLinecap="round"
            style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }}>
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input className="inp" value={query} onChange={e => setQuery(e.target.value)}
            placeholder="Search name, email, phone, reg no…" style={{ paddingLeft: 34, fontSize: 12 }} />
        </div>
        <button onClick={() => setNewestFirst(v => !v)} className="btn-g" title="Change sort order"
          style={{ padding: '9px 14px', fontSize: 10, letterSpacing: 1.5 }}>
          {newestFirst ? '↓ Newest first' : '↑ Oldest first'}
        </button>
        <div style={{ flex: 1 }} />
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>
          {q ? `${visible.length} of ${rows.length}` : `${rows.length} total`}
        </span>
        <button onClick={downloadCsv} className="btn-p" disabled={visible.length === 0}
          style={{ padding: '9px 16px', fontSize: 10, letterSpacing: 1.5 }}>
          ⤓ Download CSV
        </button>
      </div>

      {/* Table */}
      <div style={{ border: '1px solid var(--dark3)', borderRadius: 12, overflowX: 'auto', background: 'var(--dark2)' }}>
        {loading ? (
          <Empty text="Loading…" />
        ) : error ? (
          <Empty text={error} />
        ) : visible.length === 0 ? (
          <Empty text={rows.length === 0 ? emptyText : 'No matches for your search'} />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 820 }}>
            <thead>
              <tr>
                <th style={th}>Name</th>
                <th style={th}>Email</th>
                <th style={th}>Phone</th>
                {academic && <th style={th}>Reg No.</th>}
                {academic && <th style={th}>Course</th>}
                {columns.map(c => <th key={c.label} style={{ ...th, width: c.width }}>{c.label}</th>)}
                <th style={th}>
                  <button onClick={() => setNewestFirst(v => !v)} style={{ ...th, padding: 0, border: 'none', color: 'var(--orange)', cursor: 'pointer' }}>
                    {dateLabel} {newestFirst ? '↓' : '↑'}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map(r => (
                <tr key={rowKey(r)}>
                  <td style={{ ...td, color: 'var(--cream)', fontFamily: 'var(--head)', fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap' }}>
                    {r.name}
                  </td>
                  <td style={td}><a href={`mailto:${r.email}`} style={{ color: 'inherit' }}>{r.email}</a></td>
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>
                    {!r.phone ? '—' : r.phone === PLACEHOLDER_PHONE
                      ? <span title="Placeholder — this user hasn't added a phone number" style={{ color: 'var(--gray2)' }}>not set</span>
                      : r.phone}
                  </td>
                  {academic && <td style={td}>{r.reg_no || '—'}</td>}
                  {academic && <td style={td}>{r.course || '—'}</td>}
                  {columns.map(c => <td key={c.label} style={td}>{c.cell(r)}</td>)}
                  <td style={{ ...td, whiteSpace: 'nowrap' }}>{fmtDate(dateOf(r))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export function Empty({ text }: { text: string }) {
  return (
    <div style={{ padding: '48px 20px', textAlign: 'center', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>{text}</div>
  )
}


const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

// ── Members tab ───────────────────────────────────────────
export function MembersTab({ clubId, clubName, onOpenEvent }: {
  clubId: number
  clubName: string
  onOpenEvent: (eventId: number) => void   // show that event's registrations
}) {
  const [rows, setRows] = useState<ClubMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    clubsApi.members(clubId)
      .then(r => setRows(r.data))
      .catch(err => setError(apiError(err, 'Failed to load members')))
      .finally(() => setLoading(false))
  }, [clubId])

  return (
    <PeopleTable
      rows={rows}
      loading={loading}
      error={error}
      dateOf={r => r.joined_at}
      dateLabel="Member since"
      fileName={`${slug(clubName)}-members`}
      emptyText="No members yet. Students join from your club's page."
      columns={[{
        label: 'Registered for',
        width: '24%',
        csv: r => r.registered_events.map(e => e.title).join('; '),
        cell: r => r.registered_events.length === 0 ? '—' : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {r.registered_events.map(e => (
              <button key={e.id} onClick={() => onOpenEvent(e.id)}
                title="See this event's registrations"
                style={{ padding: '2px 8px', fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.3)', background: 'rgba(212,86,26,0.06)', borderRadius: 4, cursor: 'pointer' }}>
                {e.title}
              </button>
            ))}
          </div>
        ),
      }]}
    />
  )
}

// ── Registrations tab ─────────────────────────────────────
export function RegistrationsTab({ events, eventId, onPickEvent }: {
  events: Event[]                         // the admin's own events
  eventId: number | null
  onPickEvent: (id: number) => void
}) {
  const [rows, setRows] = useState<Registrant[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const event = events.find(e => e.id === eventId)

  useEffect(() => {
    if (!eventId) return
    setLoading(true)
    setError(null)
    eventsApi.registrations(eventId)
      .then(r => setRows(r.data))
      .catch(err => { setRows([]); setError(apiError(err, 'Failed to load registrations')) })
      .finally(() => setLoading(false))
  }, [eventId])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18, flexWrap: 'wrap' }}>
        <label style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.5 }}>Event</label>
        <select className="inp" value={eventId ?? ''} onChange={e => onPickEvent(Number(e.target.value))}
          style={{ width: 'auto', minWidth: 280, maxWidth: '100%', fontSize: 12, cursor: 'pointer' }}>
          <option value="" disabled>Select one of your events</option>
          {events.map(ev => <option key={ev.id} value={ev.id}>{ev.date_display} · {ev.title}</option>)}
        </select>
      </div>

      {!event ? (
        <div style={{ border: '1.5px dashed var(--dark4)', borderRadius: 12 }}>
          <Empty text={events.length === 0 ? 'No events yet.' : 'Pick an event to see who registered.'} />
        </div>
      ) : (
        <PeopleTable
          rows={rows}
          loading={loading}
          error={error}
          dateOf={r => r.registered_at}
          dateLabel="Registered on"
          fileName={`${slug(event.title)}-registrations`}
          emptyText="No registrations yet."
          columns={[]}
        />
      )}
    </div>
  )
}

// ── Club role columns (Team tab, DSW console) ─────────────
const STATUS_COLORS = { pending: '#EAB308', active: '#22C55E', rejected: '#EF4444', ended: 'var(--gray2)' }

export const roleColumns = {
  club: { label: 'Club', csv: r => r.club_name, cell: r => <span style={{ color: 'var(--cream)' }}>{r.club_name}</span> } as Column<ClubRoleDetail>,
  role: {
    label: 'Role',
    csv: r => [ROLE_LABELS[r.role], r.title].filter(Boolean).join(' · '),
    cell: r => <span>{ROLE_LABELS[r.role]}{r.title && <span style={{ color: 'var(--gray2)' }}> · {r.title}</span>}</span>,
  } as Column<ClubRoleDetail>,
  status: {
    label: 'Status',
    csv: r => r.status,
    cell: r => <span style={{ color: STATUS_COLORS[r.status], textTransform: 'capitalize' }}>{r.status === 'pending' ? 'Waiting for DSW' : r.status}</span>,
  } as Column<ClubRoleDetail>,
  proposedBy: { label: 'Proposed by', csv: r => r.proposed_by_name ?? '', cell: r => r.proposed_by_name || '—' } as Column<ClubRoleDetail>,
}

// ── Team tab ──────────────────────────────────────────────
export function TeamTab({ clubId }: { clubId: number }) {
  const { user } = useAuthStore()
  const { toast } = useToastStore()
  const [rows, setRows] = useState<ClubRoleDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [title, setTitle] = useState('')
  const [sending, setSending] = useState(false)
  // Editors are proposed by the club's owner or editors; the DSW approves
  const canPropose = activeRoles(user, 'owner', 'editor').some(r => r.club_id === clubId)

  const load = () => {
    setLoading(true)
    clubsApi.team(clubId)
      .then(r => setRows(r.data.items))
      .catch(err => setError(apiError(err, 'Failed to load the team')))
      .finally(() => setLoading(false))
  }
  useEffect(load, [clubId])

  const propose = async () => {
    setSending(true)
    try {
      await clubsApi.proposeEditor(clubId, email.trim(), title.trim())
      setEmail(''); setTitle('')
      toast('Proposed. The DSW will review it.', 'success')
      load()
    } catch (err) {
      toast(apiError(err, 'Could not propose this person'), 'error')
    } finally {
      setSending(false)
    }
  }

  return (
    <div>
      {canPropose && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 18 }}>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.5 }}>Propose an editor</span>
          <input className="inp" value={email} onChange={e => setEmail(e.target.value)} placeholder="Their college email" style={{ width: 260, fontSize: 12 }} />
          <input className="inp" value={title} onChange={e => setTitle(e.target.value)} placeholder="Title (optional)" style={{ width: 170, fontSize: 12 }} />
          <button className="btn-p" disabled={sending || !email.trim()} onClick={propose} style={{ padding: '9px 16px', fontSize: 10, letterSpacing: 1.5 }}>
            {sending ? 'Sending…' : 'Send to DSW'}
          </button>
        </div>
      )}
      <PeopleTable
        rows={rows}
        rowKey={r => r.id}
        academic={false}
        loading={loading}
        error={error}
        dateOf={r => r.created_at}
        dateLabel="Since"
        fileName={`club-${clubId}-team`}
        emptyText="No team yet."
        columns={[roleColumns.role, roleColumns.status, roleColumns.proposedBy]}
      />
    </div>
  )
}
