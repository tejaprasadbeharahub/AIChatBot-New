const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000"

type QueryValue = string | number | boolean | null | undefined

type ApiRequestOptions = RequestInit & {
  query?: Record<string, QueryValue>
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  const url = new URL(`${API_BASE_URL}${normalizedPath}`)

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== null && value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  return url.toString()
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { query, headers, ...rest } = options

  const response = await fetch(buildUrl(path, query), {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(headers ?? {}),
    },
    ...rest,
  })

  if (!response.ok) {
    let errorMessage = `API request failed: ${response.status}`
    try {
      const errorBody = (await response.json()) as { detail?: string }
      if (errorBody?.detail) {
        errorMessage = errorBody.detail
      }
    } catch {
      // Ignore JSON parse failures and keep default message.
    }
    throw new Error(errorMessage)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export { API_BASE_URL }
