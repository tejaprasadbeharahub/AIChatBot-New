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

export type Message = {
  id: string
  chat_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}
