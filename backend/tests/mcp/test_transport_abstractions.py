from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.transports.http_transport import HttpMCPTransport
from app.services.mcp.transports.stdio_transport import StdioMCPTransport
from app.services.mcp.transports.websocket_transport import WebSocketMCPTransport


@pytest.mark.asyncio
async def test_http_transport_list_and_invoke() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tools":
            payload = {
                "tools": [
                    {
                        "name": "research.search_papers_iterative",
                        "input_schema": {"type": "object"},
                        "output_schema": {"type": "array"},
                    }
                ]
            }
            return httpx.Response(200, json=payload)
        if request.url.path == "/invoke":
            return httpx.Response(200, json={"ok": True, "data": [{"arxiv_id": "x"}]})
        return httpx.Response(404, json={"detail": "not found"})

    transport = HttpMCPTransport("http://test-mcp")
    transport._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test-mcp")

    tools = await transport.list_tools()
    assert isinstance(tools[0], MCPToolDefinition)

    result = await transport.invoke_tool("research.search_papers_iterative", {"query": "x"})
    assert result["ok"] is True

    await transport.close()


@pytest.mark.asyncio
async def test_stdio_transport_roundtrip(tmp_path: Path) -> None:
    server_file = tmp_path / "fake_mcp_stdio_server.py"
    server_file.write_text(
        """
import json
import sys

for line in sys.stdin:
    payload = json.loads(line)
    action = payload.get('action')
    if action == 'list_tools':
        sys.stdout.write(json.dumps({'tools':[{'name':'research.search_papers_iterative','input_schema':{'type':'object'},'output_schema':{'type':'array'}}]}) + '\\n')
        sys.stdout.flush()
    elif action == 'invoke_tool':
        sys.stdout.write(json.dumps({'ok': True, 'data': [{'arxiv_id': 'x'}]}) + '\\n')
        sys.stdout.flush()
    elif action == 'invoke_tool_stream':
        sys.stdout.write(json.dumps({'chunks':[{'event':'result','data':[{'arxiv_id':'x'}],'done':True}]}) + '\\n')
        sys.stdout.flush()
""".strip(),
        encoding="utf-8",
    )

    cmd = f'"{Path(__import__("sys").executable)}" "{server_file}"'
    transport = StdioMCPTransport(cmd)

    tools = await transport.list_tools()
    assert tools[0].name == "research.search_papers_iterative"

    result = await transport.invoke_tool("research.search_papers_iterative", {"query": "x"})
    assert result["ok"] is True

    chunks = []
    async for chunk in transport.invoke_tool_stream("research.search_papers_iterative", {"query": "x"}):
        chunks.append(chunk)
    assert chunks[-1]["done"] is True

    await transport.close()


@pytest.mark.asyncio
async def test_websocket_transport_request_response() -> None:
    websockets = pytest.importorskip("websockets")

    async def ws_handler(conn):
        async for msg in conn:
            payload = json.loads(msg)
            action = payload.get("action")
            if action == "list_tools":
                await conn.send(json.dumps({"tools": [{"name": "research.search_papers_iterative", "input_schema": {"type": "object"}, "output_schema": {"type": "array"}}]}))
            elif action == "invoke_tool":
                await conn.send(json.dumps({"ok": True, "data": [{"arxiv_id": "x"}]}))
            elif action == "invoke_tool_stream":
                await conn.send(json.dumps({"event": "result", "data": [{"arxiv_id": "x"}], "done": True}))

    server = await websockets.serve(ws_handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    try:
        transport = WebSocketMCPTransport(f"ws://127.0.0.1:{port}")

        tools = await transport.list_tools()
        assert tools[0].name == "research.search_papers_iterative"

        result = await transport.invoke_tool("research.search_papers_iterative", {"query": "x"})
        assert result["ok"] is True

        chunks = []
        async for chunk in transport.invoke_tool_stream("research.search_papers_iterative", {"query": "x"}):
            chunks.append(chunk)
        assert chunks[-1]["done"] is True
    finally:
        server.close()
        await server.wait_closed()
