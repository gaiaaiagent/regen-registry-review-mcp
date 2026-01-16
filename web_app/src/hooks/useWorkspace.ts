import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Requirement, Evidence } from '@/contexts/WorkspaceContext'
import { useValidation } from '@/hooks/useValidation'

interface BoundingBox {
  page: number
  x0: number
  y0: number
  x1: number
  y1: number
  match_score?: number
  rects?: Array<{ x0: number; y0: number; x1: number; y1: number }>
}

interface EvidenceMatrixRow {
  requirement_id: string
  category: string
  requirement_text: string
  status: 'covered' | 'partial' | 'missing'
  confidence: number
  source_document: string
  document_id: string
  snippet_id: string
  page: number
  section: string
  extracted_value: string
  evidence_text: string
  bounding_box: BoundingBox | null
  evidence_count: number
  verified_count: number
  pending_verification: number
  validation_type: string
  human_review_required: boolean
}

interface EvidenceMatrixResponse {
  session_id: string
  matrix: EvidenceMatrixRow[]
  summary: {
    total_requirements: number
    total?: number
    covered: number
    partial: number
    missing: number
  }
}

interface RequirementsByCategory {
  [category: string]: Requirement[]
}

function transformMatrixToRequirements(matrix: EvidenceMatrixRow[]): Requirement[] {
  const requirementMap = new Map<string, Requirement>()

  for (const row of matrix) {
    const existing = requirementMap.get(row.requirement_id)

    // Use snippet_id if available, otherwise generate one
    const evidenceId = row.snippet_id || `${row.requirement_id}-${row.document_id || row.source_document}-${row.page}`

    const evidence: Evidence = {
      id: evidenceId,
      documentId: row.document_id || row.source_document,
      pageNumber: row.page,
      text: row.evidence_text || row.extracted_value,
      section: row.section,
      boundingBox: row.bounding_box ? {
        x0: row.bounding_box.x0,
        y0: row.bounding_box.y0,
        x1: row.bounding_box.x1,
        y1: row.bounding_box.y1,
        page: row.bounding_box.page,
      } : undefined,
    }

    if (existing) {
      if (existing.evidence) {
        existing.evidence.push(evidence)
      } else {
        existing.evidence = [evidence]
      }
    } else {
      requirementMap.set(row.requirement_id, {
        id: row.requirement_id,
        category: row.category,
        text: row.requirement_text || row.requirement_id,
        status: row.status,
        confidence: row.confidence,
        extractedValue: row.extracted_value,
        humanReviewRequired: row.human_review_required,
        evidence: [evidence],
      })
    }
  }

  return Array.from(requirementMap.values())
}

function groupByCategory(requirements: Requirement[]): RequirementsByCategory {
  return requirements.reduce((acc, req) => {
    const category = req.category || 'Uncategorized'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(req)
    return acc
  }, {} as RequirementsByCategory)
}

export function useEvidenceMatrix(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['evidence-matrix', sessionId],
    queryFn: async (): Promise<EvidenceMatrixResponse | null> => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error, response } = await api.GET('/sessions/{session_id}/evidence-matrix', {
        params: { path: { session_id: sessionId } },
      })
      // 400 means evidence not yet extracted - return null instead of throwing
      if (response?.status === 400) {
        return null
      }
      if (error) {
        throw new Error('Unable to load requirements.')
      }
      return data as EvidenceMatrixResponse
    },
    enabled: !!sessionId,
    staleTime: 30000,
    retry: (failureCount, error) => {
      // Don't retry on "no evidence" responses
      if (error?.message?.includes('Evidence not yet extracted')) return false
      return failureCount < 2
    },
  })
}

export function useWorkspaceRequirements(sessionId: string | undefined) {
  const { data: matrixData, isLoading, isError, error } = useEvidenceMatrix(sessionId)

  const requirements = matrixData?.matrix
    ? transformMatrixToRequirements(matrixData.matrix)
    : []

  const requirementsByCategory = groupByCategory(requirements)

  // Map API response fields to frontend expected structure
  const apiSummary = matrixData?.summary
  const summary = {
    total: apiSummary?.total_requirements ?? apiSummary?.total ?? 0,
    covered: apiSummary?.covered ?? 0,
    partial: apiSummary?.partial ?? 0,
    missing: apiSummary?.missing ?? 0,
  }

  // Check if evidence has actually been extracted (not just requirements loaded)
  // Evidence exists when at least one requirement has coverage
  const hasData = matrixData !== null && matrixData !== undefined &&
    matrixData.matrix.length > 0 &&
    (matrixData.summary.covered > 0 || matrixData.summary.partial > 0)

  return {
    requirements,
    requirementsByCategory,
    summary,
    isLoading,
    isError,
    error,
    hasData,
  }
}

