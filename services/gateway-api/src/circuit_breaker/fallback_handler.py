"""
Fallback Handler for Circuit Breaker System
============================================

Provides graceful degradation strategies when external APIs are unavailable:
- Returns cached responses when available
- Queues requests for retry when circuit opens
- Implements service-specific fallback logic
- Logs all fallback events for debugging

Author: Agent 9 - Circuit Breaker Builder
"""

import time
import logging
import asyncio
import json
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Types of fallback strategies"""
    CACHE = "cache"                     # Return cached response
    DEFAULT = "default"                 # Return default value
    QUEUE = "queue"                     # Queue for retry
    ALTERNATE_SERVICE = "alternate"     # Use alternate service
    DEGRADED_RESPONSE = "degraded"      # Return partial/degraded response


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior"""
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600       # 1 hour default

    # Queue settings
    queue_enabled: bool = True
    max_queue_size: int = 1000
    queue_ttl_seconds: int = 300        # 5 minutes in queue

    # Retry settings
    auto_retry_enabled: bool = True
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 60.0   # Initial retry delay
    retry_backoff_multiplier: float = 2.0

    # Logging
    log_fallbacks: bool = True


@dataclass
class QueuedRequest:
    """Represents a queued request waiting for retry"""
    request_id: str
    service_name: str
    function: Callable
    args: tuple
    kwargs: dict
    queued_at: float = field(default_factory=time.time)
    retry_count: int = 0
    callback: Optional[Callable] = None


@dataclass
class FallbackResult:
    """Result of a fallback operation"""
    strategy: FallbackStrategy
    data: Any
    from_cache: bool = False
    queued: bool = False
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FallbackCache:
    """
    Simple in-memory cache for fallback responses
    """

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._max_size = max_size
        self._access_times: Dict[str, float] = {}

    def get(self, key: str, max_age_seconds: Optional[int] = None) -> Optional[Any]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None

        value, cached_at = self._cache[key]
        self._access_times[key] = time.time()

        # Check expiration
        if max_age_seconds is not None:
            age = time.time() - cached_at
            if age > max_age_seconds:
                del self._cache[key]
                return None

        return value

    def set(self, key: str, value: Any):
        """Cache a value"""
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            # Remove least recently used
            oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            del self._cache[oldest_key]
            del self._access_times[oldest_key]

        self._cache[key] = (value, time.time())
        self._access_times[key] = time.time()

    def invalidate(self, key: str):
        """Remove a key from cache"""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)

    def clear(self):
        """Clear all cached values"""
        self._cache.clear()
        self._access_times.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)


class RequestQueue:
    """
    Queue for requests that need to be retried
    """

    def __init__(self, max_size: int = 1000):
        self._queue: deque[QueuedRequest] = deque(maxlen=max_size)
        self._processing = False

    def enqueue(self, request: QueuedRequest):
        """Add a request to the queue"""
        if len(self._queue) >= self._queue.maxlen:
            logger.warning(
                f"Request queue full, dropping oldest request for {request.service_name}"
            )

        self._queue.append(request)
        logger.info(
            f"Queued request {request.request_id} for {request.service_name} "
            f"(queue size: {len(self._queue)})"
        )

    def dequeue(self) -> Optional[QueuedRequest]:
        """Get next request from queue"""
        if not self._queue:
            return None
        return self._queue.popleft()

    def peek(self) -> Optional[QueuedRequest]:
        """Look at next request without removing it"""
        if not self._queue:
            return None
        return self._queue[0]

    def size(self) -> int:
        """Get current queue size"""
        return len(self._queue)

    def clear(self):
        """Clear all queued requests"""
        self._queue.clear()

    def get_all(self) -> List[QueuedRequest]:
        """Get all queued requests"""
        return list(self._queue)

    def remove_expired(self, max_age_seconds: int):
        """Remove requests older than max_age_seconds"""
        now = time.time()
        original_size = len(self._queue)

        # Filter out expired requests
        self._queue = deque(
            [req for req in self._queue if now - req.queued_at < max_age_seconds],
            maxlen=self._queue.maxlen
        )

        removed = original_size - len(self._queue)
        if removed > 0:
            logger.info(f"Removed {removed} expired requests from queue")


