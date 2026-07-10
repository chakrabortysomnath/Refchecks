import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { useLocation, useNavigate, Navigate } from 'react-router-dom'
import { loginWithGoogle } from '../api/auth'
import { useAuth } from './AuthContext'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const from = (location.state as { from?: string } | null)?.from ?? '/'

  // Already signed in — bounce to where they were headed.
  if (user) return <Navigate to={from} replace />

  return (
    <div className="min-h-full flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 p-8 text-center">
        <div className="text-4xl">⚽</div>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">RefChecks</h1>
        <p className="mt-1 text-sm text-slate-500">
          Football refereeing bias analysis
        </p>

        <div className="mt-8 flex flex-col items-center gap-4">
          {!GOOGLE_CLIENT_ID ? (
            <p className="text-sm text-red-600">
              Google sign-in is not configured. Set{' '}
              <code>VITE_GOOGLE_CLIENT_ID</code> and rebuild.
            </p>
          ) : busy ? (
            <div className="flex items-center gap-2 text-slate-500">
              <span className="h-4 w-4 rounded-full border-2 border-slate-300 border-t-pitch-600 animate-spin" />
              Signing in…
            </div>
          ) : (
            <GoogleLogin
              onSuccess={async (cred) => {
                if (!cred.credential) {
                  setError('No credential returned by Google.')
                  return
                }
                setBusy(true)
                setError(null)
                try {
                  const res = await loginWithGoogle(cred.credential)
                  login(res.access_token, res.user)
                  navigate(from, { replace: true })
                } catch (e) {
                  setError(e instanceof Error ? e.message : 'Login failed.')
                  setBusy(false)
                }
              }}
              onError={() => setError('Google sign-in failed.')}
            />
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      </div>

      <p className="mt-6 text-xs text-slate-400">
        Sign in with Google to view the bias analysis dashboard.
      </p>
    </div>
  )
}
