import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Save, Download } from 'lucide-react'

interface WorkflowProgress {
  current_stage: number
  stage_name: string
  completed_stages: string[]
}

interface WorkspaceHeaderProps {
  projectName: string
  methodology: string
  workflowProgress: WorkflowProgress
  onSave?: () => void
  onExport?: () => void
}

const WORKFLOW_STAGES = [
  'Initialize',
  'Discover',
  'Map',
  'Extract',
  'Validate',
  'Report',
] as const

export function WorkspaceHeader({
  projectName,
  methodology,
  workflowProgress,
  onSave,
  onExport,
}: WorkspaceHeaderProps) {
  const currentStage = workflowProgress.current_stage
  const totalStages = WORKFLOW_STAGES.length
  const stageName = workflowProgress.stage_name || WORKFLOW_STAGES[currentStage - 1] || 'Initialize'

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b bg-card">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Dashboard
          </Link>
        </Button>

        <div className="h-6 w-px bg-border" />

        <div>
          <h1 className="text-lg font-semibold leading-tight">{projectName}</h1>
          <p className="text-xs text-muted-foreground">{methodology}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            Stage {currentStage}/{totalStages}:
          </span>
          <Badge variant="secondary">{stageName}</Badge>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            {WORKFLOW_STAGES.map((_, index) => {
              const stageNum = index + 1
              const isCompleted = stageNum < currentStage
              const isCurrent = stageNum === currentStage
              return (
                <div
                  key={index}
                  className={`h-2 w-6 rounded-full transition-colors ${
                    isCompleted
                      ? 'bg-primary'
                      : isCurrent
                        ? 'bg-primary/50'
                        : 'bg-muted'
                  }`}
                  title={`${WORKFLOW_STAGES[index]}${isCompleted ? ' (completed)' : isCurrent ? ' (current)' : ''}`}
                />
              )
            })}
          </div>
        </div>

        <div className="h-6 w-px bg-border" />

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onSave}>
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>
          <Button variant="outline" size="sm" onClick={onExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>
    </header>
  )
}
