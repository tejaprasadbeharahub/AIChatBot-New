"""FastAPI routes for Tic Tac Toe."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.tictactoe import (
    CreateGameRequest,
    CreateGameResponse,
    GameStateResponse,
    GameStatus,
    MakeMoveRequest,
    MakeMoveResponse,
)
from app.services.tictactoe.ai_agent import get_ai_move
from app.services.tictactoe.game_logic import (
    check_winner,
    is_draw,
    is_valid_move,
)
from app.services.tictactoe.session import create_game, get_game

router = APIRouter(prefix="/tictactoe", tags=["tictactoe"])


def _resolve_status(board, player_symbol: str, ai_symbol: str) -> tuple[GameStatus, list[int]]:
    winner, cells = check_winner(board)
    if winner == player_symbol:
        return GameStatus.player_wins, cells
    if winner == ai_symbol:
        return GameStatus.ai_wins, cells
    if is_draw(board):
        return GameStatus.draw, []
    return GameStatus.ongoing, []


@router.post("/games", response_model=CreateGameResponse, status_code=201)
def create_new_game(body: CreateGameRequest) -> CreateGameResponse:
    session = create_game(body.player_symbol.value, body.difficulty.value)

    # If AI goes first, make its opening move immediately
    ai_move_made = False
    if session.current_turn == "ai" and session.status == "ongoing":
        ai_idx = get_ai_move(
            session.board, session.ai_symbol, session.player_symbol, session.difficulty
        )
        session.board[ai_idx] = session.ai_symbol
        status, cells = _resolve_status(session.board, session.player_symbol, session.ai_symbol)
        session.status = status.value
        session.winning_cells = cells
        session.current_turn = "player" if status == GameStatus.ongoing else "ai"
        ai_move_made = True

    status_enum = GameStatus(session.status)
    return CreateGameResponse(
        game_id=session.game_id,
        board=session.board,
        player_symbol=session.player_symbol,
        ai_symbol=session.ai_symbol,
        difficulty=session.difficulty,
        current_turn=session.current_turn,
        status=status_enum,
        winning_cells=session.winning_cells,
    )


@router.get("/games/{game_id}", response_model=GameStateResponse)
def get_game_state(game_id: str) -> GameStateResponse:
    session = get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found.")
    return GameStateResponse(
        game_id=session.game_id,
        board=session.board,
        player_symbol=session.player_symbol,
        ai_symbol=session.ai_symbol,
        difficulty=session.difficulty,
        current_turn=session.current_turn,
        status=GameStatus(session.status),
        winning_cells=session.winning_cells,
    )


@router.post("/games/{game_id}/move", response_model=MakeMoveResponse)
def make_move(game_id: str, body: MakeMoveRequest) -> MakeMoveResponse:
    session = get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found.")
    if session.status != "ongoing":
        raise HTTPException(status_code=400, detail="Game is already over.")
    if session.current_turn != "player":
        raise HTTPException(status_code=400, detail="It is not the player's turn.")
    if not is_valid_move(session.board, body.cell_index):
        raise HTTPException(status_code=400, detail="Invalid move: cell is occupied or out of range.")

    # Apply player move
    session.board[body.cell_index] = session.player_symbol
    status, cells = _resolve_status(session.board, session.player_symbol, session.ai_symbol)
    session.status = status.value
    session.winning_cells = cells

    ai_move_index: int | None = None

    if status == GameStatus.ongoing:
        # AI move
        ai_idx = get_ai_move(
            session.board, session.ai_symbol, session.player_symbol, session.difficulty
        )
        session.board[ai_idx] = session.ai_symbol
        ai_move_index = ai_idx
        status, cells = _resolve_status(session.board, session.player_symbol, session.ai_symbol)
        session.status = status.value
        session.winning_cells = cells
        session.current_turn = "player" if status == GameStatus.ongoing else "done"
    else:
        session.current_turn = "done"

    return MakeMoveResponse(
        board=session.board,
        player_symbol=session.player_symbol,
        ai_symbol=session.ai_symbol,
        current_turn=session.current_turn,
        status=GameStatus(session.status),
        winning_cells=session.winning_cells,
        ai_move_index=ai_move_index,
    )


@router.post("/games/{game_id}/reset", response_model=CreateGameResponse, status_code=200)
def reset_game(game_id: str) -> CreateGameResponse:
    session = get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found.")

    # Keep same settings, reset board
    session.board = [None] * 9
    first_turn = "ai" if session.ai_symbol == "X" else "player"
    session.current_turn = first_turn
    session.status = "ongoing"
    session.winning_cells = []

    # If AI goes first, make opening move
    if session.current_turn == "ai":
        ai_idx = get_ai_move(
            session.board, session.ai_symbol, session.player_symbol, session.difficulty
        )
        session.board[ai_idx] = session.ai_symbol
        status, cells = _resolve_status(session.board, session.player_symbol, session.ai_symbol)
        session.status = status.value
        session.winning_cells = cells
        session.current_turn = "player"

    return CreateGameResponse(
        game_id=session.game_id,
        board=session.board,
        player_symbol=session.player_symbol,
        ai_symbol=session.ai_symbol,
        difficulty=session.difficulty,
        current_turn=session.current_turn,
        status=GameStatus(session.status),
        winning_cells=session.winning_cells,
    )
