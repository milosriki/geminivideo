"""
Llama 4 Integration for AI Council
Supports Together AI and Fireworks AI providers

Llama 4 Models (2025):
- Meta-Llama-4-Scout-405B: Fastest, most cost-effective
- Meta-Llama-4-Maverick-405B: Higher quality, slightly more expensive

Features:
- Automatic failover between providers
- Structured JSON outputs
- Cost tracking (10x cheaper than GPT-4)
- Optimized for bulk scoring and pre-filtering

Provider APIs:
- Together AI: https://api.together.xyz/v1
- Fireworks AI: https://api.fireworks.ai/inference/v1
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional, Literal
from datetime import datetime

# Use OpenAI client with custom base URLs (both APIs are OpenAI-compatible)
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = logging.getLogger(__name__)


class Llama4ModelType:
    """Llama 4 model variants"""
    # Scout: Fastest, optimized for throughput
    SCOUT = "meta-llama/Meta-Llama-4-Scout-405B-Instruct"
    # Maverick: Higher quality reasoning
    MAVERICK = "meta-llama/Meta-Llama-4-Maverick-405B-Instruct"


class Llama4Provider:
    """Provider endpoints for Llama 4"""
    TOGETHER = "together"
    FIREWORKS = "fireworks"


class Llama4Client:
    """
    Llama 4 Integration Client

    Cost Comparison (per 1M tokens):
    - Llama 4 Scout: ~$0.20 (Together AI)
    - Llama 4 Maverick: ~$0.40 (Fireworks AI)
    - GPT-4o-mini: $0.15-0.60
    - GPT-4o: $3-15

    Use Cases:
    - Bulk script scoring (1000+ scripts)
    - Pre-filtering before expensive models
    - A/B test variations analysis
    - Quick quality checks
    """

    def __init__(
        self,
        preferred_provider: Literal["together", "fireworks"] = "together",
        preferred_model: Literal["scout", "maverick"] = "scout",
        enable_fallback: bool = True
    ):
        """
        Initialize Llama 4 client with multi-provider support

        Args:
            preferred_provider: Primary provider to use
            preferred_model: Which Llama 4 variant to use
            enable_fallback: Enable automatic failover to backup provider
        """
        self.preferred_provider = preferred_provider
        self.preferred_model = preferred_model
        self.enable_fallback = enable_fallback

        # Initialize API clients
        self.together_client = None
        self.fireworks_client = None

        # Together AI setup
        together_key = os.getenv("TOGETHER_API_KEY")
        if together_key and AsyncOpenAI:
            self.together_client = AsyncOpenAI(
                api_key=together_key,
                base_url="https://api.together.xyz/v1"
            )
            logger.info("✅ Together AI client initialized")
        else:
            logger.warning("⚠️ TOGETHER_API_KEY not set")

        # Fireworks AI setup
        fireworks_key = os.getenv("FIREWORKS_API_KEY")
        if fireworks_key and AsyncOpenAI:
            self.fireworks_client = AsyncOpenAI(
                api_key=fireworks_key,
                base_url="https://api.fireworks.ai/inference/v1"
            )
            logger.info("✅ Fireworks AI client initialized")
        else:
            logger.warning("⚠️ FIREWORKS_API_KEY not set")

        # Cost tracking
        self.total_cost = 0.0
        self.request_count = 0
        self.provider_usage = {
            "together": 0,
            "fireworks": 0
        }

        # Model selection
        self.model_id = self._get_model_id()

        if not self.together_client and not self.fireworks_client:
            logger.error("❌ No Llama 4 providers available! Set TOGETHER_API_KEY or FIREWORKS_API_KEY")
        else:
            logger.info(f"🦙 Llama 4 Client Ready: {self.model_id} via {preferred_provider}")

    def _get_model_id(self) -> str:
        """Get the appropriate model ID based on configuration"""
        # Use environment override if set
        override = os.getenv("LLAMA4_MODEL_ID")
        if override:
            return override

        # Otherwise use configured preference
        if self.preferred_model == "scout":
            return Llama4ModelType.SCOUT
        else:
            return Llama4ModelType.MAVERICK

    def _get_active_client(self) -> Optional[AsyncOpenAI]:
        """Get the active client based on preferred provider"""
        if self.preferred_provider == "together" and self.together_client:
            return self.together_client
        elif self.preferred_provider == "fireworks" and self.fireworks_client:
            return self.fireworks_client

        # Fallback to any available
        return self.together_client or self.fireworks_client

    def _get_fallback_client(self) -> Optional[AsyncOpenAI]:
        """Get fallback client (opposite of preferred)"""
        if not self.enable_fallback:
            return None

        if self.preferred_provider == "together" and self.fireworks_client:
            return self.fireworks_client
        elif self.preferred_provider == "fireworks" and self.together_client:
            return self.together_client

        return None

    async def score_script(
        self,
        script: str,
        use_structured_output: bool = True
    ) -> Dict[str, Any]:
        """
        Score an ad script using Llama 4

        Args:
            script: The ad script text to analyze
            use_structured_output: Return structured JSON response

        Returns:
            {
                "score": float (0-100),
                "confidence": float (0-1),
                "reasoning": str,
                "source": str,
                "model": str,
                "provider": str,
                "cost": float
            }
        """
        if not self._get_active_client():
            return {
                "score": 75.0,
                "confidence": 0.5,
                "reasoning": "Llama 4 not available",
                "source": "Llama 4 (Disabled)",
                "error": "No API keys configured"
            }

        # Try primary provider
        result = await self._execute_scoring(
            client=self._get_active_client(),
            provider=self.preferred_provider,
            script=script,
            use_structured_output=use_structured_output
        )

        # If failed and fallback enabled, try backup provider
        if "error" in result and self.enable_fallback:
            fallback_client = self._get_fallback_client()
            if fallback_client:
                fallback_provider = "fireworks" if self.preferred_provider == "together" else "together"
                logger.warning(f"Primary provider failed, trying {fallback_provider}...")

                result = await self._execute_scoring(
                    client=fallback_client,
                    provider=fallback_provider,
                    script=script,
                    use_structured_output=use_structured_output
                )

        return result

    async def _execute_scoring(
        self,
        client: AsyncOpenAI,
        provider: str,
        script: str,
        use_structured_output: bool
    ) -> Dict[str, Any]:
        """
        Execute scoring with specific provider

        Args:
            client: OpenAI client instance
            provider: Provider name (together/fireworks)
            script: Script to analyze
            use_structured_output: Use structured JSON response
        """
        try:
            # Build prompt for scoring
            if use_structured_output:
                system_prompt = """You are an Expert Viral Ad Analyst specializing in social media content.

