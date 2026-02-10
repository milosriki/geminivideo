"""Supabase client for agent persistence."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from supabase import create_client, Client
except ImportError:
    # Fallback if supabase-py not installed
    Client = None
    create_client = None

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except Exception:
    pass


class SupabaseClient:
    """Supabase client for agent data persistence."""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize()

    def _initialize(self):
        """Initialize Supabase client."""
        if create_client is None:
            if logger:
                logger.warning("supabase-py not installed, using mock client")
            return

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            if logger:
                logger.warning("Supabase credentials not found, using mock client")
            return

        try:
            self.client = create_client(supabase_url, supabase_key)
            if logger:
                logger.info("Supabase client initialized")
        except Exception as e:
            if logger:
                logger.error(f"Failed to initialize Supabase: {e}")

    def save_agent_execution(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: float,
    ) -> bool:
        """Save agent execution to Supabase."""
        if not self.client:
            return False

        try:
            self.client.table("agent_executions").insert({
                "agent_name": agent_name,
                "input_data": input_data,
                "result": result,
                "execution_time": execution_time,
            }).execute()
            return True
        except Exception as e:
            if logger:
                logger.error(f"Failed to save execution: {e}")
            return False

    def get_agent_memory(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent memory from Supabase."""
        if not self.client:
            return None

        try:
            response = self.client.table("agent_memories").select("*").eq(
                "agent_name", agent_name
            ).order("created_at", desc=True).limit(1).execute()

            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            if logger:
                logger.error(f"Failed to get memory: {e}")
            return None

    def save_agent_memory(
        self, agent_name: str, memory: Dict[str, Any]
    ) -> bool:
        """Save agent memory to Supabase."""
        if not self.client:
            return False

        try:
            self.client.table("agent_memories").upsert({
                "agent_name": agent_name,
                "memory": memory,
            }).execute()
            return True
        except Exception as e:
            if logger:
                logger.error(f"Failed to save memory: {e}")
            return False

    def get_learned_patterns(self) -> List[Dict[str, Any]]:
        """Get learned patterns from all agents."""
        if not self.client:
            return []

        try:
            response = self.client.table("learned_patterns").select("*").execute()
            return response.data or []
        except Exception as e:
            if logger:
                logger.error(f"Failed to get patterns: {e}")
            return []


# Global Supabase client instance
supabase_client = SupabaseClient()

