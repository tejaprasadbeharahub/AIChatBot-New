import type { TicTacToeBoard, TicTacToeSymbol } from '../../types/tictactoe'
import { Cell } from './Cell'

interface BoardProps {
  board: TicTacToeBoard
  winningCells: number[]
  lastAiMoveIndex: number | null
  disabled: boolean
  onCellClick: (index: number) => void
}

export function Board({ board, winningCells, lastAiMoveIndex, disabled, onCellClick }: BoardProps) {
  return (
    <div className="grid grid-cols-3 gap-2 w-full max-w-xs mx-auto" role="grid" aria-label="Tic Tac Toe board">
      {board.map((value, index) => (
        <Cell
          key={index}
          index={index}
          value={value as TicTacToeSymbol | null}
          isWinning={winningCells.includes(index)}
          isLastAiMove={lastAiMoveIndex === index}
          disabled={disabled}
          onClick={onCellClick}
        />
      ))}
    </div>
  )
}
