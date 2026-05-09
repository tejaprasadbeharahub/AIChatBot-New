import type { ImageGenerationRequest, ImageGenerationResponse } from '../types/image_generation'
import { API_BASE_URL } from '../lib/api'
import { getStoredToken } from './auth'

function authJsonHeaders(): HeadersInit {
  const token = getStoredToken()
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
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

export async function generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/image-generation/generate`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    let detail = `Failed to generate image: ${response.status}`
    try {
      const err = (await response.json()) as unknown
      const parsed = formatErrorDetail(err)
      if (parsed) detail = parsed
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return (await response.json()) as ImageGenerationResponse
}

export async function getImageStatus(imageId: string): Promise<ImageGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/image-generation/${imageId}`, {
    headers: authJsonHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch image status: ${response.status}`)
  }

  return (await response.json()) as ImageGenerationResponse
}

export async function getChatGeneratedImages(
  chatId: string,
  limit: number = 50,
): Promise<ImageGenerationResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/image-generation/chat/${chatId}/images?limit=${limit}`, {
    headers: authJsonHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch generated images: ${response.status}`)
  }

  return (await response.json()) as ImageGenerationResponse[]
}

export async function downloadGeneratedImage(imageId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/image-generation/download/${imageId}`, {
    headers: authJsonHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to download image: ${response.status}`)
  }

  return response.blob()
}

export async function deleteGeneratedImage(imageId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/image-generation/${imageId}`, {
    method: 'DELETE',
    headers: authJsonHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to delete image: ${response.status}`)
  }
}
