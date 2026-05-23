"""stdio transport for MCP servers using JSON-lines protocol."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.transports.base import MCPTransport


class StdioMCPTransport(MCPTransport):
    """Launches an MCP server process and communicates via stdin/stdout JSON lines."""

    def __init__(self, command: str):
        self.command = command
        self._proc: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()

    async def _ensure_process(self) -> asyncio.subprocess.Process:
        if self._proc and self._proc.returncode is None:
            return self._proc

        self._proc = await asyncio.create_subprocess_shell(
            self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        return self._proc

    async def _request(self, payload: dict[str, Any]) -> Any:
        async with self._lock:
            proc = await self._ensure_process()
            if proc.stdin is None or proc.stdout is None:
                raise RuntimeError("MCP stdio process streams are not available")

            proc.stdin.write((json.dumps(payload) + "\n").encode("utf-8"))
            await proc.stdin.drain()

            line = await proc.stdout.readline()
            if not line:
                raise RuntimeError("No response from MCP stdio server")

            return json.loads(line.decode("utf-8"))

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
        payload = await self._request(
            {
                "action": "invoke_tool_stream",
                "tool_name": tool_name,
                "arguments": arguments,
            }
        )

        chunks = payload.get("chunks", []) if isinstance(payload, dict) else []
        if chunks:
            for chunk in chunks:
                yield chunk
            return

        yield {"event": "result", "data": payload, "done": True}

    async def close(self) -> None:
        if self._proc and self._proc.returncode is None:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
                try:
                    await self._proc.stdin.wait_closed()
                except Exception:
                    pass

            try:
                await asyncio.wait_for(self._proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                self._proc.terminate()
                try:
                    await asyncio.wait_for(self._proc.wait(), timeout=2)
                except asyncio.TimeoutError:
                    self._proc.kill()
                    await self._proc.wait()
