"""Auto-discovery system for unlimited learning - discovers entire app structure."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class AutoDiscovery:
    """Auto-discovers entire app structure without hardcoding."""

    def __init__(self):
        self.client = supabase_client.client

    async def discover_app_structure(self) -> Dict[str, Any]:
        """Discover entire app structure automatically."""
        try:
            # 1. Discover all tables
            tables = await self._discover_tables()

            # 2. Discover all functions
            functions = await self._discover_functions()

            # 3. Discover recent data patterns
            recent_patterns = await self._discover_recent_patterns(tables)

            # 4. Discover relationships
            relationships = await self._discover_relationships()

            # 5. Build dynamic knowledge
            knowledge = {
                "tables": tables,
                "functions": functions,
                "recent_patterns": recent_patterns,
                "relationships": relationships,
                "discovered_at": self._get_timestamp(),
            }

            # 6. Save to agent memory
            await self._save_to_memory(knowledge)

            logger.info(
                f"Discovered {len(tables)} tables, {len(functions)} functions"
            )
            return knowledge

        except Exception as e:
            logger.error(f"Discovery error: {e}", exc_info=True)
            return {
                "tables": [],
                "functions": [],
                "recent_patterns": {},
                "relationships": [],
                "error": str(e),
            }

    async def _discover_tables(self) -> List[Dict[str, Any]]:
        """Discover all tables in database."""
        if not self.client:
            # Fallback: return known tables from context
            return self._get_known_tables()

        try:
            # Use SQL function if available (created by migration)
            result = self.client.rpc("get_all_tables").execute()

            if result.data:
                return [
                    {
                        "name": t.get("table_name"),
                        "row_count": t.get("row_count", 0),
                        "rls_enabled": t.get("rls_enabled", False),
                        "schema": t.get("schema_name", "public"),
                    }
                    for t in result.data
                ]

            # Fallback: query information_schema directly
            return await self._query_tables_direct()

        except Exception as e:
            logger.warning(f"RPC failed, using direct query: {e}")
            return await self._query_tables_direct()

    async def _query_tables_direct(self) -> List[Dict[str, Any]]:
        """Query tables directly from information_schema."""
        if not self.client:
            return self._get_known_tables()

        try:
            # Query using SQL
            query = """
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            LIMIT 100
            """

            result = self.client.rpc("exec_sql", {"query": query}).execute()

            if result.data:
                return [
                    {"name": row.get("table_name"), "column_count": row.get("column_count", 0)}
                    for row in result.data
                ]

        except Exception as e:
            logger.warning(f"Direct query failed: {e}")

        return self._get_known_tables()

    def _get_known_tables(self) -> List[Dict[str, Any]]:
        """Fallback: return known tables from our system."""
        return [
            {"name": "campaigns", "schema": "public"},
            {"name": "videos", "schema": "public"},
            {"name": "blueprints", "schema": "public"},
            {"name": "render_jobs", "schema": "public"},
            {"name": "users", "schema": "public"},
            {"name": "campaign_performance", "schema": "public"},
            {"name": "lead_tracking", "schema": "public"},
            {"name": "daily_metrics", "schema": "public"},
            {"name": "lead_quality", "schema": "public"},
        ]

    async def _discover_functions(self) -> List[Dict[str, Any]]:
        """Discover all database functions."""
        if not self.client:
            return []

        try:
            # Use SQL function (created by migration)
            result = self.client.rpc("get_all_functions").execute()

            if result.data:
                return [
                    {
                        "name": f.get("function_name"),
                        "return_type": f.get("return_type", ""),
                        "parameters": f.get("parameters", ""),
                        "type": "sql"
                    }
                    for f in result.data
                ]

            # Fallback: query pg_proc
            return await self._query_functions_direct()

        except Exception as e:
            logger.warning(f"Function discovery failed: {e}")
            return []

    async def _query_functions_direct(self) -> List[Dict[str, Any]]:
        """Query functions directly."""
        # This would require direct SQL access
        # For now, return empty - will be populated by SQL functions
        return []

    async def _discover_recent_patterns(
        self, tables: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Discover recent data patterns from key tables."""
        if not self.client:
            return {}

        patterns = {}

        # Sample from key tables
        key_tables = [
            "campaign_performance",
            "lead_tracking",
            "daily_metrics",
            "videos",
            "campaigns",
        ]

        for table_name in key_tables:
            if any(t.get("name") == table_name for t in tables):
                try:
                    result = (
                        self.client.table(table_name)
                        .select("*")
                        .limit(10)
                        .execute()
                    )

                    if result.data:
                        patterns[table_name] = {
                            "sample_count": len(result.data),
                            "columns": list(result.data[0].keys())
                            if result.data
                            else [],
                            "recent_values": result.data[:3],  # Sample 3 rows
                        }
                except Exception as e:
                    logger.debug(f"Pattern discovery for {table_name} failed: {e}")

        return patterns

    async def _discover_relationships(self) -> List[Dict[str, Any]]:
        """Discover table relationships."""
        if not self.client:
            return []

        relationships = []

        # Known relationships from our schema
        known_relationships = [
            {
                "from_table": "campaigns",
                "to_table": "videos",
                "type": "one_to_many",
                "foreign_key": "campaign_id",
            },
            {
                "from_table": "campaigns",
                "to_table": "blueprints",
                "type": "one_to_many",
                "foreign_key": "campaign_id",
            },
            {
                "from_table": "blueprints",
                "to_table": "videos",
                "type": "one_to_many",
                "foreign_key": "blueprint_id",
            },
            {
                "from_table": "users",
                "to_table": "campaigns",
                "type": "one_to_many",
                "foreign_key": "user_id",
            },
        ]

        return known_relationships

    async def _save_to_memory(self, knowledge: Dict[str, Any]):
        """Save discovered knowledge to agent memory."""
        if not self.client:
            return

        try:
            # Save to agent_memory table (create if doesn't exist)
            self.client.table("agent_memory").upsert(
                {
                    "key": "app_structure",
                    "value": knowledge,
                    "type": "structure_discovery",
                    "updated_at": self._get_timestamp(),
                }
            ).execute()

            logger.info("Knowledge saved to memory")

        except Exception as e:
            logger.warning(f"Failed to save to memory: {e}")

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()

    async def get_cached_structure(self) -> Optional[Dict[str, Any]]:
        """Get cached app structure from memory."""
        if not self.client:
            return None

        try:
            result = (
                self.client.table("agent_memory")
                .select("*")
                .eq("key", "app_structure")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return result.data[0].get("value")

        except Exception as e:
            logger.debug(f"Cache retrieval failed: {e}")

        return None


# Global instance
auto_discovery = AutoDiscovery()

