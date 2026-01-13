import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SessionCard, SessionCardSkeleton } from '@/components/SessionCard'
import { NewSessionDialog } from '@/components/NewSessionDialog'
import { useSessions } from '@/hooks/useSessions'
import { FolderOpen, RefreshCw, AlertCircle } from 'lucide-react'

export function Dashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, error, refetch, isRefetching } = useSessions()

  const sessions = data?.sessions ?? []
  const totalSessions = data?.total ?? 0

  const handleSessionCreated = (sessionId: string) => {
    // Navigate to the new session (workspace - Phase 4)
    navigate(`/workspace/${sessionId}`)
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">Registry Reviews</h1>
          <p className="text-muted-foreground">
            {totalSessions === 0
              ? 'No active reviews'
              : `${totalSessions} review${totalSessions === 1 ? '' : 's'}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <NewSessionDialog onSuccess={handleSessionCreated} />
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <SessionCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              Failed to Load Sessions
            </CardTitle>
            <CardDescription>
              {error instanceof Error ? error.message : 'An unexpected error occurred'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {!isLoading && !isError && sessions.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FolderOpen className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No reviews yet</h3>
            <p className="text-muted-foreground text-center mb-6 max-w-sm">
              Start a new registry review to analyze project documents against methodology requirements.
            </p>
            <NewSessionDialog onSuccess={handleSessionCreated} />
          </CardContent>
        </Card>
      )}

      {/* Sessions grid */}
      {!isLoading && !isError && sessions.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sessions.map((session) => (
            <SessionCard key={session.session_id} session={session} />
          ))}
        </div>
      )}
    </div>
  )
}
