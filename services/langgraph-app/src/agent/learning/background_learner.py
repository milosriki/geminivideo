"""Background learning system - learns continuously from app changes."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from agent.learning.auto_discover import auto_discovery
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class BackgroundLearner:
    """Learns from entire app hourly - unlimited learning."""

    def __init__(self, interval_hours: int = 1):
        self.interval_hours = interval_hours
        self.client = supabase_client.client
        self.running = False

    async def start(self):
        """Start background learning loop."""
        self.running = True
        logger.info("Background learner started")

        while self.running:
            try:
                await self._learn_cycle()
                await asyncio.sleep(self.interval_hours * 3600)  # Wait interval
            except Exception as e:
                logger.error(f"Learning cycle error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def stop(self):
        """Stop background learning."""
        self.running = False
        logger.info("Background learner stopped")

    async def _learn_cycle(self):
        """Execute one learning cycle."""
        logger.info("Starting learning cycle...")

        try:
            # 1. Rediscover structure
            structure = await auto_discovery.discover_app_structure()

            # 2. Learn recent changes
            changes = await self._discover_recent_changes()

            # 3. Extract patterns
            patterns = await self._extract_patterns(changes)

            # 4. Save to agent memory
            await self._save_learning(structure, changes, patterns)

            logger.info("✅ Unlimited learning cycle complete")

        except Exception as e:
            logger.error(f"Learning cycle failed: {e}", exc_info=True)

    async def _discover_recent_changes(self) -> Dict[str, Any]:
        """Discover recent changes in key tables."""
        if not self.client:
            return {}

        changes = {}
        cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()

        # Key tables to monitor
        key_tables = [
            "campaign_performance",
            "lead_tracking",
            "videos",
            "campaigns",
            "blueprints",
        ]

        for table_name in key_tables:
            try:
                result = (
                    self.client.table(table_name)
                    .select("*")
                    .gte("created_at", cutoff_time)
                    .limit(100)
                    .execute()
                )

                if result.data:
                    changes[table_name] = {
                        "count": len(result.data),
                        "recent_items": result.data[:5],  # Sample 5
                    }

            except Exception as e:
                logger.debug(f"Change discovery for {table_name} failed: {e}")

        return changes

    async def _extract_patterns(
        self, changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract patterns from changes."""
        patterns = {
            "total_changes": sum(c.get("count", 0) for c in changes.values()),
            "active_tables": list(changes.keys()),
            "change_distribution": {
                table: data.get("count", 0) for table, data in changes.items()
            },
        }

        # Analyze patterns in recent items
        for table, data in changes.items():
            recent_items = data.get("recent_items", [])
            if recent_items:
                # Extract common fields/values
                sample_item = recent_items[0]
                patterns[f"{table}_fields"] = list(sample_item.keys())

        return patterns

    async def _save_learning(
        self,
        structure: Dict[str, Any],
        changes: Dict[str, Any],
        patterns: Dict[str, Any],
    ):
        """Save learning to memory."""
        if not self.client:
            return

        try:
            learning_data = {
                "key": f"daily_learning_{datetime.now().isoformat()}",
                "value": {
                    "structure": structure,
                    "recent_changes": changes,
                    "patterns": patterns,
                    "learned_at": datetime.now().isoformat(),
                },
                "type": "daily_discovery",
                "created_at": datetime.now().isoformat(),
            }

            self.client.table("agent_memory").insert(learning_data).execute()

            logger.info("Learning saved to memory")

        except Exception as e:
            logger.error(f"Failed to save learning: {e}", exc_info=True)

    async def run_once(self):
        """Run learning cycle once (for cron jobs)."""
        await self._learn_cycle()


# Global instance
background_learner = BackgroundLearner(interval_hours=1)

