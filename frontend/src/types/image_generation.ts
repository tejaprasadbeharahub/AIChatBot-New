export type GenerationStatus = 'pending' | 'completed' | 'failed'

export interface GeneratedImage {
  id: string
  message_id: string
  chat_id?: string
  prompt: string
  image_url: string | null
  status: GenerationStatus
  error_message: string | null
  generation_timestamp: string
  completion_timestamp: string | null
}

export interface ImageGenerationRequest {
  prompt: string
  chat_id: string
  message_id: string
}

export interface ImageGenerationResponse {
  id: string
  status: GenerationStatus
  prompt: string
  image_url: string | null
  message_id: string
  generation_timestamp: string
  completion_timestamp: string | null
  error_message: string | null
}
