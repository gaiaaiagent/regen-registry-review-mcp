import { useReviewStatus } from '@/hooks/useReviewDecisions'
import { Progress } from '@/components/ui/progress'
import { CheckCircle2, XCircle, AlertTriangle, Clock, ClipboardList } from 'lucide-react'

interface ReviewProgressProps {
  sessionId: string | null
  totalRequirements: number
}

export function ReviewProgress({ sessionId, totalRequirements }: ReviewProgressProps) {
  const { data: status, isLoading } = useReviewStatus(sessionId)

  if (isLoading || !status) return null

  const { summary } = status
  const reviewed = summary.total_overrides
  const progressPercent = totalRequirements > 0 ? Math.round((reviewed / totalRequirements) * 100) : 0

  // Don't show the component if no reviews have been made yet
  // This reduces clutter for users who don't need formal review workflow
  if (reviewed === 0) {
    return (
      <div className="text-xs text-muted-foreground text-center py-2 border-t border-dashed">
        <span className="opacity-70">Optional: Use Approve/Revision/Reject buttons on requirements for formal review</span>
      </div>
    )
  }

  return (
    <div className="p-3 bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200/50 dark:border-indigo-800/50 rounded-lg space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-4 w-4 text-indigo-600" />
          <span className="text-xs font-medium text-indigo-800 dark:text-indigo-200">Review Progress</span>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{reviewed} of {totalRequirements} decisions made</span>
        <span className="font-medium">{progressPercent}%</span>
      </div>

      <Progress value={progressPercent} className="h-2 [&>div]:bg-indigo-500" />

      <div className="flex items-center gap-4 text-xs flex-wrap">
        <span className="flex items-center gap-1 text-green-600">
          <CheckCircle2 className="h-3 w-3" />
          {summary.approved} approved
        </span>
        <span className="flex items-center gap-1 text-orange-600">
          <AlertTriangle className="h-3 w-3" />
          {summary.needs_revision} revision
        </span>
        <span className="flex items-center gap-1 text-red-600">
          <XCircle className="h-3 w-3" />
          {summary.rejected} rejected
        </span>
        <span className="flex items-center gap-1 text-muted-foreground">
          <Clock className="h-3 w-3" />
          {totalRequirements - reviewed} pending
        </span>
      </div>
    </div>
  )
}
