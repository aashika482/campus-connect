// New club requests, in three places:
//  - NewClubRequestPage (/clubs/new): a student proposes a club and follows their requests
//  - FacultyClubRequestsPage (/club-requests): the named faculty coordinator confirms or declines
//  - DswClubRequests (DSW Console tab): the DSW approves (creating the club) or rejects
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { clubsApi, clubRequestsApi, apiError } from '@/api/client'
import { useDebounced } from '@/hooks/useData'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { ALL_TAGS, splitTags } from '@/types'
import type { Club, ClubRequest, ClubRequestStatus } from '@/types'
import { Empty } from './AdminPeople'

const STATUS: Record<ClubRequestStatus, { label: string; color: string }> = {
  awaiting_coordinator: { label: 'Waiting for the faculty coordinator', color: '#EAB308' },
  awaiting_dsw:         { label: 'Waiting for the DSW',                 color: '#A855F7' },
  approved:             { label: 'Approved',                            color: '#22C55E' },
  declined:             { label: 'Declined by the coordinator',         color: '#EF4444' },
  rejected:             { label: 'Rejected by the DSW',                 color: '#EF4444' },
}
const mono: React.CSSProperties = { fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', lineHeight: 1.6 }

function Header({ kicker, title, intro }: { kicker: string; title: string; intro: string }) {
  return (
    <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 900, margin: '0 auto' }}>
        <div style={{ ...mono, fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>{kicker}</div>
        <h1 style={{ fontFamily: 'var(--head)', fontSize: 38, fontWeight: 800, letterSpacing: '-2px' }}>{title}<span style={{ color: 'var(--orange)' }}>.</span></h1>
        <p style={{ ...mono, marginTop: 8 }}>{intro}</p>
      </div>
    </div>
  )
}

// One request, as everyone involved sees it; `actions` adds the buttons for whoever decides next
function RequestCard({ r, actions }: { r: ClubRequest; actions?: React.ReactNode }) {
  const navigate = useNavigate()
  const field = (label: string, value: string | null) => value && (
    <div style={{ marginTop: 10 }}>
      <div style={{ ...mono, fontSize: 9.5, textTransform: 'uppercase', letterSpacing: 1.5 }}>{label}</div>
      <div style={{ fontFamily: 'var(--body)', fontSize: 13, color: 'var(--cream3)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{value}</div>
    </div>
  )
  return (
    <div style={{ padding: '18px 20px', border: '1px solid var(--dark3)', borderRadius: 12, background: 'var(--dark2)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 17, fontWeight: 700 }}>{r.name} <span style={mono}>({r.abbr})</span></div>
          <div style={mono}>Proposed by {r.requester_name} · {r.requester_email}{r.contact_phone && ` · ${r.contact_phone}`}</div>
        </div>
        <div style={{ ...mono, color: STATUS[r.status].color }}>{STATUS[r.status].label}</div>
      </div>
      {r.status === 'awaiting_coordinator' && !r.coordinator_signed_up && (
        <div style={{ ...mono, color: '#EAB308', marginTop: 6 }}>Waiting for {r.coordinator_email} to join the portal.</div>
      )}
      {field('About', r.description)}
      {field('Why it\'s needed', r.purpose)}
      {field('First semester plans', r.plans)}
      {field('Affiliation', r.affiliation)}
      <div style={{ ...mono, marginTop: 10 }}>
        Tags: {splitTags(r.tags).join(', ')} · Coordinator: {r.coordinator_email}<br />
        Founding team: {r.founding_emails.split(',').join(', ')}
      </div>
      {r.decision_note && <div style={{ ...mono, marginTop: 8, color: 'var(--cream3)' }}>Note: {r.decision_note}</div>}
      {r.club_id && (
        <button className="btn-g" onClick={() => navigate(`/clubs/${r.club_id}`)} style={{ marginTop: 12, padding: '8px 14px', fontSize: 10 }}>Open the club →</button>
      )}
      {actions && <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>{actions}</div>}
    </div>
  )
}

// ── Students: propose a club ─────────────────────────────
const EMPTY = { name: '', abbr: '', description: '', purpose: '', plans: '', affiliation: '', instagram: '', linkedin: '',
                coordinator_email: '', contact_phone: '', founders: ['', '', '', ''], tags: [] as string[] }

export function NewClubRequestPage() {
  const { user } = useAuthStore()
  const { toast } = useToastStore()
  const [mine, setMine] = useState<ClubRequest[] | null>(null)
  const [form, setForm] = useState(EMPTY)
  const [sending, setSending] = useState(false)
  const [similar, setSimilar] = useState<Club[]>([])
  const name = useDebounced(form.name.trim(), 400)

  const load = () => clubRequestsApi.mine().then(r => setMine(r.data)).catch(() => setMine([]))
  useEffect(() => { load() }, [])
  // Existing clubs with a similar name, so students join one instead of duplicating it
  useEffect(() => {
    if (name.length < 3) { setSimilar([]); return }
    clubsApi.list({ q: name, limit: 5 }).then(r => setSimilar(r.data.items)).catch(() => {})
  }, [name])

  const set = (k: keyof typeof EMPTY, v: any) => setForm(f => ({ ...f, [k]: v }))
  const toggleTag = (id: string) => set('tags', form.tags.includes(id) ? form.tags.filter(t => t !== id) : [...form.tags, id].slice(0, 4))

  const submit = async () => {
    setSending(true)
    try {
      const optional = (v: string) => v.trim() || null
      await clubRequestsApi.submit({
        name: form.name, abbr: form.abbr, description: form.description, purpose: form.purpose, plans: form.plans,
        tags: form.tags, coordinator_email: form.coordinator_email.trim(), contact_phone: form.contact_phone,
        affiliation: optional(form.affiliation), instagram: optional(form.instagram), linkedin: optional(form.linkedin),
        founding_emails: form.founders.map(e => e.trim()).filter(Boolean),
      })
      toast('Sent. Your faculty coordinator confirms it next.', 'success')
      setForm(EMPTY)
      load()
    } catch (err) {
      toast(apiError(err, 'Could not send the request'), 'error')
    } finally {
      setSending(false)
    }
  }

  if (user?.account_type !== 'student') return <Empty text="Only students can propose a new club" />
  const open = mine?.some(r => r.status === 'awaiting_coordinator' || r.status === 'awaiting_dsw')
  const label = (text: string, hint?: string) => (
    <div style={{ ...mono, fontSize: 10, textTransform: 'uppercase', letterSpacing: 1.5, margin: '18px 0 6px' }}>
      {text}{hint && <span style={{ textTransform: 'none', letterSpacing: 0 }}> · {hint}</span>}
    </div>
  )
  const ready = form.name.trim() && form.abbr.trim() && form.description.trim() && form.purpose.trim() && form.plans.trim()
    && form.tags.length > 0 && form.coordinator_email.trim() && form.contact_phone.trim()
    && form.founders.filter(e => e.trim()).length >= 2

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <Header kicker="Campus Clubs" title="Propose a new club"
        intro="Your faculty coordinator confirms it first, then the DSW approves. Once approved you own the club and your founding team become its editors." />
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 40px 64px' }}>
        {mine && mine.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 32 }}>
            {mine.map(r => <RequestCard key={r.id} r={r} />)}
          </div>
        )}

        {open ? <div style={mono}>You can propose another club once this one is decided.</div> : (
          <div>
            {label('Club name')}
            <input className="inp" value={form.name} maxLength={150} onChange={e => set('name', e.target.value)} placeholder="e.g. Robotics Society" />
            {similar.length > 0 && (
              <div style={{ ...mono, marginTop: 6, color: '#EAB308' }}>
                Similar clubs already exist: {similar.map(c => c.name).join(', ')}. Say how yours differs below.
              </div>
            )}
            {label('Short name', 'shown on badges')}
            <input className="inp" value={form.abbr} maxLength={20} onChange={e => set('abbr', e.target.value)} placeholder="e.g. RoboSoc" style={{ maxWidth: 240 }} />
            {label('About the club')}
            <textarea className="inp" rows={3} value={form.description} maxLength={3000} onChange={e => set('description', e.target.value)} />
            {label('Tags', 'up to 4')}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {ALL_TAGS.map(t => (
                <button key={t.id} onClick={() => toggleTag(t.id)}
                  style={{ padding: '5px 12px', borderRadius: 16, fontSize: 11, fontFamily: 'var(--mono)',
                           border: `1px solid ${form.tags.includes(t.id) ? 'var(--orange)' : 'var(--dark4)'}`,
                           color: form.tags.includes(t.id) ? 'var(--orange)' : 'var(--gray2)' }}>{t.label}</button>
              ))}
            </div>
            {label('Why it\'s needed', 'and how it differs from existing clubs')}
            <textarea className="inp" rows={3} value={form.purpose} maxLength={3000} onChange={e => set('purpose', e.target.value)} />
            {label('First semester plans')}
            <textarea className="inp" rows={3} value={form.plans} maxLength={3000} onChange={e => set('plans', e.target.value)} />
            {label('Affiliation', 'optional: a chapter of IEEE, ACM, Rotaract, SAE…')}
            <input className="inp" value={form.affiliation} maxLength={120} onChange={e => set('affiliation', e.target.value)} />
            {label('Faculty coordinator\'s email', 'they confirm first; if they haven\'t joined the portal yet, the request waits for them')}
            <input className="inp" value={form.coordinator_email} onChange={e => set('coordinator_email', e.target.value)} placeholder="name@jaipur.manipal.edu" />
            {label('Founding team', '2 to 4 other students\' college emails; they become editors')}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 8 }}>
              {form.founders.map((v, i) => (
                <input key={i} className="inp" value={v} placeholder={i < 2 ? 'name@muj.manipal.edu' : 'optional'}
                  onChange={e => set('founders', form.founders.map((x, j) => (j === i ? e.target.value : x)))} />
              ))}
            </div>
            {label('Your phone', 'only the DSW sees it')}
            <input className="inp" value={form.contact_phone} maxLength={20} onChange={e => set('contact_phone', e.target.value)} style={{ maxWidth: 240 }} />
            {label('Instagram / LinkedIn', 'optional')}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <input className="inp" value={form.instagram} onChange={e => set('instagram', e.target.value)} placeholder="https://instagram.com/…" style={{ flex: 1, minWidth: 240 }} />
              <input className="inp" value={form.linkedin} onChange={e => set('linkedin', e.target.value)} placeholder="https://linkedin.com/…" style={{ flex: 1, minWidth: 240 }} />
            </div>
            <button className="btn-p" disabled={sending || !ready} onClick={submit} style={{ marginTop: 24 }}>
              {sending ? 'Sending…' : 'Send to the faculty coordinator →'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Shared by the coordinator's and the DSW's lists: decide with an optional note
function useDecide(onDone: () => void) {
  const { toast } = useToastStore()
  const [busy, setBusy] = useState<number | null>(null)
  const decide = async (r: ClubRequest, action: 'confirm' | 'decline' | 'approve' | 'reject') => {
    const negative = action === 'decline' || action === 'reject'
    const note = negative ? window.prompt(`Why? (optional, ${r.requester_name} will see it)`) : null
    if (negative && note === null) return   // cancelled
    setBusy(r.id)
    try {
      const res = await clubRequestsApi.decide(r.id, action, note ?? undefined)
      const skipped: string[] = res.data.skipped ?? []
      toast({ confirm: 'Confirmed. It goes to the DSW now.', decline: 'Declined', reject: 'Rejected',
              approve: `${r.name} is created` }[action], 'success')
      if (skipped.length) window.alert(`Not added as editors:\n\n${skipped.join('\n')}\n\nThe owner can propose them later.`)
      onDone()
    } catch (err) {
      toast(apiError(err, 'Could not update the request'), 'error')
    } finally {
      setBusy(null)
    }
  }
  return { busy, decide }
}

// ── Faculty: requests naming them as coordinator ─────────
export function FacultyClubRequestsPage() {
  const { user } = useAuthStore()
  const [rows, setRows] = useState<ClubRequest[] | null>(null)
  const load = () => clubRequestsApi.forMe().then(r => setRows(r.data)).catch(() => setRows([]))
  useEffect(() => { load() }, [])
  const { busy, decide } = useDecide(load)

  if (user?.account_type !== 'faculty') return <Empty text="Faculty only" />
  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <Header kicker="Faculty" title="Club Requests"
        intro="Students who named you faculty coordinator of a new club. Confirm to send it to the DSW." />
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 40px 64px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {rows === null ? <Empty text="Loading…" /> : rows.length === 0 ? <Empty text="No one has named you coordinator of a new club." /> :
          rows.map(r => (
            <RequestCard key={r.id} r={r} actions={r.status === 'awaiting_coordinator' && <>
              <button className="btn-p" disabled={busy === r.id} onClick={() => decide(r, 'confirm')} style={{ padding: '8px 16px', fontSize: 10 }}>Confirm</button>
              <button className="btn-g" disabled={busy === r.id} onClick={() => decide(r, 'decline')} style={{ padding: '8px 16px', fontSize: 10 }}>Decline</button>
            </>} />
          ))}
      </div>
    </div>
  )
}

// ── DSW: confirmed requests to approve or reject ─────────
export function DswClubRequests() {
  const [rows, setRows] = useState<ClubRequest[] | null>(null)
  const load = () => clubRequestsApi.queue().then(r => setRows(r.data.items)).catch(() => setRows([]))
  useEffect(() => { load() }, [])
  const { busy, decide } = useDecide(load)

  if (rows === null) return <Empty text="Loading…" />
  if (rows.length === 0) return <Empty text="No new clubs waiting for approval." />
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 900 }}>
      {rows.map(r => (
        <RequestCard key={r.id} r={r} actions={<>
          <button className="btn-p" disabled={busy === r.id} onClick={() => decide(r, 'approve')} style={{ padding: '8px 16px', fontSize: 10 }}>Approve and create the club</button>
          <button className="btn-g" disabled={busy === r.id} onClick={() => decide(r, 'reject')} style={{ padding: '8px 16px', fontSize: 10 }}>Reject</button>
        </>} />
      ))}
    </div>
  )
}
