import { useState, useEffect, useCallback } from 'react'
import type { ExtendedHighlight, NewExtendedHighlight } from '@/types/highlight'

const STORAGE_KEY_PREFIX = 'registry-review-highlights'

function generateId(): string {
  return `highlight-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function getStorageKey(documentId: string): string {
  return `${STORAGE_KEY_PREFIX}:${documentId}`
}

/**
 * Hook for managing highlights with localStorage persistence.
 * Each document has its own set of highlights stored separately.
 */
export function useHighlights(documentId: string) {
  const [highlights, setHighlights] = useState<ExtendedHighlight[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Load highlights from localStorage on mount or when documentId changes
  useEffect(() => {
    setIsLoading(true)
    try {
      const stored = localStorage.getItem(getStorageKey(documentId))
      if (stored) {
        const parsed = JSON.parse(stored)
        setHighlights(parsed)
      } else {
        setHighlights([])
      }
    } catch (error) {
      console.error('Failed to load highlights from localStorage:', error)
      setHighlights([])
    } finally {
      setIsLoading(false)
    }
  }, [documentId])

  // Persist highlights to localStorage whenever they change
  const persistHighlights = useCallback((newHighlights: ExtendedHighlight[]) => {
    try {
      localStorage.setItem(getStorageKey(documentId), JSON.stringify(newHighlights))
    } catch (error) {
      console.error('Failed to save highlights to localStorage:', error)
    }
  }, [documentId])

  const addHighlight = useCallback((newHighlight: NewExtendedHighlight): ExtendedHighlight => {
    const highlight: ExtendedHighlight = {
      ...newHighlight,
      id: generateId(),
      documentId,
      createdAt: new Date().toISOString(),
    }

    setHighlights(prev => {
      const updated = [...prev, highlight]
      persistHighlights(updated)
      return updated
    })

    return highlight
  }, [documentId, persistHighlights])

  const updateHighlight = useCallback((
    highlightId: string,
    updates: Partial<Pick<ExtendedHighlight, 'comment' | 'requirementId'>>
  ) => {
    setHighlights(prev => {
      const updated = prev.map(h =>
        h.id === highlightId
          ? { ...h, ...updates, updatedAt: new Date().toISOString() }
          : h
      )
      persistHighlights(updated)
      return updated
    })
  }, [persistHighlights])

  const removeHighlight = useCallback((highlightId: string) => {
    setHighlights(prev => {
      const updated = prev.filter(h => h.id !== highlightId)
      persistHighlights(updated)
      return updated
    })
  }, [persistHighlights])

  const clearHighlights = useCallback(() => {
    setHighlights([])
    localStorage.removeItem(getStorageKey(documentId))
  }, [documentId])

  return {
    highlights,
    isLoading,
    addHighlight,
    updateHighlight,
    removeHighlight,
    clearHighlights,
  }
}

/**
 * Hook to get all highlights across all documents.
 * Useful for the evidence scratchpad feature.
 */
export function useAllHighlights() {
  const [allHighlights, setAllHighlights] = useState<Map<string, ExtendedHighlight[]>>(new Map())

  useEffect(() => {
    const highlights = new Map<string, ExtendedHighlight[]>()

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith(STORAGE_KEY_PREFIX)) {
        try {
          const documentId = key.replace(`${STORAGE_KEY_PREFIX}:`, '')
          const stored = localStorage.getItem(key)
          if (stored) {
            highlights.set(documentId, JSON.parse(stored))
          }
        } catch (error) {
          console.error('Failed to load highlights:', error)
        }
      }
    }

    setAllHighlights(highlights)
  }, [])

  const totalCount = Array.from(allHighlights.values()).reduce(
    (sum, arr) => sum + arr.length,
    0
  )

  return {
    allHighlights,
    totalCount,
  }
}
