import { useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/context/authStore'
import { Nav } from '@/components/layout/Nav'
import { ToastContainer } from '@/components/ui/Toast'

// Pages
import { LoginPage }    from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { HomePage }     from '@/pages/HomePage'
import { EventsPage }   from '@/pages/EventsPage'
import { ClubsPage }    from '@/pages/ClubsPage'
import { EventDetailPage } from '@/pages/EventDetailPage'
import { ClubDetailPage }  from '@/pages/ClubDetailPage'
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
  const navigate = useNavigate()

  const handleViewEvent = (ev: Event) => navigate(`/events/${ev.id}`)
  const handleViewClub  = (cl: Club)  => navigate(`/clubs/${cl.id}`)

  useEffect(() => { initFromStorage() }, [])

  if (!isInitialized) return <LoadingScreen />

  return (
    <>
      <div className="grain-global" />

      {user && (
        <Nav
          onViewEvent={handleViewEvent}
          onViewClub={handleViewClub}
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
              <HomePage onViewEvent={handleViewEvent} />
            </ProtectedRoute>
          } />
          <Route path="/events" element={
            <ProtectedRoute>
              <EventsPage onViewEvent={handleViewEvent} />
            </ProtectedRoute>
          } />
          <Route path="/events/:id" element={
            <ProtectedRoute>
              <EventDetailPage />
            </ProtectedRoute>
          } />
          <Route path="/clubs" element={
            <ProtectedRoute>
              <ClubsPage onViewClub={handleViewClub} />
            </ProtectedRoute>
          } />
          <Route path="/clubs/:id" element={
            <ProtectedRoute>
              <ClubDetailPage />
            </ProtectedRoute>
          } />
          <Route path="/saved" element={
            <ProtectedRoute>
              <SavedPage onViewEvent={handleViewEvent} />
            </ProtectedRoute>
          } />
          <Route path="/calendar" element={
            <ProtectedRoute>
              <CalendarPage onViewEvent={handleViewEvent} />
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

      <ToastContainer />
    </>
  )
}
