"""In-memory game session management for Tic Tac Toe."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GameSession:
    game_id: str
    board: list[Optional[str]]
    player_symbol: str
    ai_symbol: str
    difficulty: str
    current_turn: str  # "player" or "ai"
    status: str  # "ongoing" | "player_wins" | "ai_wins" | "draw"
    winning_cells: list[int] = field(default_factory=list)


# Module-level in-memory store. Keyed by game_id.
_games: dict[str, GameSession] = {}


def create_game(player_symbol: str, difficulty: str) -> GameSession:
    ai_symbol = "O" if player_symbol == "X" else "X"
    # If AI is X, AI goes first
    first_turn = "ai" if ai_symbol == "X" else "player"
    session = GameSession(
        game_id=str(uuid.uuid4()),
        board=[None] * 9,
        player_symbol=player_symbol,
        ai_symbol=ai_symbol,
        difficulty=difficulty,
        current_turn=first_turn,
        status="ongoing",
    )
    _games[session.game_id] = session
    return session


def get_game(game_id: str) -> Optional[GameSession]:
    return _games.get(game_id)


def delete_game(game_id: str) -> None:
    _games.pop(game_id, None)
