import { useVerificationStatus } from '@/hooks/useVerification'
import { Progress } from '@/components/ui/progress'
import { CheckCircle2, XCircle, Clock } from 'lucide-react'

interface VerificationProgressProps {
  sessionId: string | null
}

export function VerificationProgress({ sessionId }: VerificationProgressProps) {
  const { data: status, isLoading } = useVerificationStatus(sessionId)

  if (isLoading || !status) return null

  const { overall } = status
  const progressPercent = Math.round(overall.progress * 100)

  return (
    <div className="p-3 bg-muted/30 rounded-lg space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium">Verification Progress</span>
        <span className="text-muted-foreground">{progressPercent}%</span>
      </div>

      <Progress value={progressPercent} className="h-2" />

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <CheckCircle2 className="h-3 w-3 text-green-600" />
          {overall.verified} verified
        </span>
        <span className="flex items-center gap-1">
          <XCircle className="h-3 w-3 text-red-600" />
          {overall.rejected} rejected
        </span>
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3 text-muted-foreground" />
          {overall.pending} pending
        </span>
      </div>
    </div>
  )
}
