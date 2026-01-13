import { useParams } from 'react-router-dom'
import { ShieldCheck, AlertCircle, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ValidationSummary } from './ValidationSummary'
import { FactSheetTable } from './FactSheetTable'
import { useValidation } from '@/hooks/useValidation'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'
import type {
  DateAlignmentRow,
  LandTenureRow,
  ProjectIdRow,
  QuantificationRow,
} from '@/hooks/useValidation'

interface ValidationPanelProps {
  sessionId?: string
  onSwitchToChecklist?: () => void
}

export function ValidationPanel({
  sessionId: propSessionId,
  onSwitchToChecklist,
}: ValidationPanelProps) {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>()
  const sessionId = propSessionId ?? paramSessionId
  const { setFocusedRequirementId } = useWorkspaceContext()

  const {
    validation,
    isLoading,
    isError,
    isStale,
    hasValidation,
    isRunning,
    runValidation,
  } = useValidation(sessionId)

  const handleIssueClick = (requirementId: string) => {
    setFocusedRequirementId(requirementId)
    onSwitchToChecklist?.()
  }

  const handleRunValidation = async () => {
    try {
      await runValidation()
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 p-4 space-y-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 flex flex-col items-center justify-center p-4 text-muted-foreground">
          <AlertCircle className="h-12 w-12 mb-4 text-destructive opacity-50" />
          <p className="text-sm font-medium">Failed to load validation</p>
          <p className="text-xs text-center mt-2">
            There was an error fetching validation data.
          </p>
        </div>
      </div>
    )
  }

  if (!hasValidation) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 flex flex-col items-center justify-center p-4 text-muted-foreground">
          <ShieldCheck className="h-12 w-12 mb-4 opacity-30" />
          <p className="text-sm font-medium">No Validation Run Yet</p>
          <p className="text-xs text-center mt-2 max-w-[280px]">
            Run cross-validation to check date alignment, land tenure consistency,
            project ID occurrences, and quantification accuracy.
          </p>
          <Button
            className="mt-4"
            onClick={handleRunValidation}
            disabled={isRunning}
          >
            {isRunning ? (
              <>Running Validation...</>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Run Validation
              </>
            )}
          </Button>
        </div>
      </div>
    )
  }

  const { summary, fact_sheets, last_run } = validation!

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b bg-muted/20">
        <ValidationSummary
          lastRun={last_run}
          isStale={isStale}
          passed={summary.passed}
          warnings={summary.warnings}
          errors={summary.errors}
          totalChecks={summary.total_checks}
          isRunning={isRunning}
          onRunValidation={handleRunValidation}
        />
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          <FactSheetTable<DateAlignmentRow>
            title="Date Alignment"
            description="Validates that project dates are consistent across documents"
            status={fact_sheets.date_alignment.status}
            rows={fact_sheets.date_alignment.rows}
            columns={[
              { key: 'document', header: 'Document' },
              { key: 'document_type', header: 'Type' },
              { key: 'start_date', header: 'Start Date' },
              { key: 'end_date', header: 'End Date' },
            ]}
            issues={fact_sheets.date_alignment.issues}
            onIssueClick={handleIssueClick}
            emptyMessage="No date information extracted"
          />

          <FactSheetTable<LandTenureRow>
            title="Land Tenure"
            description="Verifies ownership and lease information consistency"
            status={fact_sheets.land_tenure.status}
            rows={fact_sheets.land_tenure.rows}
            columns={[
              { key: 'document', header: 'Document' },
              { key: 'owner_name', header: 'Owner' },
              { key: 'area_hectares', header: 'Area (ha)' },
              { key: 'tenure_type', header: 'Tenure Type' },
              { key: 'expiry_date', header: 'Expiry' },
            ]}
            issues={fact_sheets.land_tenure.issues}
            onIssueClick={handleIssueClick}
            emptyMessage="No land tenure records found"
          />

          <FactSheetTable<ProjectIdRow>
            title="Project ID Occurrence"
            description="Checks project ID consistency across all documents"
            status={fact_sheets.project_id.status}
            rows={fact_sheets.project_id.rows}
            columns={[
              { key: 'document', header: 'Document' },
              { key: 'document_type', header: 'Type' },
              { key: 'project_id', header: 'Project ID' },
            ]}
            issues={fact_sheets.project_id.issues}
            onIssueClick={handleIssueClick}
            emptyMessage="No project IDs found"
          />

          <FactSheetTable<QuantificationRow>
            title="Quantification"
            description="Validates GHG calculations and carbon metrics"
            status={fact_sheets.quantification.status}
            rows={fact_sheets.quantification.rows}
            columns={[
              { key: 'document', header: 'Document' },
              { key: 'metric', header: 'Metric' },
              {
                key: 'value',
                header: 'Value',
                render: (value, row) =>
                  value !== null
                    ? `${Number(value).toLocaleString()} ${row.unit || ''}`
                    : '-',
              },
            ]}
            issues={fact_sheets.quantification.issues}
            onIssueClick={handleIssueClick}
            emptyMessage="No quantification data found"
          />
        </div>
      </ScrollArea>
    </div>
  )
}
