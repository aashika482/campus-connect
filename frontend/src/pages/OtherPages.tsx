import React, { useState, useEffect } from 'react'
import { useAuthStore } from '@/context/authStore'
import { useNavigate } from 'react-router-dom'
import { useEvents, useUserEvents } from '@/hooks/useData'
import { getEventColor, splitTags, ALL_TAGS, TAG_COLORS } from '@/types'
import type { Event, Discussion } from '@/types'
import { eventsApi, clubsApi, discussionsApi } from '@/api/client'
import { ImageUpload } from '@/components/ui/ImageUpload'
import { useToastStore } from '@/context/toastStore'

// ── SavedPage ─────────────────────────────────────────────
export function SavedPage({ onViewEvent }: { onViewEvent: (ev: Event) => void }) {
  const { events } = useEvents()
  const { saved, toggleSave, registered } = useUserEvents()
  const savedEvents = events.filter(e => saved.includes(e.id))

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Bookmarked</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 42, fontWeight: 800, letterSpacing: '-2px' }}>
            Saved<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>{savedEvents.length} saved events</p>
        </div>
      </div>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 40px' }}>
        {savedEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <div style={{ fontSize: 32, marginBottom: 16 }}>☆</div>
            <div style={{ fontFamily: 'var(--head)', fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Nothing saved yet</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>Bookmark events to find them here</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 18 }}>
            {savedEvents.map(ev => (
              <div key={ev.id} className="pcard au" onClick={() => onViewEvent(ev)}>
                {ev.poster_url
                  ? <img src={ev.poster_url} alt={ev.title} onError={e => { (e.target as HTMLImageElement).style.display = 'none' }} />
                  : <div style={{ width: '100%', height: '100%', background: `linear-gradient(155deg, ${getEventColor(ev)}22 0%, var(--dark2) 65%)` }} />
                }
                <div className="pcard-grad" />
                <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 2 }}>
                  <button onClick={e => { e.stopPropagation(); toggleSave(ev) }}
                    style={{ width: 28, height: 28, background: 'rgba(9,9,9,0.6)', border: '1px solid rgba(242,234,220,0.14)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--orange)', fontSize: 13 }}>★</button>
                </div>
                <div className="pcard-body" style={{ zIndex: 2 }}>
                  <h3 style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 700, lineHeight: 1.25, marginBottom: 5 }}>{ev.title}</h3>
                  <div style={{ fontSize: 10, fontFamily: 'var(--mono)', color: 'rgba(242,234,220,0.45)' }}>{ev.date_display}</div>
                  {registered.includes(ev.id) && <div style={{ marginTop: 4, fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981' }}>✓ Registered</div>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── ProfilePage ───────────────────────────────────────────
export function ProfilePage() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const { events } = useEvents()
  const { registered, saved } = useUserEvents()

  const handleLogout = () => { logout(); navigate('/login') }
  const userTags = user?.interests?.split(',').filter(Boolean) ?? []

  const stats = [
    { label: 'Registered',  val: registered.length },
    { label: 'Saved',       val: saved.length },
    { label: 'Interests',   val: userTags.length },
  ]

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 900, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 24 }}>
          <div style={{ width: 72, height: 72, background: 'var(--orange)', color: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 28, fontFamily: 'var(--head)', flexShrink: 0 }}>
            {(user?.name ?? 'U')[0].toUpperCase()}
          </div>
          <div>
            <h1 style={{ fontFamily: 'var(--head)', fontSize: 32, fontWeight: 800, letterSpacing: '-1px' }}>{user?.name}</h1>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 4 }}>
              {user?.email} · <span style={{ color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 1 }}>{user?.role}</span>
            </div>
            {user?.reg_no && <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 3 }}>{user.reg_no} · {user.course}</div>}
            {user?.club_name && <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 3 }}>{user.club_name} · {user.position}</div>}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 40px' }}>
        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 36 }}>
          {stats.map(s => (
            <div key={s.label} className="stat-card">
              <div style={{ fontFamily: 'var(--head)', fontSize: 34, fontWeight: 800, color: 'var(--orange)' }}>{s.val}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 2, marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Interests */}
        {userTags.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Your Interests</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {userTags.map(t => <span key={t} className="tag" style={{ color: 'var(--orange)', borderColor: 'rgba(212,86,26,0.35)' }}>{t}</span>)}
            </div>
          </div>
        )}

        {/* Registered events */}
        {registered.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Registered Events</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {events.filter(e => registered.includes(e.id)).map(ev => (
                <button
                  key={ev.id}
                  onClick={() => navigate(`/events/${ev.id}`)}
                  style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: `3px solid ${getEventColor(ev)}`, cursor: 'pointer', textAlign: 'left', width: '100%', transition: 'background 0.15s' }}
                  onMouseOver={e => (e.currentTarget.style.background = 'var(--dark3)')}
                  onMouseOut={e => (e.currentTarget.style.background = 'var(--dark2)')}
                >
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: getEventColor(ev), minWidth: 56 }}>{ev.date_display}</span>
                  <span style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 600, flex: 1 }}>{ev.title}</span>
                  <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 7px', flexShrink: 0 }}>✓ Going</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
          {user?.role === 'member' && (
            <button onClick={() => navigate('/admin')} className="btn-p">
              Club Dashboard →
            </button>
          )}
          <button onClick={handleLogout} className="btn-g">Sign Out</button>
        </div>
      </div>
    </div>
  )
}

