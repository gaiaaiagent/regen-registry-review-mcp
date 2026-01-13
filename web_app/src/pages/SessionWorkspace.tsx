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
  id: string
  filename: string
  doc_type?: string
  page_count?: number
  size_bytes?: number
  file_path?: string
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

  const sessionDocuments = session?.documents

  const documents = useMemo<Document[]>(() => {
    if (sessionDocuments && sessionDocuments.length > 0) {
      return sessionDocuments.map(doc => ({
        id: doc.id,
        filename: doc.filename,
        doc_type: doc.doc_type,
        page_count: doc.page_count,
        size_bytes: doc.size_bytes,
      }))
    }
    return DEMO_DOCUMENTS
  }, [sessionDocuments])

  const getDocumentUrl = useCallback((documentId: string): string | null => {
    if (DEMO_PDF_MAP[documentId]) {
      return DEMO_PDF_MAP[documentId]
    }

    if (sessionDocuments) {
      const doc = sessionDocuments.find(d => d.id === documentId)
      if (doc?.file_path) {
        return `${API_BASE_URL}/files/${encodeURIComponent(doc.file_path)}`
      }
    }

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
