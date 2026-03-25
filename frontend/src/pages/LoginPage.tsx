import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import type { UserRole } from '@/types'

export function LoginPage() {
  const { login, isLoading } = useAuthStore()
  const { toast } = useToastStore()
  const navigate = useNavigate()

  const [role, setRole]     = useState<UserRole | null>(null)
  const [email, setEmail]   = useState('')
  const [password, setPass] = useState('')

  const handleSubmit = async () => {
    if (!role) return
    try {
      await login(email, password, role)
      toast(`Welcome back! 👋`, 'success')
      navigate('/')
    } catch (err: any) {
      toast(err?.response?.data?.detail ?? 'Login failed', 'error')
    }
  }

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

        {/* Role picker */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 10 }}>
            I am a <span style={{ color: 'var(--orange)' }}>*</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {([
              { id: 'student', lbl: 'Student',     sub: 'Discover events' },
              { id: 'member',  lbl: 'Club Member',  sub: 'Manage your club' },
            ] as const).map(x => (
              <button key={x.id}
                onClick={() => setRole(x.id)}
                style={{ padding: '18px 16px', border: `1.5px solid ${role === x.id ? 'var(--orange)' : 'var(--dark4)'}`, borderRadius: 12, background: role === x.id ? 'rgba(212,86,26,0.08)' : 'var(--dark2)', color: 'var(--cream)', transition: 'all 0.18s', textAlign: 'left' }}>
                <div style={{ fontSize: 13, fontWeight: 700, fontFamily: 'var(--head)', color: role === x.id ? 'var(--orange)' : 'var(--cream)' }}>{x.lbl}</div>
                <div style={{ fontSize: 10, color: 'var(--gray2)', fontFamily: 'var(--mono)', marginTop: 4 }}>{x.sub}</div>
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, opacity: role ? 1 : 0.28, transition: 'opacity 0.2s', pointerEvents: role ? 'auto' : 'none' }}>
          <div>
            <label style={{ display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 6 }}>Email</label>
            <input className="inp" placeholder="you@muj.manipal.edu" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 10, fontFamily: 'var(--mono)', textTransform: 'uppercase', letterSpacing: 3, color: 'var(--gray2)', marginBottom: 6 }}>Password</label>
            <input className="inp" type="password" placeholder="••••••••" value={password} onChange={e => setPass(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          </div>
          <button className="btn-p" style={{ width: '100%', marginTop: 4 }} disabled={isLoading || !role} onClick={handleSubmit}>
            {isLoading ? 'Signing in…' : 'Sign In →'}
          </button>
        </div>

        <div style={{ marginTop: 22, textAlign: 'center' }}>
          <span style={{ color: 'var(--gray2)', fontSize: 12, fontFamily: 'var(--mono)' }}>New here? </span>
          <Link to="/register" style={{ color: 'var(--orange)', fontWeight: 600, fontSize: 12, fontFamily: 'var(--mono)', textDecoration: 'underline', textUnderlineOffset: 3 }}>Create account</Link>
        </div>
      </div>
    </div>
  )
}
