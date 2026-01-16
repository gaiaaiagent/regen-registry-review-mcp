import { useVerificationStatus, useBulkVerify } from '@/hooks/useVerification'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { CheckCircle2, XCircle, Clock, FileCheck, CheckCheck, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import type { Requirement } from '@/contexts/WorkspaceContext'

interface VerificationProgressProps {
  sessionId: string | null
  requirements?: Requirement[]
}

export function VerificationProgress({ sessionId, requirements = [] }: VerificationProgressProps) {
  const { data: status, isLoading } = useVerificationStatus(sessionId)
  const bulkVerify = useBulkVerify(sessionId)

  if (isLoading || !status) return null

  const { overall } = status
  const progressPercent = Math.round(overall.progress * 100)
  const totalSnippets = overall.verified + overall.rejected + overall.pending

  const handleVerifyAll = async () => {
    const pendingSnippets: { snippetId: string; requirementId: string }[] = []
    const verifiedSnippetIds = new Set(
      status.summaries.flatMap((s) =>
        Array.from({ length: s.verified }, (_, i) => `${s.requirementId}-verified-${i}`)
      )
    )

    for (const req of requirements) {
      for (const ev of req.evidence ?? []) {
        const isVerified = status.summaries.find((s) => s.requirementId === req.id)
        if (!isVerified || isVerified.pending > 0) {
          pendingSnippets.push({ snippetId: ev.id, requirementId: req.id })
        }
      }
    }

    if (pendingSnippets.length === 0) {
      toast.info('All snippets already verified')
      return
    }

    toast.info(`Verifying ${pendingSnippets.length} snippets...`)

    try {
      await bulkVerify.mutateAsync(pendingSnippets)
      toast.success('All evidence verified', {
        description: `${pendingSnippets.length} snippets marked as verified`,
      })
    } catch (error) {
      toast.error('Bulk verification failed', {
        description: error instanceof Error ? error.message : 'Please try again',
      })
    }
  }

  return (
    <div className="p-3 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200/50 dark:border-blue-800/50 rounded-lg space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileCheck className="h-4 w-4 text-blue-600" />
          <span className="text-xs font-medium text-blue-800 dark:text-blue-200">Evidence Verification</span>
        </div>
        {overall.pending > 0 && requirements.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            className="h-6 px-2 text-[10px] border-green-300 hover:bg-green-50 hover:text-green-700"
            onClick={handleVerifyAll}
            disabled={bulkVerify.isPending}
          >
            {bulkVerify.isPending ? (
              <>
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                Verifying...
              </>
            ) : (
              <>
                <CheckCheck className="h-3 w-3 mr-1" />
                Verify All
              </>
            )}
          </Button>
        )}
      </div>

      <p className="text-[11px] text-blue-600/80 dark:text-blue-300/80">
        Each requirement has evidence snippets. Expand requirements and verify each snippet is accurate.
      </p>

      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{overall.verified + overall.rejected} of {totalSnippets} snippets reviewed</span>
        <span className="font-medium">{progressPercent}%</span>
      </div>

      <Progress value={progressPercent} className="h-2 [&>div]:bg-blue-500" />

      <div className="flex items-center gap-4 text-xs">
        <span className="flex items-center gap-1 text-green-600">
          <CheckCircle2 className="h-3 w-3" />
          {overall.verified}
        </span>
        <span className="flex items-center gap-1 text-red-600">
          <XCircle className="h-3 w-3" />
          {overall.rejected}
        </span>
        <span className="flex items-center gap-1 text-muted-foreground">
          <Clock className="h-3 w-3" />
          {overall.pending} to review
        </span>
      </div>
    </div>
  )
}
