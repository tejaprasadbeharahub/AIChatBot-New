"""LangGraph-based AI orchestration for Tic Tac Toe gameplay and reasoning."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any, Optional

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from app.ai.llm import get_chat_model
from app.services.tictactoe.game_logic import get_empty_cells
from app.services.tictactoe.tools import (
    check_winner_tool,
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
        workflow.add_node("select_move", self._node_select_move)
        workflow.add_node("validate_apply", self._node_validate_apply)

        workflow.set_entry_point("analyze_board")
        workflow.add_edge("analyze_board", "llm_reason")
        workflow.add_edge("llm_reason", "select_move")
        workflow.add_edge("select_move", "validate_apply")
        workflow.add_edge("validate_apply", END)
        return workflow.compile()

    def _extract_llm_json(self, content: str) -> dict[str, Any]:
        """Parse JSON response from model, allowing markdown wrappers and loose formatting."""
        text = content.strip()
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced_match:
            text = fenced_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            brace_match = re.search(r"\{.*\}", text, re.DOTALL)
            if brace_match:
                return json.loads(brace_match.group(0))
            raise

    def _difficulty_style(self, difficulty: str) -> str:
        if difficulty == "easy":
            return "Play casually. Prefer simple and human-like moves over optimal play."
        if difficulty == "medium":
            return "Play strategically but not perfectly."
        if difficulty == "unbeatable":
            return "Play perfectly to maximize win/draw outcomes."
        if difficulty == "hybrid":
            return "Play strongly with practical tactical focus."
        return "Play strategically and provide concise rationale."

    async def _request_llm_move(
        self,
        state: AgentState,
        legal_moves: list[int],
        retry_hint: Optional[str] = None,
    ) -> tuple[Optional[int], str, Optional[float]]:
        if self._llm is None:
            return None, "LLM is unavailable for move planning.", None

        retry_line = f"\nRetry note: {retry_hint}" if retry_hint else ""
        prompt = (
            "You are a Tic Tac Toe move planner.\n"
            f"Board (index 0-8): {state['board']}\n"
            f"AI symbol: {state['ai_symbol']}, Player symbol: {state['player_symbol']}\n"
            f"Legal moves: {legal_moves}\n"
            f"Style: {self._difficulty_style(state['difficulty'])}{retry_line}\n"
            "Return only JSON with keys: move_index (int), reason (string), confidence (0..1)."
        )

        if hasattr(self._llm, "ainvoke"):
            result = await self._llm.ainvoke(prompt)
        else:
            result = await asyncio.to_thread(self._llm.invoke, prompt)

        content = result.content if hasattr(result, "content") else str(result)
        data = self._extract_llm_json(content)
        move_index = data.get("move_index")
        reason = str(data.get("reason") or "LLM selected a move.")
        confidence_raw = data.get("confidence")
        confidence = float(confidence_raw) if confidence_raw is not None else None
        return (move_index if isinstance(move_index, int) else None), reason, confidence

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
        if self._llm is None:
            state["error"] = "LLM is unavailable. LLM-only mode cannot choose a move."
            self._append_reason(
                state,
                "llm_unavailable",
                "LLM is unavailable. No deterministic fallback is used in LLM-only mode.",
                "system",
            )
            return state

        legal_moves = get_empty_cells(state["board"])
        if not legal_moves:
            state["status_after_move"] = "draw"
            state["error"] = "No legal AI moves available"
            return state

        try:
            move_index, reason, confidence = await self._request_llm_move(state, legal_moves)
            state["suggested_move"] = move_index
            self._append_reason(
                state,
                "llm_plan",
                reason,
                "llm",
                confidence,
            )
        except Exception as exc:  # pragma: no cover - network/provider dependent
            state["error"] = f"LLM planning failed: {exc}"
            self._append_reason(
                state,
                "llm_failure",
                f"LLM planning failed ({exc}).",
                "system",
            )
        return state

    async def _node_select_move(self, state: AgentState) -> AgentState:
        suggested = state.get("suggested_move")
        state["selected_move"] = suggested if isinstance(suggested, int) else None
        state["selected_strategy"] = "llm_only"

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
            retry_hint = (
                f"Previous move suggestion {selected} was invalid. "
                f"You must choose only from legal moves: {empty}."
            )
            try:
                retry_move, retry_reason, retry_confidence = await self._request_llm_move(
                    state,
                    empty,
                    retry_hint=retry_hint,
                )
            except Exception as exc:  # pragma: no cover - provider dependent
                state["error"] = f"LLM retry failed: {exc}"
                self._append_reason(
                    state,
                    "llm_retry_failure",
                    f"LLM retry for valid move failed ({exc}).",
                    "system",
                )
                return state

            if retry_move is None or not bool(validate_move_tool(state["board"], retry_move)["valid"]):
                state["error"] = "LLM returned invalid move after retry"
                self._append_reason(
                    state,
                    "llm_retry_invalid",
                    "LLM retry still produced an invalid move; move application stopped.",
                    "validation",
                )
                return state

            selected = retry_move
            state["selected_move"] = selected
            state["selected_strategy"] = "llm_retry"
            self._append_reason(
                state,
                "llm_retry_success",
                retry_reason,
                "llm",
                retry_confidence,
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
            "selected_move": None,
            "selected_strategy": "llm_only",
            "status_after_move": "ongoing",
            "winning_cells": [],
            "reasoning_steps": [],
            "error": None,
        }

        final_state = await self._graph.ainvoke(state)
        return {
            "move_index": final_state.get("selected_move"),
            "strategy": final_state.get("selected_strategy", "llm_only"),
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
            "selected_move": None,
            "selected_strategy": "llm_only",
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
                "strategy": final_state.get("selected_strategy", "llm_only"),
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
                    "I cannot answer right now because the LLM backend is unavailable. "
                    "Please retry once the LLM service is reachable."
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
