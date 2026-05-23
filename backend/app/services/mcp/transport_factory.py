"""Factory to create MCP transport instances from application settings."""

from __future__ import annotations

from app.core.config import settings
from app.services.mcp.local_server import LocalMCPServer
from app.services.mcp.transports.base import MCPTransport
from app.services.mcp.transports.http_transport import HttpMCPTransport
from app.services.mcp.transports.inprocess_transport import InProcessMCPTransport
from app.services.mcp.transports.stdio_transport import StdioMCPTransport
from app.services.mcp.transports.websocket_transport import WebSocketMCPTransport


def create_mcp_transport() -> MCPTransport:
    transport_name = (settings.mcp_transport or "inprocess").strip().lower()

    if transport_name == "inprocess":
        return InProcessMCPTransport(LocalMCPServer())

    if transport_name == "stdio":
        if not settings.mcp_stdio_command:
            raise ValueError("MCP stdio transport selected but MCP_STDIO_COMMAND is empty")
        return StdioMCPTransport(settings.mcp_stdio_command)

    if transport_name == "http":
        if not settings.mcp_http_url:
            raise ValueError("MCP http transport selected but MCP_HTTP_URL is empty")
        return HttpMCPTransport(
            base_url=settings.mcp_http_url,
            timeout_seconds=settings.mcp_request_timeout_seconds,
            auth_token=settings.mcp_auth_token,
        )

    if transport_name == "websocket":
        if not settings.mcp_ws_url:
            raise ValueError("MCP websocket transport selected but MCP_WS_URL is empty")
        return WebSocketMCPTransport(
            ws_url=settings.mcp_ws_url,
            auth_token=settings.mcp_auth_token,
        )

    raise ValueError(f"Unsupported MCP transport: {transport_name}")
