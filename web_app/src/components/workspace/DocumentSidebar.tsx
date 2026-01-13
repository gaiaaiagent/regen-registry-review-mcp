import { cn } from '@/lib/utils'
import { FileText, FileSpreadsheet, FileImage, File } from 'lucide-react'

export interface Document {
  id: string
  filename: string
  doc_type?: string
  page_count?: number
  size_bytes?: number
}

interface DocumentSidebarProps {
  documents: Document[]
  activeDocumentId: string | null
  onSelectDocument: (documentId: string) => void
}

function getDocumentIcon(docType?: string) {
  switch (docType?.toLowerCase()) {
    case 'monitoring_report':
    case 'baseline_report':
    case 'verification_report':
    case 'project_plan':
      return FileText
    case 'spreadsheet':
    case 'ghg_emissions':
      return FileSpreadsheet
    case 'gis_data':
    case 'imagery':
      return FileImage
    default:
      return File
  }
}

function getDocumentTypeLabel(docType?: string): string {
  if (!docType) return 'Document'
  return docType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function DocumentSidebar({
  documents,
  activeDocumentId,
  onSelectDocument,
}: DocumentSidebarProps) {
  if (documents.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No documents yet</p>
        <p className="text-xs mt-1">Documents will appear here after discovery</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 border-b bg-muted/30">
        <h2 className="text-sm font-medium">Documents ({documents.length})</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {documents.map((doc) => {
          const Icon = getDocumentIcon(doc.doc_type)
          const isActive = doc.id === activeDocumentId

          return (
            <button
              key={doc.id}
              onClick={() => onSelectDocument(doc.id)}
              className={cn(
                'w-full px-3 py-2 text-left transition-colors hover:bg-accent/50 border-l-2',
                isActive
                  ? 'bg-accent border-l-primary'
                  : 'border-l-transparent'
              )}
            >
              <div className="flex items-start gap-2">
                <Icon className={cn(
                  'h-4 w-4 mt-0.5 flex-shrink-0',
                  isActive ? 'text-primary' : 'text-muted-foreground'
                )} />
                <div className="flex-1 min-w-0">
                  <p className={cn(
                    'text-sm font-medium truncate',
                    isActive && 'text-primary'
                  )}>
                    {doc.filename}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{getDocumentTypeLabel(doc.doc_type)}</span>
                    {doc.page_count && (
                      <>
                        <span>-</span>
                        <span>{doc.page_count} pages</span>
                      </>
                    )}
                  </div>
                  {doc.size_bytes && (
                    <p className="text-xs text-muted-foreground/70">
                      {formatFileSize(doc.size_bytes)}
                    </p>
                  )}
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
