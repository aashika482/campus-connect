import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import { authApi, apiError } from '@/api/client'
import { useToastStore } from '@/context/toastStore'
import { ALL_TAGS } from '@/types'

type Step = 1 | 2   // 1 = details, 2 = interests (students only)
type Domains = { student: string[]; faculty: string[] }

export function RegisterPage() {
  const { register, isLoading } = useAuthStore()
  const { toast } = useToastStore()
  const navigate = useNavigate()

  const [step, setStep]   = useState<Step>(1)
  const [interests, setInterests] = useState<string[]>([])
  const [form, setForm]   = useState({ name: '', email: '', password: '', reg_no: '', course: '', phone: '' })
  const u = (k: string, v: string) => setForm(p => ({ ...p, [k]: v }))

  // Which college domains can sign up comes from the server (env config), never hardcoded here
  const [domains, setDomains] = useState<Domains | null>(null)
  useEffect(() => { authApi.config().then(r => setDomains(r.data.email_domains)).catch(() => {}) }, [])
  const emailDomain = form.email.trim().toLowerCase().split('@')[1] ?? ''
  const kind = !domains || !emailDomain ? null
    : domains.student.includes(emailDomain) ? 'student'
    : domains.faculty.includes(emailDomain) ? 'faculty'
    : 'other'
  const isStudent = kind === 'student'

  // Same rule as the backend: spaces, dashes and a +91 / 0 prefix are fine, then 10 digits
  const phoneDigits = form.phone.replace(/[\s\-()]/g, '').replace(/^(\+91|0)/, '')
  const phoneValid = /^\d{10}$/.test(phoneDigits)
  const [phoneTouched, setPhoneTouched] = useState(false)
  const ti = (id: string) => setInterests(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id])
  const detailsOk = form.name.trim() && form.password && phoneValid && (kind === 'student' || kind === 'faculty')

  const handleSubmit = async () => {
    try {
      await register({ ...form, interests: isStudent ? interests : [] })
      toast('Welcome to CamPulse! 🎉', 'success')
      navigate('/')
    } catch (err) {
      toast(apiError(err, 'Registration failed'), 'error')
    }
  }

  const field = (key: keyof typeof form, label: string, opts?: { placeholder?: string; type?: string }) => (
    <div>
      <label style={{ display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 5 }}>{label}</label>
      <input className="inp" type={opts?.type ?? 'text'} placeholder={opts?.placeholder ?? ''} value={form[key]} onChange={e => u(key, e.target.value)} />
    </div>
  )
  const hint = (text: string, color = 'var(--gray2)') => (
    <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color, marginTop: 5 }}>{text}</div>
  )
  const allDomains = domains ? [...domains.student, ...domains.faculty].map(d => `@${d}`).join(' or ') : 'your college email'

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 24px' }}>
      <div className="asi" style={{ width: '100%', maxWidth: 420 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontFamily: 'var(--syne)', fontSize: 28, fontWeight: 800, textTransform: 'uppercase' }}>
            <span style={{ color: 'var(--cream)' }}>Cam</span><span style={{ color: 'var(--orange)' }}>Pulse</span>
          </div>
        </div>

        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 9 }}>
          {isStudent ? `Step ${step} of 2` : 'Join CamPulse'}
        </div>
        <h2 style={{ fontFamily: 'var(--head)', fontSize: 34, fontWeight: 800, letterSpacing: '-2px', marginBottom: step === 2 ? 8 : 20 }}>
          {step === 1 ? 'Details' : 'Interests'}<span style={{ color: 'var(--orange)' }}>.</span>
        </h2>

        {/* Step progress bar (students have an interests step) */}
        {isStudent && (
          <div style={{ display: 'flex', gap: 5, marginBottom: 22 }}>
            <div style={{ flex: 1, height: 2, background: 'var(--orange)' }} />
            <div style={{ flex: 1, height: 2, background: step === 2 ? 'var(--orange)' : 'var(--dark4)' }} />
          </div>
        )}

        {/* Step 1 — details */}
        {step === 1 && (
          <>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
              {field('name', 'Full Name', { placeholder: 'Your name' })}
              <div>
                {field('email', 'College Email', { placeholder: domains ? `you@${domains.student[0]}` : 'you@college.edu' })}
                {kind === 'other' && hint(`Use ${allDomains}`, '#EF4444')}
                {kind === 'student' && hint('Signing up as a student')}
                {kind === 'faculty' && hint('Signing up as faculty / staff')}
              </div>
              {field('password', 'Password', { placeholder: '••••••••', type: 'password' })}
              <div onBlur={() => setPhoneTouched(true)}>
                {field('phone', 'Phone Number', { placeholder: '98765 43210', type: 'tel' })}
                {phoneTouched && form.phone && !phoneValid && hint('Enter a valid 10-digit phone number', '#EF4444')}
              </div>

              {isStudent && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  {field('reg_no', 'Reg No.', { placeholder: '219301XXX' })}
                  {field('course', 'Course', { placeholder: 'B.Tech CSE' })}
                </div>
              )}
            </div>

            <div style={{ marginTop: 20 }}>
              {isStudent
                ? <button className="btn-p" style={{ width: '100%' }} disabled={!detailsOk} onClick={() => setStep(2)}>Continue →</button>
                : <button className="btn-p" style={{ width: '100%' }} disabled={isLoading || !detailsOk} onClick={handleSubmit}>{isLoading ? 'Creating…' : 'Create Account →'}</button>
              }
            </div>
            <div style={{ marginTop: 18, textAlign: 'center' }}>
              <span style={{ color: 'var(--gray2)', fontSize: 12, fontFamily: 'var(--mono)' }}>Have an account? </span>
              <Link to="/login" style={{ color: 'var(--orange)', fontWeight: 600, fontSize: 12, fontFamily: 'var(--mono)', textDecoration: 'underline', textUnderlineOffset: 3 }}>Log in</Link>
            </div>
          </>
        )}

        {/* Step 2 — interests (students only) */}
        {step === 2 && (
          <>
            <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', marginBottom: 20 }}>Pick what excites you — we'll personalise your feed.</p>
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
