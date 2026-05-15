import type { GeneratedImage } from './image_generation'
import type { SQLQueryExecution } from './nl_sql'

export type ChatThread = {
  id: string
  user_id: string
  title: string | null
  created_at: string
  updated_at: string
}

export type ChatCreateResponse = ChatThread

export type ChatUpdateRequest = {
  title: string
}

export type Chat = ChatThread

export type Attachment = {
  id: string
  file_name: string
  file_type: 'image' | 'video' | 'code' | 'formula' | 'document'
  mime_type: string
  file_size: number
  upload_timestamp: string
}

export type { GeneratedImage } from './image_generation'

export type Message = {
  id: string
  chat_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  attachments: Attachment[]
  generated_images?: GeneratedImage[]
}
