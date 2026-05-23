from __future__ import annotations

import pytest

from app.services.mcp.client import MCPClient
from app.services.mcp.errors import MCPExecutionError
from app.services.mcp.models import MCPToolDefinition


@pytest.mark.asyncio
async def test_retry_succeeds_after_temporary_transport_failure() -> None:
    class FlakyTransport:
        def __init__(self):
            self.calls = 0

        async def list_tools(self):
            return [
                MCPToolDefinition(
                    name="research.search_papers_iterative",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer"},
                            "depth": {"type": "string"},
                        },
                        "required": ["query", "max_results", "depth"],
                    },
                    output_schema={"type": "array", "items": {"type": "object"}},
                )
            ]

        async def invoke_tool(self, tool_name, arguments):
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("temporary disconnect")
            return {"ok": True, "data": [{"arxiv_id": "x", "title": "ok"}]}

        async def invoke_tool_stream(self, tool_name, arguments):
            yield {"event": "result", "data": {"ok": True, "data": [{"arxiv_id": "x"}]}, "done": True}

        async def close(self):
            return None

    transport = FlakyTransport()
    client = MCPClient(transport=transport)

    result = await client.invoke_tool(
        "research.search_papers_iterative",
        {"query": "agentic ai", "max_results": 2, "depth": "quick"},
    )

    assert len(result) == 1
    assert transport.calls >= 2

    await client.close()


@pytest.mark.asyncio
async def test_graceful_error_when_tool_is_missing() -> None:
    class MissingToolTransport:
        async def list_tools(self):
            return []

        async def invoke_tool(self, tool_name, arguments):
            return {"ok": True, "data": None}

        async def invoke_tool_stream(self, tool_name, arguments):
            yield {"event": "result", "data": None, "done": True}

        async def close(self):
            return None

    client = MCPClient(transport=MissingToolTransport())

    with pytest.raises(MCPExecutionError):
        await client.invoke_tool(
            "research.search_papers_iterative",
            {"query": "x", "max_results": 1, "depth": "quick"},
        )

    await client.close()


@pytest.mark.asyncio
async def test_malformed_response_becomes_user_friendly_error() -> None:
    class MalformedTransport:
        async def list_tools(self):
            return [
                MCPToolDefinition(
                    name="research.search_papers_iterative",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer"},
                            "depth": {"type": "string"},
                        },
                        "required": ["query", "max_results", "depth"],
                    },
                    output_schema={"type": "array", "items": {"type": "object"}},
                )
            ]

        async def invoke_tool(self, tool_name, arguments):
            return {"ok": True}  # malformed: missing data

        async def invoke_tool_stream(self, tool_name, arguments):
            yield {"event": "result", "data": None, "done": True}

        async def close(self):
            return None

    client = MCPClient(transport=MalformedTransport())

    with pytest.raises(MCPExecutionError):
        await client.invoke_tool(
            "research.search_papers_iterative",
            {"query": "x", "max_results": 1, "depth": "quick"},
        )

    await client.close()
