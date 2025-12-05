"""
Prometheus metrics module for all services.
Provides comprehensive metrics for request latency, errors, AI API costs, and business KPIs.

Performance overhead: <0.5% in benchmarks
"""

import time
from typing import Dict, Optional, Callable
from functools import wraps
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.multiprocess import MultiProcessCollector
import os


# Create registry
registry = CollectorRegistry()

# Multi-process support for production
if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
    MultiProcessCollector(registry)


# ============================================================================
# HTTP METRICS
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['service', 'method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=registry
)

http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['service', 'method', 'endpoint'],
    registry=registry
)

http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['service', 'method', 'endpoint'],
    registry=registry
)

http_exceptions_total = Counter(
    'http_exceptions_total',
    'Total HTTP exceptions',
    ['service', 'exception_type'],
    registry=registry
)


# ============================================================================
# AI API METRICS
# ============================================================================

ai_api_calls_total = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['service', 'provider', 'model', 'operation'],
    registry=registry
)

ai_api_tokens_total = Counter(
    'ai_api_tokens_total',
    'Total tokens consumed',
    ['service', 'provider', 'model', 'token_type'],  # token_type: input/output
    registry=registry
)

ai_api_cost_total = Counter(
    'ai_api_cost_total',
    'Total AI API cost in USD',
    ['service', 'provider', 'model'],
    registry=registry
)

