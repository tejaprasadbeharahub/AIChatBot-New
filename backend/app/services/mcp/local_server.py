"""Local in-process MCP server for Project 10 research tools."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Awaitable, Callable

import logging

from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.tools.research_tools import ResearchMCPTools

ToolHandler = Callable[..., Awaitable[Any]]
logger = logging.getLogger(__name__)


class LocalMCPServer:
    """In-memory MCP server implementing dynamic tool discovery and invocation."""

    def __init__(self) -> None:
        logger.info("mcp_local_server_init_started")
        self._research = ResearchMCPTools()
        self._handlers: dict[str, ToolHandler] = {
            "research.search_papers_iterative": self._research.search_papers_iterative,
            "research.score_papers": self._research.score_papers,
            "research.generate_refined_terms": self._research.generate_refined_terms,
            "research.generate_digest": self._research.generate_digest,
        }

        self._definitions: list[MCPToolDefinition] = [
            MCPToolDefinition(
                name="research.search_papers_iterative",
                description="Search arXiv papers with iterative expansion.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer"},
                        "depth": {"type": "string"},
                    },
                    "required": ["query", "max_results", "depth"],
                },
                output_schema={
                    "type": "array",
                    "items": {"type": "object"},
                },
            ),
            MCPToolDefinition(
                name="research.score_papers",
                description="Score and rank papers for query relevance.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "papers": {"type": "array", "items": {"type": "object"}},
                    },
                    "required": ["query", "papers"],
                },
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
            MCPToolDefinition(
                name="research.generate_refined_terms",
                description="Generate refined search terms using the current LLM.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "llm": {},
                        "query": {"type": "string"},
                    },
                    "required": ["llm", "query"],
                },
                output_schema={"type": "array", "items": {"type": "string"}},
            ),
            MCPToolDefinition(
                name="research.generate_digest",
                description="Generate structured digest from papers.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "papers": {"type": "array", "items": {"type": "object"}},
                        "llm": {},
                    },
                    "required": ["query", "papers", "llm"],
                },
                output_schema={"type": "object"},
            ),
        ]
        logger.info(
            "mcp_local_server_init_completed",
            extra={"tools": [tool.name for tool in self._definitions]},
        )

    async def list_tools(self) -> list[MCPToolDefinition]:
        logger.info(
            "mcp_local_list_tools",
            extra={"count": len(self._definitions), "tools": [t.name for t in self._definitions]},
        )
        return self._definitions

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        logger.info(
            "mcp_local_invoke_requested",
            extra={"tool": tool_name, "arguments": str(arguments)[:1000]},
        )
        handler = self._handlers.get(tool_name)
        if not handler:
            logger.error("mcp_local_invoke_missing_tool", extra={"tool": tool_name})
            raise ValueError(f"Unknown MCP tool: {tool_name}")
        result = await handler(**arguments)
        logger.info(
            "mcp_local_invoke_completed",
            extra={"tool": tool_name, "response": str(result)[:1000]},
        )
        return result

    async def invoke_tool_stream(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        result = await self.invoke_tool(tool_name, arguments)
        yield {"event": "result", "data": result, "done": True}
