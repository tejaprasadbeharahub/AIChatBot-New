import type { ChatCreateResponse, ChatThread, ChatUpdateRequest, Message } from '../types/chat'
import { API_BASE_URL } from '../lib/api'
import { getStoredToken } from './auth'

export type SendChatResponse = {
  reply: string
  model: string
  chat_id: string
}

function authHeaders(): HeadersInit {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function authJsonHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json', ...authHeaders() }
}

export async function getChats(): Promise<ChatThread[]> {
  const response = await fetch(`${API_BASE_URL}/api/chats`, {
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch chats: ${response.status}`)
  }
  return (await response.json()) as ChatThread[]
}

export async function createChat(): Promise<ChatCreateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chats`, {
    method: 'POST',
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to create chat: ${response.status}`)
  }
  return (await response.json()) as ChatCreateResponse
}

export async function updateChatTitle(chatId: string, payload: ChatUpdateRequest): Promise<ChatThread> {
  const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
    method: 'PUT',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Failed to update chat: ${response.status}`)
  }
  return (await response.json()) as ChatThread
}

export async function deleteChat(chatId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
    method: 'DELETE',
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to delete chat: ${response.status}`)
  }
}

export async function getMessages(chatId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages`, {
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch messages: ${response.status}`)
  }
  return (await response.json()) as Message[]
}

export async function sendChatMessage(payload: {
  message: string
  history: Array<{ role: 'user' | 'assistant'; content: string }>
  chat_id?: string
}): Promise<SendChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let detail = `Failed to send message: ${response.status}`
    try {
      const err = (await response.json()) as { detail?: string }
      if (err?.detail) detail = err.detail
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return (await response.json()) as SendChatResponse
}
