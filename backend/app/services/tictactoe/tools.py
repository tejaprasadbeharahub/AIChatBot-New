"""Tool functions used by Tic Tac Toe LangGraph orchestration."""

from __future__ import annotations

from typing import Optional

from app.services.tictactoe.ai_agent import get_ai_move
from app.services.tictactoe.game_logic import check_winner, get_empty_cells, is_draw, is_valid_move


def validate_move_tool(board: list[Optional[str]], index: int) -> dict[str, object]:
    """Validate whether a move is legal for the current board."""
    return {
        "valid": is_valid_move(board, index),
        "index": index,
    }


def update_board_tool(board: list[Optional[str]], index: int, symbol: str) -> dict[str, object]:
    """Apply a move to a copied board and return the resulting board."""
    new_board = list(board)
    new_board[index] = symbol
    return {
        "board": new_board,
        "index": index,
        "symbol": symbol,
    }


def check_winner_tool(board: list[Optional[str]], player_symbol: str, ai_symbol: str) -> dict[str, object]:
    """Check status after a move."""
    winner, cells = check_winner(board)
    if winner == player_symbol:
        status = "player_wins"
    elif winner == ai_symbol:
        status = "ai_wins"
    elif is_draw(board):
        status = "draw"
    else:
        status = "ongoing"

    return {
        "status": status,
        "winner": winner,
        "winning_cells": cells,
    }


def generate_ai_move_tool(
    board: list[Optional[str]],
    ai_symbol: str,
    player_symbol: str,
    difficulty: str,
) -> dict[str, object]:
    """Generate a deterministic move according to selected strategy."""
    mapped_difficulty = difficulty
    if mapped_difficulty in ("reasoning", "hybrid"):
        mapped_difficulty = "unbeatable"

    if not get_empty_cells(board):
        return {"move_index": None}

    move_index = get_ai_move(board, ai_symbol, player_symbol, mapped_difficulty)
    return {
        "move_index": move_index,
        "strategy": mapped_difficulty,
    }


def reset_game_tool() -> dict[str, object]:
    """Return a clean board."""
    return {"board": [None] * 9}
