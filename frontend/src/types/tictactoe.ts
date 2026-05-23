export type TicTacToeSymbol = 'X' | 'O'
export type TicTacToeDifficulty = 'easy' | 'medium' | 'unbeatable' | 'reasoning' | 'hybrid'
export type TicTacToeStatus = 'ongoing' | 'player_wins' | 'ai_wins' | 'draw'
export type TicTacToeBoard = (TicTacToeSymbol | null)[]

export type TicTacToeReasoningSource = 'heuristic' | 'llm' | 'minimax' | 'validation' | 'system'

export interface TicTacToeReasoningStep {
  step: string
  detail: string
  source: TicTacToeReasoningSource
  confidence: number | null
}

export interface TicTacToeMoveHistoryItem {
  move_number: number
  symbol: TicTacToeSymbol
  cell_index: number
  board_snapshot: TicTacToeBoard
  reason: string | null
}

export interface TicTacToeChatHistoryItem {
  role: 'user' | 'assistant'
  message: string
}

export interface TicTacToeGameState {
  game_id: string
  board: TicTacToeBoard
  player_symbol: TicTacToeSymbol
  ai_symbol: TicTacToeSymbol
  difficulty: TicTacToeDifficulty
  current_turn: 'player' | 'ai' | 'done'
  status: TicTacToeStatus
  winning_cells: number[]
  ai_reasoning: TicTacToeReasoningStep[]
  move_history: TicTacToeMoveHistoryItem[]
  conversation_history: TicTacToeChatHistoryItem[]
}

export interface TicTacToeMoveResponse {
  board: TicTacToeBoard
  player_symbol: TicTacToeSymbol
  ai_symbol: TicTacToeSymbol
  current_turn: 'player' | 'ai' | 'done'
  status: TicTacToeStatus
  winning_cells: number[]
  ai_move_index: number | null
  ai_strategy: string
  ai_reasoning: TicTacToeReasoningStep[]
  move_history: TicTacToeMoveHistoryItem[]
}

export interface TicTacToeAskAgentResponse {
  answer: string
  strategy_hints: string[]
  conversation_history: TicTacToeChatHistoryItem[]
}
