import type { TicTacToeDifficulty, TicTacToeSymbol } from '../../types/tictactoe'

interface GameControlsProps {
  playerSymbol: TicTacToeSymbol
  difficulty: TicTacToeDifficulty
  hasGame: boolean
  isLoading: boolean
  onSymbolChange: (symbol: TicTacToeSymbol) => void
  onDifficultyChange: (diff: TicTacToeDifficulty) => void
  onNewGame: () => void
  onReset: () => void
}

const DIFFICULTIES: { value: TicTacToeDifficulty; label: string; description: string }[] = [
  { value: 'easy', label: 'Easy', description: 'Random moves' },
  { value: 'medium', label: 'Medium', description: 'Strategic play' },
  { value: 'unbeatable', label: 'Unbeatable', description: 'Minimax AI' },
]

export function GameControls({
  playerSymbol,
  difficulty,
  hasGame,
  isLoading,
  onSymbolChange,
  onDifficultyChange,
  onNewGame,
  onReset,
}: GameControlsProps) {
  return (
    <div className="flex flex-col gap-4 w-full max-w-xs mx-auto">
      {/* Symbol picker */}
      <div>
        <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">You play as</p>
        <div className="flex gap-2">
          {(['X', 'O'] as TicTacToeSymbol[]).map((sym) => (
            <button
              key={sym}
              type="button"
              disabled={hasGame}
              onClick={() => onSymbolChange(sym)}
              className={`flex-1 py-2 rounded-lg text-lg font-bold border-2 transition-all ${
                playerSymbol === sym
                  ? sym === 'X'
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-rose-600 border-rose-500 text-white'
                  : 'bg-slate-800 border-slate-600 text-slate-400 hover:border-slate-400'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {sym}
            </button>
          ))}
        </div>
        {hasGame && (
          <p className="text-xs text-slate-500 mt-1">Start a new game to change symbol</p>
        )}
      </div>

      {/* Difficulty picker */}
      <div>
        <p className="text-xs text-slate-400 uppercase tracking-wider mb-1.5">Difficulty</p>
        <div className="flex flex-col gap-1.5">
          {DIFFICULTIES.map(({ value, label, description }) => (
            <button
              key={value}
              type="button"
              disabled={hasGame}
              onClick={() => onDifficultyChange(value)}
              className={`flex items-center justify-between px-3 py-2 rounded-lg border transition-all text-sm ${
                difficulty === value
                  ? 'bg-slate-700 border-indigo-500 text-white'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <span className="font-medium">{label}</span>
              <span className="text-xs text-slate-500">{description}</span>
            </button>
          ))}
        </div>
        {hasGame && (
          <p className="text-xs text-slate-500 mt-1">Start a new game to change difficulty</p>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          type="button"
          disabled={isLoading}
          onClick={onNewGame}
          className="flex-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors"
        >
          New Game
        </button>
        {hasGame && (
          <button
            type="button"
            disabled={isLoading}
            onClick={onReset}
            className="flex-1 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 font-semibold text-sm transition-colors border border-slate-600"
          >
            Reset
          </button>
        )}
      </div>
    </div>
  )
}
