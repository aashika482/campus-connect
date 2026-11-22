import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import type { SecondStep } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { authApi, apiError } from '@/api/client'
import { MicrosoftButton } from '@/components/ui/MicrosoftButton'

export function LoginPage() {
  const { login, verify, isLoading } = useAuthStore()
  const { toast } = useToastStore()
  const navigate = useNavigate()

  const [email, setEmail]   = useState('')
  const [password, setPass] = useState('')
  const [step, setStep]     = useState<SecondStep | null>(null)   // after a correct password
  const [code, setCode]     = useState('')
  const [remember, setRemember] = useState(true)
  const welcome = () => { toast('Welcome back! 👋', 'success'); navigate('/') }

  const handleSubmit = async () => {
    try {
      const next = await login(email, password)
      if (next) setStep(next)
      else welcome()
    } catch (err) {
      toast(apiError(err, 'Login failed'), 'error')
    }
  }
  const handleVerify = async () => {
    try {
      await verify(step!.challenge, code.trim(), remember)
      welcome()
    } catch (err) {
      toast(apiError(err, 'That code didn\'t work'), 'error')
    }
  }
  const emailMeACode = async () => {
    try {
      await authApi.loginEmailCode(step!.challenge)
      setStep(s => (s ? { ...s, method: 'email' } : s))
      toast(`Code sent to ${email}`, 'success')
    } catch (err) {
      toast(apiError(err, 'Could not send a code'), 'error')
    }
  }
  const label: React.CSSProperties = { display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 6 }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="asi" style={{ width: '100%', maxWidth: 400, padding: '0 24px' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{ fontFamily: 'var(--syne)', fontSize: 32, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '-1px' }}>
            <span style={{ color: 'var(--cream)' }}>Cam</span>
            <span style={{ color: 'var(--orange)' }}>Pulse</span>
          </div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--gray2)', textTransform: 'uppercase', letterSpacing: 3, marginTop: 6 }}>
            Campus Life Discovery
          </div>
        </div>

        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--orange)', textTransform: 'uppercase', letterSpacing: 4, marginBottom: 9 }}>Welcome back</div>
        <h2 style={{ fontFamily: 'var(--head)', fontSize: 38, fontWeight: 800, letterSpacing: '-2px', marginBottom: 26 }}>
          Sign In<span style={{ color: 'var(--orange)' }}>.</span>
        </h2>

        {step ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', lineHeight: 1.6 }}>
              {step.method === 'totp' ? 'Enter the 6-digit code from your authenticator app.' : `We emailed a 6-digit code to ${email}. It works for 10 minutes.`}
            </div>
            <div>
              <label style={label}>Code</label>
              <input className="inp" inputMode="numeric" autoFocus maxLength={6} placeholder="123456" value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, ''))} onKeyDown={e => e.key === 'Enter' && code.length === 6 && handleVerify()} />
            </div>
            <label style={{ display: 'flex', gap: 8, alignItems: 'center', fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', cursor: 'pointer' }}>
              <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} style={{ accentColor: 'var(--orange)' }} />
              Don't ask again on this browser for 30 days
            </label>
            <button className="btn-p" style={{ width: '100%' }} disabled={isLoading || code.length !== 6} onClick={handleVerify}>
              {isLoading ? 'Checking…' : 'Sign In →'}
            </button>
            <button onClick={emailMeACode} style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', textDecoration: 'underline' }}>
              {step.method === 'totp' ? 'No access to the app? Email me a code' : 'Send a new code'}
            </button>
            <button onClick={() => { setStep(null); setCode('') }} style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)' }}>← Back</button>
          </div>
        ) : <>
        <MicrosoftButton onSignedIn={welcome} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label style={{ display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 6 }}>Email</label>
            <input className="inp" placeholder="Your college email" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 6 }}>Password</label>
            <input className="inp" type="password" placeholder="••••••••" value={password} onChange={e => setPass(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          </div>
          <button className="btn-p" style={{ width: '100%', marginTop: 4 }} disabled={isLoading || !email || !password} onClick={handleSubmit}>
            {isLoading ? 'Signing in…' : 'Sign In →'}
          </button>
        </div>
        </>}

        <div style={{ marginTop: 22, textAlign: 'center' }}>
          <span style={{ color: 'var(--gray2)', fontSize: 12, fontFamily: 'var(--mono)' }}>New here? </span>
          <Link to="/register" style={{ color: 'var(--orange)', fontWeight: 600, fontSize: 12, fontFamily: 'var(--mono)', textDecoration: 'underline', textUnderlineOffset: 3 }}>Create account</Link>
        </div>
      </div>
    </div>
  )
}
