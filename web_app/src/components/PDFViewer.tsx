import { useState, useCallback, useRef, useEffect } from 'react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import {
  PdfLoader,
  PdfHighlighter,
  Tip,
  Highlight as HighlightComponent,
  AreaHighlight,
  Popup,
} from 'react-pdf-highlighter'
import type { IHighlight, Content, ScaledPosition } from 'react-pdf-highlighter'

interface PDFDocument {
  numPages: number
  getPage: (pageNumber: number) => Promise<{
    getTextContent: () => Promise<{ items: unknown[] }>
  }>
}
import { useHighlights } from '@/hooks/useHighlights'
import { useWorkspaceContext, type DragData } from '@/contexts/WorkspaceContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  AlertTriangle,
  Loader2,
  Trash2,
  Clipboard,
  GripVertical,
  Link2,
} from 'lucide-react'

import { GlobalWorkerOptions } from 'pdfjs-dist'
GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString()

interface PDFViewerProps {
  url: string
  documentId: string
  onHighlightAdded?: (highlight: IHighlight) => void
  initialPage?: number
  onScrollHandlerReady?: (handler: (pageNumber: number) => void) => void
  onClipText?: (text: string, pageNumber: number, boundingBox?: { x: number; y: number; width: number; height: number }) => void
}

interface PDFContentProps {
  pdfDocument: PDFDocument
  highlights: IHighlight[]
  scrollToHighlightId: string | null
  scrollViewerToRef: React.MutableRefObject<((highlight: IHighlight) => void) | null>
  onAddHighlight: (position: ScaledPosition, content: Content, comment?: { text: string; emoji: string }) => void
  onRemoveHighlight: (id: string) => void
  onDocumentLoaded: (pageCount: number, hasText: boolean) => void
  onClipText?: (text: string, pageNumber: number, boundingBox?: { x: number; y: number; width: number; height: number }) => void
  documentId: string
}

function ensureComment(comment?: { text?: string; emoji?: string }): { text: string; emoji: string } {
  return {
    text: comment?.text || '',
    emoji: comment?.emoji || '',
  }
}

interface SelectionTipProps {
  position: ScaledPosition
  content: Content
  onConfirm: (comment?: { text: string; emoji: string }) => void
  onClip: () => void
  hideTipAndSelection: () => void
  documentId: string
}

function SelectionTip({ position, content, onConfirm, onClip, hideTipAndSelection, documentId }: SelectionTipProps) {
  const text = content.text || ''
  const pageNumber = position.pageNumber || 1

  const dragData: DragData = {
    type: 'pdf-selection',
    text,
    documentId,
    pageNumber,
    boundingBox: position.boundingRect ? {
      x: position.boundingRect.x1,
      y: position.boundingRect.y1,
      width: position.boundingRect.width,
      height: position.boundingRect.height,
    } : undefined,
  }

  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `selection-${Date.now()}`,
    data: dragData,
  })

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined

  useEffect(() => {
    if (isDragging) {
      hideTipAndSelection()
    }
  }, [isDragging, hideTipAndSelection])

  const truncatedText = text.length > 60 ? `${text.substring(0, 60)}...` : text

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-background border rounded-lg shadow-lg p-2 flex flex-col gap-2 min-w-[200px] max-w-[300px]"
    >
      <p className="text-xs text-muted-foreground line-clamp-2 px-1">
        "{truncatedText}"
      </p>
      <div className="flex items-center gap-1">
        <Button
          size="sm"
          variant="outline"
          className="flex-1 h-7 text-xs"
          onClick={() => onConfirm({ text: '', emoji: '' })}
        >
          <Link2 className="h-3 w-3 mr-1" />
          Highlight
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="flex-1 h-7 text-xs"
          onClick={onClip}
        >
          <Clipboard className="h-3 w-3 mr-1" />
          Clip
        </Button>
        <button
          {...listeners}
          {...attributes}
          className="p-1.5 rounded-md hover:bg-muted cursor-grab active:cursor-grabbing transition-colors"
          title="Drag to requirement"
        >
          <GripVertical className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>
    </div>
  )
}

