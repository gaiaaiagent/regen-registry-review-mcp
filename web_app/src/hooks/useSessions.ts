import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Session data returned from the API.
 * The backend derives status from workflow_progress.
 */
export interface Session {
  session_id: string
  project_name: string
  methodology: string
  project_id?: string
  created_at: string
  status: string
  workflow_progress: {
    current_stage: number
    stage_name: string
    completed_stages: string[]
  }
  documents_count?: number
  requirements_covered?: number
  requirements_total?: number
}

export interface SessionsResponse {
  sessions: Session[]
  total: number
}

export interface CreateSessionRequest {
  project_name: string
  methodology: string
  project_id?: string
}

export interface SessionResponse {
  session_id: string
  project_name: string
  methodology: string
  created_at: string
  requirements_total: number
  message: string
}

const SESSIONS_KEY = ['sessions'] as const

/**
 * Hook to fetch all sessions.
 */
export function useSessions() {
  return useQuery({
    queryKey: SESSIONS_KEY,
    queryFn: async (): Promise<SessionsResponse> => {
      const { data, error } = await api.GET('/sessions')
      if (error) throw new Error('Failed to fetch sessions')
      return data as SessionsResponse
    },
  })
}

/**
 * Hook to fetch a single session by ID.
 */
export function useSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ['session', sessionId],
    queryFn: async (): Promise<Session> => {
      if (!sessionId) throw new Error('Session ID required')
      const { data, error } = await api.GET('/sessions/{session_id}', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Failed to fetch session')
      return data as Session
    },
    enabled: !!sessionId,
  })
}

/**
 * Hook to create a new session.
 */
export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (request: CreateSessionRequest): Promise<SessionResponse> => {
      const { data, error } = await api.POST('/sessions', {
        body: request,
      })
      if (error) throw new Error('Failed to create session')
      return data as SessionResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
    },
  })
}

/**
 * Hook to delete a session.
 */
export function useDeleteSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (sessionId: string): Promise<void> => {
      const { error } = await api.DELETE('/sessions/{session_id}', {
        params: { path: { session_id: sessionId } },
      })
      if (error) throw new Error('Failed to delete session')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
    },
  })
}

/**
 * Available methodologies for new sessions.
 * These are derived from the checklist files in data/checklists/.
 */
export const METHODOLOGIES = [
  {
    id: 'soil-carbon-v1.2.2',
    name: 'Soil Organic Carbon v1.2.2',
    description: 'SOC Estimation in Regenerative Cropping and Managed Grassland Ecosystems',
  },
] as const

export type MethodologyId = typeof METHODOLOGIES[number]['id']
