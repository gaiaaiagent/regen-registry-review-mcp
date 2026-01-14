import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import {
  generateMockProjects,
  getAssignedProjects,
  getProject,
  updateRevisionResponse,
  type ProponentProject,
  type RevisionRequest,
} from '@/lib/mockProponentData'

export function useAssignedProjects() {
  const { user } = useAuth()
  const [projects, setProjects] = useState<ProponentProject[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!user?.email) {
      setProjects([])
      setIsLoading(false)
      return
    }

    // Simulate loading delay
    const timer = setTimeout(() => {
      const existingProjects = getAssignedProjects(user.email)
      if (existingProjects.length > 0) {
        setProjects(existingProjects)
      } else {
        // Generate mock data on first load
        const mockProjects = generateMockProjects(user.email)
        setProjects(mockProjects)
      }
      setIsLoading(false)
    }, 300)

    return () => clearTimeout(timer)
  }, [user?.email])

  const refetch = useCallback(() => {
    if (!user?.email) return
    const updatedProjects = getAssignedProjects(user.email)
    setProjects(updatedProjects)
  }, [user?.email])

  return { projects, isLoading, refetch }
}

export function useProjectRevisions(sessionId: string | undefined) {
  const [project, setProject] = useState<ProponentProject | null>(null)
  const [revisions, setRevisions] = useState<RevisionRequest[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) {
      setProject(null)
      setRevisions([])
      setIsLoading(false)
      return
    }

    // Simulate loading delay
    const timer = setTimeout(() => {
      const projectData = getProject(sessionId)
      setProject(projectData)
      setRevisions(projectData?.revisions ?? [])
      setIsLoading(false)
    }, 200)

    return () => clearTimeout(timer)
  }, [sessionId])

  const refetch = useCallback(() => {
    if (!sessionId) return
    const projectData = getProject(sessionId)
    setProject(projectData)
    setRevisions(projectData?.revisions ?? [])
  }, [sessionId])

  return { project, revisions, isLoading, refetch }
}

export function useRespondToRevision() {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const respond = useCallback(
    async (
      sessionId: string,
      revisionId: string,
      response: { comment: string; documentId?: string }
    ): Promise<ProponentProject | null> => {
      setIsSubmitting(true)

      // Simulate network delay
      await new Promise((resolve) => setTimeout(resolve, 500))

      const updated = updateRevisionResponse(sessionId, revisionId, response)
      setIsSubmitting(false)

      return updated
    },
    []
  )

  return { respond, isSubmitting }
}

export type { ProponentProject, RevisionRequest }
