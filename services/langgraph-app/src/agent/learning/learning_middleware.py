"""Learning middleware - learns from every interaction."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.learning.auto_discover import auto_discovery
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class LearningMiddleware:
    """Middleware that learns from every agent interaction."""

    def __init__(self):
        self.client = supabase_client.client

    async def before_agent_execution(
        self, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run before agent execution - load app knowledge."""
        try:
            # 1. Load cached structure or discover fresh
            cached = await auto_discovery.get_cached_structure()

            if not cached:
                # Discover fresh if no cache
                cached = await auto_discovery.discover_app_structure()

            # 2. Add to state context
            if cached:
                state["app_knowledge"] = {
                    "tables": cached.get("tables", []),
                    "functions": cached.get("functions", []),
                    "recent_patterns": cached.get("recent_patterns", {}),
                    "relationships": cached.get("relationships", []),
                }

                # Create system message with knowledge
                knowledge_summary = self._create_knowledge_summary(cached)
                state["system_context"] = knowledge_summary

            logger.debug("App knowledge loaded into state")

        except Exception as e:
            logger.error(f"Error loading knowledge: {e}", exc_info=True)

        return state

    async def after_agent_execution(
        self,
        state: Dict[str, Any],
        agent_name: str,
        result: Any,
        execution_time: float,
    ):
        """Run after agent execution - learn from it."""
        try:
            # Extract question/input
            question = state.get("input_data", {}).get("operation", "unknown")
            input_data = state.get("input_data", {})

            # Extract answer/result
            answer = result if isinstance(result, str) else str(result)

            # 1. Save to permanent memory
            await self._save_interaction(
                agent_name=agent_name,
                question=question,
                input_data=input_data,
                answer=answer,
                execution_time=execution_time,
                success=result is not None,
            )

            # 2. Extract patterns
            patterns = await self._extract_patterns(
                agent_name, question, answer, result
            )

            # 3. Update agent memory
            await self._update_agent_memory(agent_name, patterns)

            logger.info(f"✅ Learned from {agent_name}: {question[:50]}")

        except Exception as e:
            logger.error(f"Error saving learning: {e}", exc_info=True)

    async def _save_interaction(
        self,
        agent_name: str,
        question: str,
        input_data: Dict[str, Any],
        answer: Any,
        execution_time: float,
        success: bool,
    ):
        """Save interaction to memory."""
        if not self.client:
            return

        try:
            # Prepare embeddings (would use OpenAI embeddings in production)
            # For now, store without embeddings
            interaction = {
                "agent_name": agent_name,
                "thread_id": input_data.get("thread_id", "default"),
                "query": question,
                "input_data": input_data,
                "response": str(answer),
                "execution_time": execution_time,
                "success": success,
                "created_at": self._get_timestamp(),
            }

            # Save to agent_memory table
            self.client.table("agent_memory").insert(interaction).execute()

        except Exception as e:
            logger.warning(f"Failed to save interaction: {e}")

    async def _extract_patterns(
        self, agent_name: str, question: str, answer: str, result: Any
    ) -> Dict[str, Any]:
        """Extract patterns from interaction."""
        patterns = {
            "agent": agent_name,
            "question_type": self._classify_question(question),
            "answer_length": len(str(answer)),
            "has_data": result is not None and result != {},
            "execution_successful": result is not None,
        }

        # Extract entities if possible
        if isinstance(result, dict):
            patterns["result_keys"] = list(result.keys())
            patterns["result_type"] = type(result).__name__

        return patterns

    def _classify_question(self, question: str) -> str:
        """Classify question type."""
        question_lower = question.lower()

        if "analyze" in question_lower or "analysis" in question_lower:
            return "analysis"
        elif "generate" in question_lower or "create" in question_lower:
            return "generation"
        elif "optimize" in question_lower or "improve" in question_lower:
            return "optimization"
        elif "predict" in question_lower or "forecast" in question_lower:
            return "prediction"
        elif "query" in question_lower or "get" in question_lower:
            return "query"
        else:
            return "general"

    async def _update_agent_memory(
        self, agent_name: str, patterns: Dict[str, Any]
    ):
        """Update agent-specific memory."""
        if not self.client:
            return

        try:
            # Update or create agent memory entry
            self.client.table("agent_memory").upsert(
                {
                    "key": f"agent_patterns_{agent_name}",
                    "value": patterns,
                    "type": "agent_patterns",
                    "updated_at": self._get_timestamp(),
                }
            ).execute()

        except Exception as e:
            logger.debug(f"Failed to update agent memory: {e}")

    def _create_knowledge_summary(self, knowledge: Dict[str, Any]) -> str:
        """Create human-readable knowledge summary."""
        tables = knowledge.get("tables", [])
        functions = knowledge.get("functions", [])
        patterns = knowledge.get("recent_patterns", {})

        summary = f"""
CURRENT APP STRUCTURE (Auto-discovered):

TABLES ({len(tables)}): {', '.join([t.get('name', '') for t in tables[:10]])}
FUNCTIONS ({len(functions)}): {', '.join([f.get('name', '') for f in functions[:10]])}

RECENT PATTERNS:
{self._format_patterns(patterns)}

Use this knowledge to answer questions accurately.
        """.strip()

        return summary

    def _format_patterns(self, patterns: Dict[str, Any]) -> str:
        """Format patterns for display."""
        if not patterns:
            return "No recent patterns discovered."

        lines = []
        for table, data in patterns.items():
            sample_count = data.get("sample_count", 0)
            columns = data.get("columns", [])
            lines.append(
                f"  {table}: {sample_count} samples, columns: {', '.join(columns[:5])}"
            )

        return "\n".join(lines) if lines else "No patterns"

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()


# Global instance
learning_middleware = LearningMiddleware()

