import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export type ValidationStatus = 'pass' | 'warning' | 'error'

export interface SourceReference {
  document_id: string
  document_name: string
  page_number: number
}

export interface ValidationIssue {
  requirement_id: string
  message: string
  severity: 'warning' | 'error'
  source?: SourceReference
}

export interface FactSheetRowBase {
  document: string
  document_id?: string
  page_number?: number
  review_status?: 'pending' | 'approved' | 'rejected'
}

export interface DateAlignmentRow extends FactSheetRowBase {
  start_date: string | null
  end_date: string | null
  document_type: string
}

export interface LandTenureRow extends FactSheetRowBase {
  owner_name: string | null
  area_hectares: number | null
  tenure_type: string | null
  expiry_date: string | null
}

export interface ProjectIdRow extends FactSheetRowBase {
  project_id: string | null
  document_type: string
}

export interface QuantificationRow extends FactSheetRowBase {
  metric: string
  value: number | null
  unit: string | null
}

export interface FactSheet<T> {
  status: ValidationStatus
  rows: T[]
  issues: ValidationIssue[]
}

export interface ValidationResults {
  session_id: string
  last_run: string
  is_stale: boolean
  evidence_updated_at: string | null
  summary: {
    passed: number
    warnings: number
    errors: number
    total_checks: number
  }
  fact_sheets: {
    date_alignment: FactSheet<DateAlignmentRow>
    land_tenure: FactSheet<LandTenureRow>
    project_id: FactSheet<ProjectIdRow>
    quantification: FactSheet<QuantificationRow>
  }
}

interface BackendValidationResponse {
  session_id: string
  status: string
  checks: Array<{
    check: string
    status: string
    details: Record<string, unknown>
  }>
  summary: {
    passed: number
    warnings: number
    errors: number
  }
}

function transformBackendResponse(
  response: BackendValidationResponse,
  sessionId: string,
  evidenceUpdatedAt: string | null
): ValidationResults {
  const checks = response.checks || []

  const dateAlignmentCheck = checks.find(c => c.check === 'date_alignment')
  const landTenureCheck = checks.find(c => c.check === 'land_tenure')
  const projectIdCheck = checks.find(c => c.check === 'project_id_consistency')
  const quantificationCheck = checks.find(c => c.check === 'quantification')

  const extractRows = <T>(check: typeof checks[0] | undefined, key: string): T[] => {
    if (!check?.details) return []
    const data = check.details[key]
    return Array.isArray(data) ? data : []
  }

  const extractIssues = (check: typeof checks[0] | undefined): ValidationIssue[] => {
    if (!check?.details) return []
    const issues = check.details.issues || check.details.discrepancies
    if (!Array.isArray(issues)) return []
    return issues.map((issue: { requirement_id?: string; message?: string; description?: string }) => ({
      requirement_id: issue.requirement_id || '',
      message: issue.message || issue.description || '',
      severity: check.status === 'error' ? 'error' : 'warning' as const,
    }))
  }

  const mapStatus = (status: string | undefined): ValidationStatus => {
    if (!status) return 'pass'
    if (status === 'passed' || status === 'pass') return 'pass'
    if (status === 'warning') return 'warning'
    return 'error'
  }

  return {
    session_id: sessionId,
    last_run: new Date().toISOString(),
    is_stale: false,
    evidence_updated_at: evidenceUpdatedAt,
    summary: {
      passed: response.summary?.passed ?? 0,
      warnings: response.summary?.warnings ?? 0,
      errors: response.summary?.errors ?? 0,
      total_checks: checks.length,
    },
    fact_sheets: {
      date_alignment: {
        status: mapStatus(dateAlignmentCheck?.status),
        rows: extractRows<DateAlignmentRow>(dateAlignmentCheck, 'dates') ||
              extractRows<DateAlignmentRow>(dateAlignmentCheck, 'documents') ||
              (dateAlignmentCheck?.details?.sampling_dates ? [{
                document: 'Sampling Data',
                start_date: (dateAlignmentCheck.details.sampling_dates as string[])?.[0] || null,
                end_date: null,
                document_type: 'sampling',
              }] : []),
        issues: extractIssues(dateAlignmentCheck),
      },
      land_tenure: {
        status: mapStatus(landTenureCheck?.status),
        rows: extractRows<LandTenureRow>(landTenureCheck, 'tenure_records') ||
              extractRows<LandTenureRow>(landTenureCheck, 'records'),
        issues: extractIssues(landTenureCheck),
      },
      project_id: {
        status: mapStatus(projectIdCheck?.status),
        rows: extractRows<ProjectIdRow>(projectIdCheck, 'project_ids') ||
              extractRows<ProjectIdRow>(projectIdCheck, 'occurrences'),
        issues: extractIssues(projectIdCheck),
      },
      quantification: {
        status: mapStatus(quantificationCheck?.status),
        rows: extractRows<QuantificationRow>(quantificationCheck, 'metrics') ||
              extractRows<QuantificationRow>(quantificationCheck, 'calculations'),
        issues: extractIssues(quantificationCheck),
      },
    },
  }
}

