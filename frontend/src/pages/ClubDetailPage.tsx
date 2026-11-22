import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { clubsApi, announcementsApi, apiError } from '@/api/client'
import { useUserClubs, useEventsWhere } from '@/hooks/useData'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { splitTags, TAG_COLORS, getEventColor, canManage, onWorkingTeam, activeRoles, getTimeAgo, ROLE_LABELS, REACTIONS } from '@/types'
import type { Club, Event, MyApplication, Roster, Announcement, Reaction } from '@/types'

// ── Icons ─────────────────────────────────────────────────
const lp = { fill: 'none', stroke: 'currentColor', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
const IgIco  = () => <svg width={14} height={14} viewBox="0 0 24 24" {...lp} strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="0.5" fill="currentColor" stroke="none"/></svg>
const LiIco  = () => <svg width={14} height={14} viewBox="0 0 24 24" {...lp} strokeWidth="2"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
const ArrIco = () => <svg width={13} height={13} viewBox="0 0 24 24" {...lp} strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>

export function ClubDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToastStore()
  const { joinedClubs, canJoin, join } = useUserClubs()
  const { user } = useAuthStore()

  const [club, setClub] = useState<Club | null>(null)
  const [loading, setLoading] = useState(true)

  const clubId = Number(id)
  // A single club's events: small enough to load in full
  const { events, loading: eventsLoading } = useEventsWhere(id ? { club_id: clubId } : null)
  const isMember = joinedClubs.includes(clubId)
  const membership = activeRoles(user, 'member').find(r => r.club_id === clubId)
  const isWorking = activeRoles(user, 'working_member').some(r => r.club_id === clubId)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    clubsApi.get(clubId)
      .then(r => setClub(r.data))
      .catch(() => { toast('Club not found', 'error'); navigate('/clubs') })
      .finally(() => setLoading(false))
  }, [id])

  if (loading || !club) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', letterSpacing: 3, textTransform: 'uppercase' }}>Loading…</div>
      </div>
    )
  }

  const tags = splitTags(club.tags)

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>

      {/* ── Header ─────────────────────────────────────────── */}
      <div className="pg-hdr" style={{ padding: '36px 40px 40px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1100, margin: '0 auto' }}>

          {/* Back */}
          <button
            onClick={() => navigate('/clubs')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 28, transition: 'color 0.15s', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            onMouseOver={e => (e.currentTarget.style.color = 'var(--cream)')}
            onMouseOut={e => (e.currentTarget.style.color = 'var(--gray2)')}
          >
            <ArrIco /> Back to Clubs
          </button>

          {/* Main header row */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 28, flexWrap: 'wrap' }}>

            {/* Club badge */}
            <div style={{
              width: 72, height: 72, flexShrink: 0,
              background: `${club.color}14`,
              border: `2px solid ${club.color}44`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 700, color: club.color, letterSpacing: 1 }}>
                {club.abbr.slice(0, 5)}
              </span>
            </div>

            {/* Title + meta */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Campus Club</div>
              <h1 style={{ fontFamily: 'var(--syne)', fontSize: 40, fontWeight: 800, letterSpacing: '-1.5px', lineHeight: 1.05, marginBottom: 14 }}>
                {club.name}<span style={{ color: 'var(--orange)' }}>.</span>
              </h1>
              <p style={{ fontFamily: 'var(--body)', fontSize: 14, color: 'var(--cream3)', lineHeight: 1.7, maxWidth: 620, marginBottom: 18 }}>
                {club.description}
              </p>

              {/* Tags */}
              {tags.length > 0 && (
                <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginBottom: 20 }}>
                  {tags.map(t => (
                    <span key={t} style={{
                      padding: '4px 12px', borderRadius: 20, fontSize: 10.5,
                      fontFamily: 'var(--mono)', letterSpacing: 0.5,
                      border: `1.5px solid ${(TAG_COLORS[t] ?? 'var(--orange)') + '44'}`,
                      background: `${TAG_COLORS[t] ?? 'var(--orange)'}0f`,
                      color: TAG_COLORS[t] ?? 'var(--orange)',
                      textTransform: 'capitalize',
                    }}>
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Stats + actions row */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
                {/* Member count */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 800, color: club.color }}>{club.member_count}</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.5 }}>Members</span>
                </div>

                {/* Status badge */}
                {club.is_open
                  ? <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '3px 10px', background: 'rgba(16,185,129,0.06)', letterSpacing: 0.5 }}>● Open</span>
                  : <span style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--gray2)', border: '1px solid var(--dark4)', padding: '3px 10px', letterSpacing: 0.5 }}>Closed</span>
                }

                {/* Divider */}
                <div style={{ width: 1, height: 20, background: 'var(--dark4)' }} />

                {/* Join button (students; there's no leaving from the app) */}
                {(isMember || canJoin) && <button
                  onClick={() => join(club, n => setClub(c => (c ? { ...c, member_count: n } : c)))}
                  disabled={isMember}
                  style={{
                    padding: '9px 22px',
                    fontFamily: 'var(--head)', fontSize: 11, fontWeight: 700,
                    textTransform: 'uppercase', letterSpacing: 2,
                    border: `1.5px solid ${isMember ? club.color : 'var(--dark4)'}`,
                    background: isMember ? `${club.color}18` : 'rgba(242,234,220,0.04)',
                    color: isMember ? club.color : 'var(--cream)',
                    borderRadius: 8, cursor: isMember ? 'default' : 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {isMember ? (isWorking ? '✓ Working member' : '✓ Member') : '+ Join Club'}
                </button>}

                {/* Social links */}
                {club.instagram && (
                  <a href={club.instagram} target="_blank" rel="noopener noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textDecoration: 'none', letterSpacing: 0.5, transition: 'color 0.15s' }}
                    onMouseOver={e => (e.currentTarget.style.color = 'var(--cream)')}
                    onMouseOut={e => (e.currentTarget.style.color = 'var(--gray2)')}>
                    <IgIco /> Instagram
                  </a>
                )}
                {club.linkedin && (
                  <a href={club.linkedin} target="_blank" rel="noopener noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textDecoration: 'none', letterSpacing: 0.5, transition: 'color 0.15s' }}
                    onMouseOver={e => (e.currentTarget.style.color = 'var(--cream)')}
                    onMouseOut={e => (e.currentTarget.style.color = 'var(--gray2)')}>
                    <LiIco /> LinkedIn
                  </a>
                )}
              </div>

              {/* Yearly fees (collected by the club until the portal takes payments) */}
              <div style={{ marginTop: 14, fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--gray2)', lineHeight: 1.7 }}>
                {membership?.expires_on
                  ? <>Your membership runs until {fmtDay(membership.expires_on)}.</>
                  : <>Membership ₹{club.fee_member} a year · working team ₹{club.fee_working} a year, paid to the club.</>}
              </div>

              {isMember && !isWorking && user?.account_type === 'student' && (
                <WorkingTeamApplication club={club} />
              )}

              {canManage(user, clubId)
                ? <button className="btn-g" onClick={() => navigate(`/admin?club=${clubId}`)} style={{ marginTop: 20, padding: '9px 18px', fontSize: 10, letterSpacing: 1.5 }}>Manage club →</button>
                : user?.account_type === 'student' && <OwnershipRequest clubId={clubId} clubName={club.name} />}
            </div>
          </div>
        </div>
      </div>

      {/* ── Events Section ──────────────────────────────────── */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 40px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 3, marginBottom: 6 }}>Events</div>
            <div style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>
              Events by {club.name}
            </div>
          </div>
          {!eventsLoading && (
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>
              {events.length} {events.length === 1 ? 'event' : 'events'}
            </span>
          )}
        </div>

        {eventsLoading ? (
          <div style={{ textAlign: 'center', color: 'var(--gray2)', fontFamily: 'var(--mono)', fontSize: 11, padding: '48px 0' }}>Loading…</div>
        ) : events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '56px 0', border: '1.5px dashed var(--dark4)', borderRadius: 12 }}>
            <div style={{ fontSize: 28, marginBottom: 12 }}>◇</div>
            <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 8 }}>No events yet</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>
              {club.name} hasn't posted any events
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 18 }}>
            {events.map((ev, i) => (
              <EventCard key={ev.id} event={ev} delay={i * 30} onClick={() => navigate(`/events/${ev.id}`)} />
            ))}
          </div>
        )}
      </div>

      {/* ── Working team: announcements ─────────────────────── */}
      {onWorkingTeam(user, clubId) && (
        <div id="announcements" style={{ maxWidth: 1100, margin: '0 auto', padding: '0 40px 40px' }}>
          <SectionTitle kicker="Working team" title="Announcements" />
          <ClubAnnouncements clubId={clubId} canPost={canManage(user, clubId)} />
        </div>
      )}

      {/* ── Members ─────────────────────────────────────────── */}
      {user && (
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 40px 64px' }}>
          <SectionTitle kicker="This academic year" title="Members" />
          <ClubRoster clubId={clubId} />
        </div>
      )}
    </div>
  )
}

