import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom'
import { eventsApi, discussionsApi } from '@/api/client'
import { useUserEvents } from '@/hooks/useData'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { splitTags, getEventColor, getTimeAgo, TAG_COLORS } from '@/types'
import type { Event, Discussion, User } from '@/types'

const PAGE_SIZE = 10
// Must match EDIT_WINDOW_MINUTES in backend/app/api/routes/discussions.py (the backend enforces it)
const EDIT_WINDOW_MINUTES = 15

// Backend errors come back as { detail: "..." }; validation errors (422) have a list instead
const errMsg = (err: any, fallback: string) =>
  typeof err?.response?.data?.detail === 'string' ? err.response.data.detail : fallback

export function EventDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuthStore()
  const { toast } = useToastStore()
  const { registered, saved, toggleSave, register } = useUserEvents()

  const [event, setEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [regCount, setRegCount] = useState(0)
  const [showConfirm, setShowConfirm] = useState(false)

  const [discussions, setDiscussions] = useState<Discussion[]>([])
  const [discTotal, setDiscTotal] = useState(0)          // total top-level comments on the server
  const [hasMore, setHasMore] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [newComment, setNewComment] = useState('')
  const [replyingTo, setReplyingTo] = useState<number | null>(null)  // id of the top-level comment
  const [replyText, setReplyText] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const [loadingDiscussions, setLoadingDiscussions] = useState(false)

  const eventId = Number(id)
  const isRegistered = registered.includes(eventId)
  const isSaved = saved.includes(eventId)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    eventsApi.get(eventId)
      .then(r => setEvent(r.data))
      .catch(() => { toast('Event not found', 'error'); navigate('/events') })
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!id) return
    eventsApi.registrationCount(eventId)
      .then(r => setRegCount(r.data.count))
      .catch(() => {})
  }, [id, registered])

  // location.key changes on every navigation, so clicking a notification for the
  // event you're already on still reloads the thread
  useEffect(() => {
    if (!id) return
    loadDiscussions()
  }, [id, location.key])

  // Notifications link to /events/:id#discussion — scroll there once the page has rendered
  useEffect(() => {
    if (!loading && location.hash === '#discussion') {
      document.getElementById('discussion')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [loading, location.key])

  // First page. Later pages are appended by loadMoreDiscussions; post/reply/edit/delete
  // update the list in place so already-loaded pages aren't thrown away.
  const loadDiscussions = async () => {
    setLoadingDiscussions(true)
    try {
      const r = await discussionsApi.list(eventId, { limit: PAGE_SIZE })
      setDiscussions(r.data.items)
      setDiscTotal(r.data.total)
      setHasMore(r.data.items.length === PAGE_SIZE && r.data.items.length < r.data.total)
    } catch {}
    setLoadingDiscussions(false)
  }

  const loadMoreDiscussions = async () => {
    const last = discussions[discussions.length - 1]
    if (!last) return
    setLoadingMore(true)
    try {
      const r = await discussionsApi.list(eventId, { before_id: last.id, limit: PAGE_SIZE })
      setDiscussions(prev => [...prev, ...r.data.items])
      setDiscTotal(r.data.total)
      setHasMore(r.data.items.length === PAGE_SIZE)
    } catch { toast('Failed to load more comments', 'error') }
    setLoadingMore(false)
  }

  // Apply a change to one comment or reply, wherever it sits in the thread
  const patchItem = (id: number, fn: (d: Discussion) => Discussion) =>
    setDiscussions(prev => prev.map(c =>
      c.id === id ? fn(c) : { ...c, replies: c.replies.map(r => (r.id === id ? fn(r) : r)) }
    ))

  const handleRegister = async () => {
    if (!event) return
    setShowConfirm(false)
    await register(event)
    eventsApi.registrationCount(eventId).then(r => setRegCount(r.data.count)).catch(() => {})
  }

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href)
      .then(() => toast('Link copied to clipboard!', 'success'))
      .catch(() => toast('Could not copy link', 'error'))
  }

  const handlePostComment = async () => {
    if (!newComment.trim()) return
    try {
      const r = await discussionsApi.create(eventId, { content: newComment.trim() })
      setDiscussions(prev => [r.data, ...prev])
      setDiscTotal(t => t + 1)
      setNewComment(''); toast('Comment posted!', 'success')
    } catch (err) { toast(errMsg(err, 'Failed to post comment'), 'error') }
  }

  // Open the reply box under a top-level comment. Replying to a reply opens the same
  // box (threads stay one level deep) with "@Name " pre-filled.
  const handleOpenReply = (commentId: number, mention?: string) => {
    setReplyingTo(commentId)
    setReplyText(mention ? `@${mention} ` : '')
  }

  const handleReply = async (commentId: number) => {
    if (!replyText.trim()) return
    try {
      const r = await discussionsApi.reply(eventId, commentId, { content: replyText.trim() })
      patchItem(commentId, c => ({ ...c, replies: [...c.replies, r.data] }))
      setReplyText(''); setReplyingTo(null); toast('Reply posted!', 'success')
    } catch (err) { toast(errMsg(err, 'Failed to post reply'), 'error') }
  }

  const handleStartEdit = (item: Discussion) => { setEditingId(item.id); setEditText(item.content) }

  const handleSaveEdit = async (item: Discussion) => {
    if (!editText.trim()) return
    try {
      const r = await discussionsApi.edit(eventId, item.id, { content: editText.trim() })
      patchItem(item.id, d => ({ ...d, content: r.data.content, edited_at: r.data.edited_at }))
      setEditingId(null); setEditText(''); toast('Comment updated', 'success')
    } catch (err) { toast(errMsg(err, 'Failed to edit comment'), 'error') }
  }

  const handleDeleteComment = async (item: Discussion) => {
    try {
      await discussionsApi.delete(eventId, item.id)
      if (item.parent_id === null) {
        setDiscussions(prev => prev.filter(c => c.id !== item.id))  // its replies go with it
        setDiscTotal(t => t - 1)
      } else {
        patchItem(item.parent_id, c => ({ ...c, replies: c.replies.filter(r => r.id !== item.id) }))
      }
      toast('Comment deleted', 'info')
    } catch (err) { toast(errMsg(err, 'Failed to delete comment'), 'error') }
  }

  if (loading) return <PageLoader />
  if (!event) return null

  const color = getEventColor(event)
  const tags = splitTags(event.tags)
  // Open through the whole deadline day, same rule as the backend. Compare "YYYY-MM-DD"
  // strings: new Date("2026-10-01") is UTC midnight, which would close it at 5:30 AM IST.
  const now = new Date()
  const todayKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  const deadlinePassed = !!event.reg_deadline && event.reg_deadline < todayKey
  const hasDetails = event.prize_pool || event.team_size || event.contact_info ||
    (event.registration_fee && event.registration_fee !== 'Free')

  const metaItems = [
    { icon: '📅', val: event.date_display },
    { icon: '📍', val: event.venue || 'Venue TBA' },
    ...(event.time_info ? [{ icon: '🕐', val: event.time_info }] : []),
  ]

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>

      {/* ── Color identity stripe ── */}
      <div style={{
        height: 3,
        background: `linear-gradient(90deg, ${color} 0%, ${color}66 60%, transparent 100%)`,
      }} />

      {/* ══════════════════════════════════════════
          HERO HEADER
      ══════════════════════════════════════════ */}
      <div className="pg-hdr" style={{ padding: '28px 40px 38px' }}>
        {/* Extra event-color radial glow */}
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
          background: `radial-gradient(ellipse at 78% 40%, ${color}1a 0%, transparent 52%)`,
        }} />

        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1100, margin: '0 auto' }}>

          {/* Back button */}
          <button
            onClick={() => navigate(-1)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              fontFamily: 'var(--mono)', fontSize: 10,
              color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 2.5,
              marginBottom: 26, transition: 'color 0.15s',
            }}
            onMouseOver={e => (e.currentTarget.style.color = 'var(--cream)')}
            onMouseOut={e => (e.currentTarget.style.color = 'var(--gray2)')}
          >
            ← Back
          </button>

          {/* Two-column flex */}
          <div style={{ display: 'flex', gap: 44, alignItems: 'flex-start' }}>

            {/* ── LEFT: all event info ── */}
            <div style={{ flex: 1, minWidth: 0 }} className="au">

              {/* Club eyebrow chip */}
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 8,
                marginBottom: 16, padding: '5px 13px',
                background: `${color}10`, border: `1px solid ${color}2e`,
                borderRadius: 7,
              }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: color, display: 'inline-block', flexShrink: 0,
                }} />
                <Link
                  to={`/clubs/${event.club_id}`}
                  style={{
                    fontFamily: 'var(--mono)', fontSize: 10, color,
                    textDecoration: 'none', textTransform: 'uppercase', letterSpacing: 2.2,
                  }}
                  onMouseOver={e => (e.currentTarget.style.textDecoration = 'underline')}
                  onMouseOut={e => (e.currentTarget.style.textDecoration = 'none')}
                >
                  {event.club_name}
                </Link>
              </div>

              {/* Title */}
              <h1 style={{
                fontFamily: 'var(--syne)', fontWeight: 800,
                fontSize: 'clamp(26px, 3.5vw, 42px)',
                letterSpacing: '-1.5px', lineHeight: 1.07, marginBottom: 22,
              }}>
                {event.title}<span style={{ color }}>.</span>
              </h1>

              {/* Meta strip */}
              <div style={{
                display: 'flex', alignItems: 'center', flexWrap: 'wrap',
                gap: 0, marginBottom: 20,
                paddingTop: 12, paddingBottom: 12,
                borderTop: '1px solid var(--dark3)', borderBottom: '1px solid var(--dark3)',
              }}>
                {metaItems.map((m, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 7,
                      paddingRight: 18, marginRight: 18,
                      borderRight: i < metaItems.length - 1 ? '1px solid var(--dark3)' : 'none',
                    }}
                  >
                    <span style={{ fontSize: 13 }}>{m.icon}</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--cream3)' }}>
                      {m.val}
                    </span>
                  </div>
                ))}
              </div>

              {/* Tag badges + Hot */}
              <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginBottom: 18, alignItems: 'center' }}>
                {tags.map(tg => (
                  <span key={tg} style={{
                    padding: '4px 12px', fontSize: 10, fontFamily: 'var(--mono)',
                    border: `1.5px solid ${TAG_COLORS[tg] || color}44`,
                    background: `${TAG_COLORS[tg] || color}0d`,
                    color: TAG_COLORS[tg] || color,
                    borderRadius: 20, textTransform: 'capitalize', letterSpacing: 0.8,
                  }}>
                    {tg}
                  </span>
                ))}
                {event.is_hot && (
                  <span style={{
                    padding: '4px 12px', fontSize: 10, fontFamily: 'var(--mono)', fontWeight: 700,
                    background: 'var(--orange)', color: 'var(--bg)',
                    borderRadius: 20, letterSpacing: 1.2, textTransform: 'uppercase',
                  }}>
                    🔥 Hot
                  </span>
                )}
              </div>

              {/* Deadline badge */}
              {event.reg_deadline && (
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 8,
                  padding: '7px 14px', borderRadius: 8, marginBottom: 22,
                  background: deadlinePassed ? 'rgba(239,68,68,0.07)' : `${color}0d`,
                  border: `1px solid ${deadlinePassed ? 'rgba(239,68,68,0.28)' : `${color}28`}`,
                }}>
                  <span style={{ fontSize: 13 }}>{deadlinePassed ? '⚠️' : '⏰'}</span>
                  <span style={{
                    fontFamily: 'var(--mono)', fontSize: 11,
                    color: deadlinePassed ? '#EF4444' : color,
                  }}>
                    Reg. deadline:{' '}
                    {new Date(event.reg_deadline).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric',
                    })}
                    {deadlinePassed && <strong> · Closed</strong>}
                  </span>
                </div>
              )}

              {/* Action row */}
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  onClick={() => event && toggleSave(event)}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    padding: '9px 18px', fontSize: 11,
                    fontFamily: 'var(--head)', fontWeight: 700,
                    letterSpacing: 1, textTransform: 'uppercase',
                    border: `1.5px solid ${isSaved ? `${color}55` : 'var(--dark4)'}`,
                    background: isSaved ? `${color}12` : 'transparent',
                    color: isSaved ? color : 'var(--gray)',
                    borderRadius: 8, transition: 'all 0.15s',
                  }}
                >
                  {isSaved ? '★' : '☆'} {isSaved ? 'Saved' : 'Save'}
                </button>

                <button
                  onClick={handleShare}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    padding: '9px 18px', fontSize: 11,
                    fontFamily: 'var(--head)', fontWeight: 700,
                    letterSpacing: 1, textTransform: 'uppercase',
                    border: '1.5px solid var(--dark4)', background: 'transparent',
                    color: 'var(--gray)', borderRadius: 8, transition: 'all 0.15s',
                  }}
                >
                  🔗 Share
                </button>

                <span style={{
                  fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)',
                  display: 'inline-flex', alignItems: 'center', gap: 6, marginLeft: 2,
                }}>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                    width: 22, height: 22, background: 'var(--dark3)',
                    borderRadius: 5, fontSize: 11,
                  }}>
                    👥
                  </span>
                  {regCount} registered
                </span>

                {isRegistered && (
                  <span style={{
                    padding: '4px 11px', fontSize: 10,
                    fontFamily: 'var(--mono)', fontWeight: 600,
                    background: 'rgba(16,185,129,0.1)', color: '#10B981',
                    border: '1px solid rgba(16,185,129,0.28)', borderRadius: 6,
                  }}>
                    ✓ Registered
                  </span>
                )}
              </div>
            </div>

            {/* ── RIGHT: poster card ── */}
            <div className="au" style={{ animationDelay: '80ms', flexShrink: 0 }}>
              <div style={{
                width: 210, aspectRatio: '2/3', borderRadius: 15, overflow: 'hidden',
                border: `1.5px solid ${color}2e`,
                background: `linear-gradient(155deg, ${color}16 0%, var(--dark2) 65%)`,
                boxShadow: `0 20px 52px rgba(0,0,0,0.65), 0 0 44px ${color}14`,
                position: 'relative',
              }}>
                {event.poster_url ? (
                  <img
                    src={event.poster_url}
                    alt={event.title}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                    onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                ) : (
                  <div style={{
                    width: '100%', height: '100%',
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center', gap: 10,
                  }}>
                    <span style={{ fontSize: 30, opacity: 0.22 }}>🎪</span>
                    <span style={{
                      fontFamily: 'var(--mono)', fontSize: 9,
                      color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 2,
                    }}>
                      No poster
                    </span>
                  </div>
                )}
                {/* Color wash at bottom */}
                <div style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0, height: '45%',
                  background: `linear-gradient(to top, ${color}28, transparent)`,
                  pointerEvents: 'none',
                }} />
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════
          MAIN CONTENT
      ══════════════════════════════════════════ */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 40px 80px' }}>

        {/* ── Register CTA ── */}
        <div className="au" style={{ marginBottom: 48, animationDelay: '120ms' }}>
          {isRegistered ? (
            <div style={{
              padding: '22px 28px', borderRadius: 14,
              background: 'linear-gradient(145deg, rgba(16,185,129,0.07) 0%, rgba(16,185,129,0.03) 100%)',
              border: '1.5px solid rgba(16,185,129,0.2)',
              display: 'flex', alignItems: 'center',
              justifyContent: 'space-between', flexWrap: 'wrap', gap: 20,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 11, flexShrink: 0,
                  background: 'rgba(16,185,129,0.12)',
                  border: '1.5px solid rgba(16,185,129,0.28)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'var(--head)', fontSize: 20, color: '#10B981',
                }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, color: '#10B981' }}>
                    You're registered!
                  </div>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 3 }}>
                    Your spot is confirmed — see you there.
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 28 }}>
                {[
                  { n: regCount,          label: 'going' },
                  { n: discTotal,         label: 'comments' },
                ].map(s => (
                  <div key={s.label} style={{ textAlign: 'center' }}>
                    <div style={{ fontFamily: 'var(--syne)', fontSize: 24, fontWeight: 800, color: '#10B981', lineHeight: 1 }}>
                      {s.n}
                    </div>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.5, marginTop: 4 }}>
                      {s.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{
              padding: '22px 28px', borderRadius: 14,
              background: `linear-gradient(145deg, ${color}09 0%, transparent 100%)`,
              border: `1px solid ${color}22`,
              display: 'flex', alignItems: 'center',
              justifyContent: 'space-between', flexWrap: 'wrap', gap: 20,
            }}>
              <div>
                <div style={{ fontFamily: 'var(--head)', fontSize: 15, fontWeight: 700, marginBottom: 5 }}>
                  Ready to join?
                </div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>
                  {regCount > 0
                    ? `${regCount} people already registered`
                    : 'Be among the first to register'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
                {event.registration_fee && event.registration_fee !== 'Free' && (
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 3 }}>
                      Entry Fee
                    </div>
                    <div style={{ fontFamily: 'var(--syne)', fontSize: 20, fontWeight: 800, color, lineHeight: 1 }}>
                      {event.registration_fee}
                    </div>
                  </div>
                )}
                <button
                  onClick={() => setShowConfirm(true)}
                  className="btn-p"
                  style={{ padding: '14px 36px', fontSize: 12, borderRadius: 10 }}
                  disabled={!!deadlinePassed}
                >
                  {deadlinePassed ? 'Registration Closed' : 'Register Now →'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── About ── */}
        <div className="au" style={{ marginBottom: 48, maxWidth: 800, animationDelay: '160ms' }}>
          <SectionLabel color={color}>About this event</SectionLabel>
          <div style={{
            fontFamily: 'var(--body)', fontSize: 14.5, color: 'var(--cream3)',
            lineHeight: 1.88, whiteSpace: 'pre-wrap',
          }}>
            {event.description}
          </div>
        </div>

        {/* ── Details grid ── */}
        {hasDetails && (
          <div className="au" style={{ marginBottom: 48, animationDelay: '200ms' }}>
            <SectionLabel color={color}>Event Details</SectionLabel>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
              {event.registration_fee && event.registration_fee !== 'Free' && (
                <DetailPanel icon="💰" label="Registration Fee" value={event.registration_fee} color={color} />
              )}
              {event.prize_pool && (
                <DetailPanel icon="🏆" label="Prize Pool" value={event.prize_pool} color={color} />
              )}
              {event.team_size && (
                <DetailPanel icon="👥" label="Team Size" value={event.team_size} color={color} />
              )}
              {event.contact_info && (
                <DetailPanel icon="📧" label="Contact Organizers" value={event.contact_info} color={color} />
              )}
            </div>
          </div>
        )}

        {/* ── Discussion ── */}
        <div id="discussion" className="au" style={{ animationDelay: '240ms', scrollMarginTop: 80 }}>
          <SectionLabel color={color}>Discussion ({discTotal})</SectionLabel>

          {/* Comment input card */}
          <div style={{
            display: 'flex', gap: 14, marginBottom: 28,
            padding: '18px 20px', borderRadius: 13,
            background: 'linear-gradient(145deg, var(--dark2) 0%, var(--dark) 100%)',
            border: '1px solid var(--dark3)',
            maxWidth: 800,
          }}>
            {/* User avatar */}
            <div style={{
              width: 38, height: 38, flexShrink: 0, borderRadius: 9,
              background: `${color}14`, border: `1.5px solid ${color}2e`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'var(--head)', fontSize: 15, fontWeight: 700, color,
            }}>
              {(user?.name ?? 'U')[0].toUpperCase()}
            </div>
            <div style={{ flex: 1 }}>
              <textarea
                className="inp"
                value={newComment}
                onChange={e => setNewComment(e.target.value)}
                placeholder="Ask a question or leave a comment…"
                rows={3}
                style={{ resize: 'vertical', minHeight: 72, fontSize: 13.5 }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                <button
                  onClick={handlePostComment}
                  className="btn-p"
                  style={{ padding: '8px 22px', fontSize: 10, letterSpacing: 2 }}
                  disabled={!newComment.trim()}
                >
                  Post
                </button>
              </div>
            </div>
          </div>

          {/* Comment list */}
          <div style={{ maxWidth: 800 }}>
            {loadingDiscussions ? (
              <div style={{
                fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)',
                padding: '28px 0', textAlign: 'center',
                textTransform: 'uppercase', letterSpacing: 3,
              }}>
                Loading…
              </div>
            ) : discussions.length === 0 ? (
              <div style={{
                padding: '52px 24px', borderRadius: 14, textAlign: 'center',
                border: '1.5px dashed var(--dark4)',
                background: 'linear-gradient(145deg, var(--dark2) 0%, var(--dark) 100%)',
              }}>
                <div style={{ fontSize: 30, marginBottom: 12, opacity: 0.25 }}>💬</div>
                <div style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 700, marginBottom: 6 }}>
                  No discussions yet
                </div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>
                  Be the first to ask something!
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {discussions.map(c => (
                  <CommentCard
                    key={c.id}
                    comment={c}
                    ctx={{
                      currentUser: user,
                      eventClubName: event.club_name,
                      color,
                      replyingTo, replyText,
                      onOpenReply: handleOpenReply,
                      onCloseReply: () => { setReplyingTo(null); setReplyText('') },
                      onSetReplyText: setReplyText,
                      onReply: handleReply,
                      editingId, editText,
                      onStartEdit: handleStartEdit,
                      onCancelEdit: () => { setEditingId(null); setEditText('') },
                      onSetEditText: setEditText,
                      onSaveEdit: handleSaveEdit,
                      onDelete: handleDeleteComment,
                    }}
                  />
                ))}
                {hasMore && (
                  <button
                    onClick={loadMoreDiscussions}
                    className="btn-g"
                    disabled={loadingMore}
                    style={{ alignSelf: 'center', marginTop: 8, padding: '9px 26px', fontSize: 10, letterSpacing: 2 }}
                  >
                    {loadingMore ? 'Loading…' : 'Load more comments'}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

      </div>

      {/* ══════════════════════════════════════════
          REGISTRATION MODAL
      ══════════════════════════════════════════ */}
      {showConfirm && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div
            className="mbg"
            style={{ position: 'absolute', inset: 0 }}
            onClick={() => setShowConfirm(false)}
          />
          <div className="mbox asi" style={{ position: 'relative', padding: '34px 36px', maxWidth: 420, width: '90%' }}>
            {/* Color accent bar */}
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, height: 3,
              background: `linear-gradient(90deg, ${color}, ${color}44, transparent)`,
              borderRadius: '20px 20px 0 0',
            }} />

            <div style={{
              fontFamily: 'var(--mono)', fontSize: 9, color,
              textTransform: 'uppercase', letterSpacing: 3, marginBottom: 14,
            }}>
              {event.club_name}
            </div>

            <h3 style={{
              fontFamily: 'var(--syne)', fontSize: 22, fontWeight: 800,
              letterSpacing: '-0.5px', marginBottom: 14,
            }}>
              Confirm Registration
            </h3>

            <p style={{
              fontFamily: 'var(--body)', fontSize: 14, color: 'var(--cream3)',
              lineHeight: 1.65, marginBottom: 8,
            }}>
              You're about to register for{' '}
              <strong style={{ color: 'var(--cream)' }}>{event.title}</strong>.
            </p>

            {event.registration_fee && event.registration_fee !== 'Free' && (
              <div style={{
                padding: '9px 14px', borderRadius: 8, marginBottom: 10,
                background: `${color}0e`, border: `1px solid ${color}28`,
                fontFamily: 'var(--mono)', fontSize: 12, color,
              }}>
                Entry fee: {event.registration_fee}
              </div>
            )}

            <div style={{
              fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginBottom: 28,
            }}>
              {event.date_display} · {event.venue || 'Venue TBA'}
            </div>

            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={() => setShowConfirm(false)} className="btn-g" style={{ flex: 1 }}>
                Cancel
              </button>
              <button onClick={handleRegister} className="btn-p" style={{ flex: 1 }}>
                Confirm →
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}

