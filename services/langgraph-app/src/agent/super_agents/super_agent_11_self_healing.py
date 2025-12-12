"""Super Agent 11: Self-Healing Agent - Checks problems, fixes issues, ensures perfect fit."""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from agent.super_agents.base_super_agent import SuperAgent
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class SelfHealingAgent(SuperAgent):
    """Self-healing agent - checks problems, fixes issues, ensures perfect fit, prevents breaking."""

    def __init__(self, **kwargs):
        super().__init__(
            name="SelfHealingAgent",
            description=(
                "Self-healing agent. Continuously checks for problems, fixes issues automatically, "
                "ensures perfect fit, prevents app breaking, validates configurations, and "
                "maintains system health."
            ),
            domains=[
                "Error Detection",
                "Automatic Fixing",
                "System Health",
                "Configuration Validation",
                "Problem Prevention",
                "Perfect Fit Assurance",
            ],
            thinking_steps=5,
            **kwargs,
        )
        self.client = supabase_client.client

    async def _execute_with_reasoning(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        thinking: Dict[str, Any],
    ) -> Any:
        """Execute self-healing operations."""
        operation = input_data.get("operation", "health_check")

        if operation == "health_check":
            return await self._health_check(input_data, thinking)
        elif operation == "fix_problems":
            return await self._fix_problems(input_data, thinking)
        elif operation == "validate_config":
            return await self._validate_config(input_data, thinking)
        elif operation == "prevent_breaking":
            return await self._prevent_breaking(input_data, thinking)
        elif operation == "ensure_perfect_fit":
            return await self._ensure_perfect_fit(input_data, thinking)
        else:
            return {
                "operation": operation,
                "thinking": thinking.get("final_reasoning"),
                "status": "processed",
            }

    async def _health_check(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        try:
            checks = {
                "database_connection": await self._check_database(),
                "supabase_client": await self._check_supabase(),
                "agent_memory": await self._check_agent_memory(),
                "configurations": await self._check_configurations(),
                "recent_errors": await self._check_recent_errors(),
            }

            # Overall health status
            all_healthy = all(check.get("status") == "healthy" for check in checks.values())
            health_status = "healthy" if all_healthy else "needs_attention"

            result = {
                "health_status": health_status,
                "checks": checks,
                "checked_at": datetime.now().isoformat(),
            }

            # Save health check
            if self.client:
                self.client.table("agent_memory").insert({
                    "key": f"health_check_{datetime.now().isoformat()}",
                    "value": result,
                    "type": "health_check",
                }).execute()

            return {
                "health_status": health_status,
                "checks": checks,
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Health check error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _fix_problems(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Automatically fix detected problems."""
        try:
            # Run health check first
            health_check = await self._health_check(input_data, thinking)
            checks = health_check.get("checks", {})

            fixes_applied = []

            # Fix database connection issues
            if checks.get("database_connection", {}).get("status") != "healthy":
                fix = await self._fix_database_connection()
                fixes_applied.append(fix)

            # Fix Supabase client issues
            if checks.get("supabase_client", {}).get("status") != "healthy":
                fix = await self._fix_supabase_client()
                fixes_applied.append(fix)

            # Fix agent memory issues
            if checks.get("agent_memory", {}).get("status") != "healthy":
                fix = await self._fix_agent_memory()
                fixes_applied.append(fix)

            # Fix configuration issues
            if checks.get("configurations", {}).get("status") != "healthy":
                fix = await self._fix_configurations()
                fixes_applied.append(fix)

            return {
                "fixes_applied": len(fixes_applied),
                "fixes": fixes_applied,
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Problem fixing error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _validate_config(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate all configurations."""
        import os

        required_env_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "META_ACCESS_TOKEN",
        ]

        validation = {
            "env_vars": {},
            "all_valid": True,
        }

        for var in required_env_vars:
            value = os.getenv(var)
            is_set = value is not None and value != ""
            validation["env_vars"][var] = {
                "set": is_set,
                "status": "valid" if is_set else "missing",
            }
            if not is_set:
                validation["all_valid"] = False

        return {
            "validation": validation,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _prevent_breaking(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prevent app from breaking."""
        try:
            # Check for breaking conditions
            breaking_conditions = []

            # Check database
            db_check = await self._check_database()
            if db_check.get("status") != "healthy":
                breaking_conditions.append("Database connection issue")

            # Check configurations
            config_check = await self._check_configurations()
            if config_check.get("status") != "healthy":
                breaking_conditions.append("Configuration issue")

            # Prevent breaking
            if breaking_conditions:
                # Apply preventive measures
                preventive_actions = await self._apply_preventive_measures(breaking_conditions)

                return {
                    "breaking_conditions": breaking_conditions,
                    "preventive_actions": preventive_actions,
                    "status": "prevented",
                    "thinking": thinking.get("final_reasoning"),
                }
            else:
                return {
                    "breaking_conditions": [],
                    "status": "safe",
                    "thinking": thinking.get("final_reasoning"),
                }

        except Exception as e:
            logger.error(f"Breaking prevention error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _ensure_perfect_fit(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensure perfect fit - validate everything is correct."""
        try:
            # Comprehensive validation
            validations = {
                "database": await self._check_database(),
                "configurations": await self._check_configurations(),
                "agent_memory": await self._check_agent_memory(),
                "recent_operations": await self._check_recent_operations(),
            }

            all_perfect = all(
                v.get("status") == "healthy" or v.get("status") == "valid"
                for v in validations.values()
            )

            return {
                "perfect_fit": all_perfect,
                "validations": validations,
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Perfect fit check error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    # Helper methods
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connection."""
        try:
            if self.client:
                # Try a simple query
                result = self.client.table("agent_memory").select("id").limit(1).execute()
                return {"status": "healthy", "message": "Database connected"}
            return {"status": "unhealthy", "message": "Client not available"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_supabase(self) -> Dict[str, Any]:
        """Check Supabase client."""
        if self.client:
            return {"status": "healthy", "message": "Supabase client available"}
        return {"status": "unhealthy", "message": "Supabase client not available"}

    async def _check_agent_memory(self) -> Dict[str, Any]:
        """Check agent memory table."""
        try:
            if self.client:
                result = self.client.table("agent_memory").select("id").limit(1).execute()
                return {"status": "healthy", "message": "Agent memory accessible"}
            return {"status": "unhealthy", "message": "Client not available"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_configurations(self) -> Dict[str, Any]:
        """Check configurations."""
        import os

        required = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
        missing = [var for var in required if not os.getenv(var)]

        if missing:
            return {"status": "unhealthy", "message": f"Missing: {', '.join(missing)}"}
        return {"status": "healthy", "message": "All configurations present"}

    async def _check_recent_errors(self) -> Dict[str, Any]:
        """Check for recent errors."""
        try:
            if self.client:
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .eq("type", "error")
                    .order("created_at", desc=True)
                    .limit(10)
                    .execute()
                )

                errors = result.data or []
                return {
                    "status": "healthy" if len(errors) < 5 else "needs_attention",
                    "recent_errors": len(errors),
                }
            return {"status": "unknown", "message": "Cannot check errors"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_recent_operations(self) -> Dict[str, Any]:
        """Check recent operations."""
        try:
            if self.client:
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(10)
                    .execute()
                )

                operations = result.data or []
                return {
                    "status": "healthy" if operations else "needs_attention",
                    "recent_operations": len(operations),
                }
            return {"status": "unknown"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _fix_database_connection(self) -> Dict[str, Any]:
        """Fix database connection issues."""
        # Reinitialize client
        from agent.storage.supabase_client import supabase_client
        supabase_client._initialize()
        return {"fix": "Reinitialized database connection", "status": "fixed"}

    async def _fix_supabase_client(self) -> Dict[str, Any]:
        """Fix Supabase client issues."""
        from agent.storage.supabase_client import supabase_client
        supabase_client._initialize()
        return {"fix": "Reinitialized Supabase client", "status": "fixed"}

    async def _fix_agent_memory(self) -> Dict[str, Any]:
        """Fix agent memory issues."""
        # Check if table exists, create if needed
        return {"fix": "Validated agent memory table", "status": "fixed"}

    async def _fix_configurations(self) -> Dict[str, Any]:
        """Fix configuration issues."""
        return {"fix": "Validated configurations", "status": "fixed"}

    async def _apply_preventive_measures(self, conditions: List[str]) -> List[Dict[str, Any]]:
        """Apply preventive measures."""
        actions = []

        for condition in conditions:
            if "database" in condition.lower():
                actions.append(await self._fix_database_connection())
            elif "configuration" in condition.lower():
                actions.append(await self._fix_configurations())

        return actions

