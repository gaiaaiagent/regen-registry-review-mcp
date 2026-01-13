import { useState } from 'react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useWorkspaceContext, type DragData } from '@/contexts/WorkspaceContext'
import type { ScratchpadItem } from '@/hooks/useManualEvidence'
import {
  Clipboard,
  ChevronDown,
  ChevronUp,
  FileText,
  GripVertical,
  Trash2,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface ScratchpadCardProps {
  item: ScratchpadItem
  onRemove: (id: string) => void
}

function ScratchpadCard({ item, onRemove }: ScratchpadCardProps) {
  const dragData: DragData = {
    type: 'scratchpad-item',
    text: item.text,
    documentId: item.documentId,
    pageNumber: item.pageNumber,
    boundingBox: item.boundingBox,
    evidenceId: item.id,
  }

  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `scratchpad-${item.id}`,
    data: dragData,
  })

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined

  const truncatedText = item.text.length > 80 ? `${item.text.substring(0, 80)}...` : item.text

  return (
    <Card
      ref={setNodeRef}
      style={style}
      className={cn(
        'group transition-all',
        isDragging && 'opacity-50 shadow-lg'
      )}
    >
      <CardContent className="p-2">
        <div className="flex items-start gap-1.5">
          <button
            {...listeners}
            {...attributes}
            className="p-1 shrink-0 cursor-grab active:cursor-grabbing hover:bg-muted rounded transition-colors"
            title="Drag to link"
          >
            <GripVertical className="h-3.5 w-3.5 text-muted-foreground" />
          </button>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
              <FileText className="h-3 w-3 shrink-0" />
              <span className="truncate">{item.documentId}</span>
              <span className="shrink-0">p.{item.pageNumber}</span>
            </div>
            <p className="text-xs line-clamp-2">{truncatedText}</p>
          </div>

          <button
            onClick={() => onRemove(item.id)}
            className="p-1 shrink-0 opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive rounded transition-all"
            title="Remove"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      </CardContent>
    </Card>
  )
}

interface EvidenceScratchpadProps {
  items: ScratchpadItem[]
  onRemove: (id: string) => void
  onClear: () => void
}

export function EvidenceScratchpad({ items, onRemove, onClear }: EvidenceScratchpadProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const { isDragging } = useWorkspaceContext()

  if (items.length === 0 && !isDragging) {
    return null
  }

  return (
    <div className="border-t bg-muted/20">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Clipboard className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Scratchpad</span>
          <span className="text-xs text-muted-foreground">
            ({items.length} clip{items.length !== 1 ? 's' : ''})
          </span>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {isExpanded && (
        <div className="px-3 pb-3">
          {items.length > 0 ? (
            <>
              <ScrollArea className="max-h-48">
                <div className="space-y-2">
                  {items.map((item) => (
                    <ScratchpadCard
                      key={item.id}
                      item={item}
                      onRemove={onRemove}
                    />
                  ))}
                </div>
              </ScrollArea>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClear}
                className="w-full mt-2 h-7 text-xs text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="h-3 w-3 mr-1" />
                Clear All
              </Button>
            </>
          ) : (
            <div className="py-4 text-center text-muted-foreground">
              <Clipboard className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p className="text-xs">
                Click "Clip" on selected text to save it here
              </p>
              <p className="text-xs mt-1">
                Then drag clips to requirements
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