// ── CalendarPage ──────────────────────────────────────────
export function CalendarPage({ onViewEvent }: { onViewEvent: (ev: Event) => void }) {
  const { events } = useEvents()
  const { registered } = useUserEvents()
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth()

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const monthName = now.toLocaleString('default', { month: 'long' })

  // Build date → events map
  const dateMap: Record<string, Event[]> = {}
  events.forEach(ev => {
    const start = new Date(ev.start_date)
    const end   = new Date(ev.end_date)
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const key = d.toISOString().slice(0, 10)
      if (!dateMap[key]) dateMap[key] = []
      dateMap[key].push(ev)
    }
  })

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>Schedule</div>
          <h1 style={{ fontFamily: 'var(--head)', fontSize: 42, fontWeight: 800, letterSpacing: '-2px' }}>
            {monthName} {year}<span style={{ color: 'var(--orange)' }}>.</span>
          </h1>
        </div>
      </div>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 40px' }}>
        {/* Day headers */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4, marginBottom: 4 }}>
          {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => (
            <div key={d} style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textAlign: 'center', padding: '8px 0', textTransform: 'uppercase', letterSpacing: 1 }}>{d}</div>
          ))}
        </div>
        {/* Calendar grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4 }}>
          {Array.from({ length: firstDay }).map((_, i) => <div key={`e${i}`} style={{ minHeight: 80 }} />)}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1
            const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
            const dayEvents = dateMap[key] ?? []
            const isToday = day === now.getDate()
            return (
              <div key={day} style={{ minHeight: 80, minWidth: 0, overflow: 'hidden', padding: '7px 6px', border: `1.5px solid ${isToday ? 'var(--orange)' : 'var(--dark3)'}`, background: 'linear-gradient(145deg, var(--dark2) 0%, var(--dark) 100%)', borderRadius: 8, position: 'relative', boxShadow: isToday ? '0 0 0 1px var(--orange), 0 0 16px rgba(212,86,26,0.18)' : undefined }}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: isToday ? 'var(--orange)' : 'var(--gray2)', fontWeight: isToday ? 700 : 400, marginBottom: 4 }}>{day}</div>
                {dayEvents.slice(0, 2).map(ev => (
                  <button key={ev.id} onClick={() => onViewEvent(ev)}
                    style={{ display: 'block', width: '100%', minWidth: 0, marginBottom: 2, padding: '2px 5px', background: `${getEventColor(ev)}22`, border: `1px solid ${getEventColor(ev)}44`, borderRadius: 3, textAlign: 'left', cursor: 'pointer', overflow: 'hidden' }}>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 8.5, color: getEventColor(ev), overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>{ev.title}</div>
                  </button>
                ))}
                {dayEvents.length > 2 && <div style={{ fontFamily: 'var(--mono)', fontSize: 8, color: 'var(--gray2)', marginTop: 1 }}>+{dayEvents.length - 2} more</div>}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── EventCreateForm helpers ───────────────────────────────
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

function autoDateDisplay(start: string, end: string): string {
  if (!start || !end) return ''
  const s = new Date(start + 'T00:00:00')
  const e = new Date(end + 'T00:00:00')
  if (start === end) return `${MONTHS[s.getMonth()]} ${s.getDate()}`
  if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear())
    return `${MONTHS[s.getMonth()]} ${s.getDate()}-${e.getDate()}`
  return `${MONTHS[s.getMonth()]} ${s.getDate()} - ${MONTHS[e.getMonth()]} ${e.getDate()}`
}

const LBL: React.CSSProperties = {
  fontFamily: 'var(--mono)',
  fontSize: 10,
  textTransform: 'uppercase',
  letterSpacing: 1.5,
  color: 'var(--gray2)',
  marginBottom: 6,
  display: 'block',
}

function FieldLabel({ text, required }: { text: string; required?: boolean }) {
  return (
    <label style={LBL}>
      {text}
      {required && <span style={{ color: 'var(--orange)', marginLeft: 3 }}>*</span>}
    </label>
  )
}

function ErrMsg({ msg }: { msg?: string }) {
  if (!msg) return null
  return <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#ef4444', marginTop: 5 }}>{msg}</div>
}

// ── EventCreateForm ───────────────────────────────────────
interface EventCreateFormProps {
  clubId: number
  onSuccess: () => void
  onCancel: () => void
}

function EventCreateForm({ clubId, onSuccess, onCancel }: EventCreateFormProps) {
  const { toast } = useToastStore()
  const [submitting, setSubmitting] = useState(false)
  const [showOptional, setShowOptional] = useState(false)
  const [dateDisplayTouched, setDateDisplayTouched] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const [form, setForm] = useState({
    title: '',
    start_date: '',
    end_date: '',
    date_display: '',
    tags: [] as string[],
    reg_deadline: '',
    description: '',
    poster_url: '',
    contact_info: '',
    registration_fee: 'Free',
    venue: '',
    time_info: '',
    prize_pool: '',
    team_size: '',
  })

  // Auto-update date_display when dates change (unless user manually edited it)
  useEffect(() => {
    if (!dateDisplayTouched) {
      const auto = autoDateDisplay(form.start_date, form.end_date)
      if (auto) setForm(f => ({ ...f, date_display: auto }))
    }
  }, [form.start_date, form.end_date, dateDisplayTouched])

  const setField = (key: string, val: string) => {
    setForm(f => ({ ...f, [key]: val }))
    if (errors[key]) setErrors(e => ({ ...e, [key]: '' }))
  }

  const toggleTag = (id: string) => {
    setForm(f => ({
      ...f,
      tags: f.tags.includes(id) ? f.tags.filter(t => t !== id) : [...f.tags, id],
    }))
    if (errors.tags) setErrors(e => ({ ...e, tags: '' }))
  }

  const validate = (): Record<string, string> => {
    const e: Record<string, string> = {}
    if (!form.title.trim())            e.title = 'Required'
    if (!form.start_date)              e.start_date = 'Required'
    if (!form.end_date)                e.end_date = 'Required'
    if (!form.date_display.trim())     e.date_display = 'Required'
    if (form.tags.length === 0)        e.tags = 'Select at least one tag'
    if (!form.reg_deadline)            e.reg_deadline = 'Required'
    if (!form.description.trim())      e.description = 'Required'
    if (!form.poster_url.trim())       e.poster_url = 'Required'
    if (!form.contact_info.trim())     e.contact_info = 'Required'
    if (!form.registration_fee.trim()) e.registration_fee = 'Required'
    return e
  }

  const handleSubmit = async () => {
    const errs = validate()
    if (Object.keys(errs).length > 0) { setErrors(errs); return }
    setSubmitting(true)
    try {
      await eventsApi.create({
        club_id: clubId,
        title: form.title.trim(),
        description: form.description.trim(),
        start_date: form.start_date,
        end_date: form.end_date,
        reg_deadline: form.reg_deadline || undefined,
        date_display: form.date_display.trim(),
        tags: form.tags,
        poster_url: form.poster_url.trim() || undefined,
        contact_info: form.contact_info.trim() || undefined,
        registration_fee: form.registration_fee.trim() || 'Free',
        venue: form.venue.trim() || undefined,
        time_info: form.time_info.trim() || undefined,
        prize_pool: form.prize_pool.trim() || undefined,
        team_size: form.team_size.trim() || undefined,
      })
      toast(`"${form.title}" published successfully!`, 'success')
      onSuccess()
    } catch (err: any) {
      toast(err?.response?.data?.detail ?? 'Failed to publish event', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      background: 'var(--dark2)',
      border: '1.5px solid var(--dark3)',
      borderRadius: 16,
      padding: 32,
      marginBottom: 32,
      animation: 'panelIn 0.3s cubic-bezier(0.22,1,0.36,1) both',
    }}>
      {/* Form header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 28 }}>
        <div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 3, marginBottom: 6 }}>New Event</div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' }}>Post an Event</div>
        </div>
      </div>

      {/* Required fields */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '22px 28px' }}>

        {/* Title — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Event Title" required />
          <input
            className="inp"
            value={form.title}
            onChange={e => setField('title', e.target.value)}
            placeholder="e.g. HackX 4.0"
          />
          <ErrMsg msg={errors.title} />
        </div>

        {/* Start Date */}
        <div>
          <FieldLabel text="Start Date" required />
          <input
            type="date"
            className="inp"
            value={form.start_date}
            onChange={e => setField('start_date', e.target.value)}
            style={{ colorScheme: 'dark' }}
          />
          <ErrMsg msg={errors.start_date} />
        </div>

        {/* End Date */}
        <div>
          <FieldLabel text="End Date" required />
          <input
            type="date"
            className="inp"
            value={form.end_date}
            onChange={e => setField('end_date', e.target.value)}
            style={{ colorScheme: 'dark' }}
          />
          <ErrMsg msg={errors.end_date} />
        </div>

        {/* Date Display */}
        <div>
          <FieldLabel text="Date Display" required />
          <input
            className="inp"
            value={form.date_display}
            onChange={e => { setDateDisplayTouched(true); setField('date_display', e.target.value) }}
            placeholder="e.g. Oct 29-31"
          />
          <ErrMsg msg={errors.date_display} />
        </div>

        {/* Registration Deadline */}
        <div>
          <FieldLabel text="Registration Deadline" required />
          <input
            type="date"
            className="inp"
            value={form.reg_deadline}
            onChange={e => setField('reg_deadline', e.target.value)}
            style={{ colorScheme: 'dark' }}
          />
          <ErrMsg msg={errors.reg_deadline} />
        </div>

        {/* Tags — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Tags" required />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 2 }}>
            {ALL_TAGS.map(tag => {
              const selected = form.tags.includes(tag.id)
              const color = TAG_COLORS[tag.id] ?? 'var(--orange)'
              return (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 20,
                    fontSize: 11,
                    fontFamily: 'var(--mono)',
                    letterSpacing: 0.5,
                    cursor: 'pointer',
                    border: `1.5px solid ${selected ? color : 'var(--dark4)'}`,
                    background: selected ? `${color}1a` : 'transparent',
                    color: selected ? color : 'var(--gray2)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {tag.label}
                </button>
              )
            })}
          </div>
          <ErrMsg msg={errors.tags} />
        </div>

        {/* Description — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Description" required />
          <textarea
            className="inp"
            value={form.description}
            onChange={e => setField('description', e.target.value)}
            placeholder="Describe your event..."
            style={{ minHeight: 120, resize: 'vertical', lineHeight: 1.65 }}
          />
          <ErrMsg msg={errors.description} />
        </div>

        {/* Poster — full width */}
        <div style={{ gridColumn: '1 / -1' }}>
          <FieldLabel text="Poster" required />
          <ImageUpload
            value={form.poster_url}
            onChange={url => { setField('poster_url', url) }}
            error={errors.poster_url}
          />
        </div>

        {/* Contact Info */}
        <div>
          <FieldLabel text="Contact Info" required />
          <textarea
            className="inp"
            value={form.contact_info}
            onChange={e => setField('contact_info', e.target.value)}
            placeholder="Email, phone, or social handles for organizers"
            style={{ minHeight: 80, resize: 'vertical', lineHeight: 1.65 }}
          />
          <ErrMsg msg={errors.contact_info} />
        </div>

        {/* Registration Fee */}
        <div>
          <FieldLabel text="Registration Fee" required />
          <input
            className="inp"
            value={form.registration_fee}
            onChange={e => setField('registration_fee', e.target.value)}
            placeholder="e.g. ₹200 per team"
          />
          <ErrMsg msg={errors.registration_fee} />
        </div>

      </div>

      {/* Optional fields toggle */}
      <div style={{ marginTop: 28 }}>
        <button
          onClick={() => setShowOptional(s => !s)}
          style={{
            fontFamily: 'var(--mono)',
            fontSize: 11,
            color: 'var(--orange)',
            letterSpacing: 1,
            textTransform: 'uppercase',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 0,
            marginBottom: showOptional ? 22 : 0,
          }}
        >
          {showOptional ? '▲ Hide Additional Details' : '▼ Additional Details +'}
        </button>

        {showOptional && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '22px 28px' }}>
            <div>
              <FieldLabel text="Venue" />
              <input
                className="inp"
                value={form.venue}
                onChange={e => setField('venue', e.target.value)}
                placeholder="Leave empty for TBA"
              />
            </div>
            <div>
              <FieldLabel text="Time" />
              <input
                className="inp"
                value={form.time_info}
                onChange={e => setField('time_info', e.target.value)}
                placeholder="e.g. 10:00 AM - 5:00 PM"
              />
            </div>
            <div>
              <FieldLabel text="Prize Pool" />
              <input
                className="inp"
                value={form.prize_pool}
                onChange={e => setField('prize_pool', e.target.value)}
                placeholder="e.g. ₹50,000 total"
              />
            </div>
            <div>
              <FieldLabel text="Team Size" />
              <input
                className="inp"
                value={form.team_size}
                onChange={e => setField('team_size', e.target.value)}
                placeholder="e.g. 2-4 or Solo"
              />
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--dark3)' }}>
        <button onClick={handleSubmit} className="btn-p" disabled={submitting}>
          {submitting ? 'Publishing…' : 'Publish Event →'}
        </button>
        <button onClick={onCancel} className="btn-g">Cancel</button>
      </div>
    </div>
  )
}