const fmtDay = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

function SectionTitle({ kicker, title }: { kicker: string; title: string }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 3, marginBottom: 6 }}>{kicker}</div>
      <div style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>{title}</div>
    </div>
  )
}

// ── Applying to (or renewing a place on) the working team ─
const APPLICATION_TEXT = {
  applied: 'Your working-team application is in. The team will reach out for an interview.',
  shortlisted: "You're shortlisted for the working team. Expect an interview call.",
  recommended: 'The team recommended you. Waiting for the faculty coordinator.',
  accepted: '',
  declined: "Your last working-team application wasn't taken. You're still a member.",
}

function WorkingTeamApplication({ club }: { club: Club }) {
  const { refreshUser } = useAuthStore()
  const { toast } = useToastStore()
  const [mine, setMine] = useState<MyApplication | null>(null)
  const [sending, setSending] = useState(false)

  useEffect(() => { clubsApi.myApplication(club.id).then(r => setMine(r.data)).catch(() => {}) }, [club.id])

  const apply = async () => {
    setSending(true)
    try {
      const r = await clubsApi.apply(club.id)
      setMine(r.data)
      await refreshUser()
      toast('Application sent to the club', 'success')
    } catch (err) {
      toast(apiError(err, 'Could not apply'), 'error')
    } finally {
      setSending(false)
    }
  }

  if (!mine) return null
  const note: React.CSSProperties = { marginTop: 10, fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--gray2)', lineHeight: 1.6 }
  if (mine.can_apply) {
    const renewal = mine.is_renewal
    return (
      <div style={note}>
        {mine.status === 'declined' && APPLICATION_TEXT.declined + ' '}
        <button onClick={apply} disabled={sending}
          style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--orange)', textDecoration: 'underline', textUnderlineOffset: 3 }}>
          {sending ? 'Sending…' : renewal ? 'Renew your place on the working team' : `${club.name} is recruiting: apply to the working team`}
        </button>
        {' '}(₹{club.fee_working - club.fee_member} more once accepted)
      </div>
    )
  }
  // An open application: say where it stands. Otherwise stay quiet unless the club is recruiting.
  if (mine.status && mine.status !== 'accepted' && (mine.status !== 'declined' || club.recruiting)) {
    return <div style={note}>{APPLICATION_TEXT[mine.status]}{mine.status === 'declined' && mine.reason ? ` ${mine.reason}.` : ''}</div>
  }
  return club.recruiting && mine.reason ? <div style={note}>{club.name} is recruiting, but: {mine.reason}.</div> : null
}

