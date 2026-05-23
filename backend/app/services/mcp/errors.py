"""Typed MCP and tool execution exceptions."""

from __future__ import annotations


class MCPError(Exception):
    """Base class for MCP-related failures."""


class MCPTransportError(MCPError):
    """Transport/network failure while calling external APIs or MCP servers."""


class MCPRateLimitError(MCPError):
    """Rate-limiting failure from an upstream API."""

    def __init__(self, message: str, retry_after_seconds: float | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class MCPParsingError(MCPError):
    """Invalid or malformed upstream payload/response."""


class MCPExecutionError(MCPError):
    """Tool execution failure that should not crash orchestration."""
