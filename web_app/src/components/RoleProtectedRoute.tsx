import { Navigate } from 'react-router-dom'
import { useAuth, type UserRole } from '@/contexts/AuthContext'

interface RoleProtectedRouteProps {
  children: React.ReactNode
  allowedRoles: UserRole[]
  fallbackPath?: string
}

export function RoleProtectedRoute({
  children,
  allowedRoles,
  fallbackPath = '/login'
}: RoleProtectedRouteProps) {
  const { user, isLoading, signOut } = useAuth()

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Handle legacy localStorage data without role field - force re-login
  if (!user.role) {
    signOut()
    return <Navigate to="/login" replace />
  }

  if (!allowedRoles.includes(user.role)) {
    // If user is logged in but wrong role, redirect to their default dashboard
    if (user.role === 'reviewer') {
      return <Navigate to="/" replace />
    } else if (user.role === 'proponent') {
      return <Navigate to="/proponent" replace />
    }
    return <Navigate to={fallbackPath} replace />
  }

  return <>{children}</>
}