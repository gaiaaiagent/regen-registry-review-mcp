import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

export type VerificationStatus = 'unverified' | 'verified' | 'rejected' | 'partial' | 'needs_context'

export interface SnippetVerification {
  snippetId: string
  requirementId: string
  status: VerificationStatus
  notes?: string
}

export interface VerificationSummary {
  requirementId: string
  totalSnippets: number
  verified: number
  rejected: number
  pending: number
  progress: number
}

export interface SessionVerificationStatus {
  sessionId: string
  summaries: VerificationSummary[]
  overall: {
    totalSnippets: number
    verified: number
    rejected: number
    pending: number
    progress: number
  }
}

export function useVerificationStatus(sessionId: string | null) {
  return useQuery({
    queryKey: ['verification-status', sessionId],
    queryFn: async () => {
      if (!sessionId) return null
      const { data, error } = await api.GET('/sessions/{session_id}/verification-status', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Failed to fetch verification status')
      return data as SessionVerificationStatus
    },
    enabled: !!sessionId,
  })
}

export function useVerifySnippet(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      snippetId,
      requirementId,
      status,
      notes,
    }: {
      snippetId: string
      requirementId: string
      status: VerificationStatus
      notes?: string
    }) => {
      if (!sessionId) throw new Error('No session')

      const { data, error } = await api.POST('/sessions/{session_id}/verify-extraction', {
        params: { path: { session_id: sessionId } },
        body: {
          snippet_id: snippetId,
          requirement_id: requirementId,
          status,
          notes,
          reviewer: 'user',
        },
      })
      if (error) throw new Error('Failed to verify snippet')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-status', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['evidence-matrix', sessionId] })
    },
  })
}

export function useBulkVerify(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (snippets: { snippetId: string; requirementId: string }[]) => {
      if (!sessionId) throw new Error('No session')

      const results = await Promise.all(
        snippets.map(({ snippetId, requirementId }) =>
          api.POST('/sessions/{session_id}/verify-extraction', {
            params: { path: { session_id: sessionId } },
            body: {
              snippet_id: snippetId,
              requirement_id: requirementId,
              status: 'verified',
              reviewer: 'user',
            },
          })
        )
      )

      const failed = results.filter((r) => r.error)
      if (failed.length > 0) {
        throw new Error(`Failed to verify ${failed.length} snippets`)
      }

      return results.length
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verification-status', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['evidence-matrix', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['requirements', sessionId] })
    },
  })
}
