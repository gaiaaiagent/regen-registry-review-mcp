/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { AUTH_UNAUTHORIZED_EVENT } from '@/lib/api'

export type UserRole = 'reviewer' | 'proponent'

export interface User {
  email: string
  name: string
  picture?: string
  role: UserRole
}

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  signIn: () => Promise<void>
  signInAsProponent: (email: string, password: string) => Promise<void>
  signOut: () => void
  handleOAuthCallback: (code: string) => Promise<string | undefined>
}

const AuthContext = createContext<AuthContextValue | null>(null)

const STORAGE_KEY_USER = 'auth_user'
const STORAGE_KEY_TOKEN = 'auth_token'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8003'

export function getAuthToken(): string | null {
  return localStorage.getItem(STORAGE_KEY_TOKEN)
}

/**
 * Mock proponent sign-in for development.
 * In production, this would verify credentials against a backend.
 */
const MOCK_PROPONENTS = [
  { email: 'proponent@example.com', password: 'demo123', name: 'Demo Proponent' },
  { email: 'test@carbonproject.org', password: 'demo123', name: 'Carbon Project Manager' },
]

async function stubProponentSignIn(
  email: string,
  password: string
): Promise<{ user: User; token: string }> {
  await new Promise((resolve) => setTimeout(resolve, 500))

  const proponent = MOCK_PROPONENTS.find(
    (p) => p.email === email && p.password === password
  )

  if (!proponent) {
    throw new Error('Invalid email or password')
  }

  const user: User = {
    email: proponent.email,
    name: proponent.name,
    picture: undefined,
    role: 'proponent',
  }

  const token = 'proponent-token-' + Date.now()
  return { user, token }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load persisted user on mount and validate session
  useEffect(() => {
    async function validateSession() {
      try {
        const storedUser = localStorage.getItem(STORAGE_KEY_USER)
        const storedToken = localStorage.getItem(STORAGE_KEY_TOKEN)

        if (storedUser && storedToken) {
          // Validate token with backend
          const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              Authorization: `Bearer ${storedToken}`,
            },
          })

          if (response.ok) {
            const data = await response.json()
            if (data.authenticated && data.user) {
              setUser(data.user)
            } else {
              // Token invalid, clear storage
              localStorage.removeItem(STORAGE_KEY_USER)
              localStorage.removeItem(STORAGE_KEY_TOKEN)
            }
          } else if (response.status === 401) {
            // Session expired
            localStorage.removeItem(STORAGE_KEY_USER)
            localStorage.removeItem(STORAGE_KEY_TOKEN)
          } else {
            // API error, use cached user (offline mode)
            setUser(JSON.parse(storedUser))
          }
        }
      } catch {
        // Network error - use cached user if available
        const storedUser = localStorage.getItem(STORAGE_KEY_USER)
        if (storedUser) {
          try {
            setUser(JSON.parse(storedUser))
          } catch {
            localStorage.removeItem(STORAGE_KEY_USER)
            localStorage.removeItem(STORAGE_KEY_TOKEN)
          }
        }
      } finally {
        setIsLoading(false)
      }
    }

    validateSession()
  }, [])

  // Listen for unauthorized events from API client
  useEffect(() => {
    function handleUnauthorized() {
      setUser(null)
      setError('Session expired. Please sign in again.')
      localStorage.removeItem(STORAGE_KEY_USER)
      localStorage.removeItem(STORAGE_KEY_TOKEN)
    }

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
    return () => {
      window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
    }
  }, [])

  const signIn = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Get the Google OAuth URL from the backend
      const response = await fetch(`${API_BASE}/auth/google/login`)
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to start authentication')
      }

      const { auth_url } = await response.json()

      // Redirect to Google OAuth
      window.location.href = auth_url
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Sign in failed'
      setError(message)
      setIsLoading(false)
      throw err
    }
  }, [])

  const handleOAuthCallback = useCallback(async (code: string): Promise<string | undefined> => {
    setIsLoading(true)
    setError(null)

    try {
      // Exchange the code for a session token
      const response = await fetch(`${API_BASE}/auth/google/callback?code=${encodeURIComponent(code)}`)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Authentication failed')
      }

      const { token, user: userData, redirect_to } = await response.json()

      // Validate email domain
      if (!userData.email.endsWith('@regen.network')) {
        throw new Error('Only @regen.network emails are allowed')
      }

      // Store auth state
      const newUser: User = {
        email: userData.email,
        name: userData.name,
        picture: userData.picture,
        role: userData.role as UserRole,
      }

      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(newUser))
      localStorage.setItem(STORAGE_KEY_TOKEN, token)
      setUser(newUser)

      return redirect_to
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Authentication failed'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const signInAsProponent = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const { user: newUser, token } = await stubProponentSignIn(email, password)

      // Persist auth state
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(newUser))
      localStorage.setItem(STORAGE_KEY_TOKEN, token)
      setUser(newUser)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Sign in failed'
      setError(message)
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const signOut = useCallback(async () => {
    const token = localStorage.getItem(STORAGE_KEY_TOKEN)

    // Call backend to invalidate session
    if (token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
      } catch {
        // Ignore errors - we're signing out anyway
      }
    }

    setUser(null)
    setError(null)
    localStorage.removeItem(STORAGE_KEY_USER)
    localStorage.removeItem(STORAGE_KEY_TOKEN)
  }, [])

  const value: AuthContextValue = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    error,
    signIn,
    signInAsProponent,
    signOut,
    handleOAuthCallback,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
