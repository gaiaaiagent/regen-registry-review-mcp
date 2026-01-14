import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import { ClipboardCheck, ShieldCheck, MessageSquare, FileText, Loader2 } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ChecklistPanel } from './ChecklistPanel'
import { ValidationPanel } from './ValidationPanel'
import { ChatPanel } from './ChatPanel'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'

const LazyReportPanel = lazy(() => import('./ReportPanel').then(m => ({ default: m.ReportPanel })))

function ReportPanelFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      <span className="ml-2 text-muted-foreground">Loading report panel...</span>
    </div>
  )
}

interface ToolsPanelProps {
  sessionId: string
}

export function ToolsPanel({ sessionId }: ToolsPanelProps) {
  const [activeTab, setActiveTab] = useState<string>('checklist')
  const { focusedRequirementId } = useWorkspaceContext()

  const switchToChecklist = useCallback(() => {
    setActiveTab('checklist')
  }, [])

  useEffect(() => {
    if (focusedRequirementId) {
      setActiveTab('checklist')
    }
  }, [focusedRequirementId])

  return (
    <div className="h-full flex flex-col bg-card">
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="h-full flex flex-col"
      >
        <div className="px-2 pt-2 border-b bg-muted/30">
          <TabsList className="w-full grid grid-cols-4">
            <TabsTrigger value="checklist" className="flex items-center gap-1.5">
              <ClipboardCheck className="h-3.5 w-3.5" />
              <span className="text-xs">Checklist</span>
            </TabsTrigger>
            <TabsTrigger value="validation" className="flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span className="text-xs">Validation</span>
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-1.5">
              <MessageSquare className="h-3.5 w-3.5" />
              <span className="text-xs">AI Chat</span>
            </TabsTrigger>
            <TabsTrigger value="report" className="flex items-center gap-1.5">
              <FileText className="h-3.5 w-3.5" />
              <span className="text-xs">Report</span>
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="checklist" className="flex-1 m-0 overflow-hidden">
          <ErrorBoundary componentName="Checklist">
            <ChecklistPanel sessionId={sessionId} />
          </ErrorBoundary>
        </TabsContent>

        <TabsContent value="validation" className="flex-1 m-0 overflow-hidden">
          <ErrorBoundary componentName="Validation">
            <ValidationPanel
              sessionId={sessionId}
              onSwitchToChecklist={switchToChecklist}
            />
          </ErrorBoundary>
        </TabsContent>

        <TabsContent value="chat" className="flex-1 m-0 overflow-hidden">
          <ErrorBoundary componentName="AI Chat">
            <ChatPanel sessionId={sessionId} />
          </ErrorBoundary>
        </TabsContent>

        <TabsContent value="report" className="flex-1 m-0 overflow-hidden">
          <ErrorBoundary componentName="Report">
            <Suspense fallback={<ReportPanelFallback />}>
              <LazyReportPanel sessionId={sessionId} />
            </Suspense>
          </ErrorBoundary>
        </TabsContent>
      </Tabs>
    </div>
  )
}
