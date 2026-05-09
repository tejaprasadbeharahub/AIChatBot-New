import { API_BASE_URL } from '../lib/api'
import type { PdfDocument, PdfQueryResponse, PdfUploadResponse } from '../types/pdf_rag'
import { getStoredToken } from './auth'

function authHeaders(): HeadersInit {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function authJsonHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json', ...authHeaders() }
}

function formatError(err: unknown, fallback: string): string {
  if (!err || typeof err !== 'object') return fallback
  const detail = (err as { detail?: unknown }).detail
  if (typeof detail === 'string' && detail.trim().length > 0) return detail
  if (detail !== undefined) return JSON.stringify(detail)
  return fallback
}

export async function uploadPdfForChat(chatId: string, messageId: string, file: File): Promise<PdfDocument> {
  const formData = new FormData()
  formData.append('chat_id', chatId)
  formData.append('message_id', messageId)
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/pdf-rag/upload`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  })

  if (!response.ok) {
    let detail = `Failed to upload PDF: ${response.status}`
    try {
      const body = (await response.json()) as unknown
      detail = formatError(body, detail)
    } catch {
      // ignore parse failures
    }
    throw new Error(detail)
  }

  const payload = (await response.json()) as PdfUploadResponse
  return payload.document
}

export async function getPdfDocumentStatus(documentId: string): Promise<PdfDocument> {
  const response = await fetch(`${API_BASE_URL}/api/pdf-rag/documents/${documentId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch PDF status: ${response.status}`)
  }

  return (await response.json()) as PdfDocument
}

export async function getChatPdfDocuments(chatId: string): Promise<PdfDocument[]> {
  const response = await fetch(`${API_BASE_URL}/api/pdf-rag/chat/${chatId}/documents`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch PDF documents: ${response.status}`)
  }

  return (await response.json()) as PdfDocument[]
}

export async function processPdfDocument(documentId: string): Promise<PdfDocument> {
  const response = await fetch(`${API_BASE_URL}/api/pdf-rag/process/${documentId}`, {
    method: 'POST',
    headers: authJsonHeaders(),
  })

  if (!response.ok) {
    let detail = `Failed to process PDF: ${response.status}`
    try {
      const body = (await response.json()) as unknown
      detail = formatError(body, detail)
    } catch {
      // ignore parse failures
    }
    throw new Error(detail)
  }

  return (await response.json()) as PdfDocument
}

export async function queryChatPdfContext(chatId: string, query: string, topK = 5): Promise<PdfQueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/pdf-rag/chat/${chatId}/query`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify({ query, top_k: topK }),
  })

  if (!response.ok) {
    let detail = `Failed to query PDF context: ${response.status}`
    try {
      const body = (await response.json()) as unknown
      detail = formatError(body, detail)
    } catch {
      // ignore parse failures
    }
    throw new Error(detail)
  }

  return (await response.json()) as PdfQueryResponse
}
