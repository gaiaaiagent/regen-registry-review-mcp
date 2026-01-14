import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '@/contexts/AuthContext'
import { useProjectRevisions, useRespondToRevision } from '@/hooks/useProponentData'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RevisionRequestCard } from '@/components/proponent/RevisionRequestCard'
import { RevisionResponseDialog } from '@/components/proponent/RevisionResponseDialog'
import { NotificationBell } from '@/components/NotificationBell'
import {
  ArrowLeft,
  FileText,
  LogOut,
  Briefcase,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
} from 'lucide-react'
import type { RevisionRequest, ProjectStatus } from '@/lib/mockProponentData'

function getStatusConfig(status: ProjectStatus) {
  switch (status) {
    case 'under_review':
      return { label: 'Under Review', icon: Clock, className: 'bg-blue-100 text-blue-700' }
    case 'revisions_requested':
      return { label: 'Revisions Requested', icon: AlertCircle, className: 'bg-amber-100 text-amber-700' }
    case 'approved':
      return { label: 'Approved', icon: CheckCircle, className: 'bg-green-100 text-green-700' }
    case 'rejected':
      return { label: 'Rejected', icon: XCircle, className: 'bg-red-100 text-red-700' }
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function ProponentProjectView() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { user, signOut } = useAuth()
  const { project, revisions, isLoading, refetch } = useProjectRevisions(sessionId)
  const { respond, isSubmitting } = useRespondToRevision()

  const [selectedRevision, setSelectedRevision] = useState<RevisionRequest | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  const handleRespond = useCallback((revisionId: string) => {
    const revision = revisions.find((r) => r.id === revisionId)
    if (revision) {
      setSelectedRevision(revision)
      setDialogOpen(true)
    }
  }, [revisions])

  const handleSubmitResponse = useCallback(
    async (response: { comment: string; documentId?: string }) => {
      if (!sessionId || !selectedRevision) return

      await respond(sessionId, selectedRevision.id, response)
      toast.success('Response submitted', {
        description: 'Your revision response has been recorded.',
      })
      setDialogOpen(false)
      setSelectedRevision(null)
      refetch()
    },
    [sessionId, selectedRevision, respond, refetch]
  )

  const pendingRevisions = revisions.filter((r) => r.status === 'pending')
  const respondedRevisions = revisions.filter((r) => r.status === 'responded')
  const resolvedRevisions = revisions.filter((r) => r.status === 'resolved')

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Briefcase className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-semibold">Proponent Portal</h1>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell />
            <span className="text-sm text-muted-foreground hidden sm:inline">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={signOut}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/proponent">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Link>
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : !project ? (
          <div className="text-center py-12">
            <FileText className="h-16 w-16 mx-auto text-muted-foreground/30 mb-4" />
            <h2 className="text-xl font-semibold">Project Not Found</h2>
            <p className="text-muted-foreground mt-2">
              This project may have been removed or you don&apos;t have access.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Project Summary */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-xl">{project.project_name}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {project.methodology}
                    </p>
                  </div>
                  {(() => {
                    const statusConfig = getStatusConfig(project.status)
                    const StatusIcon = statusConfig.icon
                    return (
                      <Badge className={statusConfig.className}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {statusConfig.label}
                      </Badge>
                    )
                  })()}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Submitted</p>
                    <p className="font-medium">{formatDate(project.submitted_at)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Last Updated</p>
                    <p className="font-medium">{formatDate(project.last_updated)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Total Revisions</p>
                    <p className="font-medium">{project.total_revisions}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Pending</p>
                    <p className="font-medium text-amber-600">{project.pending_revisions}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Revisions */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Revision Requests</h3>

              {revisions.length === 0 ? (
                <Card>
                  <CardContent className="py-8 text-center">
                    <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
                    <p className="text-muted-foreground">No revision requests.</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Your project is being reviewed without any issues so far.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-6">
                  {pendingRevisions.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-amber-600 flex items-center gap-2">
                        <AlertCircle className="h-4 w-4" />
                        Pending Response ({pendingRevisions.length})
                      </h4>
                      {pendingRevisions.map((revision) => (
                        <RevisionRequestCard
                          key={revision.id}
                          revision={revision}
                          onRespond={handleRespond}
                        />
                      ))}
                    </div>
                  )}

                  {respondedRevisions.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-blue-600 flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        Awaiting Review ({respondedRevisions.length})
                      </h4>
                      {respondedRevisions.map((revision) => (
                        <RevisionRequestCard key={revision.id} revision={revision} />
                      ))}
                    </div>
                  )}

                  {resolvedRevisions.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-green-600 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4" />
                        Resolved ({resolvedRevisions.length})
                      </h4>
                      {resolvedRevisions.map((revision) => (
                        <RevisionRequestCard key={revision.id} revision={revision} />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      <RevisionResponseDialog
        revision={selectedRevision}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSubmit={handleSubmitResponse}
        isSubmitting={isSubmitting}
      />
    </div>
  )
}
