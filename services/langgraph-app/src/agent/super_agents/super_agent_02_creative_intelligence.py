"""Super Agent 2: Creative Intelligence - Content, Video, Creative Analysis."""

from typing import Any, Dict

from agent.super_agents.base_super_agent import SuperAgent


class CreativeIntelligenceAgent(SuperAgent):
    """Super agent for creative intelligence, content generation, and video analysis."""

    def __init__(self, **kwargs):
        super().__init__(
            name="CreativeIntelligenceAgent",
            description=(
                "Expert in creative content generation, video analysis, creative "
                "strategy, and content optimization. Thinks deeply about creative "
                "solutions and psychological triggers."
            ),
            domains=[
                "Content Generation",
                "Video Analysis",
                "Creative Strategy",
                "Copywriting",
                "Visual Design",
                "Psychological Triggers",
            ],
            thinking_steps=4,
            **kwargs,
        )

    async def _execute_with_reasoning(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        thinking: Dict[str, Any],
    ) -> Any:
        """Execute creative intelligence operations."""
        operation = input_data.get("operation", "generate")

        if operation == "generate_content":
            return await self._generate_content(input_data, thinking)
        elif operation == "analyze_video":
            return await self._analyze_video(input_data, thinking)
        elif operation == "analyze_creative":
            return await self._analyze_creative(input_data, thinking)
        elif operation == "optimize_creative":
            return await self._optimize_creative(input_data, thinking)
        else:
            return {
                "operation": operation,
                "thinking": thinking.get("final_reasoning"),
                "status": "processed",
            }

    async def _generate_content(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content with deep creative thinking."""
        campaign_data = input_data.get("campaign_data", {})
        reasoning = thinking.get("final_reasoning", "")

        # Use reasoning to create better content
        prompt = f"""
        Based on this reasoning: {reasoning}
        
        Generate high-converting content for:
        {campaign_data}
        
        Apply creative thinking and psychological triggers.
        """

        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=prompt)]
        content = await self._call_llm(messages)

        return {
            "content": content,
            "reasoning": reasoning,
            "creative_elements": [],
            "status": "generated",
        }

    async def _analyze_video(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze video with intelligent reasoning."""
        video_url = input_data.get("video_url")

        return {
            "video_url": video_url,
            "analysis": thinking.get("final_reasoning"),
            "scenes": [],
            "emotions": [],
            "hooks": [],
            "status": "analyzed",
        }

    async def _analyze_creative(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze creative with deep thinking."""
        creative_data = input_data.get("creative_data", {})

        return {
            "creative_data": creative_data,
            "analysis": thinking.get("final_reasoning"),
            "scores": {},
            "recommendations": [],
            "status": "analyzed",
        }

    async def _optimize_creative(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize creative using reasoning."""
        return {
            "optimizations": [],
            "reasoning": thinking.get("final_reasoning"),
            "expected_improvement": 0.0,
            "status": "optimized",
        }