export function useDiscoverDocuments(sessionId: string | undefined) {
  return useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error } = await api.POST('/sessions/{session_id}/discover', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Document discovery failed')
      return data
    },
  })
}

export function useMapRequirements(sessionId: string | undefined) {
  return useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error } = await api.POST('/sessions/{session_id}/map', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Requirement mapping failed')
      return data
    },
  })
}

export function useConfirmAllMappings(sessionId: string | undefined) {
  return useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error } = await api.POST('/sessions/{session_id}/confirm-all-mappings', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Mapping confirmation failed')
      return data
    },
  })
}

export function useExtractEvidence(sessionId: string | undefined) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error } = await api.POST('/sessions/{session_id}/evidence', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Evidence extraction failed')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence-matrix', sessionId] })
    },
  })
}

export function useFullWorkflow(sessionId: string | undefined) {
  const queryClient = useQueryClient()
  const discoverMutation = useDiscoverDocuments(sessionId)
  const mapMutation = useMapRequirements(sessionId)
  const confirmMutation = useConfirmAllMappings(sessionId)
  const extractMutation = useExtractEvidence(sessionId)

  const runFullWorkflow = async (onProgress?: (stage: string) => void) => {
    if (!sessionId) throw new Error('Session ID required')

    onProgress?.('Discovering documents...')
    await discoverMutation.mutateAsync()

    onProgress?.('Mapping requirements...')
    await mapMutation.mutateAsync()

    onProgress?.('Confirming mappings...')
    await confirmMutation.mutateAsync()

    onProgress?.('Extracting evidence...')
    await extractMutation.mutateAsync()

    queryClient.invalidateQueries({ queryKey: ['evidence-matrix', sessionId] })

    return { success: true }
  }

  const isPending = discoverMutation.isPending || mapMutation.isPending ||
                    confirmMutation.isPending || extractMutation.isPending

  return {
    runFullWorkflow,
    isPending,
    currentStage: discoverMutation.isPending ? 'discover' :
                  mapMutation.isPending ? 'map' :
                  confirmMutation.isPending ? 'confirm' :
                  extractMutation.isPending ? 'extract' : null,
  }
}

/**
 * Hook to run the complete review workflow end-to-end:
 * Discover → Map → Confirm → Extract → Validate → Report
 *
 * One-click automation for clean projects where all documents are present.
 */
export function useCompleteReview(sessionId: string | undefined) {
  const queryClient = useQueryClient()
  const { runFullWorkflow } = useFullWorkflow(sessionId)

  // Use the validation hook's runValidation for proper caching
  const { runValidation } = useValidation(sessionId)

  const reportMutation = useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error } = await api.POST('/sessions/{session_id}/report', {
        params: {
          path: { session_id: sessionId },
          query: { format: 'markdown' },
        },
      })
      if (error) throw new Error('Report generation failed')
      return data
    },
  })

  const [currentStage, setCurrentStage] = useState<string | null>(null)
  const [isPending, setIsPending] = useState(false)

  const runCompleteReview = async (onProgress?: (stage: string) => void) => {
    if (!sessionId) throw new Error('Session ID required')

    setIsPending(true)
    try {
      // Run extraction workflow (discover, map, confirm, extract)
      await runFullWorkflow(onProgress)

      // Run validation using the validation hook (handles caching)
      onProgress?.('Running validation...')
      setCurrentStage('validate')
      await runValidation()

      // Generate report
      onProgress?.('Generating report...')
      setCurrentStage('report')
      await reportMutation.mutateAsync()

      // Invalidate queries to refresh UI
      queryClient.invalidateQueries({ queryKey: ['validation', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['existing-report', sessionId] })

      onProgress?.('Complete!')
      setCurrentStage(null)

      return { success: true }
    } catch (error) {
      throw error
    } finally {
      setIsPending(false)
      setCurrentStage(null)
    }
  }

  return {
    runCompleteReview,
    isPending,
    currentStage,
  }
}
