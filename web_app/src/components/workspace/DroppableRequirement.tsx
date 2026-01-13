import { useDroppable } from '@dnd-kit/core'
import { cn } from '@/lib/utils'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'
import type { ReactNode } from 'react'

interface DroppableRequirementProps {
  requirementId: string
  children: ReactNode
  className?: string
}

export function DroppableRequirement({
  requirementId,
  children,
  className,
}: DroppableRequirementProps) {
  const { isDragging } = useWorkspaceContext()
  const { isOver, setNodeRef } = useDroppable({
    id: `requirement-${requirementId}`,
  })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'transition-all duration-150',
        isDragging && 'ring-2 ring-primary/30 ring-offset-1 rounded-lg',
        isOver && 'ring-2 ring-primary ring-offset-2 bg-primary/5 scale-[1.01]',
        className
      )}
    >
      {children}
      {isOver && (
        <div className="absolute inset-0 bg-primary/10 rounded-lg pointer-events-none flex items-center justify-center">
          <span className="text-xs font-medium text-primary bg-background/90 px-2 py-1 rounded">
            Drop to link
          </span>
        </div>
      )}
    </div>
  )
}
