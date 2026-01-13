import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { FileText, Loader2 } from 'lucide-react'

export function LoginPage() {
  const { isAuthenticated, isLoading, error, signIn } = useAuth()
  const [signingIn, setSigningIn] = useState(false)
  const location = useLocation()

  // Get the intended destination from router state, default to home
  const from = (location.state as { from?: string })?.from || '/'

  // If already authenticated, redirect to intended destination
  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  async function handleSignIn() {
    setSigningIn(true)
    try {
      await signIn()
    } catch {
      // Error is handled by AuthContext
    } finally {
      setSigningIn(false)
    }
  }

  const isButtonDisabled = isLoading || signingIn

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo and Title */}
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="rounded-full bg-primary/10 p-3">
              <FileText className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Registry Review
          </h1>
          <p className="text-sm text-muted-foreground">
            Carbon credit project verification workspace
          </p>
        </div>

        {/* Sign In Card */}
        <div className="rounded-lg border bg-card p-6 shadow-sm space-y-4">
          <div className="text-center space-y-1">
            <h2 className="text-lg font-medium">Sign in to continue</h2>
            <p className="text-sm text-muted-foreground">
              Access restricted to @regen.network emails
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Sign In Button */}
          <button
            onClick={handleSignIn}
            disabled={isButtonDisabled}
            className="w-full flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {signingIn ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <GoogleIcon className="h-4 w-4" />
                Sign in with Google
              </>
            )}
          </button>
        </div>

        {/* Development Notice */}
        <p className="text-center text-xs text-muted-foreground">
          Development mode: Sign in uses mock authentication
        </p>
      </div>
    </div>
  )
}

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  )
}
