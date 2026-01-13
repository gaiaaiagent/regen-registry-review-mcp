import { type ReactNode } from 'react'
import {
  DndContext,
  DragOverlay,
  useSensor,
  useSensors,
  PointerSensor,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core'
import { useWorkspaceContext, type DragData } from '@/contexts/WorkspaceContext'
import { Card, CardContent } from '@/components/ui/card'
import { FileText, GripVertical } from 'lucide-react'

interface DragDropProviderProps {
  children: ReactNode
  onDrop?: (data: DragData, targetRequirementId: string) => void
}

function DragOverlayContent({ data }: { data: DragData }) {
  const truncatedText = data.text.length > 100 ? `${data.text.substring(0, 100)}...` : data.text

  return (
    <Card className="w-72 shadow-xl border-primary/50 bg-background/95 backdrop-blur-sm cursor-grabbing">
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          <GripVertical className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1.5">
              <FileText className="h-3 w-3" />
              <span className="truncate">{data.documentId}</span>
              <span>p.{data.pageNumber}</span>
            </div>
            <p className="text-sm line-clamp-3">{truncatedText}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function DragDropProvider({ children, onDrop }: DragDropProviderProps) {
  const { setIsDragging, currentDragData, setCurrentDragData } = useWorkspaceContext()

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  const handleDragStart = (event: DragStartEvent) => {
    const data = event.active.data.current as DragData | undefined
    if (data) {
      setCurrentDragData(data)
      setIsDragging(true)
    }
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { over } = event

    if (over && currentDragData) {
      const targetId = over.id as string
      if (targetId.startsWith('requirement-')) {
        const requirementId = targetId.replace('requirement-', '')
        onDrop?.(currentDragData, requirementId)
      }
    }

    setCurrentDragData(null)
    setIsDragging(false)
  }

  const handleDragCancel = () => {
    setCurrentDragData(null)
    setIsDragging(false)
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      {children}
      <DragOverlay dropAnimation={null}>
        {currentDragData && <DragOverlayContent data={currentDragData} />}
      </DragOverlay>
    </DndContext>
  )
}
