import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { handleOAuthCallback, error } = useAuth()
  const [status, setStatus] = useState<'processing' | 'error'>('processing')

  useEffect(() => {
    async function handleCallback() {
      const code = searchParams.get('code')
      const errorParam = searchParams.get('error')

      if (errorParam) {
        setStatus('error')
        return
      }

      if (!code) {
        setStatus('error')
        return
      }

      try {
        const redirectTo = await handleOAuthCallback(code)
        // Navigate to the original destination or dashboard
        navigate(redirectTo || '/', { replace: true })
      } catch {
        setStatus('error')
      }
    }

    handleCallback()
  }, [searchParams, handleOAuthCallback, navigate])

  if (status === 'error') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="rounded-lg border border-red-200 bg-red-50 p-6">
            <h1 className="text-lg font-semibold text-red-800">Authentication Failed</h1>
            <p className="mt-2 text-sm text-red-600">
              {error || searchParams.get('error_description') || 'An error occurred during sign in.'}
            </p>
            <button
              onClick={() => navigate('/login', { replace: true })}
              className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-emerald-600 border-r-transparent"></div>
        <p className="mt-4 text-gray-600">Completing sign in...</p>
      </div>
    </div>
  )
}
