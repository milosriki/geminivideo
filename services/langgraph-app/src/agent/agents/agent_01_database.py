"""Agent 1: Database Management Agent - Handles all database operations."""

from typing import Any, Dict

from agent.core.base_agent import AgentError, BaseAgent


class DatabaseAgent(BaseAgent):
    """Manages database operations, migrations, and queries."""

    def __init__(self, **kwargs):
        super().__init__(
            name="DatabaseAgent",
            description=(
                "Expert database architect specializing in PostgreSQL, "
                "migrations, RLS policies, indexing, and query optimization. "
                "Ensures data integrity and performance."
            ),
            **kwargs,
        )

    async def _execute_impl(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database operations."""
        operation = input_data.get("operation")
        if not operation:
            raise AgentError(
                "Operation required",
                agent_name=self.name,
                error_type="validation_error",
            )

        if operation == "query":
            return await self._execute_query(input_data, context)
        elif operation == "migrate":
            return await self._execute_migration(input_data, context)
        elif operation == "optimize":
            return await self._optimize_database(input_data, context)
        elif operation == "backup":
            return await self._backup_database(input_data, context)
        else:
            raise AgentError(
                f"Unknown operation: {operation}",
                agent_name=self.name,
                error_type="validation_error",
            )

    async def _execute_query(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database query with validation."""
        query = input_data.get("query")
        if not query:
            raise AgentError(
                "Query required",
                agent_name=self.name,
                error_type="validation_error",
            )

        # Use LLM to validate and optimize query
        prompt = f"""
        Analyze this SQL query for safety and optimization:
        {query}
        
        Check for:
        1. SQL injection risks
        2. Missing indexes
        3. Performance issues
        4. RLS policy compliance
        
        Provide recommendations.
        """

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]
        analysis = await self._call_llm(messages)

        return {
            "query": query,
            "analysis": analysis,
            "status": "validated",
        }

    async def _execute_migration(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database migration."""
        migration_sql = input_data.get("migration_sql")
        if not migration_sql:
            raise AgentError(
                "Migration SQL required",
                agent_name=self.name,
                error_type="validation_error",
            )

        # Validate migration
        prompt = f"""
        Validate this database migration:
        {migration_sql}
        
        Ensure:
        1. Idempotency (IF NOT EXISTS)
        2. RLS policies enabled
        3. Indexes on foreign keys
        4. Proper error handling
        """

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]
        validation = await self._call_llm(messages)

        return {
            "migration": migration_sql,
            "validation": validation,
            "status": "ready",
        }

    async def _optimize_database(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize database performance."""
        table_name = input_data.get("table_name")

        prompt = f"""
        Analyze database optimization for table: {table_name or 'all tables'}
        
        Check:
        1. Missing indexes
        2. Unused indexes
        3. Query performance
        4. Table statistics
        5. Vacuum needs
        """

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]
        recommendations = await self._call_llm(messages)

        return {
            "table": table_name,
            "recommendations": recommendations,
            "status": "analyzed",
        }

    async def _backup_database(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Plan database backup strategy."""
        return {
            "strategy": "automated_backup",
            "frequency": "daily",
            "retention": "30_days",
            "status": "planned",
        }

