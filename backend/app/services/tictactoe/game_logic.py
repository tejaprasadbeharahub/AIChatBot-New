"""Tic Tac Toe game logic."""

from __future__ import annotations

from typing import Optional

# Winning line combinations (cell indices)
WINNING_LINES: list[tuple[int, int, int]] = [
    (0, 1, 2),  # top row
    (3, 4, 5),  # middle row
    (6, 7, 8),  # bottom row
    (0, 3, 6),  # left col
    (1, 4, 7),  # middle col
    (2, 5, 8),  # right col
    (0, 4, 8),  # diagonal
    (2, 4, 6),  # anti-diagonal
]


def check_winner(board: list[Optional[str]]) -> tuple[Optional[str], list[int]]:
    """Return (winner_symbol, winning_cells) or (None, []) if no winner yet."""
    for a, b, c in WINNING_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], [a, b, c]
    return None, []


def is_draw(board: list[Optional[str]]) -> bool:
    """Return True if the board is full with no winner."""
    return all(cell is not None for cell in board)


def get_empty_cells(board: list[Optional[str]]) -> list[int]:
    return [i for i, cell in enumerate(board) if cell is None]


def is_valid_move(board: list[Optional[str]], index: int) -> bool:
    return 0 <= index <= 8 and board[index] is None