class FallbackHandler:
    """
    Manages fallback strategies and graceful degradation

    Usage:
        handler = FallbackHandler()

        # Register a fallback function
        def openai_fallback(*args, **kwargs):
            # Return a default response
            return {"score": 50, "confidence": 0.5, "reasoning": "Fallback response"}

        handler.register_fallback("openai_api", openai_fallback)

        # Use with circuit breaker
        result = await handler.execute_with_fallback(
            "openai_api",
            some_function,
            *args,
            **kwargs
        )
    """

    def __init__(self, config: Optional[FallbackConfig] = None):
        self.config = config or FallbackConfig()

        self._cache = FallbackCache()
        self._queue = RequestQueue(max_size=self.config.max_queue_size)
        self._fallback_functions: Dict[str, Callable] = {}

        self._retry_task: Optional[asyncio.Task] = None
        self._running = False

        # Statistics
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "queue_enqueued": 0,
            "queue_processed": 0,
            "fallback_used": 0
        }

        logger.info("Fallback handler initialized")

    def register_fallback(self, service_name: str, fallback_func: Callable):
        """
        Register a fallback function for a service

        Args:
            service_name: Name of the service
            fallback_func: Function to call when service is unavailable
        """
        self._fallback_functions[service_name] = fallback_func
        logger.info(f"Registered fallback for service: {service_name}")

    def get_from_cache(
        self,
        service_name: str,
        cache_key: str
    ) -> Optional[FallbackResult]:
        """
        Try to get a cached response

        Args:
            service_name: Service name
            cache_key: Cache key (usually hash of request params)

        Returns:
            FallbackResult if cache hit, None otherwise
        """
        if not self.config.cache_enabled:
            return None

        full_key = f"{service_name}:{cache_key}"
        cached_value = self._cache.get(full_key, self.config.cache_ttl_seconds)

        if cached_value is not None:
            self._stats["cache_hits"] += 1
            logger.info(f"Cache hit for {service_name} (key: {cache_key})")

            return FallbackResult(
                strategy=FallbackStrategy.CACHE,
                data=cached_value,
                from_cache=True,
                metadata={"cache_key": cache_key}
            )

        self._stats["cache_misses"] += 1
        return None

    def save_to_cache(self, service_name: str, cache_key: str, value: Any):
        """
        Save a successful response to cache

        Args:
            service_name: Service name
            cache_key: Cache key
            value: Value to cache
        """
        if not self.config.cache_enabled:
            return

        full_key = f"{service_name}:{cache_key}"
        self._cache.set(full_key, value)
        logger.debug(f"Cached response for {service_name} (key: {cache_key})")

    def queue_for_retry(
        self,
        service_name: str,
        function: Callable,
        args: tuple,
        kwargs: dict,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Queue a request for retry when service recovers

        Args:
            service_name: Service name
            function: Function to retry
            args: Positional arguments
            kwargs: Keyword arguments
            callback: Optional callback when retry succeeds

        Returns:
            Request ID for tracking
        """
        if not self.config.queue_enabled:
            logger.warning("Request queueing is disabled")
            return ""

        request_id = f"{service_name}_{int(time.time() * 1000)}"

        request = QueuedRequest(
            request_id=request_id,
            service_name=service_name,
            function=function,
            args=args,
            kwargs=kwargs,
            callback=callback
        )

        self._queue.enqueue(request)
        self._stats["queue_enqueued"] += 1

        return request_id

    async def execute_with_fallback(
        self,
        service_name: str,
        function: Callable,
        *args,
        cache_key: Optional[str] = None,
        **kwargs
    ) -> FallbackResult:
        """
        Execute a function with fallback support

        Tries in order:
        1. Check cache
        2. Execute function
        3. Use registered fallback
        4. Queue for retry and return degraded response

        Args:
            service_name: Service name
            function: Function to execute
            cache_key: Optional cache key
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            FallbackResult with the response
        """
        # Try cache first
        if cache_key and self.config.cache_enabled:
            cached = self.get_from_cache(service_name, cache_key)
            if cached:
                return cached

        # Try to execute the function
        try:
            if asyncio.iscoroutinefunction(function):
                result = await function(*args, **kwargs)
            else:
                result = function(*args, **kwargs)

            # Cache successful result
            if cache_key and self.config.cache_enabled:
                self.save_to_cache(service_name, cache_key, result)

            return FallbackResult(
                strategy=FallbackStrategy.DEFAULT,
                data=result,
                metadata={"source": "primary"}
            )

        except Exception as e:
            logger.warning(
                f"Primary function failed for {service_name}: {str(e)}, "
                f"attempting fallback"
            )

            # Try registered fallback function
            if service_name in self._fallback_functions:
                try:
                    fallback_func = self._fallback_functions[service_name]

                    if asyncio.iscoroutinefunction(fallback_func):
                        fallback_result = await fallback_func(*args, **kwargs)
                    else:
                        fallback_result = fallback_func(*args, **kwargs)

                    self._stats["fallback_used"] += 1

                    if self.config.log_fallbacks:
                        logger.info(
                            f"Using fallback for {service_name}, "
                            f"error: {str(e)}"
                        )

                    return FallbackResult(
                        strategy=FallbackStrategy.ALTERNATE_SERVICE,
                        data=fallback_result,
                        metadata={
                            "original_error": str(e),
                            "fallback_used": True
                        }
                    )

                except Exception as fallback_error:
                    logger.error(
                        f"Fallback also failed for {service_name}: "
                        f"{str(fallback_error)}"
                    )

            # Queue for retry if enabled
            if self.config.queue_enabled:
                request_id = self.queue_for_retry(
                    service_name,
                    function,
                    args,
                    kwargs
                )

                return FallbackResult(
                    strategy=FallbackStrategy.QUEUE,
                    data=None,
                    queued=True,
                    metadata={
                        "request_id": request_id,
                        "error": str(e),
                        "message": "Request queued for retry when service recovers"
                    }
                )

            # No fallback available
            raise

    async def start_retry_processor(self):
        """Start processing queued requests"""
        if self._running:
            logger.warning("Retry processor already running")
            return

        self._running = True
        self._retry_task = asyncio.create_task(self._retry_loop())
        logger.info("Retry processor started")

    async def stop_retry_processor(self):
        """Stop processing queued requests"""
        self._running = False
        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass
        logger.info("Retry processor stopped")

    async def _retry_loop(self):
        """Process queued requests for retry"""
        while self._running:
            try:
                # Clean up expired requests
                self._queue.remove_expired(self.config.queue_ttl_seconds)

                # Process next request
                request = self._queue.dequeue()
                if not request:
                    await asyncio.sleep(5)  # Wait before checking again
                    continue

                logger.info(
                    f"Retrying request {request.request_id} for "
                    f"{request.service_name} (attempt {request.retry_count + 1})"
                )

                try:
                    # Execute the function
                    if asyncio.iscoroutinefunction(request.function):
                        result = await request.function(*request.args, **request.kwargs)
                    else:
                        result = request.function(*request.args, **request.kwargs)

                    # Success! Call callback if provided
                    if request.callback:
                        await request.callback(result)

                    self._stats["queue_processed"] += 1
                    logger.info(
                        f"Successfully retried request {request.request_id} "
                        f"for {request.service_name}"
                    )

                except Exception as e:
                    logger.warning(
                        f"Retry failed for {request.request_id}: {str(e)}"
                    )

                    # Re-queue if under max retries
                    if request.retry_count < self.config.max_retry_attempts:
                        request.retry_count += 1

                        # Calculate backoff delay
                        delay = self.config.retry_delay_seconds * (
                            self.config.retry_backoff_multiplier ** request.retry_count
                        )

                        logger.info(
                            f"Re-queueing {request.request_id}, "
                            f"will retry in {delay:.0f}s"
                        )

                        await asyncio.sleep(delay)
                        self._queue.enqueue(request)
                    else:
                        logger.error(
                            f"Max retries exceeded for {request.request_id}, "
                            f"dropping request"
                        )

                # Brief pause between retries
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retry loop: {e}")
                await asyncio.sleep(5)

    def get_stats(self) -> Dict[str, Any]:
        """Get fallback handler statistics"""
        return {
            **self._stats,
            "cache_size": self._cache.size(),
            "queue_size": self._queue.size(),
            "cache_hit_rate": (
                self._stats["cache_hits"] /
                (self._stats["cache_hits"] + self._stats["cache_misses"])
                if (self._stats["cache_hits"] + self._stats["cache_misses"]) > 0
                else 0
            )
        }

    def get_queue_status(self) -> List[Dict[str, Any]]:
        """Get status of all queued requests"""
        return [
            {
                "request_id": req.request_id,
                "service": req.service_name,
                "queued_at": req.queued_at,
                "retry_count": req.retry_count,
                "age_seconds": time.time() - req.queued_at
            }
            for req in self._queue.get_all()
        ]


# Global fallback handler instance
global_fallback_handler = FallbackHandler()
