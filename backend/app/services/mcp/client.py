"""MCP client service with discovery, retries, validation, and normalization."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from app.core.config import settings
from app.services.mcp.errors import MCPExecutionError, MCPParsingError, MCPTransportError
from app.services.mcp.registry import MCPToolRegistry
from app.services.mcp.response_normalizer import normalize_stream_chunk, normalize_tool_result
from app.services.mcp.transport_factory import create_mcp_transport
from app.services.mcp.transports.base import MCPTransport

logger = logging.getLogger(__name__)


def _safe_payload(payload: Any, limit: int = 2000) -> str:
    try:
        text = json.dumps(payload, default=str, ensure_ascii=True)
    except Exception:
        text = repr(payload)
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


class MCPClient:
    """High-level MCP client for tool discovery and invocation."""

    def __init__(self, transport: MCPTransport | None = None) -> None:
        self.transport = transport or create_mcp_transport()
        self.registry = MCPToolRegistry()
        self._discovered = False
        logger.info(
            "mcp_connection_initialized",
            extra={
                "transport": settings.mcp_transport,
            },
        )

    async def discover_tools(self, refresh: bool = False) -> None:
        if self._discovered and not refresh:
            return

        started = time.perf_counter()
        logger.info(
            "mcp_discovery_started",
            extra={
                "transport": settings.mcp_transport,
                "refresh": refresh,
            },
        )

        try:
            tools = await self.transport.list_tools()
        except Exception as exc:
            logger.error(
                "mcp_discovery_failed",
                extra={
                    "transport": settings.mcp_transport,
                    "error": str(exc),
                },
            )
            raise MCPTransportError("Tool discovery failed. Please try again.") from exc

        self.registry.register_many(tools)
        self._discovered = True

        logger.info(
            "mcp_tools_discovered",
            extra={
                "count": len(tools),
                "transport": settings.mcp_transport,
                "tool_names": [t.name for t in tools],
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
            },
        )

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        await self.discover_tools()

        logger.info(
            "mcp_tool_invocation_requested",
            extra={
                "tool": tool_name,
                "payload": _safe_payload(arguments),
            },
        )

        self.registry.validate_args(tool_name, arguments)

        retries = max(0, settings.mcp_retry_attempts)
        timeout = max(1, settings.mcp_request_timeout_seconds)
        backoff = max(0.0, settings.mcp_retry_backoff_seconds)

        last_err: Exception | None = None

        for attempt in range(retries + 1):
            started = time.perf_counter()
            try:
                raw = await asyncio.wait_for(
                    self.transport.invoke_tool(tool_name, arguments),
                    timeout=timeout,
                )
                logger.info(
                    "mcp_tool_response_received",
                    extra={
                        "tool": tool_name,
                        "attempt": attempt + 1,
                        "payload": _safe_payload(raw),
                    },
                )
                normalized = normalize_tool_result(raw)
                if not normalized.ok:
                    raise MCPExecutionError(normalized.error or "Tool execution failed")

                self.registry.validate_output(tool_name, normalized.data)

                logger.info(
                    "mcp_tool_invocation_ok",
                    extra={
                        "tool": tool_name,
                        "attempt": attempt + 1,
                        "elapsed_ms": int((time.perf_counter() - started) * 1000),
                        "response": _safe_payload(normalized.data),
                    },
                )
                return normalized.data

            except (MCPExecutionError, MCPParsingError) as exc:
                # Non-retryable class: schema/parse/execution contract issues.
                last_err = exc
                logger.error(
                    "mcp_tool_invocation_non_retryable_failure",
                    extra={
                        "tool": tool_name,
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                break
            except Exception as exc:
                last_err = exc
                logger.warning(
                    "mcp_tool_invocation_failed",
                    extra={
                        "tool": tool_name,
                        "attempt": attempt + 1,
                        "retries": retries,
                        "error": str(exc),
                    },
                )
                if attempt < retries:
                    await asyncio.sleep(backoff * (attempt + 1))

        msg = (
            f"Research tool '{tool_name}' is temporarily unavailable. "
            "Please retry in a moment."
        )
        raise MCPExecutionError(msg) from last_err

    async def invoke_tool_stream(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        await self.discover_tools()
        self.registry.validate_args(tool_name, arguments)

        logger.info(
            "mcp_tool_stream_requested",
            extra={
                "tool": tool_name,
                "payload": _safe_payload(arguments),
            },
        )

        try:
            async for raw_chunk in self.transport.invoke_tool_stream(tool_name, arguments):
                chunk = normalize_stream_chunk(raw_chunk)
                payload = {
                    "event": chunk.event,
                    "data": chunk.data,
                    "done": chunk.done,
                    "error": chunk.error,
                }
                logger.info(
                    "mcp_tool_stream_chunk",
                    extra={
                        "tool": tool_name,
                        "payload": _safe_payload(payload),
                    },
                )
                yield payload
                if chunk.done:
                    break
        except Exception as exc:
            logger.error(
                "mcp_tool_stream_failed",
                extra={
                    "tool": tool_name,
                    "error": str(exc),
                },
            )
            yield {
                "event": "error",
                "data": None,
                "done": True,
                "error": "Tool stream temporarily unavailable.",
            }

    async def close(self) -> None:
        try:
            await self.transport.close()
            logger.info("mcp_connection_closed", extra={"transport": settings.mcp_transport})
        except Exception as exc:
            logger.warning(
                "mcp_connection_close_failed",
                extra={"transport": settings.mcp_transport, "error": str(exc)},
            )
