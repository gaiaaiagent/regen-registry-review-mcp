import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Requirement, Evidence } from '@/contexts/WorkspaceContext'

interface EvidenceMatrixRow {
  requirement_id: string
  category: string
  status: 'covered' | 'partial' | 'missing'
  confidence: number
  source_document: string
  page: number
  section: string
  extracted_value: string
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

    const evidence: Evidence = {
      id: `${row.requirement_id}-${row.source_document}-${row.page}`,
      documentId: row.source_document,
      pageNumber: row.page,
      text: row.extracted_value,
      section: row.section,
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
        text: row.requirement_id,
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
