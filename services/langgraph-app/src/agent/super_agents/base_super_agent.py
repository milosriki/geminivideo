"""Base super agent with enhanced thinking and reasoning capabilities."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agent.core.base_agent import BaseAgent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class SuperAgent(BaseAgent):
    """Super agent with enhanced thinking, reasoning, and multi-domain expertise."""

    def __init__(
        self,
        name: str,
        description: str,
        domains: List[str],
        thinking_steps: int = 3,
        **kwargs,
    ):
        super().__init__(name=name, description=description, **kwargs)
        self.domains = domains
        self.thinking_steps = thinking_steps

        # Enhanced prompt with thinking framework
        self.thinking_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=f"""You are {name}, a SUPER AGENT with expertise in: {', '.join(domains)}.

You have enhanced thinking capabilities. When solving problems, you should:

1. THINK STEP BY STEP:
   - Analyze the problem deeply
   - Consider multiple perspectives
   - Evaluate different approaches
   - Reason through implications

2. USE YOUR EXPERTISE:
   - Draw from your knowledge in: {', '.join(domains)}
   - Apply best practices
   - Consider edge cases
   - Think creatively

3. REASON LOGICALLY:
   - Break down complex problems
   - Identify dependencies
   - Consider trade-offs
   - Validate assumptions

4. PROVIDE COMPREHENSIVE SOLUTIONS:
   - Consider all aspects
   - Provide detailed reasoning
   - Include alternatives
   - Explain your thinking

{description}
"""
                ),
                HumanMessage(content="{input}"),
            ]
        )

    async def think(
        self, problem: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced thinking process - reasons through problems step by step."""
        thinking_results = []

        for step in range(self.thinking_steps):
            thinking_prompt = f"""
THINKING STEP {step + 1}/{self.thinking_steps}:

Problem: {problem}
Context: {context}

Current thinking: {thinking_results[-1] if thinking_results else 'Initial analysis'}

Think deeply about:
1. What are the key aspects of this problem?
2. What information do I need?
3. What are possible approaches?
4. What are the implications?

Provide your thinking for this step.
"""

            messages = [HumanMessage(content=thinking_prompt)]
            thinking = await self._call_llm(messages)
            thinking_results.append(thinking)

        # Final synthesis
        synthesis_prompt = f"""
Based on your {self.thinking_steps} thinking steps:

{chr(10).join(f'Step {i+1}: {t}' for i, t in enumerate(thinking_results))}

Synthesize a comprehensive solution:
1. What is the best approach?
2. What are the key decisions?
3. What is the recommended action?
4. What are potential risks or alternatives?
"""

        messages = [HumanMessage(content=synthesis_prompt)]
        final_reasoning = await self._call_llm(messages)

        return {
            "thinking_steps": thinking_results,
            "final_reasoning": final_reasoning,
            "domains_used": self.domains,
        }

    async def _execute_impl(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Any:
        """Execute with enhanced thinking."""
        operation = input_data.get("operation", "think")
        problem = input_data.get("problem", str(input_data))

        # Use thinking framework
        thinking_result = await self.think(problem, context)

        # Execute based on thinking
        result = await self._execute_with_reasoning(
            input_data, context, thinking_result
        )

        return {
            "result": result,
            "thinking": thinking_result,
            "reasoning": thinking_result.get("final_reasoning"),
        }

    async def _execute_with_reasoning(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        thinking: Dict[str, Any],
    ) -> Any:
        """Execute action based on reasoning - override in subclasses."""
        # Default implementation - subclasses should override
        return {"status": "executed", "thinking_applied": True}

