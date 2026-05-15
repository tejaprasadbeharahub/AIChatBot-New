import { API_BASE_URL } from '../lib/api'
import type {
  ConnectGoogleSheetRequest,
  ConnectGoogleSheetResponse,
  ListDatasourcesResponse,
  SheetDatasource,
  SheetQueryRequest,
  SheetQueryResponse,
  SheetUploadResponse,
} from '../types/sheet_agent'
import { getStoredToken } from './auth'

function authHeaders(): HeadersInit {
  const token = getStoredToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function authJsonHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json', ...authHeaders() }
}

async function parseError(response: Response, fallback: string): Promise<never> {
  let detail = fallback
  try {
    const body = (await response.json()) as { detail?: string }
    if (body?.detail) detail = body.detail
  } catch {
    // ignore
  }
  throw new Error(detail)
}

export async function uploadSheetFile(chatId: string, file: File): Promise<SheetDatasource> {
  const formData = new FormData()
  formData.append('chat_id', chatId)
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/sheet-agent/upload`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  })

  if (!response.ok) {
    return parseError(response, `Failed to upload file: ${response.status}`)
  }

  const payload = (await response.json()) as SheetUploadResponse
  return payload.datasource
}

export async function connectGoogleSheet(payload: ConnectGoogleSheetRequest): Promise<SheetDatasource> {
  const response = await fetch(`${API_BASE_URL}/api/sheet-agent/connect-google-sheet`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    return parseError(response, `Failed to connect Google Sheet: ${response.status}`)
  }

  const data = (await response.json()) as ConnectGoogleSheetResponse
  return data.datasource
}

export async function querySheetDatasource(payload: SheetQueryRequest): Promise<SheetQueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sheet-agent/query`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    return parseError(response, `Failed to query datasource: ${response.status}`)
  }

  return (await response.json()) as SheetQueryResponse
}

export async function listChatDatasources(chatId: string): Promise<SheetDatasource[]> {
  const response = await fetch(`${API_BASE_URL}/api/sheet-agent/chat/${chatId}/datasources`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    return parseError(response, `Failed to list datasources: ${response.status}`)
  }

  const data = (await response.json()) as ListDatasourcesResponse
  return data.items
}

export async function getSheetDatasource(datasourceId: string): Promise<SheetDatasource> {
  const response = await fetch(`${API_BASE_URL}/api/sheet-agent/datasources/${datasourceId}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    return parseError(response, `Failed to get datasource: ${response.status}`)
  }

  return (await response.json()) as SheetDatasource
}

export async function deleteSheetDatasource(datasourceId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sheet-agent/datasources/${datasourceId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })

  if (!response.ok) {
    return parseError(response, `Failed to delete datasource: ${response.status}`)
  }
}
