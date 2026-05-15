export type TicTacToeSymbol = 'X' | 'O'
export type TicTacToeDifficulty = 'easy' | 'medium' | 'unbeatable'
export type TicTacToeStatus = 'ongoing' | 'player_wins' | 'ai_wins' | 'draw'
export type TicTacToeBoard = (TicTacToeSymbol | null)[]

export interface TicTacToeGameState {
  game_id: string
  board: TicTacToeBoard
  player_symbol: TicTacToeSymbol
  ai_symbol: TicTacToeSymbol
  difficulty: TicTacToeDifficulty
  current_turn: 'player' | 'ai' | 'done'
  status: TicTacToeStatus
  winning_cells: number[]
}

export interface TicTacToeMoveResponse {
  board: TicTacToeBoard
  player_symbol: TicTacToeSymbol
  ai_symbol: TicTacToeSymbol
  current_turn: 'player' | 'ai' | 'done'
  status: TicTacToeStatus
  winning_cells: number[]
  ai_move_index: number | null
}