// ── AdminPage ─────────────────────────────────────────────
export function AdminPage() {
  const { user } = useAuthStore()
  const { events, refresh } = useEvents()
  const navigate = useNavigate()
  const { toast } = useToastStore()
  const [showForm, setShowForm] = useState(false)
  const [clubId, setClubId] = useState<number | null>(null)
  const [regCounts, setRegCounts] = useState<Record<number, number>>({})
  const [discussions, setDiscussions] = useState<Discussion[]>([])
  const [discLoading, setDiscLoading] = useState(false)
  const [replyingTo, setReplyingTo] = useState<number | null>(null)
  const [replyContent, setReplyContent] = useState('')
  const [replySubmitting, setReplySubmitting] = useState(false)

  const myEvents = events.filter(e => e.club_name === user?.club_name)

  // Resolve club_id from club_name
  useEffect(() => {
    if (!user?.club_name) return
    clubsApi.list()
      .then(r => {
        const club = r.data.find((c: any) => c.name === user.club_name)
        if (club) setClubId(club.id)
      })
      .catch(() => {})
  }, [user?.club_name])

  // Fetch registration counts for each club event
  useEffect(() => {
    if (myEvents.length === 0) return
    Promise.all(
      myEvents.map(ev =>
        eventsApi.registrationCount(ev.id)
          .then((r: any) => ({ id: ev.id, count: typeof r.data === 'number' ? r.data : (r.data?.count ?? 0) }))
          .catch(() => ({ id: ev.id, count: 0 }))
      )
    ).then(results => {
      const map: Record<number, number> = {}
      results.forEach((r: any) => { map[r.id] = r.count })
      setRegCounts(map)
    })
  }, [myEvents.length])

  // Fetch discussion feed
  const fetchDiscussions = async () => {
    setDiscLoading(true)
    try {
      const r = await discussionsApi.adminFeed()
      setDiscussions(r.data)
    } catch {
      setDiscussions([])
    } finally {
      setDiscLoading(false)
    }
  }

  useEffect(() => {
    if (user?.role === 'member') fetchDiscussions()
  }, [user?.role])

  if (user?.role !== 'member') {
    return (
      <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--gray2)' }}>Admin access only</div>
      </div>
    )
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const totalRegs = Object.values(regCounts).reduce((a, b) => a + b, 0)
  const upcomingCount = myEvents.filter(e => new Date(e.start_date) >= today).length

  const timeAgo = (isoDate: string) => {
    const diff = Date.now() - new Date(isoDate).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  }

  const getEventTitle = (eventId: number) => {
    const ev = myEvents.find(e => e.id === eventId)
    return ev?.title ?? `Event #${eventId}`
  }

  const handleReply = async (disc: Discussion) => {
    if (!replyContent.trim()) return
    setReplySubmitting(true)
    try {
      await discussionsApi.reply(disc.event_id, disc.id, { content: replyContent.trim() })
      toast('Reply posted', 'success')
      setReplyingTo(null)
      setReplyContent('')
      fetchDiscussions()
    } catch (err: any) {
      toast(err?.response?.data?.detail ?? 'Failed to reply', 'error')
    } finally {
      setReplySubmitting(false)
    }
  }

  const handleDelete = async (disc: Discussion) => {
    try {
      await discussionsApi.delete(disc.event_id, disc.id)
      toast('Comment deleted', 'success')
      fetchDiscussions()
    } catch (err: any) {
      toast(err?.response?.data?.detail ?? 'Failed to delete', 'error')
    }
  }

  const handleFormSuccess = () => {
    setShowForm(false)
    refresh()
  }

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      {/* Header */}
      <div className="pg-hdr" style={{ padding: '40px 40px 32px' }}>
        <div style={{ position: 'relative', zIndex: 1, maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 8 }}>{user.club_name}</div>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
            <div>
              <h1 style={{ fontFamily: 'var(--head)', fontSize: 38, fontWeight: 800, letterSpacing: '-2px' }}>
                Club Dashboard<span style={{ color: 'var(--orange)' }}>.</span>
              </h1>
              <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginTop: 8 }}>{user.position} · {user.name}</p>
            </div>
            {!showForm && (
              <button
                onClick={() => setShowForm(true)}
                className="btn-p"
                disabled={!clubId}
                style={{ marginTop: 6, whiteSpace: 'nowrap', flexShrink: 0 }}
              >
                Post New Event +
              </button>
            )}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 40px' }}>

        {/* Event creation form */}
        {showForm && clubId !== null && (
          <EventCreateForm
            clubId={clubId}
            onSuccess={handleFormSuccess}
            onCancel={() => setShowForm(false)}
          />
        )}

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12, marginBottom: 36 }}>
          {[
            { label: 'Your Events',         val: myEvents.length },
            { label: 'Total Registrations', val: totalRegs },
            { label: 'Upcoming',            val: upcomingCount },
          ].map(s => (
            <div key={s.label} className="stat-card">
              <div style={{ fontFamily: 'var(--head)', fontSize: 36, fontWeight: 800, color: 'var(--orange)' }}>{s.val}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 2, marginTop: 4 }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Event list */}
        <div style={{ marginBottom: 44 }}>
          <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 14 }}>Your Events</div>
          {myEvents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', border: '1.5px dashed var(--dark4)', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', borderRadius: 12 }}>
              No events yet — click "Post New Event +" to create your first event.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {myEvents.map(ev => (
                <div key={ev.id} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '14px 18px', background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: `3px solid ${getEventColor(ev)}` }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: getEventColor(ev), minWidth: 60 }}>{ev.date_display}</div>
                  <div style={{ flex: 1 }}>
                    <button
                      onClick={() => navigate(`/events/${ev.id}`)}
                      style={{ fontFamily: 'var(--head)', fontSize: 14, fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--fg)', padding: 0, textAlign: 'left' }}
                    >
                      {ev.title}
                    </button>
                    <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', marginTop: 2 }}>{splitTags(ev.tags).join(' · ')}</div>
                  </div>
                  <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--gray2)', border: '1px solid var(--dark4)', padding: '2px 8px', whiteSpace: 'nowrap' }}>
                    {regCounts[ev.id] ?? '—'} registered
                  </span>
                  {ev.is_hot && <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: 'var(--orange)', border: '1px solid rgba(212,86,26,0.35)', padding: '2px 7px' }}>Hot</span>}
                  <span style={{ fontSize: 9, fontFamily: 'var(--mono)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', padding: '2px 7px' }}>Published</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Discussion feed */}
        <div>
          <div style={{ fontFamily: 'var(--head)', fontSize: 16, fontWeight: 700, marginBottom: 14 }}>Recent Discussions</div>
          {discLoading ? (
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', padding: '20px 0' }}>Loading…</div>
          ) : discussions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', border: '1.5px dashed var(--dark4)', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', borderRadius: 12 }}>
              No discussions yet
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {discussions.map(disc => (
                <div key={disc.id} style={{ background: 'var(--dark2)', border: '1px solid var(--dark3)', borderLeft: '3px solid var(--dark4)', padding: '14px 18px' }}>
                  {/* Meta row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <span style={{ fontFamily: 'var(--head)', fontSize: 13, fontWeight: 600 }}>{disc.user_name}</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: disc.user_role === 'member' ? 'var(--orange)' : 'var(--gray2)', border: `1px solid ${disc.user_role === 'member' ? 'rgba(212,86,26,0.35)' : 'var(--dark4)'}`, padding: '1px 6px', textTransform: 'uppercase', letterSpacing: 0.5 }}>{disc.user_role}</span>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', marginLeft: 'auto' }}>{timeAgo(disc.created_at)}</span>
                  </div>
                  {/* Event reference */}
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--gray2)', marginBottom: 8 }}>
                    on{' '}
                    <button
                      onClick={() => navigate(`/events/${disc.event_id}`)}
                      style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--orange)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                    >
                      {getEventTitle(disc.event_id)}
                    </button>
                  </div>
                  {/* Content */}
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--fg)', lineHeight: 1.65, marginBottom: 12 }}>
                    {disc.content.length > 200 ? disc.content.slice(0, 200) + '…' : disc.content}
                  </div>
                  {/* Actions */}
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <button
                      onClick={() => { setReplyingTo(replyingTo === disc.id ? null : disc.id); setReplyContent('') }}
                      style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', background: 'none', border: '1px solid rgba(212,86,26,0.4)', padding: '3px 12px', cursor: 'pointer' }}
                    >
                      {replyingTo === disc.id ? 'Cancel' : 'Reply'}
                    </button>
                    <button
                      onClick={() => handleDelete(disc)}
                      style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#ef4444', background: 'none', border: '1px solid rgba(239,68,68,0.3)', padding: '3px 12px', cursor: 'pointer' }}
                    >
                      Delete
                    </button>
                  </div>
                  {/* Inline reply input */}
                  {replyingTo === disc.id && (
                    <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                      <textarea
                        className="inp"
                        value={replyContent}
                        onChange={e => setReplyContent(e.target.value)}
                        placeholder="Write a reply…"
                        style={{ flex: 1, minHeight: 72, resize: 'vertical', lineHeight: 1.65, fontSize: 12 }}
                        autoFocus
                      />
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <button
                          onClick={() => handleReply(disc)}
                          className="btn-p"
                          disabled={replySubmitting || !replyContent.trim()}
                          style={{ fontSize: 11, padding: '7px 14px', whiteSpace: 'nowrap' }}
                        >
                          {replySubmitting ? '…' : 'Send →'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
