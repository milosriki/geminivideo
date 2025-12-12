"""Human-in-the-loop approval system."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class HumanApprovalQueue:
    """Manages human approval for dangerous actions."""

    def __init__(self):
        self.client = supabase_client.client

    async def request_approval(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        risk_level: str = "HIGH",
        requested_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Request human approval for action."""
        if not self.client:
            # Fallback: auto-approve with warning
            logger.warning(
                f"⚠️  AUTO-APPROVED (no DB): {tool_name} - {risk_level}"
            )
            return {"approved": True, "auto_approved": True}

        try:
            # Create approval request
            result = (
                self.client.table("human_approval_queue")
                .insert(
                    {
                        "tool_name": tool_name,
                        "parameters": parameters,
                        "risk_level": risk_level,
                        "status": "pending",
                        "requested_by": requested_by or "agent",
                    }
                )
                .execute()
            )

            approval_id = result.data[0].get("id") if result.data else None

            # In production, send notification:
            # await self._send_notification(approval_id, tool_name, parameters)

            logger.info(
                f"Approval requested: {approval_id} for {tool_name}"
            )

            # For now, poll for approval (in production, use webhooks)
            approval = await self._wait_for_approval(approval_id, timeout=300)

            return approval

        except Exception as e:
            logger.error(f"Approval request failed: {e}", exc_info=True)
            # Fallback: auto-approve
            return {"approved": False, "error": str(e)}

    async def _wait_for_approval(
        self, approval_id: str, timeout: int = 300
    ) -> Dict[str, Any]:
        """Wait for approval (polls database)."""
        import asyncio
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                result = (
                    self.client.table("human_approval_queue")
                    .select("*")
                    .eq("id", approval_id)
                    .single()
                    .execute()
                )

                if result.data:
                    status = result.data.get("status")

                    if status == "approved":
                        return {
                            "approved": True,
                            "approved_by": result.data.get("approved_by"),
                            "approved_at": result.data.get("approved_at"),
                        }

                    elif status == "rejected":
                        return {
                            "approved": False,
                            "rejected_by": result.data.get("approved_by"),
                            "reason": "Rejected by human reviewer",
                        }

                # Still pending, wait
                await asyncio.sleep(5)

            except Exception as e:
                logger.debug(f"Approval check failed: {e}")
                await asyncio.sleep(5)

        # Timeout
        return {
            "approved": False,
            "error": "Approval timeout - action blocked",
        }

    async def approve(
        self, approval_id: str, approved_by: str
    ) -> Dict[str, Any]:
        """Approve an action."""
        if not self.client:
            return {"success": False, "error": "No database connection"}

        try:
            from datetime import datetime

            result = (
                self.client.table("human_approval_queue")
                .update(
                    {
                        "status": "approved",
                        "approved_by": approved_by,
                        "approved_at": datetime.now().isoformat(),
                    }
                )
                .eq("id", approval_id)
                .execute()
            )

            return {"success": True, "approval_id": approval_id}

        except Exception as e:
            logger.error(f"Approval failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def reject(
        self, approval_id: str, rejected_by: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject an action."""
        if not self.client:
            return {"success": False, "error": "No database connection"}

        try:
            from datetime import datetime

            result = (
                self.client.table("human_approval_queue")
                .update(
                    {
                        "status": "rejected",
                        "approved_by": rejected_by,
                        "approved_at": datetime.now().isoformat(),
                    }
                )
                .eq("id", approval_id)
                .execute()
            )

            return {"success": True, "approval_id": approval_id}

        except Exception as e:
            logger.error(f"Rejection failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approvals."""
        if not self.client:
            return []

        try:
            result = (
                self.client.table("human_approval_queue")
                .select("*")
                .eq("status", "pending")
                .order("created_at", desc=True)
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Failed to get approvals: {e}", exc_info=True)
            return []


# Global instance
human_approval_queue = HumanApprovalQueue()

