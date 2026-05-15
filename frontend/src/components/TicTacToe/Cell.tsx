import type { TicTacToeSymbol } from '../../types/tictactoe'

interface CellProps {
  index: number
  value: TicTacToeSymbol | null
  isWinning: boolean
  isLastAiMove: boolean
  disabled: boolean
  onClick: (index: number) => void
}

export function Cell({ index, value, isWinning, isLastAiMove, disabled, onClick }: CellProps) {
  const base =
    'flex items-center justify-center w-full aspect-square text-4xl font-bold rounded-xl border-2 transition-all duration-200 select-none cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400'

  const stateClass = isWinning
    ? 'bg-indigo-500 border-indigo-400 text-white scale-105 shadow-lg shadow-indigo-400/40'
    : isLastAiMove
      ? 'bg-slate-600 border-slate-500 text-amber-300'
      : value
        ? 'bg-slate-700 border-slate-600 cursor-default'
        : disabled
          ? 'bg-slate-800 border-slate-700 cursor-not-allowed opacity-50'
          : 'bg-slate-800 border-slate-600 hover:bg-slate-700 hover:border-indigo-500 hover:shadow-md hover:shadow-indigo-500/20'

  const symbolClass = value === 'X' ? 'text-indigo-400' : 'text-rose-400'

  return (
    <button
      type="button"
      aria-label={`Cell ${index + 1}${value ? `, ${value}` : ', empty'}`}
      className={`${base} ${stateClass}`}
      disabled={disabled || !!value}
      onClick={() => onClick(index)}
    >
      {value && (
        <span className={`${symbolClass} drop-shadow`}>{value}</span>
      )}
    </button>
  )
}
