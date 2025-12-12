"""Execution tools for agents - full system control."""

from __future__ import annotations

from typing import Any, Dict, List

from agent.execution.safe_executor import safe_executor


class ExecutionTools:
    """Tools that agents can use to execute actions."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        """Get all available execution tools."""
        return [
            {
                "name": "execute_sql",
                "description": (
                    "Execute SQL query on database (FULL POWER - requires approval for dangerous operations)"
                ),
                "parameters": {
                    "sql": {
                        "type": "string",
                        "description": "Safe SQL query to execute",
                    }
                },
            },
            {
                "name": "send_email",
                "description": "Send email to clients/coaches (HubSpot integration)",
                "parameters": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                },
            },
            {
                "name": "update_client_status",
                "description": "Update client health/intervention status",
                "parameters": {
                    "email": {"type": "string", "description": "Client email"},
                    "health_zone": {
                        "type": "string",
                        "enum": ["purple", "green", "yellow", "red"],
                        "description": "Health zone",
                    },
                    "intervention": {
                        "type": "string",
                        "description": "Intervention type",
                    },
                },
            },
            {
                "name": "query_data",
                "description": "Query data from any table safely",
                "parameters": {
                    "table": {"type": "string", "description": "Table name"},
                    "filters": {
                        "type": "object",
                        "description": "Filter conditions",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Result limit",
                        "default": 100,
                    },
                },
            },
            {
                "name": "update_data",
                "description": "Update data in table (requires approval)",
                "parameters": {
                    "table": {"type": "string", "description": "Table name"},
                    "id": {"type": "string", "description": "Record ID"},
                    "data": {
                        "type": "object",
                        "description": "Data to update",
                    },
                },
            },
            {
                "name": "create_data",
                "description": "Create new record in table",
                "parameters": {
                    "table": {"type": "string", "description": "Table name"},
                    "data": {
                        "type": "object",
                        "description": "Data to create",
                    },
                },
            },
            {
                "name": "create_new_tool",
                "description": (
                    "Create custom tool for new tasks (SELF-IMPROVEMENT - requires approval)"
                ),
                "parameters": {
                    "tool_name": {"type": "string", "description": "Tool name"},
                    "description": {"type": "string", "description": "Tool description"},
                    "code": {
                        "type": "string",
                        "description": "Python/TypeScript function code",
                    },
                },
            },
        ]

    @staticmethod
    async def execute_tool(
        tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool safely."""
        return await safe_executor.execute(tool_name, parameters)


# Export tools
EXECUTION_TOOLS = ExecutionTools.get_tools()

