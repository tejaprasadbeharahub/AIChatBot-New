import { useState } from 'react'
import { askAgent, createGame, makeMove, makeMoveStream, resetGame } from '../../api/tictactoe'
import type {
  TicTacToeChatHistoryItem,
  TicTacToeDifficulty,
  TicTacToeGameState,
  TicTacToeReasoningStep,
  TicTacToeSymbol,
} from '../../types/tictactoe'
import { Board } from './Board'
import { CoachChatPanel } from './CoachChatPanel'
import { GameControls } from './GameControls'
import { GameStatus } from './GameStatus'
import { ReasoningPanel } from './ReasoningPanel'

export function TicTacToeGame() {
  const [game, setGame] = useState<TicTacToeGameState | null>(null)
  const [playerSymbol, setPlayerSymbol] = useState<TicTacToeSymbol>('X')
  const [difficulty, setDifficulty] = useState<TicTacToeDifficulty>('unbeatable')
  const [isLoading, setIsLoading] = useState(false)
  const [isReasoningStreaming, setIsReasoningStreaming] = useState(false)
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastAiMoveIndex, setLastAiMoveIndex] = useState<number | null>(null)
  const [reasoningSteps, setReasoningSteps] = useState<TicTacToeReasoningStep[]>([])
  const [chatHistory, setChatHistory] = useState<TicTacToeChatHistoryItem[]>([])
  const [strategyHints, setStrategyHints] = useState<string[]>([])

  async function handleNewGame() {
    setError(null)
    setLastAiMoveIndex(null)
    setReasoningSteps([])
    setChatHistory([])
    setStrategyHints([])
    setIsLoading(true)
    try {
      const state = await createGame(playerSymbol, difficulty)
      setGame(state)
      setReasoningSteps(state.ai_reasoning ?? [])
      setChatHistory(state.conversation_history ?? [])
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
    setReasoningSteps([])
    setChatHistory([])
    setStrategyHints([])
    setIsLoading(true)
    try {
      const state = await resetGame(game.game_id)
      setGame(state)
      setReasoningSteps(state.ai_reasoning ?? [])
      setChatHistory(state.conversation_history ?? [])
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
      if (difficulty === 'reasoning' || difficulty === 'hybrid') {
        setIsReasoningStreaming(true)
        setReasoningSteps([])
        await makeMoveStream(game.game_id, index, {
          onReasoning: (step) => {
            setReasoningSteps((prev) => [...prev, step])
          },
          onResult: (response) => {
            setLastAiMoveIndex(response.ai_move_index ?? null)
            setReasoningSteps(response.ai_reasoning ?? [])
            setGame((prev) =>
              prev
                ? {
                    ...prev,
                    board: response.board,
                    current_turn: response.current_turn,
                    status: response.status,
                    winning_cells: response.winning_cells,
                    move_history: response.move_history,
                    ai_reasoning: response.ai_reasoning,
                  }
                : prev,
            )
          },
        })
        setIsReasoningStreaming(false)
      } else {
        const response = await makeMove(game.game_id, index)
        setLastAiMoveIndex(response.ai_move_index ?? null)
        setReasoningSteps(response.ai_reasoning ?? [])
        setGame((prev) =>
          prev
            ? {
                ...prev,
                board: response.board,
                current_turn: response.current_turn,
                status: response.status,
                winning_cells: response.winning_cells,
                move_history: response.move_history,
                ai_reasoning: response.ai_reasoning,
              }
            : prev,
        )
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Move failed.')
    } finally {
      setIsReasoningStreaming(false)
      setIsLoading(false)
    }
  }

  async function handleAskCoach(message: string) {
    if (!game) return
    setError(null)
    setIsChatLoading(true)
    try {
      const response = await askAgent(game.game_id, message)
      setChatHistory(response.conversation_history)
      setStrategyHints(response.strategy_hints)
      setGame((prev) =>
        prev
          ? {
              ...prev,
              conversation_history: response.conversation_history,
            }
          : prev,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI coach is unavailable.')
    } finally {
      setIsChatLoading(false)
    }
  }

  const boardDisabled =
    isLoading ||
    !game ||
    game.status !== 'ongoing' ||
    game.current_turn !== 'player'

  return (
    <div className="w-full max-w-6xl mx-auto py-6 px-2 md:px-4">
      <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-5 md:p-7 shadow-[0_16px_45px_rgba(15,23,42,0.08)]">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700">Game Arena</p>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Tic Tac Toe AI</h1>
            <p className="mt-1 text-sm text-slate-600">Play a match with explainable agent reasoning.</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 min-w-[250px]">
            {game ? (
              <GameStatus
                status={game.status}
                currentTurn={game.current_turn}
                isLoading={isLoading}
              />
            ) : (
              <p className="text-sm text-slate-500">Configure options and start a new game.</p>
            )}
          </div>
        </div>

        <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-4 md:p-5">
            {game ? (
              <>
                <div className="w-full max-w-xs mx-auto">
                  <Board
                    board={game.board}
                    winningCells={game.winning_cells}
                    lastAiMoveIndex={lastAiMoveIndex}
                    disabled={boardDisabled}
                    onCellClick={handleCellClick}
                  />
                </div>

                <div className="mt-4 flex justify-center gap-6 text-xs text-slate-600">
                  <span>
                    <span className="font-semibold text-indigo-700">{game.player_symbol}</span> You
                  </span>
                  <span>
                    <span className="font-semibold text-rose-700">{game.ai_symbol}</span> Agent
                  </span>
                </div>
              </>
            ) : (
              <div className="grid grid-cols-3 gap-2 w-full max-w-xs mx-auto opacity-30 pointer-events-none">
                {Array.from({ length: 9 }).map((_, i) => (
                  <div key={i} className="aspect-square rounded-xl bg-slate-200 border-2 border-slate-300" />
                ))}
              </div>
            )}

            <div className="mt-5">
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
            </div>
          </section>

          <section className="grid gap-4 content-start">
            <ReasoningPanel
              steps={reasoningSteps}
              isStreaming={isReasoningStreaming}
            />

            <CoachChatPanel
              history={chatHistory}
              strategyHints={strategyHints}
              isLoading={isChatLoading}
              disabled={!game}
              onAsk={handleAskCoach}
            />
          </section>
        </div>

        {error && (
          <p className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </p>
        )}
      </div>
    </div>
  )
}
