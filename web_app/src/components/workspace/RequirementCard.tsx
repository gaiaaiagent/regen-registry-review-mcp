import { useState } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useWorkspaceContext, type Requirement } from '@/contexts/WorkspaceContext'
import type { ManualEvidence } from '@/hooks/useManualEvidence'
import {
  CheckCircle2,
  AlertCircle,
  XCircle,
  CircleDashed,
  ChevronDown,
  ChevronUp,
  FileText,
  ExternalLink,
  Link2Off,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface RequirementCardProps {
  requirement: Requirement
  isSelected?: boolean
  onSelect?: () => void
  manualEvidence?: ManualEvidence[]
  onUnlinkEvidence?: (evidenceId: string) => void
}

const STATUS_CONFIG = {
  covered: {
    icon: CheckCircle2,
    label: 'Covered',
    variant: 'success' as const,
    className: 'text-green-600',
  },
  partial: {
    icon: AlertCircle,
    label: 'Partial',
    variant: 'warning' as const,
    className: 'text-yellow-600',
  },
  missing: {
    icon: XCircle,
    label: 'Missing',
    variant: 'destructive' as const,
    className: 'text-red-600',
  },
  not_started: {
    icon: CircleDashed,
    label: 'Not Started',
    variant: 'secondary' as const,
    className: 'text-muted-foreground',
  },
}

export function RequirementCard({
  requirement,
  isSelected,
  onSelect,
  manualEvidence = [],
  onUnlinkEvidence,
}: RequirementCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { scrollToEvidence, isDragging } = useWorkspaceContext()

  const { isOver, setNodeRef } = useDroppable({
    id: `requirement-${requirement.id}`,
  })

  const statusConfig = STATUS_CONFIG[requirement.status]
  const StatusIcon = statusConfig.icon
  const evidenceCount = (requirement.evidence?.length ?? 0) + manualEvidence.length
  const hasEvidence = evidenceCount > 0

  const handleEvidenceClick = (documentId: string, pageNumber: number) => {
    scrollToEvidence(documentId, pageNumber)
  }

  const confidencePercent = requirement.confidence
    ? Math.round(requirement.confidence * 100)
    : null

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'relative transition-all duration-150',
        isDragging && 'ring-2 ring-primary/30 ring-offset-1 rounded-lg',
        isOver && 'ring-2 ring-primary ring-offset-2 rounded-lg scale-[1.02]'
      )}
    >
      <Card
        className={cn(
          'transition-all cursor-pointer hover:shadow-md',
          isSelected && 'ring-2 ring-primary',
          requirement.humanReviewRequired && 'border-yellow-400',
          isOver && 'bg-primary/5'
        )}
        onClick={onSelect}
      >
        <CardContent className="p-3">
          <div className="flex items-start gap-2">
            <StatusIcon className={cn('h-4 w-4 mt-0.5 shrink-0', statusConfig.className)} />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-xs text-muted-foreground">
                  {requirement.id}
                </span>
                <Badge variant={statusConfig.variant} className="text-xs">
                  {statusConfig.label}
                </Badge>
                {confidencePercent !== null && (
                  <span className="text-xs text-muted-foreground">
                    {confidencePercent}%
                  </span>
                )}
                {requirement.humanReviewRequired && (
                  <Badge variant="outline" className="text-xs border-yellow-400 text-yellow-600">
                    Review
                  </Badge>
                )}
                {manualEvidence.length > 0 && (
                  <Badge variant="outline" className="text-xs border-blue-400 text-blue-600">
                    +{manualEvidence.length} manual
                  </Badge>
                )}
              </div>

              <p className="text-sm mt-1 line-clamp-2">{requirement.text}</p>

              {requirement.extractedValue && (
                <p className="text-xs text-muted-foreground mt-1 italic line-clamp-1">
                  Value: {requirement.extractedValue}
                </p>
              )}

              {hasEvidence && (
                <div className="mt-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs"
                    onClick={(e) => {
                      e.stopPropagation()
                      setIsExpanded(!isExpanded)
                    }}
                  >
                    <FileText className="h-3 w-3 mr-1" />
                    {evidenceCount} evidence{evidenceCount !== 1 ? 's' : ''}
                    {isExpanded ? (
                      <ChevronUp className="h-3 w-3 ml-1" />
                    ) : (
                      <ChevronDown className="h-3 w-3 ml-1" />
                    )}
                  </Button>

                  {isExpanded && (
                    <div className="mt-2 space-y-2 pl-1">
                      {requirement.evidence?.map((ev) => (
                        <div
                          key={ev.id}
                          className="text-xs bg-muted/50 rounded p-2 hover:bg-muted transition-colors"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium truncate flex-1">
                              {ev.documentId}
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-5 px-1.5 text-xs shrink-0"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleEvidenceClick(ev.documentId, ev.pageNumber)
                              }}
                            >
                              p.{ev.pageNumber}
                              <ExternalLink className="h-3 w-3 ml-1" />
                            </Button>
                          </div>
                          {ev.section && (
                            <p className="text-muted-foreground mt-1">
                              Section: {ev.section}
                            </p>
                          )}
                          <p className="mt-1 line-clamp-2">{ev.text}</p>
                        </div>
                      ))}

                      {manualEvidence.map((ev) => (
                        <div
                          key={ev.id}
                          className="text-xs bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded p-2 hover:bg-blue-100 dark:hover:bg-blue-950/50 transition-colors"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-1.5">
                              <Badge variant="outline" className="text-[10px] px-1 py-0 border-blue-400 text-blue-600">
                                Manual
                              </Badge>
                              <span className="font-medium truncate flex-1">
                                {ev.documentId}
                              </span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-5 px-1.5 text-xs shrink-0"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleEvidenceClick(ev.documentId, ev.pageNumber)
                                }}
                              >
                                p.{ev.pageNumber}
                                <ExternalLink className="h-3 w-3 ml-1" />
                              </Button>
                              {onUnlinkEvidence && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-5 px-1 text-xs shrink-0 text-muted-foreground hover:text-destructive"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    onUnlinkEvidence(ev.id)
                                  }}
                                  title="Unlink evidence"
                                >
                                  <Link2Off className="h-3 w-3" />
                                </Button>
                              )}
                            </div>
                          </div>
                          <p className="mt-1 line-clamp-2">{ev.text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {isOver && (
        <div className="absolute inset-0 bg-primary/10 rounded-lg pointer-events-none flex items-center justify-center">
          <span className="text-xs font-medium text-primary bg-background/90 px-2 py-1 rounded shadow-sm">
            Drop to link evidence
          </span>
        </div>
      )}
    </div>
  )
}
