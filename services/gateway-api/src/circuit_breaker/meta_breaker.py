"""
Meta Marketing API Circuit Breaker
===================================

Circuit breaker for Meta Marketing API (Facebook/Instagram Ads) with request queuing.

Handles:
- Ad publishing failures
- Campaign management
- Rate limits
- Request queuing during outages

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


class MetaCircuitBreaker:
    """
    Circuit breaker specifically for Meta Marketing API

    Features:
    - Request queuing for ad publishes during outages
    - Automatic retry with exponential backoff
    - Rate limit handling
    - Campaign status tracking
    """

    def __init__(self, meta_access_token: Optional[str] = None):
        """
        Initialize Meta circuit breaker

        Args:
            meta_access_token: Meta API access token
        """
        self.access_token = meta_access_token or os.environ.get('META_ACCESS_TOKEN')

        # Create circuit breaker
        config = CircuitBreakerConfig(
            failure_threshold=5,        # More lenient for Meta
            success_threshold=3,
            timeout_seconds=120.0,      # Longer timeout (2 minutes)
            exponential_backoff=True,
            max_timeout_seconds=600.0,  # Max 10 minutes
        )

        self.breaker = registry.register(
            name="meta_api",
            config=config,
            fallback=self._fallback_handler
        )

        # Fallback handler with larger queue for ad publishing
        self.fallback_handler = FallbackHandler(
            config=FallbackConfig(
                cache_enabled=False,    # Don't cache ad publishes
                queue_enabled=True,
                max_queue_size=2000,    # Large queue for ads
                queue_ttl_seconds=1800, # Keep queued for 30 minutes
                auto_retry_enabled=True,
                max_retry_attempts=5
            )
        )

        # Track queued ads
        self._queued_ads: Dict[str, Dict] = {}

        logger.info("Meta circuit breaker initialized")

    async def _fallback_handler(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Fallback handler when Meta API fails
        Queues the request for retry
        """
        logger.warning("Meta circuit OPEN, queueing request for retry")

        operation = kwargs.get('operation', 'unknown')

        return {
            "success": False,
            "queued": True,
            "message": f"Meta API unavailable. {operation.title()} queued for retry.",
            "retry_info": {
                "queue_size": self.fallback_handler._queue.size(),
                "estimated_retry": "when service recovers"
            }
        }

    async def publish_ad(
        self,
        ad_account_id: str,
        campaign_id: str,
        ad_creative: Dict[str, Any],
        targeting: Dict[str, Any],
        budget: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Publish an ad to Meta with circuit breaker protection

        Args:
            ad_account_id: Meta ad account ID
            campaign_id: Campaign ID
            ad_creative: Ad creative data
            targeting: Targeting parameters
            budget: Budget configuration
            **kwargs: Additional parameters

        Returns:
            Response with ad ID and status
        """
        async def _execute():
            import requests

            if not self.access_token:
                raise ValueError("META_ACCESS_TOKEN not configured")

            # Call Meta Marketing API
            url = f"https://graph.facebook.com/v18.0/{ad_account_id}/ads"

            payload = {
                "access_token": self.access_token,
                "campaign_id": campaign_id,
                "creative": json.dumps(ad_creative),
                "targeting": json.dumps(targeting),
                "status": "PAUSED",  # Start paused for safety
                **budget,
                **kwargs
            }

            try:
                # Use asyncio-compatible approach
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=payload) as response:
                        if response.status == 429:
                            # Rate limit
                            logger.warning("Meta rate limit hit")
                            raise Exception("Rate limit exceeded")

                        if response.status >= 400:
                            error_data = await response.json()
                            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                            raise Exception(f"Meta API error: {error_msg}")

                        data = await response.json()

                        return {
                            "success": True,
                            "ad_id": data.get("id"),
                            "status": "created",
                            "queued": False
                        }

            except Exception as e:
                logger.error(f"Meta ad publish failed: {str(e)}")
                raise

        # Execute with circuit breaker
        try:
            result = await self.breaker.call(_execute)
            return result
        except Exception as e:
            # If circuit is open, queue the request
            if self.breaker.is_open:
                request_id = self.fallback_handler.queue_for_retry(
                    "meta_api",
                    _execute,
                    args=(),
                    kwargs={}
                )

                self._queued_ads[request_id] = {
                    "ad_account_id": ad_account_id,
                    "campaign_id": campaign_id,
                    "queued_at": asyncio.get_event_loop().time()
                }

                return {
                    "success": False,
                    "queued": True,
                    "request_id": request_id,
                    "message": "Meta API unavailable. Ad queued for automatic retry."
                }
            raise

    async def get_campaign_insights(
        self,
        campaign_id: str,
        fields: Optional[List[str]] = None,
        time_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get campaign insights with circuit breaker protection

        Args:
            campaign_id: Campaign ID
            fields: Fields to retrieve
            time_range: Time range for insights

        Returns:
            Campaign insights data
        """
        async def _execute():
            import aiohttp

            if not self.access_token:
                raise ValueError("META_ACCESS_TOKEN not configured")

            url = f"https://graph.facebook.com/v18.0/{campaign_id}/insights"

            params = {
                "access_token": self.access_token,
                "fields": ",".join(fields or ["impressions", "clicks", "spend", "ctr"]),
            }

            if time_range:
                params["time_range"] = json.dumps(time_range)

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status >= 400:
                        error_data = await response.json()
                        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                        raise Exception(f"Meta API error: {error_msg}")

                    data = await response.json()
                    return data.get("data", [])

        return await self.breaker.call(_execute)

    async def update_campaign_budget(
        self,
        campaign_id: str,
        daily_budget: Optional[int] = None,
        lifetime_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update campaign budget with circuit breaker protection

        Args:
            campaign_id: Campaign ID
            daily_budget: Daily budget in cents
            lifetime_budget: Lifetime budget in cents

        Returns:
            Update confirmation
        """
        async def _execute():
            import aiohttp

            if not self.access_token:
                raise ValueError("META_ACCESS_TOKEN not configured")

            url = f"https://graph.facebook.com/v18.0/{campaign_id}"

            payload = {"access_token": self.access_token}

            if daily_budget is not None:
                payload["daily_budget"] = daily_budget

            if lifetime_budget is not None:
                payload["lifetime_budget"] = lifetime_budget

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload) as response:
                    if response.status >= 400:
                        error_data = await response.json()
                        raise Exception(f"Meta API error: {error_data}")

                    return {"success": True, "campaign_id": campaign_id}

        return await self.breaker.call(_execute)

    def get_queued_ads(self) -> List[Dict[str, Any]]:
        """Get list of queued ad publish requests"""
        queue_status = self.fallback_handler.get_queue_status()

        # Enrich with ad details
        for item in queue_status:
            if item["request_id"] in self._queued_ads:
                item.update(self._queued_ads[item["request_id"]])

        return queue_status

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        return {
            **self.breaker.get_metrics(),
            "queued_ads_count": len(self._queued_ads),
            "fallback_stats": self.fallback_handler.get_stats()
        }

    def reset(self):
        """Reset circuit breaker"""
        self.breaker.reset()
        self._queued_ads.clear()


async def setup_meta_health_check(
    breaker: MetaCircuitBreaker,
    health_monitor: HealthMonitor
):
    """
    Setup health check for Meta Marketing API

    Args:
        breaker: Meta circuit breaker instance
        health_monitor: Health monitor instance
    """
    async def check_meta_health() -> bool:
        """Simple health check for Meta API"""
        try:
            import aiohttp

            if not breaker.access_token:
                logger.warning("Meta access token not configured")
                return False

            # Check if API is reachable
            url = "https://graph.facebook.com/v18.0/me"
            params = {"access_token": breaker.access_token}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200

        except Exception as e:
            logger.warning(f"Meta health check failed: {str(e)}")
            return False

    health_monitor.register_service(
        name="meta_api",
        health_check=check_meta_health,
        config=HealthCheckConfig(
            check_interval_seconds=120.0,   # Check every 2 minutes
            latency_warning_ms=3000.0,
            latency_critical_ms=10000.0,
            error_rate_warning=0.15,
            error_rate_critical=0.40
        )
    )

    logger.info("Meta health check registered")