function PDFContent({
  pdfDocument,
  highlights,
  scrollToHighlightId,
  scrollViewerToRef,
  onAddHighlight,
  onRemoveHighlight,
  onDocumentLoaded,
  onClipText,
  documentId,
}: PDFContentProps) {
  useEffect(() => {
    async function checkTextContent() {
      try {
        const numPages = pdfDocument.numPages
        let totalTextItems = 0
        const pagesToCheck = Math.min(3, numPages)

        for (let i = 1; i <= pagesToCheck; i++) {
          const page = await pdfDocument.getPage(i)
          const textContent = await page.getTextContent()
          totalTextItems += textContent.items.length
        }

        onDocumentLoaded(numPages, totalTextItems > 10)
      } catch (error) {
        console.error('Error checking text content:', error)
        onDocumentLoaded(pdfDocument.numPages, true)
      }
    }
    checkTextContent()
  }, [pdfDocument, onDocumentLoaded])

  const HighlightPopup = ({ highlight }: { highlight: IHighlight }) => (
    <div className="bg-white rounded-lg shadow-lg p-3 max-w-xs border">
      {highlight.content.text && (
        <p className="text-sm text-gray-700 mb-2 line-clamp-3">
          "{highlight.content.text}"
        </p>
      )}
      {highlight.comment?.text && (
        <p className="text-xs text-gray-500 italic mb-2">
          Note: {highlight.comment.text}
        </p>
      )}
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="destructive"
          onClick={() => onRemoveHighlight(highlight.id)}
        >
          <Trash2 className="h-3 w-3 mr-1" />
          Delete
        </Button>
      </div>
    </div>
  )

  return (
    <PdfHighlighter
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      pdfDocument={pdfDocument as any}
      enableAreaSelection={(event) => event.altKey}
      onScrollChange={() => {}}
      scrollRef={(scrollTo) => {
        scrollViewerToRef.current = scrollTo
      }}
      onSelectionFinished={(
        position,
        content,
        hideTipAndSelection,
        transformSelection
      ) => (
        <SelectionTip
          position={position}
          content={content}
          documentId={documentId}
          hideTipAndSelection={hideTipAndSelection}
          onConfirm={(comment) => {
            transformSelection()
            onAddHighlight(position, content, comment)
            hideTipAndSelection()
          }}
          onClip={() => {
            if (onClipText && content.text) {
              const boundingBox = position.boundingRect ? {
                x: position.boundingRect.x1,
                y: position.boundingRect.y1,
                width: position.boundingRect.width,
                height: position.boundingRect.height,
              } : undefined
              onClipText(content.text, position.pageNumber || 1, boundingBox)
            }
            hideTipAndSelection()
          }}
        />
      )}
      highlightTransform={(
        highlight,
        index,
        setTip,
        hideTip,
        _viewportToScaled,
        _screenshot,
        isScrolledTo
      ) => {
        const isTextHighlight = !(highlight.content && highlight.content.image)

        const component = isTextHighlight ? (
          <HighlightComponent
            isScrolledTo={isScrolledTo || scrollToHighlightId === highlight.id}
            position={highlight.position}
            comment={highlight.comment}
          />
        ) : (
          <AreaHighlight
            isScrolledTo={isScrolledTo || scrollToHighlightId === highlight.id}
            highlight={highlight}
            onChange={() => {}}
          />
        )

        return (
          <Popup
            popupContent={<HighlightPopup highlight={highlight} />}
            onMouseOver={(popupContent) => setTip(highlight, () => popupContent)}
            onMouseOut={hideTip}
            key={index}
          >
            {component}
          </Popup>
        )
      }}
      highlights={highlights}
    />
  )
}

