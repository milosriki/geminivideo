"""
Circuit Breaker System for GeminiVideo Platform
================================================

Comprehensive circuit breaker implementation to protect against cascading failures
when external APIs experience issues.

Components:
- CircuitBreaker: Core circuit breaker with state machine
- HealthMonitor: Continuous health monitoring with alerts
- FallbackHandler: Graceful degradation strategies
- Service-specific breakers: OpenAI, Anthropic, Meta

Author: Agent 9 - Circuit Breaker Builder
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    CircuitMetrics,
    CircuitBreakerRegistry,
    registry
)

from .health_monitor import (
    HealthMonitor,
    HealthCheckConfig,
    HealthStatus,
    HealthCheckResult,
    ServiceHealthMetrics,
    global_monitor
)

from .fallback_handler import (
    FallbackHandler,
    FallbackConfig,
    FallbackStrategy,
    FallbackResult,
    FallbackCache,
    RequestQueue,
    QueuedRequest,
    global_fallback_handler
)

from .openai_breaker import (
    OpenAICircuitBreaker,
    setup_openai_health_check
)

from .anthropic_breaker import (
    AnthropicCircuitBreaker,
    setup_anthropic_health_check
)

from .meta_breaker import (
    MetaCircuitBreaker,
    setup_meta_health_check
)

__all__ = [
    # Core circuit breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitState",
    "CircuitMetrics",
    "CircuitBreakerRegistry",
    "registry",

    # Health monitoring
    "HealthMonitor",
    "HealthCheckConfig",
    "HealthStatus",
    "HealthCheckResult",
    "ServiceHealthMetrics",
    "global_monitor",

    # Fallback handling
    "FallbackHandler",
    "FallbackConfig",
    "FallbackStrategy",
    "FallbackResult",
    "FallbackCache",
    "RequestQueue",
    "QueuedRequest",
    "global_fallback_handler",

    # Service-specific breakers
    "OpenAICircuitBreaker",
    "setup_openai_health_check",
    "AnthropicCircuitBreaker",
    "setup_anthropic_health_check",
    "MetaCircuitBreaker",
    "setup_meta_health_check",
]

__version__ = "1.0.0"
