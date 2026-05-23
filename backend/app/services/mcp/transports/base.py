"""Base transport interface for MCP communication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from app.services.mcp.models import MCPToolDefinition


class MCPTransport(ABC):
    """Abstract transport for tool discovery and invocation."""

    @abstractmethod
    async def list_tools(self) -> list[MCPToolDefinition]:
        raise NotImplementedError

    @abstractmethod
    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        raise NotImplementedError

    async def invoke_tool_stream(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> AsyncIterator[Any]:
        """Optional streaming invocation. Default emits one final result chunk."""
        result = await self.invoke_tool(tool_name, arguments)
        yield {"event": "result", "data": result, "done": True}

    async def close(self) -> None:
        """Close transport resources if needed."""
        return None
