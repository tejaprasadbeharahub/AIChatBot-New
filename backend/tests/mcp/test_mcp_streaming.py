from __future__ import annotations

import pytest

from app.services.mcp.client import MCPClient
from app.services.mcp.models import MCPToolDefinition


@pytest.mark.asyncio
async def test_streaming_chunks_are_normalized() -> None:
    class StreamTransport:
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
                    supports_streaming=True,
                )
            ]

        async def invoke_tool(self, tool_name, arguments):
            return {"ok": True, "data": []}

        async def invoke_tool_stream(self, tool_name, arguments):
            yield {"event": "progress", "data": {"step": 1}, "done": False}
            yield {"event": "result", "data": [{"arxiv_id": "a1"}], "done": True}

        async def close(self):
            return None

    client = MCPClient(transport=StreamTransport())

    chunks = []
    async for chunk in client.invoke_tool_stream(
        "research.search_papers_iterative",
        {"query": "agentic ai", "max_results": 2, "depth": "quick"},
    ):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0]["event"] == "progress"
    assert chunks[1]["done"] is True

    await client.close()


@pytest.mark.asyncio
async def test_streaming_failure_does_not_crash_consumer() -> None:
    class BrokenStreamTransport:
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
                    supports_streaming=True,
                )
            ]

        async def invoke_tool(self, tool_name, arguments):
            return {"ok": True, "data": []}

        async def invoke_tool_stream(self, tool_name, arguments):
            raise RuntimeError("socket disconnected")
            yield  # pragma: no cover

        async def close(self):
            return None

    client = MCPClient(transport=BrokenStreamTransport())

    chunks = []
    async for chunk in client.invoke_tool_stream(
        "research.search_papers_iterative",
        {"query": "agentic ai", "max_results": 2, "depth": "quick"},
    ):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0]["event"] == "error"
    assert chunks[0]["done"] is True

    await client.close()
