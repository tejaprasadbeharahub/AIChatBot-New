import { API_BASE_URL } from '../lib/api'
import type {
  TicTacToeAskAgentResponse,
  TicTacToeDifficulty,
  TicTacToeGameState,
  TicTacToeMoveResponse,
  TicTacToeReasoningStep,
  TicTacToeSymbol,
} from '../types/tictactoe'

type RequestOptions = RequestInit & {
  timeoutMs?: number
}

async function request<T>(path: string, init?: RequestOptions): Promise<T> {
  const { timeoutMs, ...fetchInit } = init ?? {}
  const controller = new AbortController()
  const timeoutHandle = timeoutMs
    ? setTimeout(() => {
        controller.abort()
      }, timeoutMs)
    : null

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...fetchInit,
      signal: controller.signal,
    })
  } catch (error) {
    if (timeoutHandle) clearTimeout(timeoutHandle)
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.')
    }
    throw error
  }

  if (timeoutHandle) clearTimeout(timeoutHandle)

  if (!res.ok) {
    let msg = `Request failed: ${res.status}`
    try {
      const body = (await res.json()) as { detail?: string }
      if (body.detail) msg = body.detail
    } catch { /* ignore */ }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController()
  const timeoutHandle = setTimeout(() => {
    controller.abort()
  }, timeoutMs)

  try {
    return await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
      ...init,
      signal: controller.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.')
    }
    throw error
  } finally {
    clearTimeout(timeoutHandle)
  }
}

async function requestStream(path: string, init: RequestInit, timeoutMs = 30000): Promise<Response> {
  const res = await fetchWithTimeout(`${API_BASE_URL}${path}`, init, timeoutMs)
  if (!res.ok) {
    let msg = `Request failed: ${res.status}`
    try {
      const body = (await res.json()) as { detail?: string }
      if (body.detail) msg = body.detail
    } catch {
      // ignore
    }
    throw new Error(msg)
  }
  return res
}

export function createGame(
  playerSymbol: TicTacToeSymbol,
  difficulty: TicTacToeDifficulty,
): Promise<TicTacToeGameState> {
  return request<TicTacToeGameState>('/api/tictactoe/games', {
    method: 'POST',
    body: JSON.stringify({ player_symbol: playerSymbol, difficulty }),
    timeoutMs: 15000,
  })
}

export function makeMove(gameId: string, cellIndex: number): Promise<TicTacToeMoveResponse> {
  return request<TicTacToeMoveResponse>(`/api/tictactoe/games/${gameId}/move`, {
    method: 'POST',
    body: JSON.stringify({ cell_index: cellIndex }),
    timeoutMs: 20000,
  })
}

interface MoveStreamEvent {
  event: 'reasoning' | 'move_result'
  data: TicTacToeReasoningStep | TicTacToeMoveResponse
}

export async function makeMoveStream(
  gameId: string,
  cellIndex: number,
  handlers: {
    onReasoning: (step: TicTacToeReasoningStep) => void
    onResult: (result: TicTacToeMoveResponse) => void
  },
): Promise<void> {
  const res = await requestStream(
    `/api/tictactoe/games/${gameId}/move-stream`,
    {
      method: 'POST',
      body: JSON.stringify({ cell_index: cellIndex }),
    },
    30000,
  )

  if (!res.body) throw new Error('Streaming response body is unavailable.')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''

    for (const chunk of chunks) {
      const line = chunk
        .split('\n')
        .map((x) => x.trim())
        .find((x) => x.startsWith('data:'))
      if (!line) continue

      const raw = line.slice('data:'.length).trim()
      if (!raw) continue
      const parsed = JSON.parse(raw) as MoveStreamEvent

      if (parsed.event === 'reasoning') {
        handlers.onReasoning(parsed.data as TicTacToeReasoningStep)
      }
      if (parsed.event === 'move_result') {
        handlers.onResult(parsed.data as TicTacToeMoveResponse)
      }
    }
  }
}

export function askAgent(gameId: string, message: string): Promise<TicTacToeAskAgentResponse> {
  return request<TicTacToeAskAgentResponse>(`/api/tictactoe/games/${gameId}/ask`, {
    method: 'POST',
    body: JSON.stringify({ message }),
    timeoutMs: 15000,
  })
}

export function resetGame(gameId: string): Promise<TicTacToeGameState> {
  return request<TicTacToeGameState>(`/api/tictactoe/games/${gameId}/reset`, {
    method: 'POST',
    timeoutMs: 15000,
  })
}
