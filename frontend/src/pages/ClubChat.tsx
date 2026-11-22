// A club's working-team chat (shown on the club page to its working team).
// History comes over HTTP; new and deleted messages arrive live over a WebSocket. If the socket
// drops, the panel checks for new messages every few seconds and keeps trying to reconnect
// (refreshing the sign-in first, since an access token only lasts 30 minutes).
import { useState, useEffect, useRef } from 'react'
import { chatApi, usersApi, apiError, WS_BASE } from '@/api/client'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { getTimeAgo } from '@/types'
import type { ChatMessage } from '@/types'

type Status = 'connecting' | 'live' | 'offline'

export function ClubChat({ clubId, canModerate }: { clubId: number; canModerate: boolean }) {
  const { user } = useAuthStore()
  const { toast } = useToastStore()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [hasMore, setHasMore] = useState(false)
  const [status, setStatus] = useState<Status>('connecting')
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const atBottom = useRef(true)   // only follow new messages if the reader is already at the bottom

  const add = (incoming: ChatMessage[]) => setMessages(prev => {
    const seen = new Set(prev.map(m => m.id))
    return [...prev, ...incoming.filter(m => !seen.has(m.id))].sort((a, b) => a.id - b.id)
  })
  const lastIdRef = useRef(0)   // newest message we have, for catching up after a dropped connection
  lastIdRef.current = messages[messages.length - 1]?.id ?? 0

  // History
  useEffect(() => {
    setMessages([])
    chatApi.history(clubId).then(r => { setMessages(r.data.items); setHasMore(r.data.has_more) }).catch(() => {})
  }, [clubId])

  // Live updates
  useEffect(() => {
    let ws: WebSocket | null = null
    let ping: number | undefined
    let retry: number | undefined
    let stopped = false

    const connect = () => {
      setStatus('connecting')
      ws = new WebSocket(`${WS_BASE}/clubs/${clubId}/chat/ws`)
      ws.onopen = () => ws?.send(JSON.stringify({ token: localStorage.getItem('access_token') }))
      ws.onmessage = e => {
        const data = JSON.parse(e.data)
        if (data.type === 'ready') {
          setStatus('live')
          // Catch up on anything sent while we were away
          chatApi.history(clubId, { after_id: lastIdRef.current }).then(r => add(r.data.items)).catch(() => {})
        } else if (data.type === 'message') add([data.message])
        else if (data.type === 'deleted') setMessages(p => p.filter(m => m.id !== data.id))
      }
      ws.onclose = e => {
        window.clearInterval(ping)
        if (stopped) return
        setStatus('offline')
        if (e.code === 4403) return   // not on the working team any more
        // Refresh the sign-in (the request does it if the token expired), then try again
        retry = window.setTimeout(() => { usersApi.me().catch(() => {}).finally(() => !stopped && connect()) }, 3000)
      }
      ping = window.setInterval(() => ws?.readyState === WebSocket.OPEN && ws.send('ping'), 25000)
    }
    connect()
    return () => { stopped = true; window.clearInterval(ping); window.clearTimeout(retry); ws?.close() }
  }, [clubId])

  // While offline, poll so nothing is missed
  useEffect(() => {
    if (status !== 'offline') return
    const t = window.setInterval(() => {
      chatApi.history(clubId, { after_id: lastIdRef.current }).then(r => add(r.data.items)).catch(() => {})
    }, 5000)
    return () => window.clearInterval(t)
  }, [status, clubId])

  // Follow new messages
  useEffect(() => {
    const el = listRef.current
    if (el && atBottom.current) el.scrollTop = el.scrollHeight
  }, [messages])

  const loadOlder = async () => {
    const el = listRef.current
    const before = el?.scrollHeight ?? 0
    try {
      const r = await chatApi.history(clubId, { before_id: messages[0]?.id })
      atBottom.current = false
      setMessages(p => [...r.data.items, ...p])
      setHasMore(r.data.has_more)
      requestAnimationFrame(() => { if (el) el.scrollTop = el.scrollHeight - before })   // keep the reader's place
    } catch { toast('Could not load older messages', 'error') }
  }

  const send = async () => {
    const body = draft.trim()
    if (!body) return
    setSending(true)
    try {
      const r = await chatApi.send(clubId, body)
      atBottom.current = true
      add([r.data])   // the socket may deliver it too; add() ignores duplicates
      setDraft('')
    } catch (err) {
      toast(apiError(err, 'Message not sent'), 'error')
    } finally {
      setSending(false)
    }
  }

  const remove = async (m: ChatMessage) => {
    try {
      await chatApi.delete(clubId, m.id)
      setMessages(p => p.filter(x => x.id !== m.id))
    } catch (err) { toast(apiError(err, 'Could not delete'), 'error') }
  }

  const small: React.CSSProperties = { fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)' }
  const dot = { live: '#22C55E', connecting: '#EAB308', offline: '#EF4444' }[status]
  return (
    <div style={{ maxWidth: 720, border: '1px solid var(--dark3)', borderRadius: 12, background: 'var(--dark2)', overflow: 'hidden' }}>
      <div style={{ ...small, display: 'flex', alignItems: 'center', gap: 6, padding: '10px 14px', borderBottom: '1px solid var(--dark3)' }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', background: dot }} />
        {status === 'live' ? 'Live' : status === 'connecting' ? 'Connecting…' : 'Reconnecting… (new messages still arrive every few seconds)'}
      </div>

      <div ref={listRef} onScroll={e => { const el = e.currentTarget; atBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40 }}
        style={{ height: 360, overflowY: 'auto', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {hasMore && (
          <button className="btn-g" onClick={loadOlder} style={{ alignSelf: 'center', padding: '6px 14px', fontSize: 10 }}>Load older messages</button>
        )}
        {messages.length === 0 && <div style={{ ...small, margin: 'auto' }}>No messages yet. Say hello to the team.</div>}
        {messages.map(m => {
          const mine = m.author_id === user?.id
          return (
            <div key={m.id} style={{ alignSelf: mine ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
              <div style={{ ...small, textAlign: mine ? 'right' : 'left', marginBottom: 3 }}>
                {mine ? 'You' : m.author_name ?? 'Former member'} · {getTimeAgo(m.created_at)}
                {(mine || canModerate) && (
                  <button onClick={() => remove(m)} style={{ ...small, marginLeft: 6, textDecoration: 'underline' }}>Delete</button>
                )}
              </div>
              <div style={{ padding: '8px 12px', borderRadius: 10, fontFamily: 'var(--body)', fontSize: 13.5, lineHeight: 1.5,
                            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                            background: mine ? 'rgba(212,86,26,0.14)' : 'var(--dark3)', color: 'var(--cream)' }}>
                {m.body}
              </div>
            </div>
          )
        })}
      </div>

      <div style={{ display: 'flex', gap: 8, padding: 10, borderTop: '1px solid var(--dark3)' }}>
        <textarea className="inp" value={draft} rows={1} maxLength={2000} onChange={e => setDraft(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (!sending) send() } }}
          placeholder="Message the working team… (Shift+Enter for a new line)" style={{ flex: 1, fontSize: 13, resize: 'none' }} />
        <button className="btn-p" disabled={sending || !draft.trim()} onClick={send} style={{ padding: '9px 16px', fontSize: 10 }}>Send</button>
      </div>
    </div>
  )
}
