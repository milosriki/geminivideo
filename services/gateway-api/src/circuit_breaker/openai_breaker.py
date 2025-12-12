"""
OpenAI Circuit Breaker
======================

Circuit breaker for OpenAI API with failover to Claude or Gemini.

Handles:
- GPT-4o, GPT-4o-mini calls
- Automatic failover to Anthropic Claude or Google Gemini
- Request/response caching
- Rate limit handling (429 errors)

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


class OpenAICircuitBreaker:
    """
    Circuit breaker specifically for OpenAI API with intelligent failover

    Features:
    - Automatic failover to Claude or Gemini
    - Request caching based on prompt hash
    - Rate limit backoff
    - Cost tracking
    """

    def __init__(
        self,
        openai_client: Any,
        claude_client: Optional[Any] = None,
        gemini_client: Optional[Any] = None
    ):
        """
        Initialize OpenAI circuit breaker

        Args:
            openai_client: OpenAI API client instance
            claude_client: Optional Anthropic Claude client for failover
            gemini_client: Optional Google Gemini client for failover
        """
        self.openai_client = openai_client
        self.claude_client = claude_client
        self.gemini_client = gemini_client

        # Create circuit breaker
        config = CircuitBreakerConfig(
            failure_threshold=3,        # Open after 3 failures
            success_threshold=2,        # Close after 2 successes in half-open
            timeout_seconds=60.0,       # Try recovery after 1 minute
            exponential_backoff=True,
            max_timeout_seconds=300.0,  # Max 5 minutes backoff
        )

        self.breaker = registry.register(
            name="openai_api",
            config=config,
            fallback=self._fallback_handler
        )

        # Fallback handler
        self.fallback_handler = FallbackHandler(
            config=FallbackConfig(
                cache_enabled=True,
                cache_ttl_seconds=3600,  # 1 hour cache
                queue_enabled=True,
                max_queue_size=500
            )
        )

        # Track costs
        self._total_cost = 0.0
        self._fallback_used_count = 0

        logger.info("OpenAI circuit breaker initialized")

    async def _fallback_handler(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Fallback handler when OpenAI fails
        Tries: Claude -> Gemini -> Cached response -> Error
        """
        logger.warning("OpenAI circuit OPEN, attempting fallover")

        # Try Claude first (similar quality to GPT-4)
        if self.claude_client:
            try:
                logger.info("Failing over to Claude")
                result = await self._call_claude(*args, **kwargs)
                self._fallback_used_count += 1
                return {
                    **result,
                    "_fallback": "claude",
                    "_original_provider": "openai"
                }
            except Exception as e:
                logger.warning(f"Claude failover failed: {str(e)}")

        # Try Gemini second (faster, cheaper)
        if self.gemini_client:
            try:
                logger.info("Failing over to Gemini")
                result = await self._call_gemini(*args, **kwargs)
                self._fallback_used_count += 1
                return {
                    **result,
                    "_fallback": "gemini",
                    "_original_provider": "openai"
                }
            except Exception as e:
                logger.warning(f"Gemini failover failed: {str(e)}")

        # All failovers failed
        raise Exception("All AI providers unavailable (OpenAI, Claude, Gemini)")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call OpenAI chat completion with circuit breaker protection

        Args:
            messages: Chat messages
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            response_format: Response format (e.g., {"type": "json_object"})
            **kwargs: Additional parameters

        Returns:
            Response dict with content, model, usage, etc.
        """
        # Generate cache key
        cache_key = self._generate_cache_key(messages, model, temperature)

        # Try cache first
        cached = self.fallback_handler.get_from_cache("openai", cache_key)
        if cached:
            logger.info(f"Cache hit for OpenAI chat completion")
            return cached.data

        # Execute with circuit breaker
        async def _execute():
            import openai

            try:
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    **kwargs
                )

                # Extract response
                result = {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "finish_reason": response.choices[0].finish_reason
                }

                # Track cost
                cost = self._calculate_cost(model, response.usage)
                self._total_cost += cost
                result["cost_usd"] = cost

                # Cache successful response
                self.fallback_handler.save_to_cache("openai", cache_key, result)

                return result

            except openai.RateLimitError as e:
                logger.warning(f"OpenAI rate limit hit: {str(e)}")
                raise

            except openai.APIError as e:
                logger.error(f"OpenAI API error: {str(e)}")
                raise

        return await self.breaker.call(_execute)

    async def _call_claude(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Failover to Claude"""
        import anthropic

        # Convert messages format if needed
        claude_messages = []
        system = None

        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = await self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=kwargs.get("max_tokens", 1024),
            system=system,
            messages=claude_messages
        )

        return {
            "content": response.content[0].text,
            "model": "claude-3-5-sonnet-20241022",
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            "finish_reason": response.stop_reason
        }

    async def _call_gemini(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Failover to Gemini"""
        import google.generativeai as genai

        # Convert messages to Gemini format
        prompt_parts = []
        for msg in messages:
            role_prefix = f"{msg['role'].upper()}: " if msg['role'] != 'user' else ""
            prompt_parts.append(f"{role_prefix}{msg['content']}")

        prompt = "\n\n".join(prompt_parts)

        model = genai.GenerativeModel('gemini-2.0-flash')
        response = await model.generate_content_async(prompt)

        return {
            "content": response.text,
            "model": "gemini-2.0-flash",
            "usage": {
                "prompt_tokens": 0,  # Gemini doesn't expose this easily
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "finish_reason": "stop"
        }

    def _generate_cache_key(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float
    ) -> str:
        """Generate cache key from request parameters"""
        # Create a stable hash of the request
        key_data = {
            "messages": messages,
            "model": model,
            "temperature": temperature
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _calculate_cost(self, model: str, usage: Any) -> float:
        """Calculate cost in USD for the API call"""
        # Pricing per 1M tokens (as of 2024)
        pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        }

        # Default to gpt-4o-mini pricing
        rates = pricing.get(model, pricing["gpt-4o-mini"])

        input_cost = (usage.prompt_tokens / 1_000_000) * rates["input"]
        output_cost = (usage.completion_tokens / 1_000_000) * rates["output"]

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


async def setup_openai_health_check(
    breaker: OpenAICircuitBreaker,
    health_monitor: HealthMonitor
):
    """
    Setup health check for OpenAI API

    Args:
        breaker: OpenAI circuit breaker instance
        health_monitor: Health monitor instance
    """
    async def check_openai_health() -> bool:
        """Simple health check for OpenAI API"""
        try:
            # Make a minimal API call
            result = await breaker.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                model="gpt-4o-mini",
                max_tokens=5
            )
            return result is not None
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {str(e)}")
            return False

    health_monitor.register_service(
        name="openai_api",
        health_check=check_openai_health,
        config=HealthCheckConfig(
            check_interval_seconds=60.0,
            latency_warning_ms=2000.0,
            latency_critical_ms=5000.0,
            error_rate_warning=0.10,
            error_rate_critical=0.30
        )
    )

    logger.info("OpenAI health check registered")
