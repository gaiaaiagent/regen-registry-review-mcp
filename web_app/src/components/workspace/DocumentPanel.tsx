import { useEffect, lazy, Suspense } from 'react'
import { toast } from 'sonner'
import { DocumentSidebar, type Document } from './DocumentSidebar'
import { GDriveImportDialog } from '@/components/gdrive'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { FileText, HardDrive, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'

const LazyPDFViewer = lazy(() => import('@/components/PDFViewer').then(m => ({ default: m.PDFViewer })))

function PDFViewerFallback() {
  return (
    <div className="h-full flex flex-col items-center justify-center bg-muted/10">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      <span className="mt-2 text-muted-foreground">Loading PDF viewer...</span>
    </div>
  )
}

interface DocumentPanelProps {
  sessionId: string
  documents: Document[]
  getDocumentUrl: (documentId: string) => string | null
  onClipText?: (text: string, documentId: string, pageNumber: number, boundingBox?: { x: number; y: number; width: number; height: number }) => void
  onDocumentsImported?: () => void
}

export function DocumentPanel({ sessionId, documents, getDocumentUrl, onClipText, onDocumentsImported }: DocumentPanelProps) {
  const {
    activeDocumentId,
    setActiveDocumentId,
    targetPage,
    registerScrollHandler,
  } = useWorkspaceContext()

  console.log('DocumentPanel: Render', { activeDocumentId, documentsCount: documents.length })

  useEffect(() => {
    if (activeDocumentId === null && documents.length > 0) {
      setActiveDocumentId(documents[0].id)
    }
  }, [activeDocumentId, documents, setActiveDocumentId])

  const activeDocumentUrl = activeDocumentId ? getDocumentUrl(activeDocumentId) : null
  console.log('DocumentPanel: Resolved URL', { activeDocumentId, activeDocumentUrl })

  const handleClipText = (text: string, pageNumber: number, boundingBox?: { x: number; y: number; width: number; height: number }) => {
    if (onClipText && activeDocumentId) {
      onClipText(text, activeDocumentId, pageNumber, boundingBox)
    }
  }

  const handleImportComplete = (importedCount: number) => {
    toast.success(`Imported ${importedCount} files from Google Drive`)
    onDocumentsImported?.()
  }

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Fixed Sidebar */}
      <div className="w-64 flex-shrink-0 border-r bg-muted/10 h-full overflow-hidden flex flex-col">
        <DocumentSidebar
          documents={documents}
          activeDocumentId={activeDocumentId}
          onSelectDocument={setActiveDocumentId}
        />
        <div className="p-3 border-t bg-muted/20">
          <GDriveImportDialog
            sessionId={sessionId}
            existingFilenames={new Set(documents.map(d => d.filename))}
            onImportComplete={handleImportComplete}
            trigger={
              <Button variant="outline" size="sm" className="w-full">
                <HardDrive className="h-4 w-4 mr-2" />
                Import from Drive
              </Button>
            }
          />
        </div>
      </div>

      {/* Main Content (PDF) */}
      <div className="flex-1 h-full min-w-0 bg-background relative">
        {activeDocumentUrl ? (
          <ErrorBoundary componentName="PDF Viewer" key={activeDocumentId}>
            <Suspense fallback={<PDFViewerFallback />}>
              <LazyPDFViewer
                url={activeDocumentUrl}
                documentId={activeDocumentId!}
                initialPage={targetPage ?? undefined}
                onScrollHandlerReady={registerScrollHandler}
                onClipText={handleClipText}
              />
            </Suspense>
          </ErrorBoundary>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground bg-muted/20">
            <FileText className="h-16 w-16 mb-4 opacity-30" />
            <p className="text-lg font-medium">No Document Selected</p>
            <p className="text-sm mt-1">
              {documents.length > 0
                ? 'Select a document from the sidebar to view it'
                : 'Documents will appear after running discovery'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
