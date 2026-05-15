import type { TicTacToeStatus } from '../../types/tictactoe'

interface GameStatusProps {
  status: TicTacToeStatus
  currentTurn: 'player' | 'ai' | 'done'
  isLoading: boolean
}

const STATUS_MESSAGES: Record<TicTacToeStatus, string> = {
  ongoing: '',
  player_wins: '🎉 You win!',
  ai_wins: '🤖 AI wins!',
  draw: "🤝 It's a draw!",
}

export function GameStatus({ status, currentTurn, isLoading }: GameStatusProps) {
  const isOver = status !== 'ongoing'

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-amber-300 text-sm font-medium">
        <span className="inline-block w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
        AI is thinking…
      </div>
    )
  }

  if (isOver) {
    const colorClass =
      status === 'player_wins'
        ? 'text-indigo-300'
        : status === 'ai_wins'
          ? 'text-rose-400'
          : 'text-slate-300'
    return (
      <p className={`text-xl font-bold ${colorClass}`}>{STATUS_MESSAGES[status]}</p>
    )
  }

  return (
    <p className="text-sm text-slate-400">
      {currentTurn === 'player' ? (
        <span className="text-indigo-300 font-semibold">Your turn</span>
      ) : (
        <span className="text-amber-300 font-semibold">AI's turn</span>
      )}
    </p>
  )
}
