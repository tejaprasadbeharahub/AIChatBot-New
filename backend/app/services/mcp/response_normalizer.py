"""Normalization helpers for MCP transport responses."""

from __future__ import annotations

from typing import Any

from app.services.mcp.errors import MCPParsingError
from app.services.mcp.models import MCPToolCallResult, MCPStreamChunk


def normalize_tool_result(raw: Any) -> MCPToolCallResult:
    """Normalize heterogeneous tool responses into a common structure."""
    if isinstance(raw, MCPToolCallResult):
        return raw

    if isinstance(raw, dict):
        if "ok" in raw:
            if bool(raw.get("ok")) and "data" not in raw:
                raise MCPParsingError("Malformed MCP response: success payload missing 'data'")
            return MCPToolCallResult(
                ok=bool(raw.get("ok")),
                data=raw.get("data"),
                error=raw.get("error"),
                metadata=raw.get("metadata") or {},
            )

        # Bare dict payload is considered success data.
        return MCPToolCallResult(ok=True, data=raw, metadata={})

    return MCPToolCallResult(ok=True, data=raw, metadata={})


def normalize_stream_chunk(raw: Any) -> MCPStreamChunk:
    """Normalize transport-specific chunks into the standard stream chunk."""
    if isinstance(raw, MCPStreamChunk):
        return raw

    if isinstance(raw, dict):
        if raw.get("done") and raw.get("error") and raw.get("data") is not None:
            # Keep format strict to avoid ambiguous terminal chunks.
            raise MCPParsingError("Malformed MCP stream chunk: terminal error chunk contains data")
        return MCPStreamChunk(
            event=str(raw.get("event", "chunk")),
            data=raw.get("data"),
            done=bool(raw.get("done", False)),
            error=raw.get("error"),
        )

    return MCPStreamChunk(event="chunk", data=raw)
