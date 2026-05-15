import { API_BASE_URL } from '../lib/api'
import { getStoredToken } from './auth'

export type ResearchDigestPaper = {
  arxiv_id: string
  title: string
  authors: string[]
  abstract: string
  published_date: string
  categories: string[]
  pdf_url: string
  relevance_score: number
}

export type ResearchDigest = {
  summary: string
  key_findings: Array<{ topic: string; finding: string; evidence_papers: string[] }>
  methodologies: Array<{ name: string; frequency: number; papers: string[] }>
  limitations: string[]
  trends: Array<{ trend: string; direction: 'increasing' | 'decreasing' | 'stable'; recent_papers: string[] }>
  total_papers_reviewed: number
  papers_cited: ResearchDigestPaper[]
  search_duration_seconds: number
}

export type ResearchDigestResponse = {
  session_id: string
  chat_id: string
  user_message_id: string
  assistant_message_id: string
  query: string
  digest: ResearchDigest
  search_duration_seconds: number
  papers_found: number
}

function authJsonHeaders(): HeadersInit {
  const token = getStoredToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
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

export async function runResearchQuery(payload: {
  query: string
  chat_id?: string
  depth?: 'quick' | 'balanced' | 'deep'
  max_papers?: number
}): Promise<ResearchDigestResponse> {
  const response = await fetch(`${API_BASE_URL}/api/research-agent/research`, {
    method: 'POST',
    headers: authJsonHeaders(),
    body: JSON.stringify({
      query: payload.query,
      chat_id: payload.chat_id,
      depth: payload.depth ?? 'balanced',
      max_papers: payload.max_papers ?? 20,
    }),
  })

  if (!response.ok) {
    let detail = `Failed to run research: ${response.status}`
    try {
      const err = (await response.json()) as unknown
      const parsed = formatErrorDetail(err)
      if (parsed) detail = parsed
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return (await response.json()) as ResearchDigestResponse
}