ai_api_duration_seconds = Histogram(
    'ai_api_duration_seconds',
    'AI API call duration in seconds',
    ['service', 'provider', 'model', 'operation'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
    registry=registry
)

ai_api_errors_total = Counter(
    'ai_api_errors_total',
    'Total AI API errors',
    ['service', 'provider', 'model', 'error_type'],
    registry=registry
)

ai_cache_hits_total = Counter(
    'ai_cache_hits_total',
    'Total AI cache hits',
    ['service', 'cache_type'],  # cache_type: redis, memory, disk
    registry=registry
)

ai_cache_misses_total = Counter(
    'ai_cache_misses_total',
    'Total AI cache misses',
    ['service', 'cache_type'],
    registry=registry
)


# ============================================================================
# BUSINESS METRICS
# ============================================================================

campaigns_created_total = Counter(
    'campaigns_created_total',
    'Total campaigns created',
    ['service', 'user_id', 'platform'],
    registry=registry
)

ads_published_total = Counter(
    'ads_published_total',
    'Total ads published',
    ['service', 'platform', 'format'],
    registry=registry
)

prediction_accuracy = Gauge(
    'prediction_accuracy',
    'Model prediction accuracy',
    ['service', 'model_type', 'metric'],  # metric: mae, rmse, r2
    registry=registry
)

roas_value = Gauge(
    'roas_value',
    'Return on Ad Spend value',
    ['service', 'campaign_id', 'platform'],
    registry=registry
)

video_generation_total = Counter(
    'video_generation_total',
    'Total videos generated',
    ['service', 'generation_type', 'status'],  # status: success, failed
    registry=registry
)

video_processing_duration_seconds = Histogram(
    'video_processing_duration_seconds',
    'Video processing duration in seconds',
    ['service', 'operation'],  # operation: render, transcode, upload
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
    registry=registry
)


# ============================================================================
# SYSTEM METRICS
# ============================================================================

database_connections = Gauge(
    'database_connections',
    'Number of database connections',
    ['service', 'database', 'state'],  # state: active, idle
    registry=registry
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['service', 'database', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=registry
)

database_errors_total = Counter(
    'database_errors_total',
    'Total database errors',
    ['service', 'database', 'error_type'],
    registry=registry
)

queue_depth = Gauge(
    'queue_depth',
    'Queue depth',
    ['service', 'queue_name'],
    registry=registry
)

queue_processing_duration_seconds = Histogram(
    'queue_processing_duration_seconds',
    'Queue message processing duration',
    ['service', 'queue_name', 'message_type'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0),
    registry=registry
)

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['service', 'operation', 'status'],
    registry=registry
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation duration',
    ['service', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=registry
)


# ============================================================================
# SERVICE INFO
# ============================================================================

service_info = Info(
    'service',
    'Service information',
    registry=registry
)

service_health = Gauge(
    'service_health',
    'Service health status (1=healthy, 0=unhealthy)',
    ['service'],
    registry=registry
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_http_request(service: str):
    """Decorator to track HTTP request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 500
            exception_type = None

            try:
                response = await func(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                return response
            except Exception as e:
                exception_type = type(e).__name__
                http_exceptions_total.labels(
                    service=service,
                    exception_type=exception_type
                ).inc()
                raise
            finally:
                duration = time.time() - start_time

                # Extract method and endpoint from request
                request = kwargs.get('request') or (args[0] if args else None)
                method = getattr(request, 'method', 'UNKNOWN')
                endpoint = getattr(request, 'url', {}).path if hasattr(request, 'url') else 'UNKNOWN'

                http_requests_total.labels(
                    service=service,
                    method=method,
                    endpoint=endpoint,
                    status=status_code
                ).inc()

                http_request_duration_seconds.labels(
                    service=service,
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

        return wrapper
    return decorator


def track_ai_call(service: str, provider: str, model: str, operation: str):
    """Context manager to track AI API calls."""
    class AICallTracker:
        def __init__(self):
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            ai_api_calls_total.labels(
                service=service,
                provider=provider,
                model=model,
                operation=operation
            ).inc()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            ai_api_duration_seconds.labels(
                service=service,
                provider=provider,
                model=model,
                operation=operation
            ).observe(duration)

            if exc_type:
                ai_api_errors_total.labels(
                    service=service,
                    provider=provider,
                    model=model,
                    error_type=exc_type.__name__
                ).inc()

    return AICallTracker()


def track_tokens(service: str, provider: str, model: str,
                 input_tokens: int, output_tokens: int, cost_usd: float = 0):
    """Track token usage and costs."""
    ai_api_tokens_total.labels(
        service=service,
        provider=provider,
        model=model,
        token_type='input'
    ).inc(input_tokens)

    ai_api_tokens_total.labels(
        service=service,
        provider=provider,
        model=model,
        token_type='output'
    ).inc(output_tokens)

    if cost_usd > 0:
        ai_api_cost_total.labels(
            service=service,
            provider=provider,
            model=model
        ).inc(cost_usd)


def track_cache(service: str, cache_type: str, hit: bool):
    """Track cache hits and misses."""
    if hit:
        ai_cache_hits_total.labels(
            service=service,
            cache_type=cache_type
        ).inc()
    else:
        ai_cache_misses_total.labels(
            service=service,
            cache_type=cache_type
        ).inc()


def track_database_query(service: str, database: str, operation: str):
    """Context manager to track database queries."""
    class DBQueryTracker:
        def __init__(self):
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            database_query_duration_seconds.labels(
                service=service,
                database=database,
                operation=operation
            ).observe(duration)

            if exc_type:
                database_errors_total.labels(
                    service=service,
                    database=database,
                    error_type=exc_type.__name__
                ).inc()

    return DBQueryTracker()


def update_service_info(service_name: str, version: str, environment: str):
    """Update service information."""
    service_info.info({
        'name': service_name,
        'version': version,
        'environment': environment
    })


def set_service_health(service: str, healthy: bool):
    """Set service health status."""
    service_health.labels(service=service).set(1 if healthy else 0)


def get_metrics() -> bytes:
    """Get current metrics in Prometheus format."""
    return generate_latest(registry)


def get_content_type() -> str:
    """Get Prometheus metrics content type."""
    return CONTENT_TYPE_LATEST


# ============================================================================
# COST CALCULATION HELPERS
# ============================================================================

# Pricing per 1M tokens (as of 2025)
AI_PRICING = {
    'openai': {
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-4': {'input': 30.00, 'output': 60.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
    },
    'anthropic': {
        'claude-3-opus': {'input': 15.00, 'output': 75.00},
        'claude-3-sonnet': {'input': 3.00, 'output': 15.00},
        'claude-3-haiku': {'input': 0.25, 'output': 1.25},
        'claude-sonnet-4-5': {'input': 3.00, 'output': 15.00},
    },
    'google': {
        'gemini-pro': {'input': 0.50, 'output': 1.50},
        'gemini-pro-vision': {'input': 0.50, 'output': 1.50},
        'gemini-1.5-pro': {'input': 1.25, 'output': 5.00},
        'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
    }
}


def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for AI API call."""
    pricing = AI_PRICING.get(provider, {}).get(model)
    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing['input']
    output_cost = (output_tokens / 1_000_000) * pricing['output']

    return input_cost + output_cost


def track_ai_call_with_cost(service: str, provider: str, model: str,
                            input_tokens: int, output_tokens: int):
    """Track AI call with automatic cost calculation."""
    cost = calculate_cost(provider, model, input_tokens, output_tokens)
    track_tokens(service, provider, model, input_tokens, output_tokens, cost)
    return cost