const VALIDATION_STORAGE_KEY = 'registry-review-validation'

function loadCachedValidation(sessionId: string): ValidationResults | null {
  try {
    const stored = localStorage.getItem(`${VALIDATION_STORAGE_KEY}:${sessionId}`)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

function saveCachedValidation(sessionId: string, results: ValidationResults): void {
  try {
    localStorage.setItem(`${VALIDATION_STORAGE_KEY}:${sessionId}`, JSON.stringify(results))
  } catch (error) {
    console.error('Failed to cache validation results:', error)
  }
}

export function useValidation(sessionId: string | undefined) {
  const queryClient = useQueryClient()

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['validation', sessionId],
    queryFn: async (): Promise<ValidationResults | null> => {
      if (!sessionId) return null

      const cached = loadCachedValidation(sessionId)
      if (cached) {
        const evidenceMatrixData = queryClient.getQueryData(['evidence-matrix', sessionId]) as { updated_at?: string } | undefined
        const evidenceUpdatedAt = evidenceMatrixData?.updated_at || null

        if (cached.evidence_updated_at && evidenceUpdatedAt) {
          const cacheTime = new Date(cached.last_run).getTime()
          const evidenceTime = new Date(evidenceUpdatedAt).getTime()
          if (cacheTime > evidenceTime) {
            return cached
          }
          return { ...cached, is_stale: true }
        }
        return cached
      }

      return null
    },
    enabled: !!sessionId,
    staleTime: Infinity,
  })

  const runValidationMutation = useMutation({
    mutationFn: async (): Promise<ValidationResults> => {
      if (!sessionId) throw new Error('Session ID required')

      const { data: responseData, error: apiError } = await api.POST('/sessions/{session_id}/validate', {
        params: { path: { session_id: sessionId } },
      })

      if (apiError) {
        throw new Error('Validation failed. Please ensure evidence has been extracted and try again.')
      }

      const evidenceMatrixData = queryClient.getQueryData(['evidence-matrix', sessionId]) as { updated_at?: string } | undefined
      const evidenceUpdatedAt = evidenceMatrixData?.updated_at || new Date().toISOString()

      const results = transformBackendResponse(
        responseData as BackendValidationResponse,
        sessionId,
        evidenceUpdatedAt
      )

      saveCachedValidation(sessionId, results)
      return results
    },
    onSuccess: (results) => {
      queryClient.setQueryData(['validation', sessionId], results)
    },
  })

  const isStale = data?.is_stale ?? false
  const hasValidation = data !== null && data !== undefined

  return {
    validation: data,
    isLoading,
    isError,
    error,
    isStale,
    hasValidation,
    isRunning: runValidationMutation.isPending,
    runValidation: runValidationMutation.mutateAsync,
    refetch,
  }
}
