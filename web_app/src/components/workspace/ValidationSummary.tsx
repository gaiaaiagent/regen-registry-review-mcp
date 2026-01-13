import { AlertTriangle, CheckCircle2, XCircle, RefreshCw, Clock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ValidationSummaryProps {
  lastRun: string | null
  isStale: boolean
  passed: number
  warnings: number
  errors: number
  totalChecks: number
  isRunning: boolean
  onRunValidation: () => void
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return `${diffDays}d ago`
}

export function ValidationSummary({
  lastRun,
  isStale,
  passed,
  warnings,
  errors,
  totalChecks,
  isRunning,
  onRunValidation,
}: ValidationSummaryProps) {
  const hasRun = lastRun !== null

  return (
    <div className="space-y-3">
      {isStale && hasRun && (
        <div className="flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <AlertTriangle className="h-4 w-4 text-yellow-500 shrink-0" />
          <span className="text-sm text-yellow-700 dark:text-yellow-300 flex-1">
            Validation may be out of date. Evidence has changed since last run.
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={onRunValidation}
            disabled={isRunning}
            className="shrink-0"
          >
            {isRunning ? (
              <>
                <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <RefreshCw className="h-3 w-3 mr-1" />
                Re-run
              </>
            )}
          </Button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-sm font-medium">{passed}</span>
            <span className="text-xs text-muted-foreground">passed</span>
          </div>
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            <span className="text-sm font-medium">{warnings}</span>
            <span className="text-xs text-muted-foreground">warnings</span>
          </div>
          <div className="flex items-center gap-1.5">
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm font-medium">{errors}</span>
            <span className="text-xs text-muted-foreground">errors</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {hasRun && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{formatRelativeTime(lastRun)}</span>
              {isStale && (
                <Badge variant="warning" className="ml-1 text-[10px] px-1.5 py-0">
                  Stale
                </Badge>
              )}
            </div>
          )}

          {!isStale && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRunValidation}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                  Running...
                </>
              ) : hasRun ? (
                <>
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Re-run
                </>
              ) : (
                'Run Validation'
              )}
            </Button>
          )}
        </div>
      </div>

      {hasRun && (
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <div className="h-full flex">
            <div
              className={cn('bg-green-500 transition-all')}
              style={{ width: `${(passed / totalChecks) * 100}%` }}
            />
            <div
              className={cn('bg-yellow-500 transition-all')}
              style={{ width: `${(warnings / totalChecks) * 100}%` }}
            />
            <div
              className={cn('bg-red-500 transition-all')}
              style={{ width: `${(errors / totalChecks) * 100}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
