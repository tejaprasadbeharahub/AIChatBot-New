from __future__ import annotations

import asyncio
import logging

import pytest

from app.services.mcp.client import MCPClient
from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.reliability import AsyncSingleFlight


@pytest.mark.asyncio
async def test_singleflight_deduplicates_concurrent_calls() -> None:
    sf = AsyncSingleFlight()
    counter = {"calls": 0}

    async def factory() -> int:
        counter["calls"] += 1
        await asyncio.sleep(0.05)
        return 42

    results = await asyncio.gather(
        *[sf.do("same-key", factory) for _ in range(15)]
    )

    assert results == [42] * 15
    assert counter["calls"] == 1


@pytest.mark.asyncio
async def test_client_logs_discovery_and_invocation(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)

    class LoggingTransport:
        async def list_tools(self):
            return [
                MCPToolDefinition(
                    name="research.score_papers",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "papers": {"type": "array", "items": {"type": "object"}},
                        },
                        "required": ["query", "papers"],
                    },
                    output_schema={"type": "array", "items": {"type": "object"}},
                )
            ]

        async def invoke_tool(self, tool_name, arguments):
            return {"ok": True, "data": [{"title": "t", "relevance_score": 0.9}]}

        async def invoke_tool_stream(self, tool_name, arguments):
            yield {"event": "result", "data": [], "done": True}

        async def close(self):
            return None

    client = MCPClient(transport=LoggingTransport())
    _ = await client.invoke_tool("research.score_papers", {"query": "x", "papers": []})
    await client.close()

    text = "\n".join(r.message for r in caplog.records)
    assert "mcp_tools_discovered" in text
    assert "mcp_tool_invocation_requested" in text
    assert "mcp_tool_invocation_ok" in text


@pytest.mark.asyncio
async def test_concurrent_client_invocations_remain_stable() -> None:
    class SlowTransport:
        async def list_tools(self):
            return [
                MCPToolDefinition(
                    name="research.score_papers",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "papers": {"type": "array", "items": {"type": "object"}},
                        },
                        "required": ["query", "papers"],
                    },
                    output_schema={"type": "array", "items": {"type": "object"}},
                )
            ]

        async def invoke_tool(self, tool_name, arguments):
            await asyncio.sleep(0.01)
            return {"ok": True, "data": [{"query": arguments["query"]}]}

        async def invoke_tool_stream(self, tool_name, arguments):
            yield {"event": "result", "data": [], "done": True}

        async def close(self):
            return None

    client = MCPClient(transport=SlowTransport())

    async def call(i: int):
        return await client.invoke_tool("research.score_papers", {"query": f"q{i}", "papers": []})

    results = await asyncio.gather(*[call(i) for i in range(40)])

    assert len(results) == 40
    assert all(isinstance(item, list) for item in results)

    await client.close()
