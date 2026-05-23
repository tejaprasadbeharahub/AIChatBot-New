"""FastAPI routes for Tic Tac Toe."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.tictactoe import (
    AskAgentRequest,
    AskAgentResponse,
    ChatHistoryItem,
    CreateGameRequest,
    CreateGameResponse,
    GameStateResponse,
    GameStatus,
    MakeMoveRequest,
    MakeMoveResponse,
    MoveHistoryItem,
    ReasoningStep,
)
from app.services.tictactoe.game_logic import (
    check_winner,
    is_draw,
    is_valid_move,
)
from app.services.tictactoe.session import create_game, get_game
from app.services.tictactoe.agent_graph import TicTacToeGraphAgent

router = APIRouter(prefix="/tictactoe", tags=["tictactoe"])
agent = TicTacToeGraphAgent()


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
async def create_new_game(body: CreateGameRequest) -> CreateGameResponse:
    session = create_game(body.player_symbol.value, body.difficulty.value)

    # If AI goes first, make its opening move immediately
    if session.current_turn == "ai" and session.status == "ongoing":
        decision = await agent.choose_move(
            board=session.board,
            ai_symbol=session.ai_symbol,
            player_symbol=session.player_symbol,
            difficulty=session.difficulty,
        )
        ai_idx = decision["move_index"]
        if not isinstance(ai_idx, int):
            raise HTTPException(status_code=500, detail="AI failed to produce a legal opening move.")
        session.board = decision["board"]
        status, cells = _resolve_status(session.board, session.player_symbol, session.ai_symbol)
        session.status = status.value
        session.winning_cells = cells
        session.current_turn = "player" if status == GameStatus.ongoing else "ai"
        session.ai_reasoning = list(decision.get("reasoning_steps", []))
        session.last_ai_strategy = str(decision.get("strategy") or "deterministic")
        session.move_history.append(
            {
                "move_number": len(session.move_history) + 1,
                "symbol": session.ai_symbol,
                "cell_index": ai_idx,
                "board_snapshot": list(session.board),
                "reason": "Opening move",
            }
        )

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
        ai_reasoning=[ReasoningStep.model_validate(step) for step in session.ai_reasoning],
        move_history=[MoveHistoryItem.model_validate(item) for item in session.move_history],
        conversation_history=[
            ChatHistoryItem.model_validate(item) for item in session.conversation_history
        ],
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
        ai_reasoning=[ReasoningStep.model_validate(step) for step in session.ai_reasoning],
        move_history=[MoveHistoryItem.model_validate(item) for item in session.move_history],
        conversation_history=[
            ChatHistoryItem.model_validate(item) for item in session.conversation_history
        ],
    )


@router.post("/games/{game_id}/move", response_model=MakeMoveResponse)
async def make_move(game_id: str, body: MakeMoveRequest) -> MakeMoveResponse:
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
    session.move_history.append(
        {
            "move_number": len(session.move_history) + 1,
            "symbol": session.player_symbol,
            "cell_index": body.cell_index,
            "board_snapshot": list(session.board),
            "reason": "Player move",
        }
    )
    status, cells = _resolve_status(session.board, session.player_symbol, session.ai_symbol)
    session.status = status.value
    session.winning_cells = cells

    ai_move_index: int | None = None
    ai_reasoning: list[dict[str, object]] = []
    ai_strategy = "deterministic"

    if status == GameStatus.ongoing:
        decision = await agent.choose_move(
            board=session.board,
            ai_symbol=session.ai_symbol,
            player_symbol=session.player_symbol,
            difficulty=session.difficulty,
        )
        ai_idx = decision["move_index"]
        if not isinstance(ai_idx, int):
            raise HTTPException(status_code=500, detail="AI failed to produce a legal move.")

        session.board = decision["board"]
        ai_move_index = ai_idx
        ai_reasoning = list(decision.get("reasoning_steps", []))
        ai_strategy = str(decision.get("strategy") or "deterministic")
        session.ai_reasoning = ai_reasoning
        session.last_ai_strategy = ai_strategy
        session.move_history.append(
            {
                "move_number": len(session.move_history) + 1,
                "symbol": session.ai_symbol,
                "cell_index": ai_idx,
                "board_snapshot": list(session.board),
                "reason": f"AI move via {ai_strategy}",
            }
        )
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
        ai_strategy=ai_strategy,
        ai_reasoning=[ReasoningStep.model_validate(step) for step in ai_reasoning],
        move_history=[MoveHistoryItem.model_validate(item) for item in session.move_history],
    )


@router.post("/games/{game_id}/move-stream")
async def make_move_stream(game_id: str, body: MakeMoveRequest) -> StreamingResponse:
    session = get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found.")
    if session.status != "ongoing":
        raise HTTPException(status_code=400, detail="Game is already over.")
    if session.current_turn != "player":
        raise HTTPException(status_code=400, detail="It is not the player's turn.")
    if not is_valid_move(session.board, body.cell_index):
        raise HTTPException(status_code=400, detail="Invalid move: cell is occupied or out of range.")

    session.board[body.cell_index] = session.player_symbol
    session.move_history.append(
        {
            "move_number": len(session.move_history) + 1,
            "symbol": session.player_symbol,
            "cell_index": body.cell_index,
            "board_snapshot": list(session.board),
            "reason": "Player move",
        }
    )
    status, cells = _resolve_status(session.board, session.player_symbol, session.ai_symbol)
    session.status = status.value
    session.winning_cells = cells

    async def _event_stream():
        if status != GameStatus.ongoing:
            payload = {
                "event": "move_result",
                "data": MakeMoveResponse(
                    board=session.board,
                    player_symbol=session.player_symbol,
                    ai_symbol=session.ai_symbol,
                    current_turn="done",
                    status=GameStatus(session.status),
                    winning_cells=session.winning_cells,
                    ai_move_index=None,
                    ai_strategy=session.last_ai_strategy,
                    ai_reasoning=[ReasoningStep.model_validate(step) for step in session.ai_reasoning],
                    move_history=[MoveHistoryItem.model_validate(item) for item in session.move_history],
                ).model_dump(),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            return

        ai_reasoning: list[dict[str, object]] = []
        ai_strategy = "deterministic"
        ai_move_idx: int | None = None
        async for event in agent.stream_choose_move(
            board=session.board,
            ai_symbol=session.ai_symbol,
            player_symbol=session.player_symbol,
            difficulty=session.difficulty,
        ):
            if event.get("event") == "reasoning":
                step = dict(event["data"])
                ai_reasoning.append(step)
                yield f"data: {json.dumps({'event': 'reasoning', 'data': step})}\n\n"
                continue

            move_payload = dict(event["data"])
            ai_strategy = str(move_payload.get("strategy") or "deterministic")
            maybe_idx = move_payload.get("move_index")
            if isinstance(maybe_idx, int):
                ai_move_idx = maybe_idx
            session.board = list(move_payload.get("board") or session.board)
            session.ai_reasoning = ai_reasoning
            session.last_ai_strategy = ai_strategy
            if ai_move_idx is not None:
                session.move_history.append(
                    {
                        "move_number": len(session.move_history) + 1,
                        "symbol": session.ai_symbol,
                        "cell_index": ai_move_idx,
                        "board_snapshot": list(session.board),
                        "reason": f"AI move via {ai_strategy}",
                    }
                )

            final_status, final_cells = _resolve_status(
                session.board,
                session.player_symbol,
                session.ai_symbol,
            )
            session.status = final_status.value
            session.winning_cells = final_cells
            session.current_turn = "player" if final_status == GameStatus.ongoing else "done"

            payload = {
                "event": "move_result",
                "data": MakeMoveResponse(
                    board=session.board,
                    player_symbol=session.player_symbol,
                    ai_symbol=session.ai_symbol,
                    current_turn=session.current_turn,
                    status=GameStatus(session.status),
                    winning_cells=session.winning_cells,
                    ai_move_index=ai_move_idx,
                    ai_strategy=ai_strategy,
                    ai_reasoning=[ReasoningStep.model_validate(step) for step in ai_reasoning],
                    move_history=[MoveHistoryItem.model_validate(item) for item in session.move_history],
                ).model_dump(),
            }
            yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/games/{game_id}/ask", response_model=AskAgentResponse)
async def ask_agent(game_id: str, body: AskAgentRequest) -> AskAgentResponse:
    session = get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found.")

    session.conversation_history.append({"role": "user", "message": body.message})
    answer = await agent.answer_question(
        board=session.board,
        ai_symbol=session.ai_symbol,
        player_symbol=session.player_symbol,
        message=body.message,
    )
    ai_text = str(answer.get("answer") or "")
    session.conversation_history.append({"role": "assistant", "message": ai_text})

    return AskAgentResponse(
        answer=ai_text,
        strategy_hints=[str(x) for x in answer.get("strategy_hints") or []],
        conversation_history=[
            ChatHistoryItem.model_validate(item) for item in session.conversation_history
        ],
    )


@router.post("/games/{game_id}/reset", response_model=CreateGameResponse, status_code=200)
async def reset_game(game_id: str) -> CreateGameResponse:
    session = get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found.")

    # Keep same settings, reset board
    session.board = [None] * 9
    first_turn = "ai" if session.ai_symbol == "X" else "player"
    session.current_turn = first_turn
    session.status = "ongoing"
    session.winning_cells = []
    session.ai_reasoning = []
    session.move_history = []
    session.conversation_history = []
    session.last_ai_strategy = "deterministic"

    # If AI goes first, make opening move
    if session.current_turn == "ai":
        decision = await agent.choose_move(
            board=session.board,
            ai_symbol=session.ai_symbol,
            player_symbol=session.player_symbol,
            difficulty=session.difficulty,
        )
        ai_idx = decision["move_index"]
        if not isinstance(ai_idx, int):
            raise HTTPException(status_code=500, detail="AI failed to produce a legal opening move.")
        session.board = decision["board"]
        session.ai_reasoning = list(decision.get("reasoning_steps", []))
        session.last_ai_strategy = str(decision.get("strategy") or "deterministic")
        session.move_history.append(
            {
                "move_number": len(session.move_history) + 1,
                "symbol": session.ai_symbol,
                "cell_index": ai_idx,
                "board_snapshot": list(session.board),
                "reason": "Opening move",
            }
        )
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
        ai_reasoning=[ReasoningStep.model_validate(step) for step in session.ai_reasoning],
        move_history=[MoveHistoryItem.model_validate(item) for item in session.move_history],
        conversation_history=[
            ChatHistoryItem.model_validate(item) for item in session.conversation_history
        ],
    )
