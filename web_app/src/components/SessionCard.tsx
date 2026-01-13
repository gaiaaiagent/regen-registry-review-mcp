import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Trash2, ExternalLink, Calendar, FileText, CheckCircle2 } from 'lucide-react'
import { type Session, useDeleteSession } from '@/hooks/useSessions'

interface SessionCardProps {
  session: Session
}

/**
 * Get badge variant based on workflow stage.
 */
function getStatusVariant(stageName: string): 'default' | 'secondary' | 'success' | 'warning' | 'outline' {
  switch (stageName.toLowerCase()) {
    case 'initialized':
    case 'session created':
      return 'secondary'
    case 'document discovery':
    case 'documents discovered':
      return 'outline'
    case 'mapping':
    case 'requirements mapped':
      return 'warning'
    case 'evidence extraction':
    case 'evidence extracted':
      return 'default'
    case 'validation':
    case 'validated':
      return 'success'
    case 'report generated':
    case 'complete':
      return 'success'
    default:
      return 'secondary'
  }
}

/**
 * Format a stage name for display.
 */
function formatStageName(stageName: string): string {
  return stageName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Format ISO date string to readable format.
 */
function formatDate(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function SessionCard({ session }: SessionCardProps) {
  const navigate = useNavigate()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const deleteSession = useDeleteSession()

  const stageName = session.workflow_progress?.stage_name || 'Initialized'
  const currentStage = session.workflow_progress?.current_stage || 1
  const completedStages = session.workflow_progress?.completed_stages || []

  const handleCardClick = () => {
    navigate(`/workspace/${session.session_id}`)
  }

  const handleDelete = async () => {
    try {
      await deleteSession.mutateAsync(session.session_id)
      setShowDeleteDialog(false)
    } catch {
      // Error handled by mutation
    }
  }

  return (
    <>
      <Card
        className="hover:shadow-md transition-shadow cursor-pointer group"
        onClick={handleCardClick}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg truncate">{session.project_name}</CardTitle>
              <CardDescription className="text-xs mt-1">
                {session.methodology}
              </CardDescription>
            </div>
            <Badge variant={getStatusVariant(stageName)}>
              {formatStageName(stageName)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-3">
            {/* Progress indicator */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <div className="flex-1">
                <div className="flex items-center gap-1 mb-1">
                  <span>Stage {currentStage} of 6</span>
                </div>
                <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${(currentStage / 6) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Metadata row */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(session.created_at)}
              </span>
              {session.documents_count !== undefined && (
                <span className="flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  {session.documents_count} docs
                </span>
              )}
              {session.requirements_total !== undefined && session.requirements_covered !== undefined && (
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  {session.requirements_covered}/{session.requirements_total} reqs
                </span>
              )}
            </div>

            {/* Completed stages */}
            {completedStages.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {completedStages.slice(0, 3).map((stage) => (
                  <Badge key={stage} variant="outline" className="text-xs py-0">
                    {formatStageName(stage)}
                  </Badge>
                ))}
                {completedStages.length > 3 && (
                  <Badge variant="outline" className="text-xs py-0">
                    +{completedStages.length - 3} more
                  </Badge>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={(e) => {
                  e.stopPropagation()
                  handleCardClick()
                }}
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                Open
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowDeleteDialog(true)
                }}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Delete confirmation dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Session</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{session.project_name}"? This action cannot be undone and will permanently remove all session data.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleteSession.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteSession.isPending}
            >
              {deleteSession.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

/**
 * Skeleton loader for session cards.
 */
export function SessionCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 space-y-2">
            <div className="h-5 bg-primary/10 rounded animate-pulse w-3/4" />
            <div className="h-3 bg-primary/10 rounded animate-pulse w-1/2" />
          </div>
          <div className="h-5 w-20 bg-primary/10 rounded animate-pulse" />
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          <div className="space-y-1">
            <div className="h-3 bg-primary/10 rounded animate-pulse w-24" />
            <div className="h-1.5 bg-primary/10 rounded-full animate-pulse" />
          </div>
          <div className="flex gap-4">
            <div className="h-3 bg-primary/10 rounded animate-pulse w-20" />
            <div className="h-3 bg-primary/10 rounded animate-pulse w-16" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
