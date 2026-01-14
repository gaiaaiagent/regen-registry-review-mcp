import { useState } from 'react'
import { AlertCircle, CheckCircle, Clock, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import type { RevisionRequest, RevisionStatus, RevisionPriority } from '@/lib/mockProponentData'

interface RevisionRequestCardProps {
  revision: RevisionRequest
  onRespond?: (revisionId: string) => void
}

function getStatusConfig(status: RevisionStatus) {
  switch (status) {
    case 'pending':
      return {
        label: 'Pending',
        icon: AlertCircle,
        className: 'bg-amber-100 text-amber-700',
      }
    case 'responded':
      return {
        label: 'Responded',
        icon: Clock,
        className: 'bg-blue-100 text-blue-700',
      }
    case 'resolved':
      return {
        label: 'Resolved',
        icon: CheckCircle,
        className: 'bg-green-100 text-green-700',
      }
  }
}

function getPriorityConfig(priority: RevisionPriority) {
  switch (priority) {
    case 'high':
      return { label: 'High Priority', className: 'bg-red-100 text-red-700' }
    case 'medium':
      return { label: 'Medium', className: 'bg-amber-100 text-amber-700' }
    case 'low':
      return { label: 'Low', className: 'bg-gray-100 text-gray-600' }
  }
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function RevisionRequestCard({ revision, onRespond }: RevisionRequestCardProps) {
  const [isExpanded, setIsExpanded] = useState(revision.status === 'pending')
  const statusConfig = getStatusConfig(revision.status)
  const priorityConfig = getPriorityConfig(revision.priority)
  const StatusIcon = statusConfig.icon

  const isResolved = revision.status === 'resolved' || revision.status === 'responded'

  return (
    <Card className={isResolved ? 'opacity-75' : ''}>
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className="text-xs font-mono">
                  {revision.requirement_id}
                </Badge>
                <Badge className={priorityConfig.className}>
                  {priorityConfig.label}
                </Badge>
              </div>
              <CardTitle className="text-base">{revision.title}</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge className={statusConfig.className}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {statusConfig.label}
              </Badge>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>
        </CardHeader>

        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Request Details</p>
                <p className="text-sm">{revision.description}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  Requested: {formatDate(revision.created_at)}
                </p>
              </div>

              {revision.response_comment && (
                <div className="rounded-lg bg-muted/50 p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    <p className="text-sm font-medium">Your Response</p>
                  </div>
                  <p className="text-sm">{revision.response_comment}</p>
                  {revision.responded_at && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Responded: {formatDate(revision.responded_at)}
                    </p>
                  )}
                </div>
              )}

              {revision.status === 'pending' && onRespond && (
                <Button onClick={() => onRespond(revision.id)} className="w-full">
                  Respond to Revision
                </Button>
              )}
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  )
}