// ── Roster: names for everyone, details for the working team ─
function ClubRoster({ clubId }: { clubId: number }) {
  const [roster, setRoster] = useState<Roster | null>(null)
  const [query, setQuery] = useState('')
  useEffect(() => { clubsApi.roster(clubId).then(r => setRoster(r.data)).catch(() => setRoster({ detailed: false, items: [] })) }, [clubId])

  if (!roster) return <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>Loading…</div>
  if (roster.items.length === 0) return <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>No members this year yet.</div>

  const q = query.trim().toLowerCase()
  const people = roster.items.filter(p => !q || [p.name, p.course, p.interests].some(v => v?.toLowerCase().includes(q)))
  // Team first, then working members, then everyone else
  const rank = (roles: string[]) => roles.includes('owner') ? 0 : roles.includes('faculty_coordinator') ? 1
    : roles.includes('editor') ? 2 : roles.includes('working_member') ? 3 : 4
  if (roster.detailed) people.sort((a, b) => rank(a.roles) - rank(b.roles) || a.name.localeCompare(b.name))

  return (
    <div>
      <input className="inp" value={query} onChange={e => setQuery(e.target.value)} placeholder={roster.detailed ? 'Search name, course, interests…' : 'Search names…'}
        style={{ maxWidth: 320, fontSize: 12, marginBottom: 14 }} />
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(auto-fill, minmax(${roster.detailed ? 240 : 180}px, 1fr))`, gap: 10 }}>
        {people.map(p => {
          const role = roster.detailed && p.roles.find(r => r !== 'member')
          return (
            <div key={p.user_id} style={{ padding: '12px 14px', border: '1px solid var(--dark3)', borderRadius: 10, background: 'var(--dark2)' }}>
              <div style={{ fontFamily: 'var(--head)', fontSize: 13.5, fontWeight: 600 }}>{p.name}</div>
              {roster.detailed && (
                <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--gray2)', marginTop: 4, lineHeight: 1.6 }}>
                  <div style={{ color: role ? 'var(--orange)' : 'var(--gray2)' }}>{p.title || (role ? ROLE_LABELS[role] : 'Member')}</div>
                  {p.course && <div>{p.course}</div>}
                  {p.interests && <div>{splitTags(p.interests).join(' · ')}</div>}
                </div>
              )}
            </div>
          )
        })}
      </div>
      {!roster.detailed && (
        <div style={{ marginTop: 12, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }}>The working team sees more about each member.</div>
      )}
    </div>
  )
}

// ── Announcements: the team posts; the working team reacts and comments ─
function ClubAnnouncements({ clubId, canPost }: { clubId: number; canPost: boolean }) {
  const { user } = useAuthStore()
  const { toast } = useToastStore()
  const [items, setItems] = useState<Announcement[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [draft, setDraft] = useState('')
  const [posting, setPosting] = useState(false)
  const PAGE = 10

  const load = (before?: number) => announcementsApi.list(clubId, { before_id: before, limit: PAGE })
    .then(r => { setItems(p => (before ? [...p, ...r.data.items] : r.data.items)); setTotal(r.data.total) })
    .catch(err => toast(apiError(err, 'Could not load announcements'), 'error'))
    .finally(() => setLoading(false))
  useEffect(() => { setLoading(true); load() }, [clubId])

  const post = async () => {
    setPosting(true)
    try {
      await announcementsApi.post(clubId, draft.trim())
      setDraft('')
      await load()
      toast('Posted to the working team', 'success')
    } catch (err) {
      toast(apiError(err, 'Could not post'), 'error')
    } finally {
      setPosting(false)
    }
  }
  const patch = (id: number, fn: (a: Announcement) => Announcement) => setItems(p => p.map(a => (a.id === id ? fn(a) : a)))
  const remove = async (a: Announcement) => {
    try {
      await announcementsApi.delete(clubId, a.id)
      setItems(p => p.filter(x => x.id !== a.id)); setTotal(t => t - 1)
    } catch (err) { toast(apiError(err, 'Could not delete'), 'error') }
  }

  return (
    <div style={{ maxWidth: 720 }}>
      {canPost && (
        <div style={{ marginBottom: 20 }}>
          <textarea className="inp" value={draft} onChange={e => setDraft(e.target.value)} rows={3} maxLength={3000}
            placeholder="Share an update with the working team…" style={{ fontSize: 13, resize: 'vertical' }} />
          <button className="btn-p" disabled={posting || !draft.trim()} onClick={post} style={{ marginTop: 8, padding: '9px 18px', fontSize: 10, letterSpacing: 1.5 }}>
            {posting ? 'Posting…' : 'Post announcement'}
          </button>
        </div>
      )}
      {loading ? (
        <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>Loading…</div>
      ) : items.length === 0 ? (
        <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>No announcements yet.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {items.map(a => (
            <AnnouncementCard key={a.id} clubId={clubId} a={a} canModerate={canPost} myId={user?.id}
              onChange={fn => patch(a.id, fn)} onDelete={() => remove(a)} />
          ))}
          {items.length < total && (
            <button className="btn-g" onClick={() => load(items[items.length - 1].id)} style={{ alignSelf: 'center', padding: '9px 22px', fontSize: 10 }}>Load older</button>
          )}
        </div>
      )}
    </div>
  )
}

function AnnouncementCard({ clubId, a, canModerate, myId, onChange, onDelete }: {
  clubId: number
  a: Announcement
  canModerate: boolean
  myId?: number
  onChange: (fn: (a: Announcement) => Announcement) => void
  onDelete: () => void
}) {
  const { user } = useAuthStore()
  const { toast } = useToastStore()
  const [comment, setComment] = useState('')
  const [sending, setSending] = useState(false)

  const react = async (emoji: string) => {
    try {
      const r = await announcementsApi.react(clubId, a.id, emoji)
      onChange(x => ({ ...x, reactions: r.data as Reaction[] }))
    } catch (err) { toast(apiError(err, 'Could not react'), 'error') }
  }
  const send = async () => {
    setSending(true)
    try {
      const r = await announcementsApi.comment(clubId, a.id, comment.trim())
      onChange(x => ({ ...x, comments: [...x.comments, r.data] }))
      setComment('')
    } catch (err) { toast(apiError(err, 'Could not comment'), 'error') }
    finally { setSending(false) }
  }
  const removeComment = async (id: number) => {
    try {
      await announcementsApi.deleteComment(clubId, a.id, id)
      onChange(x => ({ ...x, comments: x.comments.filter(c => c.id !== id) }))
    } catch (err) { toast(apiError(err, 'Could not delete'), 'error') }
  }

  const small: React.CSSProperties = { fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }
  const counts = new Map(a.reactions.map(r => [r.emoji, r]))
  return (
    <div style={{ padding: '16px 18px', border: '1px solid var(--dark3)', borderRadius: 12, background: 'var(--dark2)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginBottom: 8 }}>
        <div style={small}>
          <span style={{ color: 'var(--cream)', fontFamily: 'var(--head)', fontSize: 12.5, fontWeight: 600 }}>{a.author_name ?? 'Former member'}</span>
          {a.author_title && <> · {a.author_title}</>} · {getTimeAgo(a.created_at)}
        </div>
        {(canModerate || a.author_id === myId) && (
          <button onClick={onDelete} style={{ ...small, textDecoration: 'underline' }}>Delete</button>
        )}
      </div>
      <div style={{ fontFamily: 'var(--body)', fontSize: 14, color: 'var(--cream2, var(--cream))', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>{a.body}</div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 }}>
        {REACTIONS.map(e => {
          const r = counts.get(e)
          return (
            <button key={e} onClick={() => react(e)} title={r?.mine ? 'Take back your reaction' : 'React'}
              style={{ padding: '3px 9px', borderRadius: 14, fontSize: 13, border: `1px solid ${r?.mine ? 'var(--orange)' : 'var(--dark4)'}`,
                       background: r?.mine ? 'rgba(212,86,26,0.1)' : 'transparent', opacity: r ? 1 : 0.55 }}>
              {e}{r && <span style={{ ...small, marginLeft: 4, color: 'var(--cream)' }}>{r.count}</span>}
            </button>
          )
        })}
      </div>

      {a.comments.length > 0 && (
        <div style={{ marginTop: 14, paddingTop: 10, borderTop: '1px solid var(--dark3)', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {a.comments.map(c => (
            <div key={c.id} style={{ fontFamily: 'var(--body)', fontSize: 13, lineHeight: 1.55 }}>
              <span style={{ fontFamily: 'var(--head)', fontWeight: 600 }}>{c.author_name ?? 'Former member'}</span>{' '}
              <span style={{ color: 'var(--cream3)', whiteSpace: 'pre-wrap' }}>{c.body}</span>
              <span style={{ ...small, marginLeft: 8 }}>{getTimeAgo(c.created_at)}</span>
              {(canModerate || c.author_id === user?.id) && (
                <button onClick={() => removeComment(c.id)} style={{ ...small, marginLeft: 8, textDecoration: 'underline' }}>Delete</button>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input className="inp" value={comment} onChange={e => setComment(e.target.value)} maxLength={3000}
          onKeyDown={e => { if (e.key === 'Enter' && comment.trim() && !sending) send() }}
          placeholder="Write a comment…" style={{ fontSize: 12, flex: 1 }} />
        <button className="btn-g" disabled={sending || !comment.trim()} onClick={send} style={{ padding: '8px 14px', fontSize: 10 }}>Comment</button>
      </div>
    </div>
  )
}

// ── Asking the DSW to run this club ───────────────────────
function OwnershipRequest({ clubId, clubName }: { clubId: number; clubName: string }) {
  const { user, refreshUser } = useAuthStore()
  const { toast } = useToastStore()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [sending, setSending] = useState(false)
  const request = user?.club_roles.find(r => r.club_id === clubId && r.role !== 'member' && r.status !== 'active')

  const send = async () => {
    setSending(true)
    try {
      await clubsApi.requestOwnership(clubId, title.trim())
      await refreshUser()
      setOpen(false)
      toast('Request sent to the DSW', 'success')
    } catch (err) {
      toast(apiError(err, 'Could not send the request'), 'error')
    } finally {
      setSending(false)
    }
  }

  const note: React.CSSProperties = { marginTop: 20, fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--gray2)' }
  if (request?.status === 'pending') {
    return <div style={note}>Your request to be {request.role === 'owner' ? 'owner' : 'an editor'} of {clubName} is waiting for the DSW.</div>
  }
  if (!open) {
    return (
      <div style={note}>
        {request?.status === 'rejected' && "The DSW didn't approve your last request. "}
        <button onClick={() => setOpen(true)} style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--orange)', textDecoration: 'underline', textUnderlineOffset: 3 }}>
          Do you run {clubName}? Ask the DSW to make you its owner
        </button>
      </div>
    )
  }
  return (
    <div style={{ marginTop: 20, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
      <input className="inp" value={title} onChange={e => setTitle(e.target.value)} placeholder="Your title, e.g. President"
        style={{ width: 240, padding: '8px 12px', fontSize: 12 }} />
      <button className="btn-p" disabled={sending} onClick={send} style={{ padding: '9px 16px', fontSize: 10, letterSpacing: 1.5 }}>
        {sending ? 'Sending…' : 'Send to DSW'}
      </button>
      <button className="btn-g" onClick={() => setOpen(false)} style={{ padding: '9px 14px', fontSize: 10 }}>Cancel</button>
    </div>
  )
}

// ── EventCard ─────────────────────────────────────────────
function EventCard({ event: ev, delay, onClick }: { event: Event; delay: number; onClick: () => void }) {
  const color = getEventColor(ev)
  return (
    <div
      className="pcard au"
      style={{ animationDelay: `${delay}ms`, cursor: 'pointer' }}
      onClick={onClick}
    >
      {ev.poster_url
        ? <img src={ev.poster_url} alt={ev.title} onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
        : <div style={{ width: '100%', height: '100%', background: `linear-gradient(155deg, ${color}22 0%, var(--dark2) 65%)` }} />
      }
      <div className="pcard-grad" />
      <div className="pcard-body" style={{ zIndex: 2 }}>
        <h3 style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 700, lineHeight: 1.25, marginBottom: 5 }}>{ev.title}</h3>
        <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'rgba(242,234,220,0.45)' }}>{ev.date_display}</div>
        {ev.is_hot && (
          <div style={{ marginTop: 5, display: 'inline-block', fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '1px 6px' }}>Hot</div>
        )}
      </div>
    </div>
  )
}
