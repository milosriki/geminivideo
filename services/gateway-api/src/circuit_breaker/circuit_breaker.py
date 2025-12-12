"""
Circuit Breaker Implementation for GeminiVideo Platform
========================================================

Implements the circuit breaker pattern to protect against cascading failures
when external APIs (OpenAI, Anthropic, Meta, Google) experience issues.

Circuit States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are blocked/fallback immediately
- HALF_OPEN: Testing if service has recovered

Author: Agent 9 - Circuit Breaker Builder
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, blocking requests
    HALF_OPEN = "half_open"    # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5          # Failures before opening circuit
    success_threshold: int = 2          # Successes in half-open to close
    timeout_seconds: float = 60.0       # Time before attempting recovery
    half_open_max_calls: int = 3        # Max calls to allow in half-open state

    # Exponential backoff settings
    exponential_backoff: bool = True
    max_timeout_seconds: float = 300.0  # Max backoff time (5 minutes)
    backoff_multiplier: float = 2.0

    # Monitoring settings
    rolling_window_seconds: int = 60    # Time window for failure tracking
    min_throughput: int = 10            # Min requests before triggering breaker


@dataclass
class CircuitMetrics:
    """Tracks circuit breaker metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0          # Rejected by open circuit

    consecutive_failures: int = 0
    consecutive_successes: int = 0

    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_state_change_time: float = field(default_factory=time.time)

    # Rolling window for failure tracking
    failure_timestamps: List[float] = field(default_factory=list)

    # Latency tracking (milliseconds)
    latency_samples: List[float] = field(default_factory=list)
    max_latency_samples: int = 1000


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open and rejects a call"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation with exponential backoff and metrics tracking

    Usage:
        breaker = CircuitBreaker(
            name="openai_api",
            failure_threshold=5,
            timeout_seconds=60
        )

        # Decorator usage
        @breaker.protected
        async def call_openai():
            # Your API call here
            pass

        # Context manager usage
        async with breaker:
            # Your API call here
            pass
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.fallback = fallback

        self._state = CircuitState.CLOSED
        self._metrics = CircuitMetrics()
        self._lock = Lock()

        self._opened_at: Optional[float] = None
        self._backoff_count = 0

        logger.info(
            f"Circuit breaker '{name}' initialized with "
            f"failure_threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout_seconds}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)"""
        return self._state == CircuitState.HALF_OPEN

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self._lock:
            success_rate = 0.0
            if self._metrics.total_requests > 0:
                success_rate = (
                    self._metrics.successful_requests /
                    self._metrics.total_requests * 100
                )

            # Calculate latency percentiles
            p50 = p95 = p99 = 0.0
            if self._metrics.latency_samples:
                sorted_latencies = sorted(self._metrics.latency_samples)
                n = len(sorted_latencies)
                p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
                p95 = sorted_latencies[int(n * 0.95)] if n > 0 else 0
                p99 = sorted_latencies[int(n * 0.99)] if n > 0 else 0

            return {
                "name": self.name,
                "state": self._state.value,
                "total_requests": self._metrics.total_requests,
                "successful_requests": self._metrics.successful_requests,
                "failed_requests": self._metrics.failed_requests,
                "rejected_requests": self._metrics.rejected_requests,
                "success_rate": round(success_rate, 2),
                "consecutive_failures": self._metrics.consecutive_failures,
                "consecutive_successes": self._metrics.consecutive_successes,
                "last_failure_time": self._metrics.last_failure_time,
                "last_success_time": self._metrics.last_success_time,
                "latency_p50_ms": round(p50, 2),
                "latency_p95_ms": round(p95, 2),
                "latency_p99_ms": round(p99, 2),
                "uptime_seconds": time.time() - self._metrics.last_state_change_time
            }

    def reset(self):
        """Reset circuit breaker to initial state"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._metrics = CircuitMetrics()
            self._opened_at = None
            self._backoff_count = 0
            logger.info(f"Circuit breaker '{self.name}' reset")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self._state != CircuitState.OPEN:
            return False

        if self._opened_at is None:
            return True

        # Calculate timeout with exponential backoff
        timeout = self.config.timeout_seconds
        if self.config.exponential_backoff:
            timeout = min(
                timeout * (self.config.backoff_multiplier ** self._backoff_count),
                self.config.max_timeout_seconds
            )

        elapsed = time.time() - self._opened_at
        return elapsed >= timeout

    def _transition_to_half_open(self):
        """Transition circuit to half-open state"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                logger.info(
                    f"Circuit breaker '{self.name}' transitioning to HALF_OPEN "
                    f"(testing recovery)"
                )
                self._state = CircuitState.HALF_OPEN
                self._metrics.consecutive_successes = 0
                self._metrics.last_state_change_time = time.time()

    def _transition_to_open(self):
        """Transition circuit to open state"""
        with self._lock:
            if self._state != CircuitState.OPEN:
                logger.error(
                    f"Circuit breaker '{self.name}' transitioning to OPEN "
                    f"(consecutive failures: {self._metrics.consecutive_failures})"
                )
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                self._backoff_count += 1
                self._metrics.last_state_change_time = time.time()

    def _transition_to_closed(self):
        """Transition circuit to closed state"""
        with self._lock:
            if self._state != CircuitState.CLOSED:
                logger.info(
                    f"Circuit breaker '{self.name}' transitioning to CLOSED "
                    f"(service recovered)"
                )
                self._state = CircuitState.CLOSED
                self._metrics.consecutive_failures = 0
                self._backoff_count = 0  # Reset backoff on successful recovery
                self._metrics.last_state_change_time = time.time()

    def _record_success(self, latency_ms: float):
        """Record a successful call"""
        with self._lock:
            self._metrics.total_requests += 1
            self._metrics.successful_requests += 1
            self._metrics.consecutive_successes += 1
            self._metrics.consecutive_failures = 0
            self._metrics.last_success_time = time.time()

            # Track latency
            self._metrics.latency_samples.append(latency_ms)
            if len(self._metrics.latency_samples) > self._metrics.max_latency_samples:
                self._metrics.latency_samples.pop(0)

            # State transitions based on success
            if self._state == CircuitState.HALF_OPEN:
                if self._metrics.consecutive_successes >= self.config.success_threshold:
                    self._transition_to_closed()

    def _record_failure(self):
        """Record a failed call"""
        with self._lock:
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1
            self._metrics.consecutive_failures += 1
            self._metrics.consecutive_successes = 0
            self._metrics.last_failure_time = time.time()

            # Track failure timestamp for rolling window
            self._metrics.failure_timestamps.append(time.time())

            # Clean old failures outside rolling window
            cutoff_time = time.time() - self.config.rolling_window_seconds
            self._metrics.failure_timestamps = [
                t for t in self._metrics.failure_timestamps if t > cutoff_time
            ]

            # State transitions based on failure
            if self._state == CircuitState.HALF_OPEN:
                # Immediately open if failure during half-open
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                # Check if we should open the circuit
                recent_failures = len(self._metrics.failure_timestamps)
                if (
                    recent_failures >= self.config.failure_threshold and
                    self._metrics.total_requests >= self.config.min_throughput
                ):
                    self._transition_to_open()

    def _record_rejection(self):
        """Record a rejected call (circuit is open)"""
        with self._lock:
            self._metrics.rejected_requests += 1

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection

        Args:
            func: Function to execute (can be sync or async)
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result from the function or fallback

        Raises:
            CircuitBreakerError: If circuit is open and no fallback provided
        """
        # Check if we should attempt reset from open state
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            self._transition_to_half_open()

        # If circuit is open, reject the call
        if self._state == CircuitState.OPEN:
            self._record_rejection()
            logger.warning(
                f"Circuit breaker '{self.name}' is OPEN, rejecting call"
            )

            if self.fallback:
                logger.info(f"Using fallback for '{self.name}'")
                return await self._execute_fallback(*args, **kwargs)

            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service is currently unavailable."
            )

        # Execute the function
        start_time = time.time()
        try:
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            latency_ms = (time.time() - start_time) * 1000
            self._record_success(latency_ms)
            return result

        except Exception as e:
            self._record_failure()
            logger.error(
                f"Circuit breaker '{self.name}' recorded failure: {str(e)}"
            )

            # If we have a fallback and circuit just opened, use it
            if self.fallback and self._state == CircuitState.OPEN:
                logger.info(f"Using fallback for '{self.name}' after failure")
                return await self._execute_fallback(*args, **kwargs)

            raise

    async def _execute_fallback(self, *args, **kwargs) -> Any:
        """Execute fallback function"""
        if self.fallback:
            if asyncio.iscoroutinefunction(self.fallback):
                return await self.fallback(*args, **kwargs)
            else:
                return self.fallback(*args, **kwargs)
        return None

    def protected(self, func: Callable) -> Callable:
        """
        Decorator to protect a function with circuit breaker

        Usage:
            @breaker.protected
            async def my_api_call():
                return await some_api()
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper

    async def __aenter__(self):
        """Context manager entry"""
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            self._transition_to_half_open()

        if self._state == CircuitState.OPEN:
            self._record_rejection()
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN"
            )

        self._call_start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            latency_ms = (time.time() - self._call_start_time) * 1000
            self._record_success(latency_ms)
        else:
            self._record_failure()
        return False


class CircuitBreakerRegistry:
    """
    Global registry for managing multiple circuit breakers
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def register(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        fallback: Optional[Callable] = None
    ) -> CircuitBreaker:
        """Register a new circuit breaker"""
        with self._lock:
            if name in self._breakers:
                logger.warning(
                    f"Circuit breaker '{name}' already registered, returning existing"
                )
                return self._breakers[name]

            breaker = CircuitBreaker(name, config, fallback)
            self._breakers[name] = breaker
            logger.info(f"Registered circuit breaker: {name}")
            return breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name"""
        return self._breakers.get(name)

    def get_all(self) -> Dict[str, CircuitBreaker]:
        """Get all registered circuit breakers"""
        return self._breakers.copy()

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all circuit breakers"""
        return [breaker.get_metrics() for breaker in self._breakers.values()]

    def reset_all(self):
        """Reset all circuit breakers"""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
            logger.info("All circuit breakers reset")


# Global registry instance
registry = CircuitBreakerRegistry()
