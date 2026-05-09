import type { ChatCreateResponse, ChatThread, ChatUpdateRequest, Message } from '../types/chat'
import { API_BASE_URL } from '../lib/api'
import { getStoredToken } from './auth'

export type SendChatResponse = {
  reply: string
  model: string
  chat_id: string
  user_message_id: string
}

export type UploadAttachmentResponse = {
  id: string
  file_name: string
  file_type: string
  mime_type: string
  file_size: number
  upload_timestamp: string
}

export type AttachmentTextExtractionResponse = {
  attachment_id: string
  attachment_type: string
  extracted_text: string
  summary_text: string
}

function authHeaders(): HeadersInit {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function authJsonHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json', ...authHeaders() }
}

function formatErrorDetail(err: unknown): string | null {
  if (!err || typeof err !== 'object') return null
  const detail = (err as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== 'object') return String(item)
        const msg = (item as { msg?: unknown }).msg
        const loc = (item as { loc?: unknown }).loc
        const locText = Array.isArray(loc) ? loc.join('.') : ''
        return `${locText ? `${locText}: ` : ''}${typeof msg === 'string' ? msg : JSON.stringify(item)}`
      })
      .join('; ')
  }
  if (detail !== undefined) return JSON.stringify(detail)
  return null
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

export async function createUserMessage(chatId: string, content: string): Promise<Message> {
  const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify({ content }),
  })

  if (!response.ok) {
    let detail = `Failed to create user message: ${response.status}`
    try {
      const err = (await response.json()) as unknown
      const parsed = formatErrorDetail(err)
      if (parsed) detail = parsed
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return (await response.json()) as Message
}

export async function sendChatMessage(payload: {
  message: string
  chat_id?: string
  temperature?: number
  attachment_context?: string[]
}): Promise<SendChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let detail = `Failed to send message: ${response.status}`
    try {
      const err = (await response.json()) as unknown
      const parsed = formatErrorDetail(err)
      if (parsed) detail = parsed
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return (await response.json()) as SendChatResponse
}

export async function uploadAttachment(
  messageId: string,
  fileType: string,
  file: File,
): Promise<UploadAttachmentResponse> {
  console.log(`[Attachment] Starting upload: messageId=${messageId}, type=${fileType}, file=${file.name}`)
  
  const formData = new FormData()
  formData.append('message_id', messageId)
  formData.append('file_type', fileType)
  formData.append('file', file)

  const token = getStoredToken()
  const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}

  const response = await fetch(`${API_BASE_URL}/api/attachments/upload`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    let detail = `Failed to upload attachment: ${response.status}`
    try {
      const err = (await response.json()) as unknown
      const parsed = formatErrorDetail(err)
      if (parsed) detail = parsed
    } catch {
      // ignore parse errors
    }
    console.error(`[Attachment] Upload failed: ${detail}`)
    throw new Error(detail)
  }

  const result = (await response.json()) as UploadAttachmentResponse
  console.log(`[Attachment] Upload successful: ${result.file_name} (${result.file_size} bytes)`)
  return result
}

export async function downloadAttachment(attachmentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/attachments/download/${attachmentId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to download attachment: ${response.status}`)
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'download'
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/attachments/${attachmentId}`, {
    method: 'DELETE',
    headers: authJsonHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to delete attachment: ${response.status}`)
  }
}

export async function extractAttachmentText(attachmentId: string): Promise<AttachmentTextExtractionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/attachments/extract-text/${attachmentId}`, {
    method: 'POST',
    headers: authJsonHeaders(),
  })

  if (!response.ok) {
    let detail = `Failed to extract text: ${response.status}`
    try {
      const err = (await response.json()) as { detail?: string }
      if (err?.detail) detail = err.detail
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return (await response.json()) as AttachmentTextExtractionResponse
}
