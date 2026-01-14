import { useParams, Link } from 'react-router-dom'
import { useCallback, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useSession } from '@/hooks/useSessions'
import { WorkspaceLayout } from '@/components/workspace'
import type { Document } from '@/components/workspace'
import { ArrowLeft, AlertCircle, RefreshCw } from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'

const DEMO_DOCUMENTS: Document[] = [
  { id: 'demo-1', filename: '4997Botany22_Public_Project_Plan.pdf', doc_type: 'project_plan', page_count: 45 },
  { id: 'demo-2', filename: '4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf', doc_type: 'baseline_report', page_count: 32 },
  { id: 'demo-3', filename: '4998Botany23_GHG_Emissions_30_Sep_2023.pdf', doc_type: 'ghg_emissions', page_count: 8 },
  { id: 'demo-4', filename: '4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf', doc_type: 'monitoring_report', page_count: 28 },
  { id: 'demo-5', filename: 'Botany_Farm_Credit_Issuance_Registry_Agent_Review_2023_Monitoring.pdf', doc_type: 'verification_report', page_count: 15 },
]

const DEMO_PDF_MAP: Record<string, string> = {
  'demo-1': '/pdfs/4997Botany22_Public_Project_Plan.pdf',
  'demo-2': '/pdfs/4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf',
  'demo-3': '/pdfs/4998Botany23_GHG_Emissions_30_Sep_2023.pdf',
  'demo-4': '/pdfs/4998Botany23_Soil_Organic_Carbon_Project_Public_Monitoring_Report_2023.pdf',
  'demo-5': '/pdfs/Botany_Farm_Credit_Issuance_Registry_Agent_Review_2023_Monitoring.pdf',
}

interface SessionDocument {
  document_id: string
  filename: string
  classification?: string
  metadata?: {
    page_count?: number
    file_size_bytes?: number
  }
  filepath?: string
}

interface SessionWithDocuments {
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
  documents?: SessionDocument[]
}

export function SessionWorkspace() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { data: session, isLoading, isError, error, refetch } = useSession(sessionId) as {
    data: SessionWithDocuments | undefined
    isLoading: boolean
    isError: boolean
    error: Error | null
    refetch: () => void
  }

  // Debug: Check what session data we actually have
  if (session) {
    console.log('SessionWorkspace: Loaded session data', { 
      hasDocuments: !!session.documents, 
      documentCount: session.documents?.length,
      firstDoc: session.documents?.[0],
      allIds: session.documents?.map(d => d.document_id)
    })
  }

  const sessionDocuments = session?.documents

  const documents = useMemo<Document[]>(() => {
    if (sessionDocuments && sessionDocuments.length > 0) {
      return sessionDocuments.map(doc => ({
        id: doc.document_id,
        filename: doc.filename,
        doc_type: doc.classification,
        page_count: doc.metadata?.page_count,
        size_bytes: doc.metadata?.file_size_bytes,
      }))
    }
    return DEMO_DOCUMENTS
  }, [sessionDocuments])

  const getDocumentUrl = useCallback((documentId: string): string | null => {
    console.log('SessionWorkspace: getDocumentUrl called for', documentId)
    
    // 1. Try demo map first
    if (DEMO_PDF_MAP[documentId]) {
      return DEMO_PDF_MAP[documentId]
    }

    // 2. Try finding in session documents
    if (sessionDocuments) {
      console.log('SessionWorkspace: Searching session documents', sessionDocuments.length)
      if (sessionDocuments.length > 0) {
        console.log('SessionWorkspace: First doc structure:', sessionDocuments[0])
      }

      // a. Try ID match
      let doc = sessionDocuments.find(d => {
        const match = d.document_id === documentId
        if (match) console.log('SessionWorkspace: ID Match found!', d)
        return match
      })
      
      // b. Try filename match (if ID didn't work)
      if (!doc) {
        console.log('SessionWorkspace: No ID match, trying filename')
        doc = sessionDocuments.find(d => {
          const nameMatch = d.filename.toLowerCase() === documentId.toLowerCase() ||
                            d.filename.toLowerCase().includes(documentId.toLowerCase())
          if (nameMatch) console.log('SessionWorkspace: Filename match found!', d)
          return nameMatch
        })
      }

      if (doc?.filepath) {
        // Use direct path concatenation to preserve slashes for the backend 'path' parameter
        // The backend expects /files/ + absolute_path (e.g. /files//Users/...)
        const url = `${API_BASE_URL}/files${doc.filepath.startsWith('/') ? '' : '/'}${doc.filepath}`
        console.log('SessionWorkspace: Generated URL', url)
        return url
      } else if (doc) {
        console.error('SessionWorkspace: Document found but no filepath!', doc)
      }
    } else {
      console.warn('SessionWorkspace: sessionDocuments is undefined/empty')
    }

    // 3. Fallback...

    // 3. Fallback: If documentId looks like a filename, try to find it in DEMO_DOCUMENTS
    const demoDoc = DEMO_DOCUMENTS.find(d => d.filename === documentId || d.id === documentId)
    if (demoDoc && DEMO_PDF_MAP[demoDoc.id]) {
      return DEMO_PDF_MAP[demoDoc.id]
    }

    console.warn('SessionWorkspace: Could not find URL for document', documentId)
    return null
  }, [sessionDocuments])

  if (isLoading) {
    return (
      <div className="h-screen flex flex-col">
        <div className="flex items-center gap-4 p-4 border-b">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="flex-1 flex">
          <Skeleton className="w-1/3 h-full" />
          <Skeleton className="w-1/3 h-full" />
          <Skeleton className="w-1/3 h-full" />
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-4 mb-8">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Link>
          </Button>
        </div>
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              Failed to Load Session
            </CardTitle>
            <CardDescription>
              {error instanceof Error ? error.message : 'Session not found or an error occurred'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center gap-4 mb-8">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Link>
          </Button>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Session Not Found</h3>
            <p className="text-muted-foreground text-center mb-6">
              The session you're looking for doesn't exist or has been deleted.
            </p>
            <Button asChild>
              <Link to="/">Return to Dashboard</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <WorkspaceLayout
      sessionId={session.session_id}
      projectName={session.project_name}
      methodology={session.methodology}
      workflowProgress={session.workflow_progress}
      documents={documents}
      getDocumentUrl={getDocumentUrl}
    />
  )
}
