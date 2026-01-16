import { useCallback, useState, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { ShieldCheck, AlertCircle, Play, RefreshCw, AlertTriangle, CheckCircle2, XCircle, Info } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { ValidationSummary } from './ValidationSummary'
import { FactSheetTable } from './FactSheetTable'
import { useValidation } from '@/hooks/useValidation'
import { useExtractEvidence } from '@/hooks/useWorkspace'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'
import { cn } from '@/lib/utils'
import type {
  DateAlignmentRow,
  LandTenureRow,
  ProjectIdRow,
  QuantificationRow,
  GeneralCheck,
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
  const { setFocusedRequirementId, scrollToEvidence } = useWorkspaceContext()
  const [isReextracting, setIsReextracting] = useState(false)

  const {
    validation,
    isLoading,
    isError,
    isStale,
    hasValidation,
    isRunning,
    runValidation,
  } = useValidation(sessionId)

  const extractEvidence = useExtractEvidence(sessionId)

  const handleIssueClick = (requirementId: string) => {
    setFocusedRequirementId(requirementId)
    onSwitchToChecklist?.()
  }

  const handleShowSource = useCallback((documentId: string, pageNumber: number) => {
    scrollToEvidence(documentId, pageNumber)
    toast.success('Navigated to source', {
      description: `Page ${pageNumber}`,
    })
  }, [scrollToEvidence])

  const handleReviewStatusChange = useCallback((rowIndex: number, status: 'approved' | 'rejected') => {
    toast.info(`Row ${rowIndex + 1} marked as ${status}`, {
      description: 'Review status updated (local only)',
    })
  }, [])

  const handleRunValidation = async () => {
    try {
      await runValidation()
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleReextractAndValidate = async () => {
    setIsReextracting(true)
    try {
      toast.info('Re-extracting evidence...', {
        description: 'This may take a few minutes for large document sets.',
      })
      await extractEvidence.mutateAsync()
      toast.success('Evidence re-extracted', {
        description: 'Now running validation with structured field data...',
      })
      await runValidation()
      toast.success('Validation complete')
    } catch (error) {
      console.error('Re-extraction failed:', error)
      toast.error('Re-extraction failed', {
        description: 'Please try again or check the console for details.',
      })
    } finally {
      setIsReextracting(false)
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

  const { summary, fact_sheets, last_run, general_checks } = validation!

  // Filter general checks to show warnings and errors
  const warningChecks = useMemo(() =>
    (general_checks || []).filter(c => c.status === 'warning'),
    [general_checks]
  )
  const errorChecks = useMemo(() =>
    (general_checks || []).filter(c => c.status === 'error'),
    [general_checks]
  )
  const hasGeneralIssues = warningChecks.length > 0 || errorChecks.length > 0

  // Check if validation ran but found no data (structured fields missing)
  const hasNoData = summary.total_checks === 0 &&
    fact_sheets.date_alignment.rows.length === 0 &&
    fact_sheets.land_tenure.rows.length === 0 &&
    fact_sheets.project_id.rows.length === 0 &&
    fact_sheets.quantification.rows.length === 0

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
          isRunning={isRunning || isReextracting}
          onRunValidation={handleRunValidation}
        />
      </div>

      {hasNoData && (
        <div className="mx-4 my-3 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-500 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-700 dark:text-yellow-300">
                No structured data found for validation
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Evidence was extracted without structured field data (dates, owner names, project IDs).
                Re-extract evidence to enable validation checks.
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={handleReextractAndValidate}
                disabled={isReextracting || extractEvidence.isPending}
              >
                {isReextracting || extractEvidence.isPending ? (
                  <>
                    <RefreshCw className="h-3 w-3 mr-2 animate-spin" />
                    Re-extracting...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-3 w-3 mr-2" />
                    Re-extract Evidence & Validate
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

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
            onShowSource={handleShowSource}
            onReviewStatusChange={handleReviewStatusChange}
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
            onShowSource={handleShowSource}
            onReviewStatusChange={handleReviewStatusChange}
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
            onShowSource={handleShowSource}
            onReviewStatusChange={handleReviewStatusChange}
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
            onShowSource={handleShowSource}
            onReviewStatusChange={handleReviewStatusChange}
            emptyMessage="No quantification data found"
          />

          {hasGeneralIssues && (
            <div className="border rounded-lg overflow-hidden bg-card">
              <div className="px-4 py-3 border-b bg-muted/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-blue-500" />
                    <h3 className="font-medium text-sm">General Validation Checks</h3>
                  </div>
                  <div className="flex items-center gap-2">
                    {warningChecks.length > 0 && (
                      <Badge variant="warning">{warningChecks.length} warning{warningChecks.length !== 1 ? 's' : ''}</Badge>
                    )}
                    {errorChecks.length > 0 && (
                      <Badge variant="destructive">{errorChecks.length} error{errorChecks.length !== 1 ? 's' : ''}</Badge>
                    )}
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Additional structural and cross-document validation results
                </p>
              </div>

              <div className="p-4 space-y-2">
                {errorChecks.map((check) => (
                  <div
                    key={check.check_id}
                    className="flex items-start gap-2 p-2 rounded bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800"
                  >
                    <XCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-red-700 dark:text-red-300">
                          {check.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <Badge variant="outline" className="text-[10px] px-1 py-0">
                          {check.check_type}
                        </Badge>
                      </div>
                      <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                        {check.message}
                      </p>
                    </div>
                  </div>
                ))}
                {warningChecks.map((check) => (
                  <div
                    key={check.check_id}
                    className="flex items-start gap-2 p-2 rounded bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800"
                  >
                    <AlertTriangle className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-yellow-700 dark:text-yellow-300">
                          {check.field_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <Badge variant="outline" className="text-[10px] px-1 py-0">
                          {check.check_type}
                        </Badge>
                      </div>
                      <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-1">
                        {check.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
