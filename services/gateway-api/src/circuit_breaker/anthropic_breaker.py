"""
Anthropic Claude Circuit Breaker
=================================

Circuit breaker for Anthropic Claude API with failover to GPT-4o or Gemini.

Handles:
- Claude 3.5 Sonnet, Claude 3 Opus calls
- Automatic failover to OpenAI GPT-4 or Google Gemini
- Request/response caching
- Rate limit handling

Author: Agent 9 - Circuit Breaker Builder
"""

import os
import logging
import asyncio
from typing import Any, Dict, Optional, List
import hashlib
import json

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, registry
from .fallback_handler import FallbackHandler, FallbackConfig
from .health_monitor import HealthMonitor, HealthCheckConfig

logger = logging.getLogger(__name__)


class AnthropicCircuitBreaker:
    """
    Circuit breaker specifically for Anthropic Claude API

    Features:
    - Automatic failover to GPT-4 or Gemini
    - Request caching
    - Cost tracking
    """

    def __init__(
        self,
        anthropic_client: Any,
        openai_client: Optional[Any] = None,
        gemini_client: Optional[Any] = None
    ):
        """
        Initialize Anthropic circuit breaker

        Args:
            anthropic_client: Anthropic API client instance
            openai_client: Optional OpenAI client for failover
            gemini_client: Optional Google Gemini client for failover
        """
        self.anthropic_client = anthropic_client
        self.openai_client = openai_client
        self.gemini_client = gemini_client

        # Create circuit breaker
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=60.0,
            exponential_backoff=True,
            max_timeout_seconds=300.0,
        )

        self.breaker = registry.register(
            name="anthropic_api",
            config=config,
            fallback=self._fallback_handler
        )

        # Fallback handler
        self.fallback_handler = FallbackHandler(
            config=FallbackConfig(
                cache_enabled=True,
                cache_ttl_seconds=3600,
                queue_enabled=True,
                max_queue_size=500
            )
        )

        # Track costs
        self._total_cost = 0.0
        self._fallback_used_count = 0

        logger.info("Anthropic circuit breaker initialized")

    async def _fallback_handler(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Fallback handler when Claude fails
        Tries: GPT-4 -> Gemini -> Cached response -> Error
        """
        logger.warning("Claude circuit OPEN, attempting failover")

        # Try GPT-4 first (similar quality to Claude)
        if self.openai_client:
            try:
                logger.info("Failing over to GPT-4")
                result = await self._call_openai(*args, **kwargs)
                self._fallback_used_count += 1
                return {
                    **result,
                    "_fallback": "openai",
                    "_original_provider": "anthropic"
                }
            except Exception as e:
                logger.warning(f"GPT-4 failover failed: {str(e)}")

        # Try Gemini second
        if self.gemini_client:
            try:
                logger.info("Failing over to Gemini")
                result = await self._call_gemini(*args, **kwargs)
                self._fallback_used_count += 1
                return {
                    **result,
                    "_fallback": "gemini",
                    "_original_provider": "anthropic"
                }
            except Exception as e:
                logger.warning(f"Gemini failover failed: {str(e)}")

        raise Exception("All AI providers unavailable (Claude, GPT-4, Gemini)")

    async def create_message(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Claude with circuit breaker protection

        Args:
            messages: List of messages
            model: Claude model to use
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            system: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Response dict with content, model, usage, etc.
        """
        # Generate cache key
        cache_key = self._generate_cache_key(messages, model, temperature, system)

        # Try cache first
        cached = self.fallback_handler.get_from_cache("anthropic", cache_key)
        if cached:
            logger.info("Cache hit for Claude message")
            return cached.data

        # Execute with circuit breaker
        async def _execute():
            import anthropic

            try:
                response = await self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    temperature=temperature,
                    system=system,
                    **kwargs
                )

                # Extract response
                result = {
                    "content": response.content[0].text,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    "stop_reason": response.stop_reason
                }

                # Track cost
                cost = self._calculate_cost(model, response.usage)
                self._total_cost += cost
                result["cost_usd"] = cost

                # Cache successful response
                self.fallback_handler.save_to_cache("anthropic", cache_key, result)

                return result

            except anthropic.RateLimitError as e:
                logger.warning(f"Claude rate limit hit: {str(e)}")
                raise

            except anthropic.APIError as e:
                logger.error(f"Claude API error: {str(e)}")
                raise

        return await self.breaker.call(_execute)

    async def _call_openai(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Failover to OpenAI GPT-4"""
        import openai

        # Convert messages format if needed
        openai_messages = []

        if system:
            openai_messages.append({"role": "system", "content": system})

        openai_messages.extend(messages)

        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1024)
        )

        return {
            "content": response.choices[0].message.content,
            "model": "gpt-4o",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "stop_reason": response.choices[0].finish_reason
        }

    async def _call_gemini(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Failover to Gemini"""
        import google.generativeai as genai

        # Convert messages to Gemini format
        prompt_parts = []

        if system:
            prompt_parts.append(f"SYSTEM: {system}")

        for msg in messages:
            role_prefix = f"{msg['role'].upper()}: "
            prompt_parts.append(f"{role_prefix}{msg['content']}")

        prompt = "\n\n".join(prompt_parts)

        model = genai.GenerativeModel('gemini-2.0-flash')
        response = await model.generate_content_async(prompt)

        return {
            "content": response.text,
            "model": "gemini-2.0-flash",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "stop_reason": "stop"
        }

    def _generate_cache_key(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        system: Optional[str]
    ) -> str:
        """Generate cache key from request parameters"""
        key_data = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "system": system
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _calculate_cost(self, model: str, usage: Any) -> float:
        """Calculate cost in USD for the API call"""
        # Pricing per 1M tokens (as of 2024)
        pricing = {
            "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        }

        rates = pricing.get(model, pricing["claude-3-5-sonnet-20241022"])

        input_cost = (usage.input_tokens / 1_000_000) * rates["input"]
        output_cost = (usage.output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        return {
            **self.breaker.get_metrics(),
            "total_cost_usd": round(self._total_cost, 4),
            "fallback_used_count": self._fallback_used_count,
            "fallback_stats": self.fallback_handler.get_stats()
        }

    def reset(self):
        """Reset circuit breaker and metrics"""
        self.breaker.reset()
        self._total_cost = 0.0
        self._fallback_used_count = 0


async def setup_anthropic_health_check(
    breaker: AnthropicCircuitBreaker,
    health_monitor: HealthMonitor
):
    """
    Setup health check for Anthropic API

    Args:
        breaker: Anthropic circuit breaker instance
        health_monitor: Health monitor instance
    """
    async def check_claude_health() -> bool:
        """Simple health check for Claude API"""
        try:
            result = await breaker.create_message(
                messages=[{"role": "user", "content": "test"}],
                model="claude-3-5-sonnet-20241022",
                max_tokens=5
            )
            return result is not None
        except Exception as e:
            logger.warning(f"Claude health check failed: {str(e)}")
            return False

    health_monitor.register_service(
        name="anthropic_api",
        health_check=check_claude_health,
        config=HealthCheckConfig(
            check_interval_seconds=60.0,
            latency_warning_ms=2000.0,
            latency_critical_ms=5000.0,
            error_rate_warning=0.10,
            error_rate_critical=0.30
        )
    )

    logger.info("Claude health check registered")
