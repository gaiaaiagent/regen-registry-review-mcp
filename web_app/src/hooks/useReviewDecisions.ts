import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api/client'

export type OverrideStatus = 'approved' | 'rejected' | 'needs_revision' | 'conditional' | 'pending'
export type DeterminationStatus = 'approve' | 'conditional' | 'reject' | 'hold'

export interface RequirementOverride {
  requirement_id: string
  status: OverrideStatus
  notes?: string | null
  set_by: string
  set_at: string
}

export interface ReviewStatusSummary {
  total_overrides: number
  total_annotations: number
  approved: number
  rejected: number
  needs_revision: number
  conditional: number
  pending: number
}

export interface ReviewStatusResponse {
  session_id: string
  overrides: Record<string, RequirementOverride>
  annotations: Record<string, Array<{
    type: string
    note: string
    added_by: string
    added_at: string
  }>>
  summary: ReviewStatusSummary
}

export interface FinalDetermination {
  determination: DeterminationStatus | null
  notes?: string | null
  conditions?: string | null
  set_by?: string | null
  set_at?: string | null
  history?: Array<{
    previous_determination?: DeterminationStatus
    changed_by: string
    changed_at: string
  }>
}

export function useReviewStatus(sessionId: string | null) {
  return useQuery({
    queryKey: ['review-status', sessionId],
    queryFn: async () => {
      if (!sessionId) return null
      const { data, error } = await api.GET('/sessions/{session_id}/review-status', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Failed to fetch review status')
      return data as ReviewStatusResponse
    },
    enabled: !!sessionId,
  })
}

export function useRequirementOverride(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      requirementId,
      status,
      notes,
      reviewer = 'user',
    }: {
      requirementId: string
      status: OverrideStatus
      notes?: string
      reviewer?: string
    }) => {
      if (!sessionId) throw new Error('No session')

      const { data, error } = await api.POST('/sessions/{session_id}/override', {
        params: { path: { session_id: sessionId } },
        body: {
          requirement_id: requirementId,
          override_status: status,
          notes,
          reviewer,
        },
      })
      if (error) throw new Error('Failed to set override')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-status', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['requirements', sessionId] })
    },
  })
}

export function useClearOverride(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      requirementId,
      reviewer = 'user',
    }: {
      requirementId: string
      reviewer?: string
    }) => {
      if (!sessionId) throw new Error('No session')

      const { data, error } = await api.DELETE('/sessions/{session_id}/override/{requirement_id}', {
        params: {
          path: { session_id: sessionId, requirement_id: requirementId },
          query: { reviewer },
        },
      })
      if (error) throw new Error('Failed to clear override')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-status', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['requirements', sessionId] })
    },
  })
}

export function useFinalDetermination(sessionId: string | null) {
  return useQuery({
    queryKey: ['determination', sessionId],
    queryFn: async () => {
      if (!sessionId) return null
      const { data, error } = await api.GET('/sessions/{session_id}/determination', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Failed to fetch determination')
      return data as FinalDetermination & { session_id: string }
    },
    enabled: !!sessionId,
  })
}

export function useSetFinalDetermination(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      determination,
      notes,
      conditions,
      reviewer = 'user',
    }: {
      determination: DeterminationStatus
      notes: string
      conditions?: string
      reviewer?: string
    }) => {
      if (!sessionId) throw new Error('No session')

      const { data, error } = await api.POST('/sessions/{session_id}/determination', {
        params: { path: { session_id: sessionId } },
        body: {
          determination,
          notes,
          conditions,
          reviewer,
        },
      })
      if (error) throw new Error('Failed to set determination')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['determination', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    },
  })
}

export function useClearDetermination(sessionId: string | null) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ reviewer = 'user' }: { reviewer?: string } = {}) => {
      if (!sessionId) throw new Error('No session')

      const { data, error } = await api.DELETE('/sessions/{session_id}/determination', {
        params: {
          path: { session_id: sessionId },
          query: { reviewer },
        },
      })
      if (error) throw new Error('Failed to clear determination')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['determination', sessionId] })
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
    },
  })
}
