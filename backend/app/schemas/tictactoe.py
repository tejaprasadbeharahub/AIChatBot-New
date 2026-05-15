"""Schemas for Tic Tac Toe game."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Symbol(str, Enum):
    X = "X"
    O = "O"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    unbeatable = "unbeatable"


class GameStatus(str, Enum):
    ongoing = "ongoing"
    player_wins = "player_wins"
    ai_wins = "ai_wins"
    draw = "draw"


# Board is 9 cells, index 0-8 (row-major). None = empty.
Board = list[Optional[str]]


class CreateGameRequest(BaseModel):
    player_symbol: Symbol = Symbol.X
    difficulty: Difficulty = Difficulty.unbeatable


class CreateGameResponse(BaseModel):
    game_id: str
    board: Board
    player_symbol: str
    ai_symbol: str
    difficulty: str
    current_turn: str  # "player" or "ai"
    status: GameStatus
    winning_cells: list[int]


class MakeMoveRequest(BaseModel):
    cell_index: int = Field(..., ge=0, le=8)


class MakeMoveResponse(BaseModel):
    board: Board
    player_symbol: str
    ai_symbol: str
    current_turn: str
    status: GameStatus
    winning_cells: list[int]
    ai_move_index: Optional[int] = None


class GameStateResponse(BaseModel):
    game_id: str
    board: Board
    player_symbol: str
    ai_symbol: str
    difficulty: str
    current_turn: str
    status: GameStatus
    winning_cells: list[int]
