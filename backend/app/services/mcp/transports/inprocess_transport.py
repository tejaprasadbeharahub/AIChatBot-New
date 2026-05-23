"""In-process MCP transport for local tool execution."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.transports.base import MCPTransport


class InProcessMCPTransport(MCPTransport):
    """Transport that calls an in-memory MCP server implementation directly."""

    def __init__(self, server: Any):
        self.server = server

    async def list_tools(self) -> list[MCPToolDefinition]:
        return await self.server.list_tools()

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        return await self.server.invoke_tool(tool_name, arguments)

    async def invoke_tool_stream(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> AsyncIterator[Any]:
        async for chunk in self.server.invoke_tool_stream(tool_name, arguments):
            yield chunk