Analyze ad scripts for viral potential based on:
1. Hook Strength: Pattern interrupt, curiosity gap, immediate attention grab
2. Emotional Resonance: Psychological triggers, relatability
3. Clarity: Clear value proposition and call-to-action
4. Pacing: Content flow and retention mechanics
5. Viral Elements: Shareability, trend alignment

Provide scores and reasoning in JSON format."""

                user_prompt = f"""Analyze this ad script and rate its viral potential.

SCRIPT:
{script}

Return JSON with:
- score (0-100): Overall viral potential
- confidence (0-1): How confident you are in this score
- reasoning (string): Brief explanation of score

Response format:
{{
  "score": 85,
  "confidence": 0.9,
  "reasoning": "Strong hook with curiosity gap..."
}}"""
            else:
                # Simple scoring without structured output
                user_prompt = f"""Rate this ad script's viral potential from 0-100.

SCRIPT:
{script}

Return ONLY the score as a number (0-100)."""
                system_prompt = "You are a viral ad expert. Score ad scripts 0-100 for viral potential."

            # Make API call
            response = await client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500 if use_structured_output else 50,
                response_format={"type": "json_object"} if use_structured_output else None
            )

            content = response.choices[0].message.content.strip()

            # Parse response
            if use_structured_output:
                try:
                    parsed = json.loads(content)
                    score = float(parsed.get("score", 75.0))
                    confidence = float(parsed.get("confidence", 0.8))
                    reasoning = parsed.get("reasoning", "Analysis completed")
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse structured output: {e}")
                    score = 75.0
                    confidence = 0.7
                    reasoning = content[:200] if content else "Parse error"
            else:
                # Extract number from response
                numbers = re.findall(r'(?<![.\d])\d{1,3}(?:\.\d+)?(?![.\d])', content)
                valid_scores = [float(n) for n in numbers if 0 <= float(n) <= 100]
                score = valid_scores[0] if valid_scores else 75.0
                confidence = 0.8
                reasoning = "Simple scoring completed"

            # Clamp score to valid range
            score = max(0.0, min(100.0, score))
            confidence = max(0.0, min(1.0, confidence))

            # Calculate cost
            input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
            output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
            cost = self._calculate_cost(provider, input_tokens, output_tokens)

            # Update tracking
            self.total_cost += cost
            self.request_count += 1
            self.provider_usage[provider] += 1

            model_name = "Scout" if "Scout" in self.model_id else "Maverick"

            return {
                "score": score,
                "confidence": confidence,
                "reasoning": reasoning,
                "source": f"Llama 4 {model_name}",
                "model": self.model_id,
                "provider": provider,
                "cost": cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }

        except Exception as e:
            logger.error(f"Llama 4 execution failed on {provider}: {e}")
            return {
                "score": 75.0,
                "confidence": 0.5,
                "reasoning": f"Error: {str(e)}",
                "source": f"Llama 4 ({provider} - Failed)",
                "provider": provider,
                "error": str(e)
            }

    def _calculate_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for Llama 4 inference

        Pricing (approximate per 1M tokens):
        - Together AI (Scout): $0.20 input, $0.20 output
        - Fireworks AI (Scout): $0.20 input, $0.20 output
        - Together AI (Maverick): $0.40 input, $0.40 output
        - Fireworks AI (Maverick): $0.40 input, $0.40 output
        """
        # Determine rate based on model type
        if "Scout" in self.model_id:
            rate_per_million = 0.20
        else:  # Maverick
            rate_per_million = 0.40

        input_cost = (input_tokens / 1_000_000) * rate_per_million
        output_cost = (output_tokens / 1_000_000) * rate_per_million

        return input_cost + output_cost

    async def batch_score_scripts(self, scripts: list[str]) -> list[Dict[str, Any]]:
        """
        Score multiple scripts efficiently

        Args:
            scripts: List of script strings

        Returns:
            List of scoring results
        """
        import asyncio

        tasks = [self.score_script(script) for script in scripts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch script {i} failed: {result}")
                processed_results.append({
                    "score": 75.0,
                    "confidence": 0.5,
                    "reasoning": f"Error: {str(result)}",
                    "source": "Llama 4 (Batch Error)"
                })
            else:
                processed_results.append(result)

        return processed_results

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics and cost metrics"""
        avg_cost = self.total_cost / self.request_count if self.request_count > 0 else 0

        return {
            "total_requests": self.request_count,
            "total_cost": round(self.total_cost, 6),
            "avg_cost_per_request": round(avg_cost, 6),
            "provider_usage": self.provider_usage,
            "model": self.model_id,
            "preferred_provider": self.preferred_provider,
            "cost_vs_gpt4o_mini": round((avg_cost / 0.0003) * 100, 2) if avg_cost > 0 else 0  # % of GPT-4o-mini cost
        }

    def reset_stats(self):
        """Reset usage statistics"""
        self.total_cost = 0.0
        self.request_count = 0
        self.provider_usage = {
            "together": 0,
            "fireworks": 0
        }


# Global instance
llama4_client = Llama4Client(
    preferred_provider=os.getenv("LLAMA4_PROVIDER", "together"),
    preferred_model=os.getenv("LLAMA4_VARIANT", "scout"),
    enable_fallback=os.getenv("LLAMA4_ENABLE_FALLBACK", "true").lower() == "true"
)