// ── Section label with color accent bar ────────────────────
function SectionLabel({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      marginBottom: 22, paddingBottom: 14,
      borderBottom: '1px solid var(--dark3)',
    }}>
      <div style={{
        width: 3, height: 18, background: color,
        borderRadius: 2, flexShrink: 0,
        boxShadow: `0 0 8px ${color}66`,
      }} />
      <span style={{ fontFamily: 'var(--head)', fontSize: 17, fontWeight: 700 }}>
        {children}
      </span>
    </div>
  )
}

// ── Detail panel card ──────────────────────────────────────
function DetailPanel({ icon, label, value, color }: {
  icon: string; label: string; value: string; color: string
}) {
  return (
    <div style={{
      padding: '18px 20px', borderRadius: 12,
      background: 'linear-gradient(145deg, var(--dark2) 0%, var(--dark) 100%)',
      border: '1px solid var(--dark3)',
      display: 'flex', gap: 14, alignItems: 'flex-start',
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: 10, flexShrink: 0,
        background: `${color}10`, border: `1px solid ${color}22`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 18,
      }}>
        {icon}
      </div>
      <div>
        <div style={{
          fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)',
          textTransform: 'uppercase', letterSpacing: 1.8, marginBottom: 6,
        }}>
          {label}
        </div>
        <div style={{
          fontFamily: 'var(--body)', fontSize: 13.5, color: 'var(--cream3)',
          lineHeight: 1.65, whiteSpace: 'pre-wrap',
        }}>
          {value}
        </div>
      </div>
    </div>
  )
}

