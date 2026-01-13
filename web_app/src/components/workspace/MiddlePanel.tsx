import { useState, useEffect, useCallback } from 'react'
import { ClipboardCheck, ShieldCheck } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ChecklistPanel } from './ChecklistPanel'
import { ValidationPanel } from './ValidationPanel'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'

interface MiddlePanelProps {
  sessionId: string
}

export function MiddlePanel({ sessionId }: MiddlePanelProps) {
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
          <TabsList className="w-full grid grid-cols-2">
            <TabsTrigger value="checklist" className="flex items-center gap-1.5">
              <ClipboardCheck className="h-3.5 w-3.5" />
              <span className="text-xs">Checklist</span>
            </TabsTrigger>
            <TabsTrigger value="validation" className="flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span className="text-xs">Validation</span>
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="checklist" className="flex-1 m-0 overflow-hidden">
          <ChecklistPanel sessionId={sessionId} />
        </TabsContent>

        <TabsContent value="validation" className="flex-1 m-0 overflow-hidden">
          <ValidationPanel
            sessionId={sessionId}
            onSwitchToChecklist={switchToChecklist}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
