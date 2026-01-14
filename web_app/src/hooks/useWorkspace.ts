import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Requirement, Evidence } from '@/contexts/WorkspaceContext'

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
    total: number
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
    queryFn: async (): Promise<EvidenceMatrixResponse> => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error } = await api.GET('/sessions/{session_id}/evidence-matrix', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Failed to fetch evidence matrix')
      return data as EvidenceMatrixResponse
    },
    enabled: !!sessionId,
    staleTime: 30000,
  })
}

export function useWorkspaceRequirements(sessionId: string | undefined) {
  const { data: matrixData, isLoading, isError, error } = useEvidenceMatrix(sessionId)

  const requirements = matrixData?.matrix
    ? transformMatrixToRequirements(matrixData.matrix)
    : []

  const requirementsByCategory = groupByCategory(requirements)

  const summary = matrixData?.summary ?? {
    total: 0,
    covered: 0,
    partial: 0,
    missing: 0,
  }

  return {
    requirements,
    requirementsByCategory,
    summary,
    isLoading,
    isError,
    error,
    hasData: matrixData !== undefined && matrixData.matrix.length > 0,
  }
}
