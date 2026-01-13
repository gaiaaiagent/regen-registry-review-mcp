import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Progress } from '@/components/ui/progress'
import { RequirementCard } from './RequirementCard'
import { useWorkspaceContext, type Requirement } from '@/contexts/WorkspaceContext'
import type { ManualEvidence } from '@/hooks/useManualEvidence'
import { cn } from '@/lib/utils'

interface CategoryAccordionProps {
  categories: { [category: string]: Requirement[] }
  expandedCategories: string[]
  onExpandedChange: (categories: string[]) => void
  manualEvidence?: ManualEvidence[]
  onUnlinkEvidence?: (evidenceId: string) => void
}

function getCategoryProgress(requirements: Requirement[]): {
  covered: number
  partial: number
  total: number
  percentage: number
} {
  const covered = requirements.filter((r) => r.status === 'covered').length
  const partial = requirements.filter((r) => r.status === 'partial').length
  const total = requirements.length
  const percentage = total > 0 ? Math.round(((covered + partial * 0.5) / total) * 100) : 0

  return { covered, partial, total, percentage }
}

function getProgressColor(percentage: number): string {
  if (percentage >= 80) return 'bg-green-500'
  if (percentage >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
}

export function CategoryAccordion({
  categories,
  expandedCategories,
  onExpandedChange,
  manualEvidence = [],
  onUnlinkEvidence,
}: CategoryAccordionProps) {
  const { focusedRequirementId, setFocusedRequirementId } = useWorkspaceContext()

  const sortedCategories = Object.entries(categories).sort(([a], [b]) =>
    a.localeCompare(b)
  )

  const getEvidenceForRequirement = (requirementId: string) =>
    manualEvidence.filter((e) => e.requirementId === requirementId)

  return (
    <Accordion
      type="multiple"
      value={expandedCategories}
      onValueChange={onExpandedChange}
      className="w-full"
    >
      {sortedCategories.map(([category, requirements]) => {
        const progress = getCategoryProgress(requirements)
        const progressColor = getProgressColor(progress.percentage)

        return (
          <AccordionItem key={category} value={category} className="border-b-0 mb-1">
            <AccordionTrigger className="px-3 py-2 hover:no-underline hover:bg-muted/50 rounded-md transition-colors">
              <div className="flex flex-col items-start gap-1 flex-1 mr-2">
                <div className="flex items-center justify-between w-full">
                  <span className="font-medium text-sm">{category}</span>
                  <span className="text-xs text-muted-foreground">
                    {progress.covered}/{progress.total} covered
                  </span>
                </div>
                <div className="w-full flex items-center gap-2">
                  <Progress
                    value={progress.percentage}
                    className={cn('h-1.5 flex-1', '[&>div]:' + progressColor)}
                  />
                  <span className="text-xs text-muted-foreground w-8 text-right">
                    {progress.percentage}%
                  </span>
                </div>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-1 pt-1 pb-2">
              <div className="space-y-2">
                {requirements.map((req) => (
                  <RequirementCard
                    key={req.id}
                    requirement={req}
                    isSelected={focusedRequirementId === req.id}
                    onSelect={() => setFocusedRequirementId(req.id)}
                    manualEvidence={getEvidenceForRequirement(req.id)}
                    onUnlinkEvidence={onUnlinkEvidence}
                  />
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        )
      })}
    </Accordion>
  )
}
