import { apiRequest } from './api'
import type { ChatMessage, SessionListItem } from '@/store/aiAssistantStore'

export interface AssistantConfigPayload {
  api_url: string
  api_key: string
  model: string
  temperature: number
  max_tokens: number
  system_prompt: string
  enable_tools: boolean
  auto_approve: boolean
}

export interface ChatRequestPayload {
  session_id?: string | null
  message: string
  config: AssistantConfigPayload
  workflow_context?: Record<string, any>
}

export interface ChatResponsePayload {
  session_id: string
  message: ChatMessage
}

export const aiAssistantApi = {
  listSessions: () =>
    apiRequest<SessionListItem[]>('/ai-assistant/sessions'),

  createSession: (title?: string) =>
    apiRequest<{ session_id: string; title: string }>('/ai-assistant/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),

  getSession: (id: string) =>
    apiRequest<{ id: string; title: string; messages: ChatMessage[] }>(
      `/ai-assistant/sessions/${id}`
    ),

  deleteSession: (id: string) =>
    apiRequest<{ success: boolean }>(`/ai-assistant/sessions/${id}`, {
      method: 'DELETE',
    }),

  renameSession: (id: string, title: string) =>
    apiRequest<{ success: boolean }>(`/ai-assistant/sessions/${id}/title`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),

  chat: (req: ChatRequestPayload) =>
    apiRequest<ChatResponsePayload>('/ai-assistant/chat', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  listSkills: () =>
    apiRequest<{ count: number; skills: any[] }>('/ai-assistant/skills'),

  listMemories: () =>
    apiRequest<{ entries: any[] }>('/ai-assistant/memories'),

  addMemory: (content: string, tags: string[] = []) =>
    apiRequest('/ai-assistant/memories', {
      method: 'POST',
      body: JSON.stringify({ content, tags }),
    }),

  deleteMemory: (id: string) =>
    apiRequest(`/ai-assistant/memories/${id}`, { method: 'DELETE' }),
}
