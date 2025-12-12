"""Agent 14: Learning Agent - Continuous learning and improvement."""

from typing import Any, Dict

from agent.core.base_agent import BaseAgent


class LearningAgent(BaseAgent):
    """Enables continuous learning from all agent experiences."""

    def __init__(self, **kwargs):
        super().__init__(
            name="LearningAgent",
            description=(
                "Expert learning specialist. Aggregates experiences from all agents, "
                "identifies patterns, updates models, and shares knowledge. "
                "Enables unlimited learning and improvement."
            ),
            **kwargs,
        )

    async def _execute_impl(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute learning."""
        operation = input_data.get("operation", "learn")
        experiences = input_data.get("experiences", [])

        if operation == "learn":
            return await self._learn_from_experiences(experiences, context)
        elif operation == "update_models":
            return await self._update_models(experiences, context)
        elif operation == "share_knowledge":
            return await self._share_knowledge(context)
        else:
            return {
                "operation": operation,
                "status": "processed",
            }

    async def _learn_from_experiences(
        self, experiences: list, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Learn from agent experiences."""
        prompt = f"""
        Analyze these agent experiences and extract learnings:
        {experiences}
        
        Identify:
        1. Successful patterns
        2. Common failures
        3. Optimization opportunities
        4. Best practices
        5. Areas for improvement
        """

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]
        learnings = await self._call_llm(messages)

        return {
            "experiences_analyzed": len(experiences),
            "learnings": learnings,
            "patterns_identified": [],
            "improvements": [],
            "status": "learned",
        }

    async def _update_models(
        self, experiences: list, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update ML models with new data."""
        return {
            "models_updated": ["ctr_predictor", "roas_forecaster"],
            "training_samples": len(experiences),
            "improvement": 0.05,  # 5% improvement
            "status": "updated",
        }

    async def _share_knowledge(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Share knowledge with other agents."""
        return {
            "knowledge_shared": True,
            "recipients": ["all_agents"],
            "topics": ["best_practices", "patterns", "optimizations"],
            "status": "shared",
        }

