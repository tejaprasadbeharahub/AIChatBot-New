from __future__ import annotations

import pytest

from app.services.research_agent.agent import ResearchAgent, ResearchState


class DummyLLM:
    async def ainvoke(self, prompt: str):
        class Resp:
            content = "term1,term2"
        return Resp()


@pytest.mark.asyncio
async def test_search_node_gracefully_falls_back_when_mcp_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.research_agent.agent.get_chat_model", lambda temperature=0.0: DummyLLM())

    agent = ResearchAgent(db=None, user_id="u", chat_id="c")

    async def fail_invoke(tool_name: str, arguments: dict):
        raise RuntimeError("mcp down")

    monkeypatch.setattr(agent.mcp_client, "invoke_tool", fail_invoke)

    events = []

    async def on_event(event: dict):
        events.append(event)

    agent.event_callback = on_event

    state: ResearchState = {
        "query": "agentic ai",
        "papers": [],
        "max_papers": 5,
        "depth": "quick",
        "llm": DummyLLM(),
        "digest": None,
        "error": None,
        "should_continue": False,
        "search_attempts": 0,
        "refined_terms": [],
    }

    out = await agent._node_search_papers(state)

    assert out["papers"] == []
    assert any(e.get("event_type") == "warning" for e in events)


@pytest.mark.asyncio
async def test_generate_digest_returns_fallback_when_no_papers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.research_agent.agent.get_chat_model", lambda temperature=0.0: DummyLLM())

    agent = ResearchAgent(db=None, user_id="u", chat_id="c")

    state: ResearchState = {
        "query": "agentic ai",
        "papers": [],
        "max_papers": 5,
        "depth": "quick",
        "llm": DummyLLM(),
        "digest": None,
        "error": None,
        "should_continue": False,
        "search_attempts": 0,
        "refined_terms": [],
    }

    out = await agent._node_generate_digest(state)

    assert out["digest"] is not None
    assert out["digest"].total_papers_reviewed == 0
    assert "temporary" in out["digest"].summary.lower()
