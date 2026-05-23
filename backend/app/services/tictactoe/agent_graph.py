"""LangGraph-based AI orchestration for Tic Tac Toe gameplay and reasoning."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any, Optional

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from app.ai.llm import get_chat_model
from app.services.tictactoe.game_logic import get_empty_cells
from app.services.tictactoe.tools import (
    check_winner_tool,
    generate_ai_move_tool,
    update_board_tool,
    validate_move_tool,
)

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    board: list[Optional[str]]
    ai_symbol: str
    player_symbol: str
    difficulty: str
    llm_available: bool
    suggested_move: Optional[int]
    deterministic_move: Optional[int]
    selected_move: Optional[int]
    selected_strategy: str
    status_after_move: str
    winning_cells: list[int]
    reasoning_steps: list[dict[str, object]]
    error: Optional[str]


class TicTacToeGraphAgent:
    """Encapsulates LangGraph workflow for move reasoning + safe execution."""

    def __init__(self) -> None:
        self._llm = None
        self._llm_error: Optional[str] = None
        try:
            self._llm = get_chat_model(temperature=0.2)
        except Exception as exc:  # pragma: no cover - environment dependent
            self._llm_error = str(exc)
            logger.info("tictactoe_llm_unavailable", extra={"error": str(exc)})
        self._graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("analyze_board", self._node_analyze_board)
        workflow.add_node("llm_reason", self._node_llm_reason)
        workflow.add_node("deterministic", self._node_deterministic)
        workflow.add_node("select_move", self._node_select_move)
        workflow.add_node("validate_apply", self._node_validate_apply)

        workflow.set_entry_point("analyze_board")
        workflow.add_edge("analyze_board", "llm_reason")
        workflow.add_edge("llm_reason", "deterministic")
        workflow.add_edge("deterministic", "select_move")
        workflow.add_edge("select_move", "validate_apply")
        workflow.add_edge("validate_apply", END)
        return workflow.compile()

    def _append_reason(
        self,
        state: AgentState,
        step: str,
        detail: str,
        source: str,
        confidence: Optional[float] = None,
    ) -> None:
        state["reasoning_steps"].append(
            {
                "step": step,
                "detail": detail,
                "source": source,
                "confidence": confidence,
            }
        )

    async def _node_analyze_board(self, state: AgentState) -> AgentState:
        empty = get_empty_cells(state["board"])
        self._append_reason(
            state,
            "board_scan",
            f"Detected {len(empty)} legal move(s).",
            "heuristic",
        )
        if 4 in empty:
            self._append_reason(
                state,
                "positional_hint",
                "Center cell is still available and usually improves control.",
                "heuristic",
                0.6,
            )
        return state

    async def _node_llm_reason(self, state: AgentState) -> AgentState:
        if state["difficulty"] not in ("reasoning", "hybrid"):
            self._append_reason(
                state,
                "llm_skip",
                "Difficulty is deterministic-first; skipping LLM planner.",
                "system",
            )
            return state

        if self._llm is None:
            self._append_reason(
                state,
                "llm_unavailable",
                "LLM is unavailable. Falling back to deterministic strategy.",
                "system",
            )
            return state

        empty = get_empty_cells(state["board"])
        prompt = (
            "You are planning a Tic Tac Toe move.\n"
            f"Board (index 0-8): {state['board']}\n"
            f"AI symbol: {state['ai_symbol']}, Player symbol: {state['player_symbol']}\n"
            f"Legal moves: {empty}\n"
            "Respond as JSON: {\"move_index\": <int>, \"reason\": <string>, \"confidence\": <0-1 float>}"
        )

        try:
            if hasattr(self._llm, "ainvoke"):
                result = await self._llm.ainvoke(prompt)
            else:
                result = await asyncio.to_thread(self._llm.invoke, prompt)
            content = result.content if hasattr(result, "content") else str(result)
            data = json.loads(content)
            move_index = data.get("move_index")
            if isinstance(move_index, int):
                state["suggested_move"] = move_index
            self._append_reason(
                state,
                "llm_plan",
                str(data.get("reason") or "LLM generated a strategic move suggestion."),
                "llm",
                float(data.get("confidence")) if data.get("confidence") is not None else None,
            )
        except Exception as exc:  # pragma: no cover - network/provider dependent
            self._append_reason(
                state,
                "llm_parse_fallback",
                f"LLM planning failed ({exc}). Using deterministic fallback.",
                "system",
            )
        return state

    async def _node_deterministic(self, state: AgentState) -> AgentState:
        tool_out = generate_ai_move_tool(
            board=state["board"],
            ai_symbol=state["ai_symbol"],
            player_symbol=state["player_symbol"],
            difficulty=state["difficulty"],
        )
        move_index = tool_out.get("move_index")
        state["deterministic_move"] = move_index if isinstance(move_index, int) else None

        mapped_strategy = str(tool_out.get("strategy") or "unbeatable")
        self._append_reason(
            state,
            "deterministic_plan",
            f"Deterministic engine suggests index {state['deterministic_move']} using {mapped_strategy} strategy.",
            "minimax",
            0.95 if mapped_strategy == "unbeatable" else 0.75,
        )
        return state

    async def _node_select_move(self, state: AgentState) -> AgentState:
        suggested = state.get("suggested_move")
        deterministic = state.get("deterministic_move")

        if state["difficulty"] == "reasoning" and isinstance(suggested, int):
            state["selected_move"] = suggested
            state["selected_strategy"] = "llm"
        elif state["difficulty"] == "hybrid" and isinstance(suggested, int):
            validation = validate_move_tool(state["board"], suggested)
            if bool(validation["valid"]):
                state["selected_move"] = suggested
                state["selected_strategy"] = "hybrid_llm"
            else:
                state["selected_move"] = deterministic
                state["selected_strategy"] = "hybrid_fallback"
                self._append_reason(
                    state,
                    "hybrid_fallback",
                    "LLM suggestion was invalid for current board; switched to deterministic fallback.",
                    "validation",
                )
        else:
            state["selected_move"] = deterministic
            state["selected_strategy"] = "deterministic"

        self._append_reason(
            state,
            "selection",
            f"Selected move index {state['selected_move']} with strategy {state['selected_strategy']}.",
            "system",
        )
        return state

    async def _node_validate_apply(self, state: AgentState) -> AgentState:
        selected = state.get("selected_move")
        empty = get_empty_cells(state["board"])

        if selected is None or not bool(validate_move_tool(state["board"], selected)["valid"]):
            if not empty:
                state["error"] = "No legal AI moves available"
                state["status_after_move"] = "draw"
                return state
            selected = empty[0]
            state["selected_move"] = selected
            state["selected_strategy"] = "safety_fallback"
            self._append_reason(
                state,
                "safety_fallback",
                f"Selected move was invalid; forced legal move index {selected}.",
                "validation",
            )

        apply_out = update_board_tool(state["board"], selected, state["ai_symbol"])
        state["board"] = apply_out["board"]
        status_out = check_winner_tool(state["board"], state["player_symbol"], state["ai_symbol"])
        state["status_after_move"] = str(status_out["status"])
        state["winning_cells"] = list(status_out["winning_cells"])
        return state

    async def choose_move(
        self,
        board: list[Optional[str]],
        ai_symbol: str,
        player_symbol: str,
        difficulty: str,
    ) -> dict[str, object]:
        state: AgentState = {
            "board": list(board),
            "ai_symbol": ai_symbol,
            "player_symbol": player_symbol,
            "difficulty": difficulty,
            "llm_available": self._llm is not None,
            "suggested_move": None,
            "deterministic_move": None,
            "selected_move": None,
            "selected_strategy": "deterministic",
            "status_after_move": "ongoing",
            "winning_cells": [],
            "reasoning_steps": [],
            "error": None,
        }

        final_state = await self._graph.ainvoke(state)
        return {
            "move_index": final_state.get("selected_move"),
            "strategy": final_state.get("selected_strategy", "deterministic"),
            "board": final_state["board"],
            "status": final_state.get("status_after_move", "ongoing"),
            "winning_cells": final_state.get("winning_cells", []),
            "reasoning_steps": final_state.get("reasoning_steps", []),
            "error": final_state.get("error"),
        }

    async def stream_choose_move(
        self,
        board: list[Optional[str]],
        ai_symbol: str,
        player_symbol: str,
        difficulty: str,
    ) -> AsyncIterator[dict[str, object]]:
        state: AgentState = {
            "board": list(board),
            "ai_symbol": ai_symbol,
            "player_symbol": player_symbol,
            "difficulty": difficulty,
            "llm_available": self._llm is not None,
            "suggested_move": None,
            "deterministic_move": None,
            "selected_move": None,
            "selected_strategy": "deterministic",
            "status_after_move": "ongoing",
            "winning_cells": [],
            "reasoning_steps": [],
            "error": None,
        }

        emitted = 0
        final_state: Optional[AgentState] = None
        async for current in self._graph.astream(state, stream_mode="values"):
            final_state = current
            steps = current.get("reasoning_steps", [])
            while emitted < len(steps):
                yield {
                    "event": "reasoning",
                    "data": steps[emitted],
                }
                emitted += 1

        if final_state is None:
            final_state = await self._graph.ainvoke(state)

        yield {
            "event": "move",
            "data": {
                "move_index": final_state.get("selected_move"),
                "strategy": final_state.get("selected_strategy", "deterministic"),
                "board": final_state["board"],
                "status": final_state.get("status_after_move", "ongoing"),
                "winning_cells": final_state.get("winning_cells", []),
                "error": final_state.get("error"),
            },
        }

    async def answer_question(
        self,
        board: list[Optional[str]],
        ai_symbol: str,
        player_symbol: str,
        message: str,
    ) -> dict[str, object]:
        hints = []
        empty = get_empty_cells(board)
        if 4 in empty:
            hints.append("Control the center when possible.")
        if len(empty) >= 6:
            hints.append("Prioritize corners early to create forks.")
        if not hints:
            hints.append("Avoid giving opponent two-way winning threats.")

        if self._llm is None:
            return {
                "answer": (
                    "I am currently running in deterministic mode. "
                    "I validate all moves and prioritize winning or blocking lines."
                ),
                "strategy_hints": hints,
            }

        prompt = (
            "You are a Tic Tac Toe coach AI.\n"
            f"Board: {board}\n"
            f"AI symbol: {ai_symbol}, Player symbol: {player_symbol}\n"
            f"User question: {message}\n"
            "Answer concisely in 2-4 sentences and include practical advice."
        )

        try:
            if hasattr(self._llm, "ainvoke"):
                result = await self._llm.ainvoke(prompt)
            else:
                result = await asyncio.to_thread(self._llm.invoke, prompt)
            content = result.content if hasattr(result, "content") else str(result)
            return {
                "answer": content,
                "strategy_hints": hints,
            }
        except Exception as exc:  # pragma: no cover
            logger.warning("tictactoe_ai_chat_fallback", extra={"error": str(exc)})
            return {
                "answer": "I could not generate a detailed explanation right now. Keep blocking immediate threats first.",
                "strategy_hints": hints,
            }