export function PDFViewer({ url, documentId, onHighlightAdded, initialPage, onScrollHandlerReady, onClipText }: PDFViewerProps) {
  const {
    highlights,
    addHighlight,
    removeHighlight,
    clearHighlights,
  } = useHighlights(documentId)

  const { isDragging } = useWorkspaceContext()

  const [scrollToHighlightId, setScrollToHighlightId] = useState<string | null>(null)
  const [hasTextContent, setHasTextContent] = useState<boolean | null>(null)
  const [pageCount, setPageCount] = useState<number>(0)
  const scrollViewerToRef = useRef<((highlight: IHighlight) => void) | null>(null)
  const pdfContainerRef = useRef<HTMLDivElement | null>(null)
  const pendingScrollRef = useRef<number | null>(initialPage ?? null)

  const scrollToPage = useCallback((pageNumber: number) => {
    if (pdfContainerRef.current && pageNumber >= 1) {
      const pageElement = pdfContainerRef.current.querySelector(
        `[data-page-number="${pageNumber}"]`
      ) as HTMLElement | null
      if (pageElement) {
        pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        pendingScrollRef.current = pageNumber
      }
    }
  }, [])

  useEffect(() => {
    if (onScrollHandlerReady) {
      onScrollHandlerReady(scrollToPage)
    }
  }, [onScrollHandlerReady, scrollToPage])

  useEffect(() => {
    if (pendingScrollRef.current && pageCount > 0) {
      const targetPage = pendingScrollRef.current
      pendingScrollRef.current = null
      requestAnimationFrame(() => {
        scrollToPage(targetPage)
      })
    }
  }, [pageCount, scrollToPage])

  const highlightsForViewer: IHighlight[] = highlights.map(h => ({
    id: h.id,
    position: h.position,
    content: h.content,
    comment: ensureComment(h.comment),
  }))

  const handleAddHighlight = useCallback(
    (position: ScaledPosition, content: Content, comment?: { text: string; emoji: string }) => {
      const newHighlight = addHighlight({
        position,
        content,
        comment,
      })

      if (onHighlightAdded) {
        onHighlightAdded({
          id: newHighlight.id,
          position,
          content,
          comment: ensureComment(comment),
        })
      }
    },
    [addHighlight, onHighlightAdded]
  )

  const handleDocumentLoaded = useCallback((pages: number, hasText: boolean) => {
    setPageCount(pages)
    setHasTextContent(hasText)
  }, [])

  const scrollToHighlightFn = useCallback((highlightId: string) => {
    const highlight = highlightsForViewer.find(h => h.id === highlightId)
    if (highlight && scrollViewerToRef.current) {
      scrollViewerToRef.current(highlight)
      setScrollToHighlightId(highlightId)
      setTimeout(() => setScrollToHighlightId(null), 1000)
    }
  }, [highlightsForViewer])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-2 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {pageCount > 0 ? `${pageCount} pages` : 'Loading...'}
          </span>
          {isDragging && (
            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full animate-pulse">
              Drag to requirement...
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            {highlights.length} highlight{highlights.length !== 1 ? 's' : ''}
          </span>
          {highlights.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (confirm('Clear all highlights for this document?')) {
                  clearHighlights()
                }
              }}
            >
              Clear All
            </Button>
          )}
        </div>
      </div>

      {hasTextContent === false && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 border-b border-amber-200 text-amber-800">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <div>
            <p className="font-medium">Scanned PDF Detected</p>
            <p className="text-sm">
              This PDF appears to be a scanned image without embedded text.
              Text selection and highlighting may not work properly.
            </p>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden relative" ref={pdfContainerRef}>
        <PdfLoader
          url={url}
          beforeLoad={
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="ml-2">Loading PDF...</span>
            </div>
          }
          onError={(error) => (
            <div className="flex items-center justify-center h-full text-destructive">
              <AlertTriangle className="h-8 w-8 mr-2" />
              <span>Failed to load PDF: {error.message}</span>
            </div>
          )}
        >
          {(pdfDocument) => (
            <PDFContent
              pdfDocument={pdfDocument}
              highlights={highlightsForViewer}
              scrollToHighlightId={scrollToHighlightId}
              scrollViewerToRef={scrollViewerToRef}
              onAddHighlight={handleAddHighlight}
              onRemoveHighlight={removeHighlight}
              onDocumentLoaded={handleDocumentLoaded}
              onClipText={onClipText}
              documentId={documentId}
            />
          )}
        </PdfLoader>
      </div>

      {highlights.length > 0 && (
        <div className="border-t p-3 bg-muted/30 max-h-48 overflow-y-auto">
          <h3 className="text-sm font-medium mb-2">Highlights</h3>
          <div className="space-y-2">
            {highlights.map((highlight) => (
              <Card
                key={highlight.id}
                className="cursor-pointer hover:bg-accent/50 transition-colors"
                onClick={() => scrollToHighlightFn(highlight.id)}
              >
                <CardContent className="p-2">
                  <p className="text-xs text-muted-foreground mb-1">
                    Page {highlight.position.pageNumber}
                  </p>
                  {highlight.content.text && (
                    <p className="text-sm line-clamp-2">
                      "{highlight.content.text}"
                    </p>
                  )}
                  {highlight.comment?.text && (
                    <p className="text-xs text-muted-foreground mt-1 italic">
                      Note: {highlight.comment.text}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
