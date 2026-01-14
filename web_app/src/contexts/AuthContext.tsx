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
}

const AuthContext = createContext<AuthContextValue | null>(null)

const STORAGE_KEY_USER = 'auth_user'
const STORAGE_KEY_TOKEN = 'auth_token'

/**
 * Stub implementation for development.
 * In production, this would call a backend endpoint that verifies
 * the Google ID token and returns a session token.
 */
async function stubGoogleSignIn(): Promise<{ user: User; token: string }> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  // For development, create a mock user with @regen.network email
  const mockUser: User = {
    email: 'developer@regen.network',
    name: 'Development User',
    picture: undefined,
    role: 'reviewer',
  }

  // Mock token - in production this would come from the backend
  const mockToken = 'dev-token-' + Date.now()

  return { user: mockUser, token: mockToken }
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
  // Simulate network delay
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

  // Load persisted user on mount
  useEffect(() => {
    try {
      const storedUser = localStorage.getItem(STORAGE_KEY_USER)
      const storedToken = localStorage.getItem(STORAGE_KEY_TOKEN)
      if (storedUser && storedToken) {
        setUser(JSON.parse(storedUser))
      }
    } catch {
      // Invalid stored data, clear it
      localStorage.removeItem(STORAGE_KEY_USER)
      localStorage.removeItem(STORAGE_KEY_TOKEN)
    } finally {
      setIsLoading(false)
    }
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
      const { user: newUser, token } = await stubGoogleSignIn()

      // Validate email domain
      if (!newUser.email.endsWith('@regen.network')) {
        throw new Error('Only @regen.network emails are allowed')
      }

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

  const signOut = useCallback(() => {
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
