"""
Integration of Smart Router with Existing Ensemble System

This module provides drop-in replacements for existing model calls
with intelligent routing capabilities.
"""

import logging
from typing import Dict, Any, Optional

from .model_router import router, TaskComplexity
from .analytics import analytics
from .ab_testing import ab_test_manager

logger = logging.getLogger(__name__)


class SmartEnsembleEvaluator:
    """
    Drop-in replacement for CouncilEvaluator with smart routing

    Usage:
        # Instead of:
        # from backend_core.engines.ensemble import council

        # Use:
        # from backend_core.routing.integration import smart_council

        # API is exactly the same:
        # result = await smart_council.evaluate_script(script, niche)
    """

    def __init__(self):
        """Initialize smart evaluator with routing"""
        self.router = router
        self.analytics = analytics
        self.ab_test_manager = ab_test_manager

    async def evaluate_script(
        self,
        script_content: str,
        niche: str = "fitness",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate script with smart routing

        This method maintains the same API as the original CouncilEvaluator
        but uses intelligent model routing under the hood.

        Args:
            script_content: The script/content to evaluate
            niche: Business vertical (fitness, e-commerce, etc.)
            user_id: Optional user ID for A/B test assignment

        Returns:
            Same format as original CouncilEvaluator:
            {
                "verdict": "APPROVED" | "NEEDS_REVISION",
                "final_score": float (0-100),
                "breakdown": {...},
                "feedback": str,
                "confidence": float,
                "timestamp": str,

                # Additional routing metadata:
                "_routing_metadata": {
                    "model_used": str,
                    "complexity": str,
                    "cost": float,
                    "escalated": bool
                }
            }
        """
        # Create task metadata
        task = {
            "text": script_content,
            "type": "creative",  # Script evaluation is creative work
            "niche": niche,
            "requirements": {
                "creative_reasoning": True,
                "deep_analysis": True
            }
        }

        # A/B testing: assign strategy
        strategy = self.ab_test_manager.assign_strategy(user_id)
        if self.ab_test_manager.enabled:
            task = self.ab_test_manager.apply_strategy(strategy, task, "complex")
            logger.info(f"A/B Test: Using strategy {strategy.value}")

        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(script_content, niche)

        # Response format for structured output
        response_format = {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Step-by-step analysis"
                },
                "score": {
                    "type": "number",
                    "description": "Final score from 0-100"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence in the score (0-1)"
                },
                "feedback": {
                    "type": "string",
                    "description": "Actionable feedback"
                }
            },
            "required": ["reasoning", "score", "confidence", "feedback"]
        }

        # Route and execute
        result = await self.router.route_and_execute(
            task=task,
            prompt=prompt,
            response_format=response_format
        )

        # Parse structured response
        try:
            import json
            parsed = json.loads(result["result"])
            score = float(parsed["score"])
            feedback = parsed.get("feedback", "")
            reasoning = parsed.get("reasoning", "")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse structured response: {e}")
            # Fallback
            score = 70.0
            feedback = "Unable to parse evaluation"
            reasoning = result["result"]

        # Determine verdict (same threshold logic as original)
        threshold = self._get_threshold_for_niche(niche)
        verdict = "APPROVED" if score >= threshold else "NEEDS_REVISION"

        # Build response in original format
        response = {
            "verdict": verdict,
            "final_score": round(score, 2),
            "breakdown": {
                result["model_used"]: round(score, 2)
            },
            "feedback": feedback,
            "confidence": round(result["confidence"], 2),
            "timestamp": result["timestamp"],

            # Additional routing metadata
            "_routing_metadata": {
                "model_used": result["model_used"],
                "complexity": result["complexity"],
                "cost": result["cost"],
                "escalated": result.get("escalated", False),
                "execution_time": result.get("execution_time", 0)
            }
        }

        # Log to analytics
        self.analytics.log_request(task, result)

        # Log to A/B testing
        if self.ab_test_manager.enabled:
            self.ab_test_manager.log_result(strategy, task, result)

        return response

    def _build_evaluation_prompt(self, script: str, niche: str) -> str:
        """Build comprehensive evaluation prompt"""
        return f"""You are a world-class creative director and advertising expert evaluating an ad script for the {niche} industry.

Script to evaluate:
{script}

Think step by step and rate this script on a scale of 0-100 based on:

1. Hook strength (first 3 seconds) - 30 points
   - Does it grab attention immediately?
   - Is it relevant to the target audience?

2. Emotional resonance - 25 points
   - Does it tap into pain points or desires?
   - Does it create an emotional connection?

3. Clarity of value proposition - 20 points
   - Is the benefit clear and compelling?
   - Does it answer "what's in it for me?"

4. Call-to-action effectiveness - 15 points
   - Is the CTA clear and actionable?
   - Is there urgency or scarcity?

5. Overall virality potential - 10 points
   - Is it shareable?
   - Does it have social proof potential?

Provide:
1. Detailed reasoning for each criterion
2. Final score (0-100)
3. Confidence in your evaluation (0-1)
4. Actionable feedback for improvement

Respond in JSON format with: reasoning, score, confidence, feedback"""

    def _get_threshold_for_niche(self, niche: str) -> float:
        """Get approval threshold for specific niche"""
        thresholds = {
            "fitness": 85.0,
            "e-commerce": 82.0,
            "education": 88.0,
            "finance": 90.0,
            "entertainment": 80.0,
            "default": 85.0
        }
        return thresholds.get(niche, thresholds["default"])


class SmartSingleModelExecutor:
    """
    Smart executor for single model calls with routing

    Usage:
        executor = SmartSingleModelExecutor()
        result = await executor.execute(
            text="Analyze this...",
            task_type="analysis",
            prompt_template="You are an expert analyst..."
        )
    """

    def __init__(self):
        """Initialize executor"""
        self.router = router
        self.analytics = analytics

    async def execute(
        self,
        text: str,
        task_type: str = "general",
        prompt_template: Optional[str] = None,
        response_format: Optional[Dict] = None,
        complexity_hint: Optional[TaskComplexity] = None
    ) -> Dict[str, Any]:
        """
        Execute single task with smart routing

        Args:
            text: Input text to process
            task_type: Type of task (score, classify, creative, etc.)
            prompt_template: Optional prompt template
            response_format: Optional JSON schema
            complexity_hint: Optional complexity override

        Returns:
            {
                "result": str or dict,
                "model_used": str,
                "cost": float,
                "confidence": float,
                "metadata": {...}
            }
        """
        # Build task
        task = {
            "text": text,
            "type": task_type
        }

        if complexity_hint:
            task["complexity_override"] = complexity_hint.value

        # Build prompt
        if prompt_template:
            prompt = prompt_template.format(text=text)
        else:
            prompt = text

        # Route and execute
        result = await self.router.route_and_execute(
            task=task,
            prompt=prompt,
            response_format=response_format
        )

        # Log analytics
        self.analytics.log_request(task, result)

        return result


# Global instances
smart_council = SmartEnsembleEvaluator()
smart_executor = SmartSingleModelExecutor()
