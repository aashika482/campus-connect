import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import { useToastStore } from '@/context/toastStore'
import { Nav } from '@/components/layout/Nav'
import { ToastContainer } from '@/components/ui/Toast'

// Pages (lazy-ish — just direct imports for now)
import { LoginPage }    from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { HomePage }     from '@/pages/HomePage'
import { EventsPage }   from '@/pages/EventsPage'
import { ClubsPage }    from '@/pages/ClubsPage'
import { SavedPage, ProfilePage, CalendarPage, AdminPage } from '@/pages/OtherPages'




import type { Event, Club } from '@/types'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isInitialized } = useAuthStore()
  if (!isInitialized) return <LoadingScreen />
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function LoadingScreen() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--gray2)', letterSpacing: 3, textTransform: 'uppercase' }}>
        Loading…
      </div>
    </div>
  )
}

export default function App() {
  const { initFromStorage, user, isInitialized } = useAuthStore()
  const { toast } = useToastStore()

  // Modal state — lifted here so Nav can open modals from search
  const [viewEv,   setViewEv]   = useState<Event | null>(null)
  const [viewClub, setViewClub] = useState<Club  | null>(null)

  useEffect(() => { initFromStorage() }, [])

  // Keyboard shortcut: Cmd/Ctrl+K → open search (handled in Nav itself)
  // Escape to close modals
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { setViewEv(null); setViewClub(null) }
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [])

  if (!isInitialized) return <LoadingScreen />

  return (
    <>
      <div className="grain-global" />

      {user && (
        <Nav
          onViewEvent={setViewEv}
          onViewClub={setViewClub}
        />
      )}

      <div style={user ? { paddingTop: 60 } : {}}>
        <Routes>
          {/* Public */}
          <Route path="/login"    element={!user ? <LoginPage />    : <Navigate to="/" replace />} />
          <Route path="/register" element={!user ? <RegisterPage /> : <Navigate to="/" replace />} />

          {/* Protected */}
          <Route path="/" element={
            <ProtectedRoute>
              <HomePage onViewEvent={setViewEv} />
            </ProtectedRoute>
          } />
          <Route path="/events" element={
            <ProtectedRoute>
              <EventsPage onViewEvent={setViewEv} />
            </ProtectedRoute>
          } />
          <Route path="/clubs" element={
            <ProtectedRoute>
              <ClubsPage onViewClub={setViewClub} />
            </ProtectedRoute>
          } />
          <Route path="/saved" element={
            <ProtectedRoute>
              <SavedPage onViewEvent={setViewEv} />
            </ProtectedRoute>
          } />
          <Route path="/calendar" element={
            <ProtectedRoute>
              <CalendarPage onViewEvent={setViewEv} />
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute>
              <AdminPage />
            </ProtectedRoute>
          } />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>

      {/* Global modals would go here — wire EventModal & ClubModal from your prototype */}
      {/* <EventModal ev={viewEv} onClose={() => setViewEv(null)} ... /> */}
      {/* <ClubModal  club={viewClub} onClose={() => setViewClub(null)} ... /> */}

      <ToastContainer />
    </>
  )
}
