import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { SessionCard, SessionCardSkeleton } from '@/components/SessionCard'
import { NewSessionDialog } from '@/components/NewSessionDialog'
import { useSessions } from '@/hooks/useSessions'
import {
  useGDriveProjects,
  useCreateSessionFromProject,
  formatSubmittedDate,
  type DiscoveredProject,
} from '@/hooks/useGoogleDrive'
import {
  FolderOpen,
  RefreshCw,
  AlertCircle,
  Inbox,
  FileText,
  User,
  Calendar,
  Loader2,
  ArrowRight,
  HardDrive,
} from 'lucide-react'

// New Submissions Card Component
function NewSubmissionCard({
  project,
  onStartReview,
  isCreating,
  creatingFolderId,
}: {
  project: DiscoveredProject
  onStartReview: (folderId: string) => void
  isCreating: boolean
  creatingFolderId: string | null
}) {
  const isThisCreating = isCreating && creatingFolderId === project.folder_id
  const hasExistingSession = !!project.existing_session_id
  const navigate = useNavigate()

  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base font-semibold truncate">
              {project.manifest.project_name}
            </CardTitle>
            {project.manifest.project_id && (
              <Badge variant="outline" className="mt-1 text-xs">
                {project.manifest.project_id}
              </Badge>
            )}
          </div>
          {hasExistingSession ? (
            <Badge variant="secondary" className="shrink-0">
              Imported
            </Badge>
          ) : (
            <Badge variant="default" className="shrink-0 bg-green-600 hover:bg-green-700">
              New
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 shrink-0" />
            <span>{project.pdf_count} document{project.pdf_count !== 1 ? 's' : ''}</span>
            <span className="text-muted-foreground/50">|</span>
            <span className="truncate">{project.manifest.methodology}</span>
          </div>
          {project.manifest.proponent && (
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 shrink-0" />
              <span className="truncate">{project.manifest.proponent.name}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 shrink-0" />
            <span>Submitted {formatSubmittedDate(project.manifest.submitted_at)}</span>
          </div>
        </div>

        {hasExistingSession ? (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => navigate(`/workspace/${project.existing_session_id}`)}
          >
            Open Review
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        ) : (
          <Button
            size="sm"
            className="w-full"
            onClick={() => onStartReview(project.folder_id)}
            disabled={isCreating}
          >
            {isThisCreating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                Start Review
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

// Loading skeleton for new submissions
function NewSubmissionSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-5 w-16 mt-1" />
          </div>
          <Skeleton className="h-5 w-12" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <Skeleton className="h-8 w-full" />
      </CardContent>
    </Card>
  )
}

export function Dashboard() {
  const navigate = useNavigate()
  const { data, isLoading, isError, error, refetch, isRefetching } = useSessions()

  // Google Drive project discovery
  const {
    data: projectsData,
    isLoading: projectsLoading,
    isError: projectsError,
    error: projectsErrorDetail,
    refetch: refetchProjects,
  } = useGDriveProjects()

  const createSessionMutation = useCreateSessionFromProject()

  const sessions = data?.sessions ?? []
  const totalSessions = data?.total ?? 0

  // Filter to show only new (unimported) projects
  const newProjects = projectsData?.projects?.filter(p => !p.existing_session_id) ?? []
  const importedProjects = projectsData?.projects?.filter(p => !!p.existing_session_id) ?? []

  const handleSessionCreated = (sessionId: string) => {
    navigate(`/workspace/${sessionId}`)
  }

  const handleStartReview = (folderId: string) => {
    createSessionMutation.mutate(folderId)
  }

  const handleRefreshAll = () => {
    refetch()
    refetchProjects()
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
            {newProjects.length > 0 && (
              <span className="text-green-600 font-medium">
                {' '} | {newProjects.length} new submission{newProjects.length !== 1 ? 's' : ''}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshAll}
            disabled={isRefetching || projectsLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefetching || projectsLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <NewSessionDialog onSuccess={handleSessionCreated} />
        </div>
      </div>

      {/* New Submissions Section from Google Drive */}
      {(projectsLoading || newProjects.length > 0 || projectsError) && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Inbox className="h-5 w-5 text-green-600" />
            <h2 className="text-lg font-semibold">New Submissions</h2>
            <Badge variant="secondary" className="ml-auto">
              <HardDrive className="h-3 w-3 mr-1" />
              Google Drive
            </Badge>
          </div>

          {/* Projects loading state */}
          {projectsLoading && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2].map((i) => (
                <NewSubmissionSkeleton key={i} />
              ))}
            </div>
          )}

          {/* Projects error state */}
          {projectsError && !projectsLoading && (
            <Card className="border-amber-500/50 bg-amber-50/50 dark:bg-amber-950/20">
              <CardContent className="flex items-center gap-3 py-4">
                <AlertCircle className="h-5 w-5 text-amber-600 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                    Could not load submissions from Google Drive
                  </p>
                  <p className="text-xs text-amber-600 dark:text-amber-400 truncate">
                    {projectsErrorDetail instanceof Error
                      ? projectsErrorDetail.message
                      : 'Check that GDRIVE_PROJECTS_FOLDER_ID is configured'}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetchProjects()}
                  className="shrink-0"
                >
                  Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {/* New projects grid */}
          {!projectsLoading && !projectsError && newProjects.length > 0 && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {newProjects.map((project) => (
                <NewSubmissionCard
                  key={project.folder_id}
                  project={project}
                  onStartReview={handleStartReview}
                  isCreating={createSessionMutation.isPending}
                  creatingFolderId={createSessionMutation.variables ?? null}
                />
              ))}
            </div>
          )}

          {/* Create session error */}
          {createSessionMutation.isError && (
            <Card className="border-destructive mt-4">
              <CardContent className="flex items-center gap-3 py-4">
                <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-destructive">
                    Failed to create session
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {createSessionMutation.error instanceof Error
                      ? createSessionMutation.error.message
                      : 'An unexpected error occurred'}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Empty state for new submissions (no new projects) */}
          {!projectsLoading && !projectsError && newProjects.length === 0 && importedProjects.length > 0 && (
            <Card className="border-dashed">
              <CardContent className="flex items-center justify-center py-6 text-muted-foreground">
                <p className="text-sm">All submissions have been imported. Check for new folders in Google Drive.</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

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

      {/* Empty state - only show if no new submissions either */}
      {!isLoading && !isError && sessions.length === 0 && newProjects.length === 0 && !projectsLoading && (
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
        <>
          <div className="flex items-center gap-2 mb-4">
            <FolderOpen className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Active Reviews</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <SessionCard key={session.session_id} session={session} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
