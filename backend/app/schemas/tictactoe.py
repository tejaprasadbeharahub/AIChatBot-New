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
    reasoning = "reasoning"
    hybrid = "hybrid"


class GameStatus(str, Enum):
    ongoing = "ongoing"
    player_wins = "player_wins"
    ai_wins = "ai_wins"
    draw = "draw"


# Board is 9 cells, index 0-8 (row-major). None = empty.
Board = list[Optional[str]]


class ReasoningSource(str, Enum):
    heuristic = "heuristic"
    llm = "llm"
    minimax = "minimax"
    validation = "validation"
    system = "system"


class ReasoningStep(BaseModel):
    step: str
    detail: str
    source: ReasoningSource
    confidence: Optional[float] = None


class MoveHistoryItem(BaseModel):
    move_number: int
    symbol: str
    cell_index: int
    board_snapshot: Board
    reason: Optional[str] = None


class ChatHistoryItem(BaseModel):
    role: str
    message: str


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
    ai_reasoning: list[ReasoningStep] = Field(default_factory=list)
    move_history: list[MoveHistoryItem] = Field(default_factory=list)
    conversation_history: list[ChatHistoryItem] = Field(default_factory=list)


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
    ai_strategy: str = "deterministic"
    ai_reasoning: list[ReasoningStep] = Field(default_factory=list)
    move_history: list[MoveHistoryItem] = Field(default_factory=list)


class GameStateResponse(BaseModel):
    game_id: str
    board: Board
    player_symbol: str
    ai_symbol: str
    difficulty: str
    current_turn: str
    status: GameStatus
    winning_cells: list[int]
    ai_reasoning: list[ReasoningStep] = Field(default_factory=list)
    move_history: list[MoveHistoryItem] = Field(default_factory=list)
    conversation_history: list[ChatHistoryItem] = Field(default_factory=list)


class AskAgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class AskAgentResponse(BaseModel):
    answer: str
    strategy_hints: list[str] = Field(default_factory=list)
    conversation_history: list[ChatHistoryItem] = Field(default_factory=list)
