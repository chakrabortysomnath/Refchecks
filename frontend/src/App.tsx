import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './auth/LoginPage'
import Dashboard from './pages/Dashboard'

/**
 * Google auth is deferred to a later phase. The bias-analysis data endpoints
 * are public, so the dashboard renders without login for now.
 *
 * The auth stack (GoogleOAuthProvider, AuthProvider, LoginPage, ProtectedRoute)
 * is kept in the codebase so the login gate can be re-enabled by wrapping the
 * "/" route in <ProtectedRoute> again once Google OAuth config is sorted.
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      {/* Login page is reachable but not required yet. */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
