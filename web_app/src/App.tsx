import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/contexts/AuthContext'
import { NotificationProvider } from '@/contexts/NotificationContext'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { RoleProtectedRoute } from '@/components/RoleProtectedRoute'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { PDFTestPage } from '@/pages/PDFTestPage'
import { SessionWorkspace } from '@/pages/SessionWorkspace'
import { LoginPage } from '@/pages/LoginPage'
import { AuthCallback } from '@/pages/AuthCallback'
import { ProponentDashboard } from '@/pages/ProponentDashboard'
import { ProponentProjectView } from '@/pages/ProponentProjectView'
import { Toaster } from '@/components/ui/toaster'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff: 1s, 2s, 4s... max 30s
    },
    mutations: {
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // Exponential backoff for mutations
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <NotificationProvider>
          <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            {/* Reviewer routes (requires reviewer role) */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <RoleProtectedRoute allowedRoles={['reviewer']} fallbackPath="/proponent">
                    <Layout />
                  </RoleProtectedRoute>
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="pdf-test" element={<PDFTestPage />} />
              <Route path="workspace/:sessionId" element={<SessionWorkspace />} />
            </Route>

            {/* Proponent routes (requires proponent role) */}
            <Route
              path="/proponent"
              element={
                <ProtectedRoute>
                  <RoleProtectedRoute allowedRoles={['proponent']} fallbackPath="/">
                    <ProponentDashboard />
                  </RoleProtectedRoute>
                </ProtectedRoute>
              }
            />
            <Route
              path="/proponent/project/:sessionId"
              element={
                <ProtectedRoute>
                  <RoleProtectedRoute allowedRoles={['proponent']} fallbackPath="/">
                    <ProponentProjectView />
                  </RoleProtectedRoute>
                </ProtectedRoute>
              }
            />
          </Routes>
          </BrowserRouter>
          <Toaster />
        </NotificationProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
