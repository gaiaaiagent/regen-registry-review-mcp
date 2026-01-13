import { useState, useRef, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { MessageSquare, Send, Trash2, Info } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ChatMessage } from './ChatMessage'
import { useAgentChat, type AgentAction, type AgentSource, type AgentContext } from '@/hooks/useAgentChat'
import { useWorkspaceContext } from '@/contexts/WorkspaceContext'

interface ChatPanelProps {
  sessionId?: string
}

export function ChatPanel({ sessionId: propSessionId }: ChatPanelProps) {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>()
  const sessionId = propSessionId ?? paramSessionId

  const { messages, sendMessage, clearMessages, isLoading } = useAgentChat(sessionId)
  const {
    focusedRequirementId,
    activeDocumentId,
    scrollToEvidence,
  } = useWorkspaceContext()

  const [inputValue, setInputValue] = useState('')
  const [confirmAction, setConfirmAction] = useState<AgentAction | null>(null)

  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const buildContext = useCallback((): AgentContext => {
    return {
      focused_requirement_id: focusedRequirementId,
      visible_document_id: activeDocumentId,
      visible_page: null,
    }
  }, [focusedRequirementId, activeDocumentId])

  const handleSubmit = useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault()
      if (!inputValue.trim() || isLoading) return

      const context = buildContext()
      sendMessage(inputValue, context)
      setInputValue('')
    },
    [inputValue, isLoading, sendMessage, buildContext]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit()
      }
    },
    [handleSubmit]
  )

  const handleActionClick = useCallback((action: AgentAction) => {
    setConfirmAction(action)
  }, [])

  const executeAction = useCallback(() => {
    if (!confirmAction) return

    switch (confirmAction.type) {
      case 'navigate': {
        const documentId = confirmAction.params.document_id as string
        const page = confirmAction.params.page as number
        if (documentId && page) {
          scrollToEvidence(documentId, page)
          toast.success('Navigated to document', {
            description: `Page ${page}`,
          })
        }
        break
      }
      case 'validate':
        toast.info('Validation', {
          description: 'Validation feature will run cross-document checks.',
        })
        break
      case 'extract':
        toast.info('Extract Evidence', {
          description: `Would extract evidence for ${confirmAction.params.requirement_id}`,
        })
        break
      default:
        toast.info('Action', {
          description: `Would execute: ${confirmAction.label}`,
        })
    }

    setConfirmAction(null)
  }, [confirmAction, scrollToEvidence])

  const handleSourceClick = useCallback(
    (source: AgentSource) => {
      if (source.document_id && source.page) {
        scrollToEvidence(source.document_id, source.page)
        toast.success('Navigated to source', {
          description: `${source.document_name}, page ${source.page}`,
        })
      } else if (source.document_id) {
        scrollToEvidence(source.document_id, 1)
        toast.success('Opened document', {
          description: source.document_name,
        })
      }
    },
    [scrollToEvidence]
  )

  const handleClearChat = useCallback(() => {
    clearMessages()
    toast.success('Chat cleared')
  }, [clearMessages])

  const hasContext = focusedRequirementId || activeDocumentId

  return (
    <div className="h-full flex flex-col bg-card">
      <div className="px-4 py-3 border-b bg-muted/30">
        <div className="flex items-center justify-between">
          <h2 className="font-medium flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            AI Assistant
          </h2>
          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearChat}
              className="h-7 text-xs"
            >
              <Trash2 className="h-3 w-3 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {hasContext && (
        <div className="px-4 py-2 border-b bg-muted/10 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Info className="h-3 w-3" />
            <span>Context:</span>
            {focusedRequirementId && (
              <span className="px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                {focusedRequirementId}
              </span>
            )}
            {activeDocumentId && (
              <span className="px-1.5 py-0.5 rounded bg-muted">
                Doc: {activeDocumentId.slice(0, 8)}...
              </span>
            )}
          </div>
        </div>
      )}

      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-4 space-y-4">
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onActionClick={handleActionClick}
                onSourceClick={handleSourceClick}
              />
            ))
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t bg-muted/20">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about requirements, evidence, or documents..."
            className="min-h-[40px] max-h-[120px] flex-1"
            disabled={isLoading || !sessionId}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!inputValue.trim() || isLoading || !sessionId}
            className="h-10 w-10 shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>

      <Dialog open={!!confirmAction} onOpenChange={() => setConfirmAction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogDescription>
              The AI assistant suggests the following action:
            </DialogDescription>
          </DialogHeader>
          {confirmAction && (
            <div className="py-4">
              <p className="font-medium">{confirmAction.label}</p>
              <p className="text-sm text-muted-foreground mt-1">
                Type: {confirmAction.type}
              </p>
              {Object.keys(confirmAction.params).length > 0 && (
                <div className="mt-2 text-sm">
                  <p className="text-muted-foreground">Parameters:</p>
                  <pre className="mt-1 p-2 bg-muted rounded text-xs overflow-auto">
                    {JSON.stringify(confirmAction.params, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmAction(null)}>
              Cancel
            </Button>
            <Button onClick={executeAction}>Execute</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <MessageSquare className="h-12 w-12 text-muted-foreground/30 mb-4" />
      <h3 className="font-medium text-sm">AI Assistant</h3>
      <p className="text-xs text-muted-foreground mt-2 max-w-[200px]">
        Ask questions about the review, search for evidence, or get help understanding requirements.
      </p>
      <div className="mt-4 space-y-2 text-xs text-muted-foreground">
        <p className="font-medium">Try asking:</p>
        <ul className="space-y-1">
          <li>"What evidence do we have for land tenure?"</li>
          <li>"Which requirements are missing evidence?"</li>
          <li>"Summarize the project status"</li>
        </ul>
      </div>
    </div>
  )
}
