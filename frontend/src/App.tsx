import { Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './auth/LoginPage'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      {/* Unknown routes fall back to the dashboard (which redirects to login
          if unauthenticated). */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
