import { Bot, User, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ChatMessage as ChatMessageType, AgentAction, AgentSource } from '@/hooks/useAgentChat'
import { ActionButton } from './ActionButton'

interface ChatMessageProps {
  message: ChatMessageType
  onActionClick: (action: AgentAction) => void
  onSourceClick: (source: AgentSource) => void
}

export function ChatMessage({ message, onActionClick, onSourceClick }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isLoading = message.isLoading
  const hasError = !!message.error

  return (
    <div
      className={cn(
        'flex gap-3 p-3 rounded-lg',
        isUser ? 'bg-muted/50' : 'bg-background'
      )}
    >
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        )}
      >
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <Bot className="h-4 w-4" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium">
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
        </div>

        {isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Thinking...</span>
          </div>
        ) : hasError ? (
          <div className="flex items-start gap-2 text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm">{message.content}</p>
              <p className="text-xs mt-1 text-muted-foreground">
                Error: {message.error}
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="text-sm whitespace-pre-wrap break-words">
              {message.content}
            </div>

            {message.actions && message.actions.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {message.actions.map((action, index) => (
                  <ActionButton
                    key={`${action.type}-${index}`}
                    action={action}
                    onClick={() => onActionClick(action)}
                  />
                ))}
              </div>
            )}

            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 pt-2 border-t">
                <p className="text-xs text-muted-foreground mb-2">Sources:</p>
                <div className="flex flex-wrap gap-1">
                  {message.sources.map((source, index) => (
                    <button
                      key={`${source.document_id}-${index}`}
                      onClick={() => onSourceClick(source)}
                      className="text-xs px-2 py-1 rounded bg-muted hover:bg-muted/80 transition-colors"
                    >
                      {source.document_name}
                      {source.page && ` (p. ${source.page})`}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
