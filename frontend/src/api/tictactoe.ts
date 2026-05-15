import { API_BASE_URL } from '../lib/api'
import type {
  TicTacToeDifficulty,
  TicTacToeGameState,
  TicTacToeMoveResponse,
  TicTacToeSymbol,
} from '../types/tictactoe'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
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

export function createGame(
  playerSymbol: TicTacToeSymbol,
  difficulty: TicTacToeDifficulty,
): Promise<TicTacToeGameState> {
  return request<TicTacToeGameState>('/api/tictactoe/games', {
    method: 'POST',
    body: JSON.stringify({ player_symbol: playerSymbol, difficulty }),
  })
}

export function makeMove(gameId: string, cellIndex: number): Promise<TicTacToeMoveResponse> {
  return request<TicTacToeMoveResponse>(`/api/tictactoe/games/${gameId}/move`, {
    method: 'POST',
    body: JSON.stringify({ cell_index: cellIndex }),
  })
}

export function resetGame(gameId: string): Promise<TicTacToeGameState> {
  return request<TicTacToeGameState>(`/api/tictactoe/games/${gameId}/reset`, {
    method: 'POST',
  })
}
