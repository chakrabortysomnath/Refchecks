import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { getToken, setToken as persistToken } from '../api/client'
import { fetchMe } from '../api/auth'
import type { User } from '../api/types'

interface AuthState {
  user: User | null
  /** True while restoring a session from a stored token on first load. */
  loading: boolean
  login: (token: string, user: User) => void
  logout: () => void
}

const AuthContext = createContext<AuthState | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // On mount, if a JWT is stored, validate it by fetching the current user.
  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    fetchMe()
      .then(setUser)
      .catch(() => {
        // Token invalid/expired — clear it.
        persistToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = (token: string, u: User) => {
    persistToken(token)
    setUser(u)
  }

  const logout = () => {
    persistToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
