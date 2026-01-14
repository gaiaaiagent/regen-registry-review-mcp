import { Link } from 'react-router-dom'
import { FileText, Clock, AlertCircle, CheckCircle, XCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { ProponentProject, ProjectStatus } from '@/lib/mockProponentData'

interface ProjectCardProps {
  project: ProponentProject
}

function getStatusConfig(status: ProjectStatus) {
  switch (status) {
    case 'under_review':
      return {
        label: 'Under Review',
        variant: 'secondary' as const,
        icon: Clock,
        className: 'bg-blue-100 text-blue-700 hover:bg-blue-100',
      }
    case 'revisions_requested':
      return {
        label: 'Revisions Requested',
        variant: 'destructive' as const,
        icon: AlertCircle,
        className: 'bg-amber-100 text-amber-700 hover:bg-amber-100',
      }
    case 'approved':
      return {
        label: 'Approved',
        variant: 'default' as const,
        icon: CheckCircle,
        className: 'bg-green-100 text-green-700 hover:bg-green-100',
      }
    case 'rejected':
      return {
        label: 'Rejected',
        variant: 'destructive' as const,
        icon: XCircle,
        className: 'bg-red-100 text-red-700 hover:bg-red-100',
      }
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function ProjectCard({ project }: ProjectCardProps) {
  const statusConfig = getStatusConfig(project.status)
  const StatusIcon = statusConfig.icon

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base">{project.project_name}</CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                {project.methodology}
              </p>
            </div>
          </div>
          <Badge className={statusConfig.className}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {statusConfig.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
          <span>Submitted: {formatDate(project.submitted_at)}</span>
          <span>Updated: {formatDate(project.last_updated)}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm">
            {project.pending_revisions > 0 && (
              <span className="flex items-center gap-1 text-amber-600 font-medium">
                <AlertCircle className="h-4 w-4" />
                {project.pending_revisions} pending revision{project.pending_revisions !== 1 ? 's' : ''}
              </span>
            )}
            {project.total_revisions > 0 && project.pending_revisions === 0 && (
              <span className="flex items-center gap-1 text-green-600">
                <CheckCircle className="h-4 w-4" />
                All revisions addressed
              </span>
            )}
          </div>

          <Button asChild size="sm">
            <Link to={`/proponent/project/${project.session_id}`}>
              {project.pending_revisions > 0 ? 'Respond to Revisions' : 'View Details'}
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
