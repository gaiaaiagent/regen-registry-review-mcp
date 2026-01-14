import { useCallback } from 'react'
import { toast } from 'sonner'
import { useQueryClient } from '@tanstack/react-query'
import { Group, Panel, Separator } from 'react-resizable-panels'
import { WorkspaceHeader } from './WorkspaceHeader'
import { DocumentPanel } from './DocumentPanel'
import { ToolsPanel } from './MiddlePanel'
import { ChatPanel } from './ChatPanel'
import { DragDropProvider } from './DragDropProvider'
import { WorkspaceProvider, type DragData } from '@/contexts/WorkspaceContext'
import { useManualEvidence } from '@/hooks/useManualEvidence'
import type { Document } from './DocumentSidebar'

interface WorkflowProgress {
  current_stage: number
  stage_name: string
  completed_stages: string[]
}

interface WorkspaceLayoutProps {
  sessionId: string
  projectName: string
  methodology: string
  workflowProgress: WorkflowProgress
  documents: Document[]
  getDocumentUrl: (documentId: string) => string | null
}

function WorkspaceContent({
  sessionId,
  projectName,
  methodology,
  workflowProgress,
  documents,
  getDocumentUrl,
}: WorkspaceLayoutProps) {
  const queryClient = useQueryClient()
  const { addEvidence, linkToRequirement } = useManualEvidence(sessionId)

  const handleSave = () => {
    console.log('Save clicked - to be implemented')
  }

  const handleExport = () => {
    console.log('Export clicked - to be implemented')
  }

  const handleClipText = useCallback(
    async (text: string, documentId: string, pageNumber: number, boundingBox?: { x: number; y: number; width: number; height: number }) => {
      try {
        await addEvidence({
          documentId,
          pageNumber,
          text,
          boundingBox,
          requirementId: null,
        })
        toast.success('Text clipped', {
          description: 'Added to scratchpad. Drag to a requirement to link.',
        })
      } catch (error) {
        toast.error('Failed to clip text')
        console.error('Clip error:', error)
      }
    },
    [addEvidence]
  )

  const handleDrop = useCallback(
    async (data: DragData, requirementId: string) => {
      try {
        if (data.type === 'scratchpad-item' && data.evidenceId) {
          await linkToRequirement(data.evidenceId, requirementId)
        } else {
          await addEvidence({
            documentId: data.documentId,
            pageNumber: data.pageNumber,
            text: data.text,
            boundingBox: data.boundingBox,
            requirementId,
          })
          toast.success('Evidence linked', {
            description: `Linked to ${requirementId}`,
          })
        }
      } catch (error) {
        toast.error('Failed to link evidence')
        console.error('Link error:', error)
      }
    },
    [addEvidence, linkToRequirement]
  )

  const handleDocumentsImported = useCallback(() => {
    // Invalidate session query to refresh document list
    queryClient.invalidateQueries({ queryKey: ['session', sessionId] })
  }, [queryClient, sessionId])

  return (
    <DragDropProvider onDrop={handleDrop}>
      <div className="h-screen flex flex-col">
        <WorkspaceHeader
          sessionId={sessionId}
          projectName={projectName}
          methodology={methodology}
          workflowProgress={workflowProgress}
          onSave={handleSave}
          onExport={handleExport}
        />

        <div className="flex-1 overflow-hidden">
          <Group orientation="horizontal" className="h-full">
            <Panel defaultSize={65} minSize={40} maxSize={80}>
              <DocumentPanel
                sessionId={sessionId}
                documents={documents}
                getDocumentUrl={getDocumentUrl}
                onClipText={handleClipText}
                onDocumentsImported={handleDocumentsImported}
              />
            </Panel>

            <Separator className="w-1.5 bg-border hover:bg-primary/20 transition-colors cursor-col-resize" />

            <Panel defaultSize={35} minSize={20} maxSize={50}>
              <ToolsPanel sessionId={sessionId} />
            </Panel>
          </Group>
        </div>
      </div>
    </DragDropProvider>
  )
}

export function WorkspaceLayout(props: WorkspaceLayoutProps) {
  const initialDocumentId = props.documents.length > 0 ? props.documents[0].id : null

  return (
    <WorkspaceProvider initialDocumentId={initialDocumentId}>
      <WorkspaceContent {...props} />
    </WorkspaceProvider>
  )
}
