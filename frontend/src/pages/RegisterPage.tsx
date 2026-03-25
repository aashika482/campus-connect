import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { ALL_TAGS } from '@/types'
import type { UserRole } from '@/types'

type Step = 0 | 1 | 2   // 0=pick role, 1=details, 2=interests (student only)

export function RegisterPage() {
  const { registerStudent, registerMember, isLoading } = useAuthStore()
  const { toast } = useToastStore()
  const navigate = useNavigate()

  const [role, setRole]   = useState<UserRole | null>(null)
  const [step, setStep]   = useState<Step>(0)
  const [interests, setInterests] = useState<string[]>([])
  const [form, setForm]   = useState({
    name: '', email: '', password: '', reg_no: '', course: '', phone: '',
    club_name: '', position: '',
  })
  const u = (k: string, v: string) => setForm(p => ({ ...p, [k]: v }))
  const ti = (id: string) => setInterests(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id])

  const handleSubmit = async () => {
    try {
      if (role === 'student') {
        await registerStudent({ ...form, interests, role: 'student' })
      } else {
        await registerMember({ ...form, role: 'member' })
      }
      toast('Welcome to CamPulse! 🎉', 'success')
      navigate('/')
    } catch (err: any) {
      toast(err?.response?.data?.detail ?? 'Registration failed', 'error')
    }
  }

  const field = (key: keyof typeof form, label: string, opts?: { placeholder?: string; type?: string }) => (
    <div>
      <label style={{ display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 5 }}>{label}</label>
      <input className="inp" type={opts?.type ?? 'text'} placeholder={opts?.placeholder ?? ''} value={form[key]} onChange={e => u(key, e.target.value)} />
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
      <div className="asi" style={{ width: '100%', maxWidth: 420 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontFamily: 'var(--syne)', fontSize: 28, fontWeight: 800, textTransform: 'uppercase' }}>
            <span style={{ color: 'var(--cream)' }}>Cam</span><span style={{ color: 'var(--orange)' }}>Pulse</span>
          </div>
        </div>

        {/* Step 0 — pick role */}
        {step === 0 && (
          <>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 9 }}>Join CamPulse</div>
            <h2 style={{ fontFamily: 'var(--head)', fontSize: 34, fontWeight: 800, letterSpacing: '-2px', marginBottom: 24 }}>I'm a<span style={{ color: 'var(--orange)' }}>…</span></h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 22 }}>
              {([
                { id: 'student', lbl: 'Student',     sub: 'Discover events, follow clubs, register for everything' },
                { id: 'member',  lbl: 'Club Member',  sub: 'Post events, manage membership, grow your community' },
              ] as const).map(x => (
                <button key={x.id} onClick={() => setRole(x.id)}
                  style={{ padding: '18px 16px', border: `1.5px solid ${role === x.id ? 'var(--orange)' : 'var(--dark4)'}`, borderRadius: 12, background: role === x.id ? 'rgba(212,86,26,0.08)' : 'var(--dark2)', color: 'var(--cream)', transition: 'all 0.18s', textAlign: 'left' }}>
                  <div style={{ fontSize: 14, fontWeight: 700, fontFamily: 'var(--head)', color: role === x.id ? 'var(--orange)' : 'var(--cream)' }}>{x.lbl}</div>
                  <div style={{ fontSize: 11, color: 'var(--gray2)', fontFamily: 'var(--mono)', marginTop: 4 }}>{x.sub}</div>
                </button>
              ))}
            </div>
            <button className="btn-p" style={{ width: '100%', opacity: role ? 1 : 0.33 }} disabled={!role} onClick={() => setStep(1)}>Continue →</button>
            <div style={{ marginTop: 18, textAlign: 'center' }}>
              <span style={{ color: 'var(--gray2)', fontSize: 12, fontFamily: 'var(--mono)' }}>Have an account? </span>
              <Link to="/login" style={{ color: 'var(--orange)', fontWeight: 600, fontSize: 12, fontFamily: 'var(--mono)', textDecoration: 'underline', textUnderlineOffset: 3 }}>Log in</Link>
            </div>
          </>
        )}

        {/* Step 1 — details */}
        {step === 1 && (
          <>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 9 }}>
              {role === 'student' ? 'Step 1 of 2' : 'Step 1 of 1'}
            </div>
            <h2 style={{ fontFamily: 'var(--head)', fontSize: 34, fontWeight: 800, letterSpacing: '-2px', marginBottom: 20 }}>
              Details<span style={{ color: 'var(--orange)' }}>.</span>
            </h2>

            {/* Step progress bar */}
            <div style={{ display: 'flex', gap: 5, marginBottom: 22 }}>
              <div style={{ flex: 1, height: 2, background: 'var(--orange)' }} />
              {role === 'student' && <div style={{ flex: 1, height: 2, background: 'var(--dark4)' }} />}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
              {field('name', 'Full Name', { placeholder: 'Your name' })}
              {field('email', 'Email', { placeholder: 'you@muj.manipal.edu' })}
              {field('password', 'Password', { placeholder: '••••••••', type: 'password' })}

              {role === 'student' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  {field('reg_no', 'Reg No.', { placeholder: '219301XXX' })}
                  {field('course', 'Course', { placeholder: 'B.Tech CSE' })}
                </div>
              )}

              {role === 'member' && (
                <>
                  {field('club_name', 'Club Name', { placeholder: 'ACM Student Chapter' })}
                  {field('position', 'Position', { placeholder: 'President, Coordinator…' })}
                </>
              )}
            </div>

            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button className="btn-g" onClick={() => setStep(0)}>← Back</button>
              {role === 'student'
                ? <button className="btn-p" style={{ flex: 1 }} onClick={() => setStep(2)}>Continue →</button>
                : <button className="btn-p" style={{ flex: 1 }} disabled={isLoading} onClick={handleSubmit}>{isLoading ? 'Creating…' : 'Create Account →'}</button>
              }
            </div>
          </>
        )}

        {/* Step 2 — interests (student only) */}
        {step === 2 && role === 'student' && (
          <>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 9 }}>Step 2 of 2</div>
            <h2 style={{ fontFamily: 'var(--head)', fontSize: 34, fontWeight: 800, letterSpacing: '-2px', marginBottom: 8 }}>
              Interests<span style={{ color: 'var(--orange)' }}>.</span>
            </h2>
            <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginBottom: 20 }}>Pick what excites you — we'll personalise your feed.</p>

            {/* Progress bar */}
            <div style={{ display: 'flex', gap: 5, marginBottom: 22 }}>
              <div style={{ flex: 1, height: 2, background: 'var(--orange)' }} />
              <div style={{ flex: 1, height: 2, background: 'var(--orange)' }} />
            </div>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 24 }}>
              {ALL_TAGS.map(t => {
                const on = interests.includes(t.id)
                return (
                  <button key={t.id} onClick={() => ti(t.id)}
                    style={{ padding: '8px 14px', fontSize: 11, fontFamily: 'var(--mono)', border: `1.5px solid ${on ? 'var(--orange)' : 'var(--dark4)'}`, borderRadius: 20, background: on ? 'rgba(212,86,26,0.12)' : 'transparent', color: on ? 'var(--orange)' : 'var(--gray2)', transition: 'all 0.15s', letterSpacing: 0.5 }}>
                    {t.label}
                  </button>
                )
              })}
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn-g" onClick={() => setStep(1)}>← Back</button>
              <button className="btn-p" style={{ flex: 1 }} disabled={isLoading} onClick={handleSubmit}>
                {isLoading ? 'Creating…' : 'Finish →'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