// ── Comment thread ────────────────────────────────────────
// Everything a comment card needs from the page, bundled so it isn't 15 separate props
interface ThreadCtx {
  currentUser: User | null
  eventClubName: string
  color: string
  replyingTo: number | null
  replyText: string
  onOpenReply: (commentId: number, mention?: string) => void
  onCloseReply: () => void
  onSetReplyText: (text: string) => void
  onReply: (commentId: number) => void
  editingId: number | null
  editText: string
  onStartEdit: (item: Discussion) => void
  onCancelEdit: () => void
  onSetEditText: (text: string) => void
  onSaveEdit: (item: Discussion) => void
  onDelete: (item: Discussion) => void
}

const withinEditWindow = (createdAt: string) =>
  Date.now() - new Date(createdAt).getTime() < EDIT_WINDOW_MINUTES * 60_000

// ── Comment card (top-level comment + its replies) ────────
function CommentCard({ comment, ctx }: { comment: Discussion; ctx: ThreadCtx }) {
  const isReplying = ctx.replyingTo === comment.id

  return (
    <div style={{
      padding: '18px 20px', borderRadius: 13,
      background: 'linear-gradient(145deg, var(--dark2) 0%, var(--dark) 100%)',
      border: '1px solid var(--dark3)',
    }}>
      {/* Comment header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 12 }}>
        <Avatar name={comment.user_name} official={comment.is_official} size={34} />

        {/* Name + time */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--head)', fontSize: 13, fontWeight: 600 }}>
              {comment.user_name}
            </span>
            {comment.is_official && <AdminBadge />}
          </div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 2 }}>
            {getTimeAgo(comment.created_at)}{comment.edited_at && ' (edited)'}
          </div>
        </div>

        <ItemActions
          item={comment}
          ctx={ctx}
          replyLabel={isReplying ? 'Cancel' : 'Reply'}
          onReplyClick={() => (isReplying ? ctx.onCloseReply() : ctx.onOpenReply(comment.id))}
        />
      </div>

      {/* Comment content (or edit box) */}
      <div style={{ marginLeft: 46 }}>
        <ItemBody item={comment} ctx={ctx} fontSize={13.5} />
      </div>

      {/* Nested replies */}
      {comment.replies.length > 0 && (
        <div style={{ marginLeft: 46, marginTop: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {comment.replies.map(reply => (
            <ReplyItem key={reply.id} reply={reply} parentId={comment.id} ctx={ctx} />
          ))}
        </div>
      )}

      {/* Reply input — sits under the thread so it reads like the next message */}
      {isReplying && (
        <div style={{ marginLeft: 46, marginTop: 14 }}>
          <textarea
            className="inp"
            value={ctx.replyText}
            onChange={e => ctx.onSetReplyText(e.target.value)}
            placeholder="Write a reply…"
            rows={2}
            autoFocus
            style={{ resize: 'vertical', fontSize: 13, minHeight: 58 }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
            <button onClick={ctx.onCloseReply} className="btn-g" style={{ padding: '7px 16px', fontSize: 10, letterSpacing: 2 }}>
              Cancel
            </button>
            <button
              onClick={() => ctx.onReply(comment.id)}
              className="btn-p"
              style={{ padding: '7px 18px', fontSize: 10, letterSpacing: 2 }}
              disabled={!ctx.replyText.trim()}
            >
              Reply
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Single reply inside a thread ──────────────────────────
function ReplyItem({ reply, parentId, ctx }: { reply: Discussion; parentId: number; ctx: ThreadCtx }) {
  const { color } = ctx
  const official = reply.is_official
  // Replying to a reply stays in the same thread, @mentioning its author (unless it's you)
  const mention = reply.user_id !== ctx.currentUser?.id ? reply.user_name : undefined

  return (
    <div style={{
      padding: '13px 16px', borderRadius: 10,
      background: official ? `${color}06` : 'rgba(242,234,220,0.02)',
      borderLeft: `2px solid ${official ? `${color}55` : 'var(--dark4)'}`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 7 }}>
        <Avatar name={reply.user_name} official={official} size={26} />
        <span style={{
          fontFamily: 'var(--head)', fontSize: 12, fontWeight: 600,
          color: official ? 'var(--orange)' : 'var(--cream)',
        }}>
          {reply.user_name}
        </span>
        {official && <AdminBadge small />}
        <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)' }}>
          {getTimeAgo(reply.created_at)}{reply.edited_at && ' (edited)'}
        </span>
        <div style={{ marginLeft: 'auto' }}>
          <ItemActions
            item={reply}
            ctx={ctx}
            replyLabel="Reply"
            onReplyClick={() => ctx.onOpenReply(parentId, mention)}
          />
        </div>
      </div>
      <div style={{ marginLeft: 34 }}>
        <ItemBody item={reply} ctx={ctx} fontSize={13} />
      </div>
    </div>
  )
}

// ── Reply / Edit / Delete buttons for a comment or reply ──
function ItemActions({ item, ctx, replyLabel, onReplyClick }: {
  item: Discussion
  ctx: ThreadCtx
  replyLabel: string
  onReplyClick: () => void
}) {
  const me = ctx.currentUser
  const isOwn = me?.id === item.user_id
  // Admins moderate only their own club's events (matches the backend check)
  const canModerate = me?.role === 'member' && me.club_name === ctx.eventClubName
  const canEdit = isOwn && withinEditWindow(item.created_at) && ctx.editingId !== item.id
  const canDelete = isOwn || canModerate

  return (
    <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
      <ActionBtn color="var(--orange)" border="rgba(212,86,26,0.28)" onClick={onReplyClick}>{replyLabel}</ActionBtn>
      {canEdit && (
        <ActionBtn color="var(--gray)" border="var(--dark4)" onClick={() => ctx.onStartEdit(item)}>Edit</ActionBtn>
      )}
      {canDelete && (
        <ActionBtn color="#EF4444" border="rgba(239,68,68,0.28)" onClick={() => ctx.onDelete(item)}>Delete</ActionBtn>
      )}
    </div>
  )
}

// ── Comment text, or an inline edit box while editing ─────
function ItemBody({ item, ctx, fontSize }: { item: Discussion; ctx: ThreadCtx; fontSize: number }) {
  if (ctx.editingId !== item.id) {
    return (
      <div style={{
        fontFamily: 'var(--body)', fontSize, color: 'var(--cream3)',
        lineHeight: 1.65, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {item.content}
      </div>
    )
  }
  return (
    <div>
      <textarea
        className="inp"
        value={ctx.editText}
        onChange={e => ctx.onSetEditText(e.target.value)}
        rows={2}
        autoFocus
        style={{ resize: 'vertical', fontSize: 13, minHeight: 58 }}
      />
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
        <button onClick={ctx.onCancelEdit} className="btn-g" style={{ padding: '7px 16px', fontSize: 10, letterSpacing: 2 }}>
          Cancel
        </button>
        <button
          onClick={() => ctx.onSaveEdit(item)}
          className="btn-p"
          style={{ padding: '7px 18px', fontSize: 10, letterSpacing: 2 }}
          disabled={!ctx.editText.trim()}
        >
          Save
        </button>
      </div>
    </div>
  )
}

// ── Small building blocks ─────────────────────────────────
function Avatar({ name, official, size }: { name: string; official: boolean; size: number }) {
  return (
    <div style={{
      width: size, height: size, borderRadius: size > 30 ? 8 : 6, flexShrink: 0,
      background: official ? 'rgba(212,86,26,0.14)' : 'var(--dark3)',
      border: official ? '1.5px solid rgba(212,86,26,0.3)' : '1px solid var(--dark4)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'var(--head)', fontSize: size > 30 ? 13 : 11, fontWeight: 700,
      color: official ? 'var(--orange)' : 'var(--gray)',
    }}>
      {name[0].toUpperCase()}
    </div>
  )
}

function AdminBadge({ small }: { small?: boolean }) {
  return (
    <span style={{
      padding: small ? '1px 6px' : '1px 7px', fontSize: small ? 7 : 8,
      fontFamily: 'var(--mono)', fontWeight: 600,
      background: 'rgba(212,86,26,0.1)', color: 'var(--orange)',
      border: '1px solid rgba(212,86,26,0.25)', borderRadius: 4,
      textTransform: 'uppercase', letterSpacing: 1.2,
    }}>
      Admin
    </span>
  )
}

function ActionBtn({ children, color, border, onClick }: {
  children: React.ReactNode; color: string; border: string; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      style={{
        fontSize: 10, fontFamily: 'var(--mono)', fontWeight: 500,
        color, padding: '4px 9px',
        border: `1px solid ${border}`, borderRadius: 5,
        transition: 'all 0.15s',
      }}
    >
      {children}
    </button>
  )
}

// ── Page loader ───────────────────────────────────────────
function PageLoader() {
  return (
    <div style={{ minHeight: '70vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
        fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)',
        textTransform: 'uppercase', letterSpacing: 4,
      }}>
        Loading…
      </div>
    </div>
  )
}
