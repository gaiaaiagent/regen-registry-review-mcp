import {
  ArrowRight,
  FileSearch,
  CheckCircle,
  PlayCircle,
  FileText,
  ExternalLink,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { AgentAction } from '@/hooks/useAgentChat'

interface ActionButtonProps {
  action: AgentAction
  onClick: () => void
  disabled?: boolean
}

function getActionIcon(type: string) {
  switch (type) {
    case 'navigate':
      return ArrowRight
    case 'extract':
      return FileSearch
    case 'validate':
      return CheckCircle
    case 'run':
      return PlayCircle
    case 'view':
      return FileText
    case 'open':
      return ExternalLink
    default:
      return PlayCircle
  }
}

function getActionVariant(type: string): 'default' | 'secondary' | 'outline' {
  switch (type) {
    case 'navigate':
      return 'outline'
    case 'extract':
    case 'validate':
      return 'secondary'
    default:
      return 'default'
  }
}

export function ActionButton({ action, onClick, disabled }: ActionButtonProps) {
  const Icon = getActionIcon(action.type)
  const variant = getActionVariant(action.type)

  return (
    <Button
      variant={variant}
      size="sm"
      onClick={onClick}
      disabled={disabled}
      className="h-7 text-xs"
    >
      <Icon className="h-3 w-3 mr-1" />
      {action.label}
    </Button>
  )
}
