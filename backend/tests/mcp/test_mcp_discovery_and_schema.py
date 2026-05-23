from __future__ import annotations

import pytest

from app.services.mcp.client import MCPClient
from app.services.mcp.errors import MCPExecutionError
from app.services.mcp.models import MCPToolDefinition


@pytest.mark.asyncio
async def test_discovery_returns_expected_research_tools() -> None:
    client = MCPClient()
    await client.discover_tools(refresh=True)

    tool_names = {tool.name for tool in client.registry.list()}
    assert "research.search_papers_iterative" in tool_names
    assert "research.score_papers" in tool_names
    assert "research.generate_refined_terms" in tool_names
    assert "research.generate_digest" in tool_names

    await client.close()


@pytest.mark.asyncio
async def test_schema_validation_blocks_invalid_arguments() -> None:
    client = MCPClient()
    await client.discover_tools(refresh=True)

    with pytest.raises(MCPExecutionError):
        await client.invoke_tool(
            "research.search_papers_iterative",
            {
                "query": "agentic ai",
                # max_results missing on purpose
                "depth": "quick",
            },
        )

    await client.close()


@pytest.mark.asyncio
async def test_dynamic_tool_discovery_without_agent_code_changes() -> None:
    class DynamicTransport:
        async def list_tools(self):
            return [
                MCPToolDefinition(
                    name="custom.dynamic_tool",
                    description="Dynamically discovered",
                    input_schema={"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]},
                    output_schema={"type": "object"},
                    supports_streaming=False,
                )
            ]

        async def invoke_tool(self, tool_name, arguments):
            assert tool_name == "custom.dynamic_tool"
            return {"ok": True, "data": {"y": arguments["x"] + 1}}

        async def invoke_tool_stream(self, tool_name, arguments):
            yield {"event": "result", "data": {"ok": True, "data": {"y": arguments["x"] + 1}}, "done": True}

        async def close(self):
            return None

    client = MCPClient(transport=DynamicTransport())
    await client.discover_tools(refresh=True)

    discovered = {tool.name for tool in client.registry.list()}
    assert "custom.dynamic_tool" in discovered

    result = await client.invoke_tool("custom.dynamic_tool", {"x": 41})
    assert result["y"] == 42

    await client.close()
