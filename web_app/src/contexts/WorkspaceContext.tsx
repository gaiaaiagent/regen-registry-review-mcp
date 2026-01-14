/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from 'react'
import type { BoundingBox, ManualEvidence, ScratchpadItem } from '@/hooks/useManualEvidence'

export interface Evidence {
  id: string
  documentId: string
  pageNumber: number
  text: string
  section?: string
  boundingBox?: {
    x0: number
    y0: number
    x1: number
    y1: number
    page: number
  }
}

export interface Requirement {
  id: string
  category: string
  text: string
  status: 'covered' | 'partial' | 'missing' | 'not_started'
  confidence?: number
  evidence?: Evidence[]
  extractedValue?: string
  humanReviewRequired?: boolean
}

export interface DragData {
  type: 'pdf-selection' | 'scratchpad-item'
  text: string
  documentId: string
  pageNumber: number
  boundingBox?: BoundingBox
  evidenceId?: string
}

interface WorkspaceContextType {
  activeDocumentId: string | null
  setActiveDocumentId: (id: string | null) => void
  focusedRequirementId: string | null
  setFocusedRequirementId: (id: string | null) => void
  targetPage: number | null
  setTargetPage: (page: number | null) => void
  scrollToEvidence: (documentId: string, pageNumber: number) => void
  registerScrollHandler: (handler: (pageNumber: number) => void) => void
  isDragging: boolean
  setIsDragging: (dragging: boolean) => void
  currentDragData: DragData | null
  setCurrentDragData: (data: DragData | null) => void
  pendingSelection: PendingSelection | null
  setPendingSelection: (selection: PendingSelection | null) => void
  scratchpadItems: ScratchpadItem[]
  setScratchpadItems: React.Dispatch<React.SetStateAction<ScratchpadItem[]>>
  manualEvidence: ManualEvidence[]
  setManualEvidence: React.Dispatch<React.SetStateAction<ManualEvidence[]>>
  externalHighlight: ExternalHighlight | null
  highlightFromCoordinates: (highlight: ExternalHighlight | null) => void
}

export interface PendingSelection {
  text: string
  documentId: string
  pageNumber: number
  boundingBox?: BoundingBox
  position: { x: number; y: number }
}

export interface ExternalHighlight {
  documentId: string
  pageNumber: number
  boundingBox: {
    x0: number  // normalized 0-1
    y0: number
    x1: number
    y1: number
  }
  text?: string
}

const WorkspaceContext = createContext<WorkspaceContextType | null>(null)

interface WorkspaceProviderProps {
  children: ReactNode
  initialDocumentId?: string | null
}

export function WorkspaceProvider({ children, initialDocumentId = null }: WorkspaceProviderProps) {
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(initialDocumentId)
  const [focusedRequirementId, setFocusedRequirementId] = useState<string | null>(null)
  const [targetPage, setTargetPage] = useState<number | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [currentDragData, setCurrentDragData] = useState<DragData | null>(null)
  const [pendingSelection, setPendingSelection] = useState<PendingSelection | null>(null)
  const [scratchpadItems, setScratchpadItems] = useState<ScratchpadItem[]>([])
  const [manualEvidence, setManualEvidence] = useState<ManualEvidence[]>([])
  const [externalHighlight, setExternalHighlight] = useState<ExternalHighlight | null>(null)
  const scrollHandlerRef = useRef<((pageNumber: number) => void) | null>(null)

  const scrollToEvidence = useCallback((documentId: string, pageNumber: number) => {
    if (documentId !== activeDocumentId) {
      setActiveDocumentId(documentId)
      setTargetPage(pageNumber)
    } else if (scrollHandlerRef.current) {
      scrollHandlerRef.current(pageNumber)
    }
  }, [activeDocumentId])

  const registerScrollHandler = useCallback((handler: (pageNumber: number) => void) => {
    scrollHandlerRef.current = handler
    if (targetPage !== null) {
      handler(targetPage)
      setTargetPage(null)
    }
  }, [targetPage])

  const highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const highlightFromCoordinates = useCallback((highlight: ExternalHighlight | null) => {
    if (highlight) {
      // Switch to the document if needed and scroll to the page
      if (highlight.documentId !== activeDocumentId) {
        setActiveDocumentId(highlight.documentId)
        setTargetPage(highlight.pageNumber)
      } else if (scrollHandlerRef.current) {
        scrollHandlerRef.current(highlight.pageNumber)
      }
    }
    setExternalHighlight(highlight)
  }, [activeDocumentId])

  const value: WorkspaceContextType = {
    activeDocumentId,
    setActiveDocumentId,
    focusedRequirementId,
    setFocusedRequirementId,
    targetPage,
    setTargetPage,
    scrollToEvidence,
    registerScrollHandler,
    isDragging,
    setIsDragging,
    currentDragData,
    setCurrentDragData,
    pendingSelection,
    setPendingSelection,
    scratchpadItems,
    setScratchpadItems,
    manualEvidence,
    setManualEvidence,
    externalHighlight,
    highlightFromCoordinates,
  }

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspaceContext(): WorkspaceContextType {
  const context = useContext(WorkspaceContext)
  if (!context) {
    throw new Error('useWorkspaceContext must be used within a WorkspaceProvider')
  }
  return context
}
