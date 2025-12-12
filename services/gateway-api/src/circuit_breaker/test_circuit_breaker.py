"""
Tests for Circuit Breaker System
=================================

Comprehensive test suite for circuit breaker, health monitor,
and fallback handler.

Author: Agent 9 - Circuit Breaker Builder
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    registry
)
from health_monitor import (
    HealthMonitor,
    HealthCheckConfig,
    HealthStatus
)
from fallback_handler import (
    FallbackHandler,
    FallbackConfig,
    FallbackStrategy
)


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    """Test circuit breaker in normal closed state"""
    breaker = CircuitBreaker(
        name="test_closed",
        config=CircuitBreakerConfig(failure_threshold=3)
    )

    # Function that succeeds
    async def successful_call():
        return "success"

    result = await breaker.call(successful_call)
    assert result == "success"
    assert breaker.is_closed
    assert breaker.get_metrics()["successful_requests"] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures"""
    breaker = CircuitBreaker(
        name="test_open",
        config=CircuitBreakerConfig(
            failure_threshold=3,
            min_throughput=1
        )
    )

    # Function that fails
    async def failing_call():
        raise Exception("API error")

    # Make failures to trigger circuit open
    for i in range(3):
        with pytest.raises(Exception):
            await breaker.call(failing_call)

    # Circuit should now be open
    assert breaker.is_open

    # Next call should be rejected
    with pytest.raises(CircuitBreakerError):
        await breaker.call(failing_call)

    metrics = breaker.get_metrics()
    assert metrics["failed_requests"] == 3
    assert metrics["rejected_requests"] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker transitions to half-open and recovers"""
    breaker = CircuitBreaker(
        name="test_recovery",
        config=CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.1,  # Short timeout for testing
            min_throughput=1
        )
    )

    # Fail to open circuit
    async def failing_call():
        raise Exception("API error")

    for _ in range(2):
        with pytest.raises(Exception):
            await breaker.call(failing_call)

    assert breaker.is_open

    # Wait for timeout
    await asyncio.sleep(0.2)

    # Successful call should transition to half-open then closed
    async def successful_call():
        return "success"

    # First success (half-open)
    result1 = await breaker.call(successful_call)
    assert result1 == "success"
    assert breaker.is_half_open

    # Second success (should close)
    result2 = await breaker.call(successful_call)
    assert result2 == "success"
    assert breaker.is_closed


@pytest.mark.asyncio
async def test_circuit_breaker_with_fallback():
    """Test circuit breaker with fallback function"""
    def fallback_func(*args, **kwargs):
        return "fallback_response"

    breaker = CircuitBreaker(
        name="test_fallback",
        config=CircuitBreakerConfig(failure_threshold=2, min_throughput=1),
        fallback=fallback_func
    )

    # Fail to open circuit
    async def failing_call():
        raise Exception("API error")

    for _ in range(2):
        with pytest.raises(Exception):
            await breaker.call(failing_call)

    assert breaker.is_open

    # Should use fallback
    result = await breaker.call(failing_call)
    assert result == "fallback_response"


@pytest.mark.asyncio
async def test_circuit_breaker_exponential_backoff():
    """Test exponential backoff increases timeout"""
    breaker = CircuitBreaker(
        name="test_backoff",
        config=CircuitBreakerConfig(
            failure_threshold=1,
            timeout_seconds=1.0,
            exponential_backoff=True,
            backoff_multiplier=2.0,
            min_throughput=1
        )
    )

    # Open circuit
    async def failing_call():
        raise Exception("API error")

    with pytest.raises(Exception):
        await breaker.call(failing_call)

    assert breaker.is_open
    first_timeout = breaker._opened_at

    # Force another open after recovery attempt
    await asyncio.sleep(1.1)

    # Should still fail
    with pytest.raises(Exception):
        await breaker.call(failing_call)

    # Backoff count should increase
    assert breaker._backoff_count > 0


@pytest.mark.asyncio
async def test_circuit_breaker_decorator():
    """Test circuit breaker decorator syntax"""
    breaker = CircuitBreaker(
        name="test_decorator",
        config=CircuitBreakerConfig(failure_threshold=3)
    )

    @breaker.protected
    async def protected_function():
        return "protected_result"

    result = await protected_function()
    assert result == "protected_result"
    assert breaker.get_metrics()["successful_requests"] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_context_manager():
    """Test circuit breaker context manager syntax"""
    breaker = CircuitBreaker(
        name="test_context",
        config=CircuitBreakerConfig(failure_threshold=3)
    )

    async with breaker:
        # Do some work
        result = "context_result"

    assert breaker.get_metrics()["successful_requests"] == 1


# ============================================================================
# Health Monitor Tests
# ============================================================================

@pytest.mark.asyncio
async def test_health_monitor_registration():
    """Test service registration with health monitor"""
    monitor = HealthMonitor()

    async def health_check():
        return True

    monitor.register_service("test_service", health_check)

    assert "test_service" in monitor._services
    assert monitor._services["test_service"].status == HealthStatus.UNKNOWN


@pytest.mark.asyncio
async def test_health_monitor_check_healthy():
    """Test health check for healthy service"""
    monitor = HealthMonitor()

    async def healthy_check():
        await asyncio.sleep(0.01)  # Small latency
        return True

    monitor.register_service(
        "healthy_service",
        healthy_check,
        HealthCheckConfig(latency_warning_ms=100.0)
    )

    result = await monitor.check_service_health("healthy_service")
    assert result.status == HealthStatus.HEALTHY
    assert result.response_time_ms < 100


@pytest.mark.asyncio
async def test_health_monitor_check_degraded():
    """Test health check detects degraded service"""
    monitor = HealthMonitor()

    async def slow_check():
        await asyncio.sleep(0.15)  # Slow response
        return True

    monitor.register_service(
        "slow_service",
        slow_check,
        HealthCheckConfig(latency_warning_ms=100.0)
    )

    result = await monitor.check_service_health("slow_service")
    assert result.status == HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_health_monitor_check_unhealthy():
    """Test health check detects unhealthy service"""
    monitor = HealthMonitor()

    async def failing_check():
        raise Exception("Service unavailable")

    monitor.register_service("failing_service", failing_check)

    result = await monitor.check_service_health("failing_service")
    assert result.status == HealthStatus.UNHEALTHY
    assert result.error is not None


@pytest.mark.asyncio
async def test_health_monitor_alerts():
    """Test health monitor sends alerts"""
    monitor = HealthMonitor()
    alerts_received = []

    async def alert_handler(service: str, alert_type: str, details: Dict):
        alerts_received.append({
            "service": service,
            "type": alert_type,
            "details": details
        })

    monitor.register_alert_handler(alert_handler)

    # Create service that will trigger alerts
    async def failing_check():
        raise Exception("Failure")

    monitor.register_service(
        "alert_service",
        failing_check,
        HealthCheckConfig(
            error_rate_critical=0.5,
            alert_cooldown_seconds=0
        )
    )

    # Trigger multiple failures
    for _ in range(5):
        await monitor.check_service_health("alert_service")

    # Should have triggered alert
    await asyncio.sleep(0.1)  # Give time for async alert handling
    assert len(alerts_received) > 0


@pytest.mark.asyncio
async def test_health_monitor_summary():
    """Test health monitor summary report"""
    monitor = HealthMonitor()

    async def healthy_check():
        return True

    async def unhealthy_check():
        raise Exception("Failed")

    monitor.register_service("healthy_1", healthy_check)
    monitor.register_service("healthy_2", healthy_check)
    monitor.register_service("unhealthy_1", unhealthy_check)

    # Run checks
    await monitor.check_service_health("healthy_1")
    await monitor.check_service_health("healthy_2")
    await monitor.check_service_health("unhealthy_1")

    summary = monitor.get_health_summary()

    assert summary["total_services"] == 3
    assert summary["healthy"] >= 2
    assert summary["unhealthy"] >= 1


# ============================================================================
# Fallback Handler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_fallback_handler_cache():
    """Test fallback handler caching"""
    handler = FallbackHandler()

    # Save to cache
    handler.save_to_cache("test_service", "key1", {"data": "value"})

    # Retrieve from cache
    result = handler.get_from_cache("test_service", "key1")

    assert result is not None
    assert result.from_cache is True
    assert result.data == {"data": "value"}


@pytest.mark.asyncio
async def test_fallback_handler_cache_expiration():
    """Test cache expiration"""
    handler = FallbackHandler(
        config=FallbackConfig(cache_ttl_seconds=1)
    )

    handler.save_to_cache("test_service", "key1", "value")

    # Should be in cache
    result1 = handler.get_from_cache("test_service", "key1")
    assert result1 is not None

    # Wait for expiration
    await asyncio.sleep(1.1)

    # Should be expired
    result2 = handler.get_from_cache("test_service", "key1")
    assert result2 is None


@pytest.mark.asyncio
async def test_fallback_handler_queue():
    """Test request queueing"""
    handler = FallbackHandler()

    async def test_func():
        return "result"

    request_id = handler.queue_for_retry(
        "test_service",
        test_func,
        args=(),
        kwargs={}
    )

    assert request_id != ""
    assert handler._queue.size() == 1

    queue_status = handler.get_queue_status()
    assert len(queue_status) == 1
    assert queue_status[0]["service"] == "test_service"


@pytest.mark.asyncio
async def test_fallback_handler_with_registered_fallback():
    """Test fallback handler with registered fallback function"""
    handler = FallbackHandler()

    def fallback_func(*args, **kwargs):
        return "fallback_value"

    handler.register_fallback("test_service", fallback_func)

    async def failing_func():
        raise Exception("Primary failed")

    result = await handler.execute_with_fallback(
        "test_service",
        failing_func
    )

    assert result.strategy == FallbackStrategy.ALTERNATE_SERVICE
    assert result.data == "fallback_value"


@pytest.mark.asyncio
async def test_fallback_handler_stats():
    """Test fallback handler statistics"""
    handler = FallbackHandler()

    # Add some cache operations
    handler.save_to_cache("service1", "key1", "value1")
    handler.get_from_cache("service1", "key1")  # Hit
    handler.get_from_cache("service1", "key2")  # Miss

    stats = handler.get_stats()

    assert stats["cache_hits"] == 1
    assert stats["cache_misses"] == 1
    assert stats["cache_hit_rate"] > 0


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_circuit_breaker_registry():
    """Test circuit breaker registry"""
    # Clear registry first
    registry._breakers.clear()

    # Register breakers
    breaker1 = registry.register("service1", CircuitBreakerConfig())
    breaker2 = registry.register("service2", CircuitBreakerConfig())

    assert registry.get("service1") == breaker1
    assert registry.get("service2") == breaker2

    all_breakers = registry.get_all()
    assert len(all_breakers) == 2

    # Get all metrics
    all_metrics = registry.get_all_metrics()
    assert len(all_metrics) == 2


@pytest.mark.asyncio
async def test_full_circuit_breaker_lifecycle():
    """Test complete lifecycle: closed -> open -> half-open -> closed"""
    breaker = CircuitBreaker(
        name="lifecycle_test",
        config=CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=0.1,
            min_throughput=1
        )
    )

    # Start in closed state
    assert breaker.is_closed

    # Cause failures to open
    async def failing():
        raise Exception("Error")

    for _ in range(2):
        with pytest.raises(Exception):
            await breaker.call(failing)

    assert breaker.is_open

    # Rejected while open
    with pytest.raises(CircuitBreakerError):
        await breaker.call(failing)

    # Wait for timeout
    await asyncio.sleep(0.15)

    # Should transition to half-open on next call
    async def succeeding():
        return "ok"

    result1 = await breaker.call(succeeding)
    assert breaker.is_half_open

    # Second success should close
    result2 = await breaker.call(succeeding)
    assert breaker.is_closed

    metrics = breaker.get_metrics()
    assert metrics["successful_requests"] >= 2
    assert metrics["failed_requests"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
