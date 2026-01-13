import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'

export interface AgentContext {
  focused_requirement_id?: string | null
  visible_document_id?: string | null
  visible_page?: number | null
}

export interface AgentAction {
  type: string
  label: string
  params: Record<string, unknown>
}

export interface AgentSource {
  document_id: string
  document_name: string
  page?: number | null
  text?: string | null
}

export interface AgentChatResponse {
  message: string
  actions: AgentAction[]
  sources: AgentSource[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  actions?: AgentAction[]
  sources?: AgentSource[]
  isLoading?: boolean
  error?: string
}

interface SendMessageParams {
  sessionId: string
  message: string
  context?: AgentContext
}

async function sendAgentMessage(params: SendMessageParams): Promise<AgentChatResponse> {
  const token = localStorage.getItem('auth_token')

  const response = await fetch(`${API_URL}/sessions/${params.sessionId}/agent/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      message: params.message,
      context: params.context,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export function useAgentChat(sessionId: string | undefined) {
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const mutation = useMutation({
    mutationFn: sendAgentMessage,
    onMutate: async (params) => {
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: params.message,
        timestamp: new Date(),
      }

      const loadingMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isLoading: true,
      }

      setMessages((prev) => [...prev, userMessage, loadingMessage])

      return { loadingMessageId: loadingMessage.id }
    },
    onSuccess: (data, _params, context) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === context?.loadingMessageId
            ? {
                ...msg,
                content: data.message,
                actions: data.actions,
                sources: data.sources,
                isLoading: false,
              }
            : msg
        )
      )
    },
    onError: (error: Error, _params, context) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === context?.loadingMessageId
            ? {
                ...msg,
                content: 'Sorry, I encountered an error. Please try again.',
                error: error.message,
                isLoading: false,
              }
            : msg
        )
      )
    },
  })

  const sendMessage = useCallback(
    (message: string, context?: AgentContext) => {
      if (!sessionId || !message.trim()) return

      mutation.mutate({
        sessionId,
        message: message.trim(),
        context,
      })
    },
    [sessionId, mutation]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    sendMessage,
    clearMessages,
    isLoading: mutation.isPending,
    error: mutation.error,
  }
}
