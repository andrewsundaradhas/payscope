"""
MCP (Model Context Protocol) servers for tool orchestration.

Enables secure agent-tool interaction and tool discovery.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP server for tool orchestration.
    
    Provides tool registration, discovery, and secure execution for agents.
    """

    def __init__(self, name: str = "payscope-tools"):
        self.name = name
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.logger = logger

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: callable,
        requires_auth: bool = False,
    ) -> None:
        """
        Register a tool with the MCP server.
        
        Args:
            name: Tool name (unique identifier)
            description: Tool description
            input_schema: JSON schema for tool inputs
            handler: Callable that executes the tool
            requires_auth: Whether tool requires authentication
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "handler": handler,
            "requiresAuth": requires_auth,
        }
        self.logger.info(f"Registered tool: {name}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.
        
        Returns:
            List of tool definitions (without handlers)
        """
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
                "requiresAuth": tool["requiresAuth"],
            }
            for tool in self.tools.values()
        ]

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a registered tool.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            context: Execution context (auth, permissions, etc.)
        
        Returns:
            Tool execution result
        
        Raises:
            ValueError: If tool not found
            PermissionError: If authentication required but not provided
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        tool = self.tools[tool_name]

        # Check authentication
        if tool["requiresAuth"]:
            if not context or not context.get("authenticated"):
                raise PermissionError(f"Tool {tool_name} requires authentication")

        try:
            # Execute tool handler
            result = tool["handler"](**arguments)
            
            return {
                "tool": tool_name,
                "success": True,
                "result": result,
            }
        except Exception as e:
            self.logger.exception(f"Tool execution failed: {tool_name}")
            return {
                "tool": tool_name,
                "success": False,
                "error": str(e),
            }

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get JSON schema for a tool."""
        if tool_name not in self.tools:
            return None
        return {
            "name": self.tools[tool_name]["name"],
            "description": self.tools[tool_name]["description"],
            "inputSchema": self.tools[tool_name]["inputSchema"],
            "requiresAuth": self.tools[tool_name]["requiresAuth"],
        }


# Global MCP server instance
_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get global MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
        _register_default_tools(_mcp_server)
    return _mcp_server


def _register_default_tools(server: MCPServer) -> None:
    """Register default PayScope tools."""
    
    # Query tool
    server.register_tool(
        name="query_reports",
        description="Query payment reports using natural language",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language query"},
                "bank_id": {"type": "string", "description": "Bank ID filter"},
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string"},
                        "end": {"type": "string"},
                    },
                },
            },
            "required": ["query"],
        },
        handler=lambda query, bank_id=None, date_range=None: {
            "query": query,
            "bank_id": bank_id,
            "date_range": date_range,
        },
        requires_auth=True,
    )

    # Compare tool
    server.register_tool(
        name="compare_reports",
        description="Compare metrics across reports or time periods",
        input_schema={
            "type": "object",
            "properties": {
                "metric": {"type": "string"},
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["metric"],
        },
        handler=lambda metric, dimensions=None: {
            "metric": metric,
            "dimensions": dimensions or [],
        },
        requires_auth=True,
    )

    # Forecast tool
    server.register_tool(
        name="forecast_metric",
        description="Generate forecast for a metric",
        input_schema={
            "type": "object",
            "properties": {
                "metric": {"type": "string"},
                "horizon_days": {"type": "integer", "default": 14},
                "bank_id": {"type": "string"},
            },
            "required": ["metric"],
        },
        handler=lambda metric, horizon_days=14, bank_id=None: {
            "metric": metric,
            "horizon_days": horizon_days,
            "bank_id": bank_id,
        },
        requires_auth=True,
    )

    # What-if tool
    server.register_tool(
        name="what_if_simulation",
        description="Run what-if scenario simulation",
        input_schema={
            "type": "object",
            "properties": {
                "scenario": {"type": "object"},
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["scenario"],
        },
        handler=lambda scenario, metrics=None: {
            "scenario": scenario,
            "metrics": metrics or [],
        },
        requires_auth=True,
    )



