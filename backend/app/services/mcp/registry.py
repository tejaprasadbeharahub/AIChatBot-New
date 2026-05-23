"""Central registry for discovered MCP tools."""

from __future__ import annotations

from typing import Any

from app.services.mcp.errors import MCPExecutionError
from app.services.mcp.models import MCPToolDefinition
from app.services.mcp.schema_validation import SchemaValidationError, validate_against_schema


class MCPToolRegistry:
    """Stores discovered tool metadata and validates arguments/results."""

    def __init__(self) -> None:
        self._tools: dict[str, MCPToolDefinition] = {}

    def register_many(self, tools: list[MCPToolDefinition]) -> None:
        for tool in tools:
            self._tools[tool.name] = tool

    def get(self, name: str) -> MCPToolDefinition | None:
        return self._tools.get(name)

    def list(self) -> list[MCPToolDefinition]:
        return list(self._tools.values())

    def validate_args(self, tool_name: str, args: dict[str, Any]) -> None:
        tool = self.get(tool_name)
        if not tool:
            raise MCPExecutionError(f"Tool '{tool_name}' is not available right now.")
        try:
            validate_against_schema(args, tool.input_schema, path=f"$.{tool_name}.args")
        except SchemaValidationError as exc:
            raise MCPExecutionError(f"Invalid input for tool '{tool_name}': {exc}") from exc

    def validate_output(self, tool_name: str, data: Any) -> None:
        tool = self.get(tool_name)
        if not tool:
            raise MCPExecutionError(f"Tool '{tool_name}' is not available right now.")
        try:
            validate_against_schema(data, tool.output_schema, path=f"$.{tool_name}.output")
        except SchemaValidationError as exc:
            raise MCPExecutionError(f"Invalid output from tool '{tool_name}': {exc}") from exc
