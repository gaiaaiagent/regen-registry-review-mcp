import { useState, useRef, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { MessageSquare, Send, Trash2, Info, Loader2 } from 'lucide-react'
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

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'

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
  const [isExecuting, setIsExecuting] = useState(false)

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

  const executeAction = useCallback(async () => {
    if (!confirmAction || !sessionId) return

    setIsExecuting(true)

    try {
      // Handle navigate locally for immediate response
      if (confirmAction.type === 'navigate' || confirmAction.type === 'navigate_to_citation') {
        const documentId = confirmAction.params.document_id as string
        const page = confirmAction.params.page as number
        if (documentId && page) {
          scrollToEvidence(documentId, page)
          toast.success('Navigated to document', { description: `Page ${page}` })
        }
        setConfirmAction(null)
        setIsExecuting(false)
        return
      }

      // Call the backend execute endpoint for other actions
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`${API_URL}/sessions/${sessionId}/agent/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          action_type: confirmAction.type,
          params: confirmAction.params,
        }),
      })

      const result = await response.json()

      if (!result.success) {
        toast.error('Action failed', { description: result.error })
        setConfirmAction(null)
        setIsExecuting(false)
        return
      }

      // Handle different action results
      switch (confirmAction.type) {
        case 'search_evidence': {
          const matches = result.result?.matches ?? []
          if (matches.length === 0) {
            toast.info('No matches', { description: `No evidence found for "${result.result?.query}"` })
          } else {
            toast.success('Search complete', {
              description: `Found ${result.result?.total_matches} matches. First: ${matches[0]?.document_name}, page ${matches[0]?.page}`,
            })
            // Navigate to the first match
            if (matches[0]?.document_id && matches[0]?.page) {
              scrollToEvidence(matches[0].document_id, matches[0].page)
            }
          }
          break
        }
        case 'get_requirement_status': {
          const data = result.result
          toast.success(`Requirement ${data?.requirement_id}`, {
            description: `Status: ${data?.status}, ${data?.evidence_count} evidence snippets`,
          })
          break
        }
        case 'suggest_verification': {
          toast.success('Verification suggested', {
            description: result.result?.message ?? 'Check the checklist panel',
          })
          break
        }
        default:
          toast.success('Action executed', {
            description: JSON.stringify(result.result).slice(0, 100),
          })
      }
    } catch (err) {
      toast.error('Action failed', {
        description: err instanceof Error ? err.message : 'Unknown error',
      })
    } finally {
      setConfirmAction(null)
      setIsExecuting(false)
    }
  }, [confirmAction, sessionId, scrollToEvidence])

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
            <Button variant="outline" onClick={() => setConfirmAction(null)} disabled={isExecuting}>
              Cancel
            </Button>
            <Button onClick={executeAction} disabled={isExecuting}>
              {isExecuting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Executing...
                </>
              ) : (
                'Execute'
              )}
            </Button>
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
        Ask questions about the review, search for evidence, or get help navigating documents.
      </p>
      <div className="mt-4 space-y-2 text-xs text-muted-foreground">
        <p className="font-medium">Try asking:</p>
        <ul className="space-y-1 text-left">
          <li>"Show me where you found the project start date"</li>
          <li>"What evidence do we have for land tenure?"</li>
          <li>"Which requirements are missing evidence?"</li>
          <li>"Navigate to the baseline report section"</li>
        </ul>
      </div>
    </div>
  )
}
