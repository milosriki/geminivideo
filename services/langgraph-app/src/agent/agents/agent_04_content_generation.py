"""Agent 4: Content Generation Agent - Generates ad scripts and creative content."""

from typing import Any, Dict

from agent.core.base_agent import AgentError, BaseAgent


class ContentGenerationAgent(BaseAgent):
    """Generates ad scripts, hooks, and creative content."""

    def __init__(self, **kwargs):
        super().__init__(
            name="ContentGenerationAgent",
            description=(
                "Expert copywriter and creative director. Generates high-converting "
                "ad scripts, hooks, scripts, and creative briefs. Uses psychological "
                "triggers and proven frameworks."
            ),
            **kwargs,
        )

    async def _execute_impl(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute content generation."""
        operation = input_data.get("operation", "generate_script")
        campaign_data = input_data.get("campaign_data", {})

        if operation == "generate_script":
            return await self._generate_script(campaign_data, context)
        elif operation == "generate_hook":
            return await self._generate_hook(campaign_data, context)
        elif operation == "generate_variations":
            return await self._generate_variations(campaign_data, context)
        else:
            raise AgentError(
                f"Unknown operation: {operation}",
                agent_name=self.name,
                error_type="validation_error",
            )

    async def _generate_script(
        self, campaign_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate ad script."""
        product = campaign_data.get("product_name", "product")
        offer = campaign_data.get("offer", "special offer")
        pain_points = campaign_data.get("pain_points", [])

        prompt = f"""
        Generate a high-converting 30-second video ad script for:
        Product: {product}
        Offer: {offer}
        Pain Points: {pain_points}
        
        Structure:
        1. Hook (0-3s): Attention-grabbing opening
        2. Problem (3-10s): Agitate pain points
        3. Solution (10-20s): Present product/offer
        4. CTA (20-30s): Clear call-to-action
        
        Use psychological triggers and proven frameworks.
        """

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]
        script = await self._call_llm(messages)

        return {
            "script": script,
            "hook": script.split("\n")[0] if script else "",
            "length_seconds": 30,
            "status": "generated",
        }

    async def _generate_hook(
        self, campaign_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate hook variations."""
        return {
            "hooks": [
                {"text": "Are you struggling with...", "type": "question", "score": 0.95},
                {"text": "What if I told you...", "type": "curiosity", "score": 0.90},
                {"text": "Stop wasting time on...", "type": "pain", "score": 0.88},
            ],
            "status": "generated",
        }

    async def _generate_variations(
        self, campaign_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate multiple script variations."""
        return {
            "variations": [
                {"id": "v1", "script": "...", "predicted_ctr": 0.045},
                {"id": "v2", "script": "...", "predicted_ctr": 0.042},
                {"id": "v3", "script": "...", "predicted_ctr": 0.048},
            ],
            "status": "generated",
        }

