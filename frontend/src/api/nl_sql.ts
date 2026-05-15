import { API_BASE_URL } from '../lib/api'
import type {
  DBConnection,
  DBConnectionCreateRequest,
  DBConnectionUpdateRequest,
  DBConnectionValidationResponse,
  ExecuteNLQueryRequest,
  ExecuteNLQueryResponse,
  SchemaMetadataResponse,
  SQLQueryHistoryResponse,
} from '../types/nl_sql'
import { getStoredToken } from './auth'

function authJsonHeaders(): HeadersInit {
  const token = getStoredToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function parseError(response: Response, fallback: string): Promise<never> {
  let detail = fallback
  try {
    const payload = (await response.json()) as { detail?: string }
    if (payload?.detail) detail = payload.detail
  } catch {
    // ignore parse errors
  }
  throw new Error(detail)
}

export async function listDBConnections(): Promise<DBConnection[]> {
  const response = await fetch(`${API_BASE_URL}/api/nl-sql/connections`, {
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    return parseError(response, `Failed to fetch DB connections: ${response.status}`)
  }
  return (await response.json()) as DBConnection[]
}

export async function createDBConnection(payload: DBConnectionCreateRequest): Promise<DBConnection> {
  const response = await fetch(`${API_BASE_URL}/api/nl-sql/connections`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    return parseError(response, `Failed to create DB connection: ${response.status}`)
  }
  return (await response.json()) as DBConnection
}

export async function updateDBConnection(connectionId: string, payload: DBConnectionUpdateRequest): Promise<DBConnection> {
  const response = await fetch(`${API_BASE_URL}/api/nl-sql/connections/${connectionId}`, {
    method: 'PUT',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    return parseError(response, `Failed to update DB connection: ${response.status}`)
  }
  return (await response.json()) as DBConnection
}

export async function deleteDBConnection(connectionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/nl-sql/connections/${connectionId}`, {
    method: 'DELETE',
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    return parseError(response, `Failed to delete DB connection: ${response.status}`)
  }
}

export async function validateDBConnection(connectionId: string): Promise<DBConnectionValidationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/nl-sql/connections/${connectionId}/validate`, {
    method: 'POST',
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    return parseError(response, `Failed to validate DB connection: ${response.status}`)
  }
  return (await response.json()) as DBConnectionValidationResponse
}

export async function getDBSchema(connectionId: string): Promise<SchemaMetadataResponse> {
  const response = await fetch(`${API_BASE_URL}/api/nl-sql/connections/${connectionId}/schema`, {
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    return parseError(response, `Failed to fetch schema: ${response.status}`)
  }
  return (await response.json()) as SchemaMetadataResponse
}

export async function executeNLSQL(payload: ExecuteNLQueryRequest): Promise<ExecuteNLQueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/nl-sql/query`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    return parseError(response, `Failed to execute NL SQL query: ${response.status}`)
  }
  return (await response.json()) as ExecuteNLQueryResponse
}

export async function getSQLQueryHistory(chatId?: string, connectionId?: string): Promise<SQLQueryHistoryResponse> {
  const params = new URLSearchParams()
  if (chatId) params.set('chat_id', chatId)
  if (connectionId) params.set('connection_id', connectionId)

  const response = await fetch(`${API_BASE_URL}/api/nl-sql/history?${params.toString()}`, {
    headers: authJsonHeaders(),
  })
  if (!response.ok) {
    return parseError(response, `Failed to fetch SQL query history: ${response.status}`)
  }
  return (await response.json()) as SQLQueryHistoryResponse
}
