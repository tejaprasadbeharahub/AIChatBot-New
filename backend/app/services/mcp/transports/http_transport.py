"""HTTP transport for MCP servers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.transports.base import MCPTransport


class HttpMCPTransport(MCPTransport):
    """Calls MCP endpoints over HTTP JSON APIs."""

    def __init__(self, base_url: str, timeout_seconds: int = 20, auth_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    async def list_tools(self) -> list[MCPToolDefinition]:
        response = await self._client.get(f"{self.base_url}/tools", headers=self._headers)
        response.raise_for_status()
        payload = response.json()
        raw_tools = payload.get("tools", payload)
        return [MCPToolDefinition.model_validate(item) for item in raw_tools]

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        response = await self._client.post(
            f"{self.base_url}/invoke",
            headers=self._headers,
            json={"tool_name": tool_name, "arguments": arguments},
        )
        response.raise_for_status()
        return response.json()

    async def invoke_tool_stream(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> AsyncIterator[Any]:
        async with self._client.stream(
            "POST",
            f"{self.base_url}/invoke/stream",
            headers=self._headers,
            json={"tool_name": tool_name, "arguments": arguments},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                yield {"event": "chunk", "data": line, "done": False}

    async def close(self) -> None:
        await self._client.aclose()
