from __future__ import annotations

from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_research_agent_uses_mcp_invoke_not_direct_arxiv_import() -> None:
    agent_file = Path(__file__).resolve().parents[2] / "app" / "services" / "research_agent" / "agent.py"
    source = _read(agent_file)

    assert "from app.services.mcp.client import MCPClient" in source
    assert "self.mcp_client.invoke_tool(" in source
    assert "from app.services.research_agent.arxiv_service import search_papers_iterative" not in source


def test_no_mcp_frontend_coupling() -> None:
    frontend_src = Path(__file__).resolve().parents[3] / "frontend" / "src"
    mentions = []
    for file in frontend_src.rglob("*.ts*"):
        txt = _read(file)
        if "mcp_" in txt.lower() or "model context protocol" in txt.lower():
            mentions.append(str(file))

    assert not mentions, f"Frontend should not be MCP-coupled; found references: {mentions}"


def test_research_api_contract_still_exists() -> None:
    api_file = Path(__file__).resolve().parents[2] / "app" / "api" / "research_agent.py"
    source = _read(api_file)

    assert "@router.post(\"/research-stream\")" in source
    assert "@router.post(\"/research\")" in source


def test_research_orchestration_flow_nodes_unchanged() -> None:
    agent_file = Path(__file__).resolve().parents[2] / "app" / "services" / "research_agent" / "agent.py"
    source = _read(agent_file)

    expected_nodes = [
        'workflow.add_node("search_papers", self._node_search_papers)',
        'workflow.add_node("analyze_papers", self._node_analyze_papers)',
        'workflow.add_node("decide_continue", self._node_decide_continue)',
        'workflow.add_node("refine_search", self._node_refine_search)',
        'workflow.add_node("generate_digest", self._node_generate_digest)',
    ]

    for node in expected_nodes:
        assert node in source


def test_prompts_are_not_mcp_coupled() -> None:
    prompts_dir = Path(__file__).resolve().parents[2] / "app" / "ai" / "prompts"
    if not prompts_dir.exists():
        return

    bad = []
    for file in prompts_dir.rglob("*"):
        if not file.is_file():
            continue
        txt = _read(file).lower()
        if "mcp" in txt or "model context protocol" in txt:
            bad.append(str(file))

    assert not bad, f"System prompts should remain unchanged and MCP-agnostic: {bad}"


def test_chat_and_thread_endpoints_still_present() -> None:
    main_file = Path(__file__).resolve().parents[2] / "app" / "main.py"
    source = _read(main_file)

    # Guardrail for chat/thread wiring continuity.
    assert "app.include_router(chat_router, prefix=\"/api\")" in source
    assert "app.include_router(chats_router, prefix=\"/api\")" in source
