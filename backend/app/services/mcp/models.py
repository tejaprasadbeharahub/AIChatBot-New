"""Core models for MCP integration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MCPToolDefinition(BaseModel):
    """Tool metadata discovered from an MCP server."""

    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    supports_streaming: bool = False


class MCPToolCallResult(BaseModel):
    """Normalized result for MCP tool calls."""

    ok: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPStreamChunk(BaseModel):
    """Normalized streaming chunk for MCP tool streaming."""

    event: str
    data: Any = None
    done: bool = False
    error: str | None = None
