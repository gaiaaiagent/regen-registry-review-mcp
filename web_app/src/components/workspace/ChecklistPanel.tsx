import { useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import {
  ClipboardCheck,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { CategoryAccordion } from './CategoryAccordion'
import { EvidenceScratchpad } from './EvidenceScratchpad'
import { useWorkspaceRequirements } from '@/hooks/useWorkspace'
import { useManualEvidence, type ScratchpadItem } from '@/hooks/useManualEvidence'
import { cn } from '@/lib/utils'

interface ChecklistPanelProps {
  sessionId?: string
}

export function ChecklistPanel({ sessionId: propSessionId }: ChecklistPanelProps) {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>()
  const sessionId = propSessionId ?? paramSessionId

  const {
    requirementsByCategory,
    summary,
    isLoading,
    isError,
    hasData,
  } = useWorkspaceRequirements(sessionId)

  const {
    scratchpadItems,
    linkedEvidence,
    addEvidence,
    linkToRequirement,
    unlinkEvidence,
    removeEvidence,
    clearScratchpad,
  } = useManualEvidence(sessionId)

  const [expandedCategories, setExpandedCategories] = useState<string[]>([])

  const allCategories = useMemo(
    () => Object.keys(requirementsByCategory),
    [requirementsByCategory]
  )

  const handleExpandAll = () => {
    setExpandedCategories(allCategories)
  }

  const handleCollapseAll = () => {
    setExpandedCategories([])
  }

  const isAllExpanded = expandedCategories.length === allCategories.length && allCategories.length > 0

  const overallProgress = summary.total > 0
    ? Math.round(((summary.covered + summary.partial * 0.5) / summary.total) * 100)
    : 0

  const handleRemoveScratchpadItem = (id: string) => {
    removeEvidence(id)
  }

  const handleClearScratchpad = () => {
    clearScratchpad()
  }

  const handleUnlinkEvidence = (evidenceId: string) => {
    unlinkEvidence(evidenceId)
  }

  if (isLoading) {
    return (
      <div className="h-full flex flex-col bg-card">
        <div className="px-4 py-3 border-b bg-muted/30">
          <h2 className="font-medium flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            Requirements Checklist
          </h2>
        </div>
        <div className="flex-1 p-4 space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="h-full flex flex-col bg-card">
        <div className="px-4 py-3 border-b bg-muted/30">
          <h2 className="font-medium flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            Requirements Checklist
          </h2>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-4 text-muted-foreground">
          <AlertCircle className="h-12 w-12 mb-4 text-destructive opacity-50" />
          <p className="text-sm font-medium">Failed to load requirements</p>
          <p className="text-xs text-center mt-2">
            There was an error fetching the checklist data.
          </p>
        </div>
      </div>
    )
  }

  if (!hasData) {
    return (
      <div className="h-full flex flex-col bg-card">
        <div className="px-4 py-3 border-b bg-muted/30">
          <h2 className="font-medium flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            Requirements Checklist
          </h2>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-4 text-muted-foreground">
          <ClipboardCheck className="h-12 w-12 mb-4 opacity-30" />
          <p className="text-sm font-medium">No Evidence Yet</p>
          <p className="text-xs text-center mt-2">
            Run evidence extraction to populate the requirements checklist with findings from your documents.
          </p>
        </div>
        <EvidenceScratchpad
          items={scratchpadItems}
          onRemove={handleRemoveScratchpadItem}
          onClear={handleClearScratchpad}
        />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-card">
      <div className="px-4 py-3 border-b bg-muted/30">
        <div className="flex items-center justify-between">
          <h2 className="font-medium flex items-center gap-2">
            <ClipboardCheck className="h-4 w-4" />
            Requirements Checklist
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={isAllExpanded ? handleCollapseAll : handleExpandAll}
            className="h-7 text-xs"
          >
            {isAllExpanded ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1" />
                Collapse
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1" />
                Expand
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="px-4 py-3 border-b bg-muted/20">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Overall Progress</span>
          <span className="text-sm text-muted-foreground">{overallProgress}%</span>
        </div>
        <Progress
          value={overallProgress}
          className={cn(
            'h-2',
            overallProgress >= 80 && '[&>div]:bg-green-500',
            overallProgress >= 50 && overallProgress < 80 && '[&>div]:bg-yellow-500',
            overallProgress < 50 && '[&>div]:bg-red-500'
          )}
        />
        <div className="flex items-center justify-between mt-3 text-xs">
          <div className="flex items-center gap-1 text-green-600">
            <CheckCircle2 className="h-3 w-3" />
            <span>{summary.covered} covered</span>
          </div>
          <div className="flex items-center gap-1 text-yellow-600">
            <AlertTriangle className="h-3 w-3" />
            <span>{summary.partial} partial</span>
          </div>
          <div className="flex items-center gap-1 text-red-600">
            <XCircle className="h-3 w-3" />
            <span>{summary.missing} missing</span>
          </div>
        </div>
        {linkedEvidence.length > 0 && (
          <div className="mt-2 text-xs text-blue-600">
            +{linkedEvidence.length} manual evidence linked
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <CategoryAccordion
          categories={requirementsByCategory}
          expandedCategories={expandedCategories}
          onExpandedChange={setExpandedCategories}
          manualEvidence={linkedEvidence}
          onUnlinkEvidence={handleUnlinkEvidence}
        />
      </div>

      <EvidenceScratchpad
        items={scratchpadItems}
        onRemove={handleRemoveScratchpadItem}
        onClear={handleClearScratchpad}
      />
    </div>
  )
}

export { useManualEvidence }
