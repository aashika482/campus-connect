import { useState, useEffect } from 'react'
import { fetchAllClubs } from '@/hooks/useData'
import type { Club } from '@/types'

// Dropdown of every club (value = club id as a string, '' = none picked).
// Used where a committee member picks the club they run: sign-up, and re-applying.
export function ClubSelect({ value, onChange }: { value: string; onChange: (clubId: string) => void }) {
  const [clubs, setClubs] = useState<Club[]>([])
  const [state, setState] = useState<'loading' | 'idle' | 'error'>('loading')

  const load = () => {
    setState('loading')
    fetchAllClubs()   // the dropdown needs every club, so read all pages
      .then(all => { setClubs(all); setState('idle') })
      .catch(() => setState('error'))
  }
  useEffect(load, [])

  return (
    <div>
      <label style={{ display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 5 }}>Club</label>
      <select
        className="inp"
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={state !== 'idle'}
        style={{ cursor: 'pointer', color: value ? 'var(--cream)' : 'var(--gray2)' }}
      >
        <option value="" disabled>
          {state === 'loading' ? 'Loading clubs…' : 'Select your club'}
        </option>
        {clubs.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>
      {state === 'error' && (
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#EF4444', marginTop: 6 }}>
          Couldn't load clubs.{' '}
          <button onClick={load} style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textDecoration: 'underline', textUnderlineOffset: 3 }}>Retry</button>
        </div>
      )}
    </div>
  )
}
