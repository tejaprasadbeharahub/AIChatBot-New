import { useState } from 'react'
import { createGame, makeMove, resetGame } from '../../api/tictactoe'
import type {
  TicTacToeDifficulty,
  TicTacToeGameState,
  TicTacToeSymbol,
} from '../../types/tictactoe'
import { Board } from './Board'
import { GameControls } from './GameControls'
import { GameStatus } from './GameStatus'

export function TicTacToeGame() {
  const [game, setGame] = useState<TicTacToeGameState | null>(null)
  const [playerSymbol, setPlayerSymbol] = useState<TicTacToeSymbol>('X')
  const [difficulty, setDifficulty] = useState<TicTacToeDifficulty>('unbeatable')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastAiMoveIndex, setLastAiMoveIndex] = useState<number | null>(null)

  async function handleNewGame() {
    setError(null)
    setLastAiMoveIndex(null)
    setIsLoading(true)
    try {
      const state = await createGame(playerSymbol, difficulty)
      setGame(state)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start game.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleReset() {
    if (!game) return
    setError(null)
    setLastAiMoveIndex(null)
    setIsLoading(true)
    try {
      const state = await resetGame(game.game_id)
      setGame(state)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset game.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleCellClick(index: number) {
    if (!game || isLoading || game.status !== 'ongoing' || game.current_turn !== 'player') return
    setError(null)
    setLastAiMoveIndex(null)
    setIsLoading(true)
    try {
      const response = await makeMove(game.game_id, index)
      setLastAiMoveIndex(response.ai_move_index ?? null)
      setGame((prev) =>
        prev
          ? {
              ...prev,
              board: response.board,
              current_turn: response.current_turn,
              status: response.status,
              winning_cells: response.winning_cells,
            }
          : prev,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Move failed.')
    } finally {
      setIsLoading(false)
    }
  }

  const boardDisabled =
    isLoading ||
    !game ||
    game.status !== 'ongoing' ||
    game.current_turn !== 'player'

  return (
    <div className="flex flex-col items-center gap-6 py-8 px-4 min-h-full">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white tracking-tight">Tic Tac Toe</h1>
        <p className="text-slate-400 text-sm mt-1">Play against an AI agent</p>
      </div>

      {/* Game status / intro */}
      <div className="h-8 flex items-center justify-center">
        {game ? (
          <GameStatus
            status={game.status}
            currentTurn={game.current_turn}
            isLoading={isLoading}
          />
        ) : (
          <p className="text-slate-500 text-sm">Configure and start a new game below</p>
        )}
      </div>

      {/* Board */}
      {game ? (
        <div className="w-full max-w-xs">
          <Board
            board={game.board}
            winningCells={game.winning_cells}
            lastAiMoveIndex={lastAiMoveIndex}
            disabled={boardDisabled}
            onCellClick={handleCellClick}
          />

          {/* Legend */}
          <div className="flex justify-center gap-6 mt-4 text-xs text-slate-500">
            <span>
              <span className="text-indigo-400 font-semibold">{game.player_symbol}</span> — You
            </span>
            <span>
              <span className="text-rose-400 font-semibold">{game.ai_symbol}</span> — AI
            </span>
          </div>
        </div>
      ) : (
        /* Placeholder board skeleton */
        <div className="grid grid-cols-3 gap-2 w-full max-w-xs mx-auto opacity-20 pointer-events-none">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="aspect-square rounded-xl bg-slate-700 border-2 border-slate-600" />
          ))}
        </div>
      )}

      {/* Controls */}
      <GameControls
        playerSymbol={playerSymbol}
        difficulty={difficulty}
        hasGame={!!game}
        isLoading={isLoading}
        onSymbolChange={setPlayerSymbol}
        onDifficultyChange={setDifficulty}
        onNewGame={handleNewGame}
        onReset={handleReset}
      />

      {/* Error */}
      {error && (
        <p className="text-rose-400 text-sm bg-rose-950/40 border border-rose-800 rounded-lg px-4 py-2 max-w-xs text-center">
          {error}
        </p>
      )}
    </div>
  )
}
