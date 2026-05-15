"""AI agent for Tic Tac Toe with Easy, Medium, and Unbeatable (Minimax + Alpha-Beta Pruning) modes."""

from __future__ import annotations

import random
from typing import Optional

from app.services.tictactoe.game_logic import (
    check_winner,
    get_empty_cells,
    is_draw,
)


def _minimax(
    board: list[Optional[str]],
    ai_symbol: str,
    player_symbol: str,
    is_maximizing: bool,
    alpha: float,
    beta: float,
    depth: int,
) -> float:
    """Minimax with Alpha-Beta Pruning. Returns score from AI perspective."""
    winner, _ = check_winner(board)
    if winner == ai_symbol:
        return 10 - depth
    if winner == player_symbol:
        return depth - 10
    if is_draw(board):
        return 0

    empty = get_empty_cells(board)

    if is_maximizing:
        best = float("-inf")
        for idx in empty:
            board[idx] = ai_symbol
            score = _minimax(board, ai_symbol, player_symbol, False, alpha, beta, depth + 1)
            board[idx] = None
            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = float("inf")
        for idx in empty:
            board[idx] = player_symbol
            score = _minimax(board, ai_symbol, player_symbol, True, alpha, beta, depth + 1)
            board[idx] = None
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def _best_minimax_move(
    board: list[Optional[str]], ai_symbol: str, player_symbol: str
) -> int:
    """Return the best move index for the AI using Minimax + Alpha-Beta."""
    empty = get_empty_cells(board)
    best_score = float("-inf")
    best_idx = empty[0]
    for idx in empty:
        board[idx] = ai_symbol
        score = _minimax(board, ai_symbol, player_symbol, False, float("-inf"), float("inf"), 0)
        board[idx] = None
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx


def _find_winning_or_blocking_move(
    board: list[Optional[str]], symbol: str
) -> Optional[int]:
    """Return a move index that wins (or blocks) for the given symbol, or None."""
    empty = get_empty_cells(board)
    for idx in empty:
        board[idx] = symbol
        winner, _ = check_winner(board)
        board[idx] = None
        if winner == symbol:
            return idx
    return None


def get_ai_move(
    board: list[Optional[str]],
    ai_symbol: str,
    player_symbol: str,
    difficulty: str,
) -> int:
    """Return AI's chosen cell index for the given difficulty."""
    empty = get_empty_cells(board)
    if not empty:
        raise ValueError("No empty cells available.")

    if difficulty == "easy":
        # Fully random
        return random.choice(empty)

    if difficulty == "medium":
        # Win if possible
        move = _find_winning_or_blocking_move(board, ai_symbol)
        if move is not None:
            return move
        # Block player win
        move = _find_winning_or_blocking_move(board, player_symbol)
        if move is not None:
            return move
        # Take center if free
        if board[4] is None:
            return 4
        # Pick a random corner
        corners = [i for i in [0, 2, 6, 8] if board[i] is None]
        if corners:
            return random.choice(corners)
        return random.choice(empty)

    # unbeatable — Minimax + Alpha-Beta
    return _best_minimax_move(board, ai_symbol, player_symbol)
