import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import { api } from '@/lib/api'

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export interface ManualEvidence {
  id: string
  requirementId: string | null
  documentId: string
  pageNumber: number
  text: string
  boundingBox?: BoundingBox
  createdAt: string
}

export type ScratchpadItem = ManualEvidence & { requirementId: null }

const STORAGE_KEY = 'registry-review-manual-evidence'

function generateId(): string {
  return `evidence-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

function loadFromStorage(sessionId: string): ManualEvidence[] {
  try {
    const stored = localStorage.getItem(`${STORAGE_KEY}:${sessionId}`)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

function saveToStorage(sessionId: string, evidence: ManualEvidence[]): void {
  try {
    localStorage.setItem(`${STORAGE_KEY}:${sessionId}`, JSON.stringify(evidence))
  } catch (error) {
    console.error('Failed to save evidence to localStorage:', error)
  }
}

interface CreateEvidenceInput {
  documentId: string
  pageNumber: number
  text: string
  boundingBox?: BoundingBox
  requirementId?: string | null
}

export function useManualEvidence(sessionId: string | undefined) {
  const [evidence, setEvidence] = useState<ManualEvidence[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) {
      setEvidence([])
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    const loaded = loadFromStorage(sessionId)
    setEvidence(loaded)
    setIsLoading(false)
  }, [sessionId])

  const scratchpadItems = evidence.filter(
    (e): e is ScratchpadItem => e.requirementId === null
  )

  const linkedEvidence = evidence.filter((e) => e.requirementId !== null)

  const getEvidenceForRequirement = useCallback(
    (requirementId: string) => evidence.filter((e) => e.requirementId === requirementId),
    [evidence]
  )

  const addEvidence = useCallback(
    async (input: CreateEvidenceInput): Promise<ManualEvidence> => {
      if (!sessionId) throw new Error('Session ID required')

      const newEvidence: ManualEvidence = {
        id: generateId(),
        documentId: input.documentId,
        pageNumber: input.pageNumber,
        text: input.text,
        boundingBox: input.boundingBox,
        requirementId: input.requirementId ?? null,
        createdAt: new Date().toISOString(),
      }

      setEvidence((prev) => {
        const updated = [...prev, newEvidence]
        saveToStorage(sessionId, updated)
        return updated
      })

      if (input.requirementId) {
        try {
          await api.POST('/sessions/{session_id}/annotation', {
            params: { path: { session_id: sessionId } },
            body: {
              requirement_id: input.requirementId,
              note: `Manual evidence linked: "${input.text.substring(0, 100)}..." (Page ${input.pageNumber})`,
              annotation_type: 'note',
              reviewer: 'user',
            },
          })
        } catch {
          console.warn('Failed to save annotation to API, evidence stored locally')
        }
      }

      return newEvidence
    },
    [sessionId]
  )

  const linkToRequirement = useCallback(
    async (evidenceId: string, requirementId: string): Promise<boolean> => {
      if (!sessionId) return false

      const evidenceItem = evidence.find((e) => e.id === evidenceId)
      if (!evidenceItem) return false

      setEvidence((prev) => {
        const updated = prev.map((e) =>
          e.id === evidenceId ? { ...e, requirementId } : e
        )
        saveToStorage(sessionId, updated)
        return updated
      })

      toast.success('Evidence linked', {
        description: `Linked to ${requirementId}`,
      })

      try {
        await api.POST('/sessions/{session_id}/annotation', {
          params: { path: { session_id: sessionId } },
          body: {
            requirement_id: requirementId,
            note: `Manual evidence linked: "${evidenceItem.text.substring(0, 100)}..." (Page ${evidenceItem.pageNumber})`,
            annotation_type: 'note',
            reviewer: 'user',
          },
        })
        return true
      } catch {
        console.warn('Failed to save annotation to API, evidence stored locally')
        return true
      }
    },
    [sessionId, evidence]
  )

  const unlinkEvidence = useCallback(
    (evidenceId: string) => {
      if (!sessionId) return

      setEvidence((prev) => {
        const updated = prev.map((e) =>
          e.id === evidenceId ? { ...e, requirementId: null } : e
        )
        saveToStorage(sessionId, updated)
        return updated
      })

      toast.info('Evidence unlinked', {
        description: 'Moved to scratchpad',
      })
    },
    [sessionId]
  )

  const removeEvidence = useCallback(
    (evidenceId: string) => {
      if (!sessionId) return

      setEvidence((prev) => {
        const updated = prev.filter((e) => e.id !== evidenceId)
        saveToStorage(sessionId, updated)
        return updated
      })

      toast.info('Evidence removed')
    },
    [sessionId]
  )

  const clearScratchpad = useCallback(() => {
    if (!sessionId) return

    setEvidence((prev) => {
      const updated = prev.filter((e) => e.requirementId !== null)
      saveToStorage(sessionId, updated)
      return updated
    })

    toast.info('Scratchpad cleared')
  }, [sessionId])

  return {
    evidence,
    scratchpadItems,
    linkedEvidence,
    isLoading,
    getEvidenceForRequirement,
    addEvidence,
    linkToRequirement,
    unlinkEvidence,
    removeEvidence,
    clearScratchpad,
  }
}
