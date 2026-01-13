import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import type { DragData } from '@/contexts/WorkspaceContext'
import { cn } from '@/lib/utils'
import { GripVertical } from 'lucide-react'
import type { ReactNode } from 'react'

interface DraggableSelectionProps {
  id: string
  data: DragData
  children: ReactNode
  className?: string
  handleClassName?: string
}

export function DraggableSelection({
  id,
  data,
  children,
  className,
  handleClassName,
}: DraggableSelectionProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id,
    data,
  })

  const style = transform
    ? {
        transform: CSS.Translate.toString(transform),
      }
    : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'relative group',
        isDragging && 'opacity-50',
        className
      )}
    >
      <div
        {...listeners}
        {...attributes}
        className={cn(
          'absolute left-0 top-0 bottom-0 w-6 flex items-center justify-center cursor-grab active:cursor-grabbing',
          'opacity-0 group-hover:opacity-100 transition-opacity',
          'bg-gradient-to-r from-muted/80 to-transparent',
          handleClassName
        )}
      >
        <GripVertical className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="pl-6">{children}</div>
    </div>
  )
}

interface DraggableHandleProps {
  id: string
  data: DragData
  className?: string
}

export function DraggableHandle({ id, data, className }: DraggableHandleProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id,
    data,
  })

  return (
    <button
      ref={setNodeRef}
      {...listeners}
      {...attributes}
      className={cn(
        'p-1.5 rounded-md cursor-grab active:cursor-grabbing',
        'hover:bg-muted transition-colors',
        isDragging && 'bg-muted',
        className
      )}
      title="Drag to link evidence"
    >
      <GripVertical className="h-4 w-4 text-muted-foreground" />
    </button>
  )
}
