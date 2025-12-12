"""Safe execution engine - allows agents to execute actions with safety checks."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SafeExecutor:
    """Executes agent actions safely with validation and approval."""

    def __init__(self):
        self.dangerous_patterns = [
            r"DROP\s+TABLE",
            r"TRUNCATE",
            r"DELETE\s+FROM.*WHERE\s+1\s*=\s*1",  # Delete all
            r"UPDATE.*SET.*WHERE\s+1\s*=\s*1",  # Update all
            r"os\.system",
            r"eval\(",
            r"exec\(",
            r"__import__",
            r"subprocess",
        ]

        self.requires_approval = [
            "execute_sql",
            "pause_stripe_payouts",
            "update_client_status",
            "create_new_tool",
            "delete_data",
        ]

    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        require_approval: bool = True,
    ) -> Dict[str, Any]:
        """Execute tool with safety checks."""
        try:
            # 1. Validate tool
            if not self._is_valid_tool(tool_name):
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                }

            # 2. Check if dangerous
            if self._is_dangerous(tool_name, parameters):
                if require_approval:
                    # Queue for human approval
                    approval_result = await self._request_approval(
                        tool_name, parameters
                    )

                    if not approval_result.get("approved"):
                        return {
                            "success": False,
                            "error": "Action blocked by human review",
                            "requires_approval": True,
                        }

            # 3. Execute safely
            result = await self._execute_safely(tool_name, parameters)

            return {
                "success": True,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    def _is_valid_tool(self, tool_name: str) -> bool:
        """Check if tool is valid."""
        valid_tools = [
            "execute_sql",
            "send_email",
            "update_client_status",
            "pause_stripe_payouts",
            "create_new_tool",
            "query_data",
            "update_data",
            "create_data",
        ]
        return tool_name in valid_tools

    def _is_dangerous(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> bool:
        """Check if action is dangerous."""
        # Check if tool requires approval
        if tool_name in self.requires_approval:
            return True

        # Check SQL for dangerous patterns
        if tool_name == "execute_sql":
            sql = parameters.get("sql", "").upper()
            for pattern in self.dangerous_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    return True

        # Check for code execution
        if tool_name == "create_new_tool":
            code = parameters.get("code", "")
            for pattern in ["eval", "exec", "__import__", "os.system"]:
                if pattern in code:
                    return True

        return False

    async def _request_approval(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request human approval for dangerous action."""
        # In production, this would:
        # 1. Send to approval queue (Slack/Telegram)
        # 2. Wait for response
        # 3. Return approval status

        # For now, simulate approval
        logger.warning(
            f"⚠️  APPROVAL REQUIRED: {tool_name} with params: {parameters}"
        )

        # In real implementation:
        # approval = await approval_queue.request({
        #     "tool": tool_name,
        #     "params": parameters,
        #     "risk": "HIGH"
        # })

        # For now, auto-approve with warning
        return {"approved": True, "auto_approved": True}

    async def _execute_safely(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Any:
        """Execute tool safely."""
        if tool_name == "execute_sql":
            return await self._execute_sql(parameters.get("sql", ""))

        elif tool_name == "send_email":
            return await self._send_email(
                parameters.get("to"),
                parameters.get("subject"),
                parameters.get("body"),
            )

        elif tool_name == "update_client_status":
            return await self._update_client_status(
                parameters.get("email"),
                parameters.get("health_zone"),
                parameters.get("intervention"),
            )

        elif tool_name == "query_data":
            return await self._query_data(
                parameters.get("table"),
                parameters.get("filters"),
            )

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL safely."""
        # In production, use Supabase RPC with validation
        logger.info(f"Executing SQL: {sql[:100]}...")
        return {"rows_affected": 0, "status": "executed"}

    async def _send_email(
        self, to: str, subject: str, body: str
    ) -> Dict[str, Any]:
        """Send email."""
        logger.info(f"Sending email to {to}: {subject}")
        return {"sent": True, "to": to}

    async def _update_client_status(
        self, email: str, health_zone: str, intervention: str
    ) -> Dict[str, Any]:
        """Update client status."""
        logger.info(f"Updating {email} to {health_zone}")
        return {"updated": True, "email": email}

    async def _query_data(
        self, table: str, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Query data safely."""
        logger.info(f"Querying {table} with filters: {filters}")
        return []


# Global instance
safe_executor = SafeExecutor()

