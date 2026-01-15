import { useEffect, useRef, useState, lazy, Suspense } from 'react'
import { toast } from 'sonner'
import { DocumentSidebar, type Document } from './DocumentSidebar'
import { GDriveImportDialog } from '@/components/gdrive'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { FileText, HardDrive, Loader2, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'

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

  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)

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

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    const token = localStorage.getItem('auth_token')
    let successCount = 0
    let errorCount = 0

    for (const file of Array.from(files)) {
      try {
        // Read file as ArrayBuffer and convert to base64
        const arrayBuffer = await file.arrayBuffer()
        const bytes = new Uint8Array(arrayBuffer)
        let binary = ''
        for (let i = 0; i < bytes.length; i++) {
          binary += String.fromCharCode(bytes[i])
        }
        const base64 = btoa(binary)

        const response = await fetch(`${API_URL}/sessions/${sessionId}/upload`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            filename: file.name,
            content_base64: base64,
          }),
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Upload failed')
        }

        successCount++
      } catch (err) {
        errorCount++
        console.error(`Failed to upload ${file.name}:`, err)
      }
    }

    setIsUploading(false)
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }

    if (successCount > 0) {
      toast.success(`Uploaded ${successCount} file${successCount > 1 ? 's' : ''}`)
      onDocumentsImported?.()
    }
    if (errorCount > 0) {
      toast.error(`Failed to upload ${errorCount} file${errorCount > 1 ? 's' : ''}`)
    }
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
        <div className="p-3 border-t bg-muted/20 space-y-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.xlsx,.csv,.json,.shp,.dbf,.shx,.prj"
            multiple
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload Files
              </>
            )}
          </Button>
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
