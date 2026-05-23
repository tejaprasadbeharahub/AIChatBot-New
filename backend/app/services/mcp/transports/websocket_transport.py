"""WebSocket transport for MCP servers."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

try:
    from websockets.asyncio.client import connect
except Exception:  # pragma: no cover - compatibility fallback
    from websockets.client import connect

from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.transports.base import MCPTransport


class WebSocketMCPTransport(MCPTransport):
    """Uses a request/response protocol over WebSocket for MCP operations."""

    def __init__(self, ws_url: str, auth_token: str | None = None):
        self.ws_url = ws_url
        self.auth_token = auth_token

    async def _request(self, payload: dict[str, Any]) -> Any:
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else None
        async with connect(self.ws_url, additional_headers=headers) as ws:
            await ws.send(json.dumps(payload))
            response = await ws.recv()
            return json.loads(response)

    async def list_tools(self) -> list[MCPToolDefinition]:
        payload = await self._request({"action": "list_tools"})
        tools = payload.get("tools", [])
        return [MCPToolDefinition.model_validate(item) for item in tools]

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        return await self._request(
            {
                "action": "invoke_tool",
                "tool_name": tool_name,
                "arguments": arguments,
            }
        )

    async def invoke_tool_stream(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> AsyncIterator[Any]:
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else None
        async with connect(self.ws_url, additional_headers=headers) as ws:
            await ws.send(
                json.dumps(
                    {
                        "action": "invoke_tool_stream",
                        "tool_name": tool_name,
                        "arguments": arguments,
                    }
                )
            )
            async for message in ws:
                chunk = json.loads(message)
                yield chunk
                if chunk.get("done"):
                    break
