import { useEffect } from 'react'
import { Group, Panel, Separator } from 'react-resizable-panels'
import { DocumentSidebar, type Document } from './DocumentSidebar'
import { PDFViewer } from '@/components/PDFViewer'
import { FileText } from 'lucide-react'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'

interface DocumentPanelProps {
  documents: Document[]
  getDocumentUrl: (documentId: string) => string | null
  onClipText?: (text: string, documentId: string, pageNumber: number, boundingBox?: { x: number; y: number; width: number; height: number }) => void
}

export function DocumentPanel({ documents, getDocumentUrl, onClipText }: DocumentPanelProps) {
  const {
    activeDocumentId,
    setActiveDocumentId,
    targetPage,
    registerScrollHandler,
  } = useWorkspaceContext()

  useEffect(() => {
    if (activeDocumentId === null && documents.length > 0) {
      setActiveDocumentId(documents[0].id)
    }
  }, [activeDocumentId, documents, setActiveDocumentId])

  const activeDocumentUrl = activeDocumentId ? getDocumentUrl(activeDocumentId) : null

  const handleClipText = (text: string, pageNumber: number, boundingBox?: { x: number; y: number; width: number; height: number }) => {
    if (onClipText && activeDocumentId) {
      onClipText(text, activeDocumentId, pageNumber, boundingBox)
    }
  }

  return (
    <Group orientation="horizontal" className="h-full">
      <Panel defaultSize={30} minSize={20} maxSize={50}>
        <DocumentSidebar
          documents={documents}
          activeDocumentId={activeDocumentId}
          onSelectDocument={setActiveDocumentId}
        />
      </Panel>

      <Separator className="w-1 bg-border hover:bg-primary/20 transition-colors" />

      <Panel defaultSize={70} minSize={50}>
        {activeDocumentUrl ? (
          <PDFViewer
            url={activeDocumentUrl}
            documentId={activeDocumentId!}
            initialPage={targetPage ?? undefined}
            onScrollHandlerReady={registerScrollHandler}
            onClipText={handleClipText}
          />
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
      </Panel>
    </Group>
  )
}
