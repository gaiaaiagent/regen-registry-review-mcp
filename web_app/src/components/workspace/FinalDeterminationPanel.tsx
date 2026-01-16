import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Loader2,
  Gavel,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  useFinalDetermination,
  useSetFinalDetermination,
  useClearDetermination,
  type DeterminationStatus,
} from '@/hooks/useReviewDecisions'
import { cn } from '@/lib/utils'

interface FinalDeterminationPanelProps {
  sessionId?: string
}

const DETERMINATION_OPTIONS: {
  value: DeterminationStatus
  label: string
  description: string
  icon: typeof CheckCircle2
  className: string
}[] = [
  {
    value: 'approve',
    label: 'Approve',
    description: 'Project meets all requirements and is recommended for registration.',
    icon: CheckCircle2,
    className: 'border-green-400 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  },
  {
    value: 'conditional',
    label: 'Conditional Approval',
    description: 'Project can proceed pending specified conditions being met.',
    icon: AlertTriangle,
    className: 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
  },
  {
    value: 'reject',
    label: 'Reject',
    description: 'Project does not meet requirements and cannot proceed.',
    icon: XCircle,
    className: 'border-red-400 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300',
  },
  {
    value: 'hold',
    label: 'Hold',
    description: 'Review is paused pending additional information or review.',
    icon: Clock,
    className: 'border-blue-400 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  },
]

export function FinalDeterminationPanel({ sessionId: propSessionId }: FinalDeterminationPanelProps) {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>()
  const sessionId = propSessionId ?? paramSessionId ?? ''

  const { data: currentDetermination, isLoading } = useFinalDetermination(sessionId)
  const setDetermination = useSetFinalDetermination(sessionId)
  const clearDetermination = useClearDetermination(sessionId)

  const [selectedDetermination, setSelectedDetermination] = useState<DeterminationStatus | null>(null)
  const [notes, setNotes] = useState('')
  const [conditions, setConditions] = useState('')

  useEffect(() => {
    if (currentDetermination?.determination) {
      setSelectedDetermination(currentDetermination.determination)
      setNotes(currentDetermination.notes ?? '')
      setConditions(currentDetermination.conditions ?? '')
    }
  }, [currentDetermination])

  const handleSubmit = async () => {
    if (!selectedDetermination) {
      toast.error('Please select a determination')
      return
    }
    if (!notes.trim()) {
      toast.error('Notes are required')
      return
    }
    if (selectedDetermination === 'conditional' && !conditions.trim()) {
      toast.error('Conditions are required for conditional approval')
      return
    }

    try {
      await setDetermination.mutateAsync({
        determination: selectedDetermination,
        notes: notes.trim(),
        conditions: selectedDetermination === 'conditional' ? conditions.trim() : undefined,
      })
      toast.success('Determination saved', {
        description: `Project marked as ${selectedDetermination}`,
      })
    } catch (error) {
      toast.error('Failed to save determination', {
        description: error instanceof Error ? error.message : 'Please try again',
      })
    }
  }

  const handleClear = async () => {
    try {
      await clearDetermination.mutateAsync({})
      setSelectedDetermination(null)
      setNotes('')
      setConditions('')
      toast.success('Determination cleared')
    } catch (error) {
      toast.error('Failed to clear determination', {
        description: error instanceof Error ? error.message : 'Please try again',
      })
    }
  }

  if (!sessionId) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p>No session selected</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const selectedOption = DETERMINATION_OPTIONS.find(o => o.value === selectedDetermination)

  return (
    <Card className="m-4">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Gavel className="h-5 w-5" />
          Final Determination
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Status */}
        {currentDetermination?.determination && (
          <div className={cn(
            'p-3 rounded-lg border-2',
            DETERMINATION_OPTIONS.find(o => o.value === currentDetermination.determination)?.className
          )}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">Current</Badge>
                <span className="font-medium">
                  {DETERMINATION_OPTIONS.find(o => o.value === currentDetermination.determination)?.label}
                </span>
              </div>
              <span className="text-xs text-muted-foreground">
                by {currentDetermination.set_by} on {currentDetermination.set_at ? new Date(currentDetermination.set_at).toLocaleDateString() : ''}
              </span>
            </div>
            {currentDetermination.notes && (
              <p className="text-sm mt-2">{currentDetermination.notes}</p>
            )}
            {currentDetermination.conditions && (
              <p className="text-sm mt-2 italic">Conditions: {currentDetermination.conditions}</p>
            )}
          </div>
        )}

        {/* Selection */}
        <div className="space-y-2">
          <Label className="text-sm font-medium">Select Determination</Label>
          <div className="grid grid-cols-2 gap-2">
            {DETERMINATION_OPTIONS.map((option) => {
              const Icon = option.icon
              const isSelected = selectedDetermination === option.value
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setSelectedDetermination(option.value)}
                  className={cn(
                    'p-3 rounded-lg border-2 text-left transition-all hover:shadow-md',
                    isSelected ? option.className : 'border-muted hover:border-muted-foreground/30'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Icon className={cn('h-4 w-4', isSelected ? '' : 'text-muted-foreground')} />
                    <span className={cn('font-medium text-sm', isSelected ? '' : 'text-muted-foreground')}>
                      {option.label}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {option.description}
                  </p>
                </button>
              )
            })}
          </div>
        </div>

        {/* Notes */}
        <div className="space-y-2">
          <Label htmlFor="determination-notes" className="text-sm font-medium">
            Notes <span className="text-red-500">*</span>
          </Label>
          <Textarea
            id="determination-notes"
            placeholder="Explain the rationale for this determination..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="resize-none"
          />
        </div>

        {/* Conditions (only for conditional) */}
        {selectedDetermination === 'conditional' && (
          <div className="space-y-2">
            <Label htmlFor="determination-conditions" className="text-sm font-medium">
              Conditions <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="determination-conditions"
              placeholder="List the conditions that must be met for approval..."
              value={conditions}
              onChange={(e) => setConditions(e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2">
          <Button
            onClick={handleSubmit}
            disabled={setDetermination.isPending || !selectedDetermination || !notes.trim()}
            className={cn(
              selectedOption?.value === 'approve' && 'bg-green-600 hover:bg-green-700',
              selectedOption?.value === 'conditional' && 'bg-yellow-600 hover:bg-yellow-700',
              selectedOption?.value === 'reject' && 'bg-red-600 hover:bg-red-700',
              selectedOption?.value === 'hold' && 'bg-blue-600 hover:bg-blue-700'
            )}
          >
            {setDetermination.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Gavel className="h-4 w-4 mr-2" />
                {currentDetermination?.determination ? 'Update Determination' : 'Set Determination'}
              </>
            )}
          </Button>

          {currentDetermination?.determination && (
            <Button
              variant="outline"
              onClick={handleClear}
              disabled={clearDetermination.isPending}
            >
              {clearDetermination.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                'Clear'
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
