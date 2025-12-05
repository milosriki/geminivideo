"""
GeminiVideo Monitoring & Observability Package

Provides comprehensive monitoring, logging, and alerting for production operations.
"""

__version__ = "1.0.0"

# Import main modules for convenience
from .metrics import (
    # HTTP metrics
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes,
    http_exceptions_total,

    # AI API metrics
    ai_api_calls_total,
    ai_api_tokens_total,
    ai_api_cost_total,
    ai_api_duration_seconds,
    ai_api_errors_total,
    ai_cache_hits_total,
    ai_cache_misses_total,

    # Business metrics
    campaigns_created_total,
    ads_published_total,
    prediction_accuracy,
    roas_value,
    video_generation_total,
    video_processing_duration_seconds,

    # System metrics
    database_connections,
    database_query_duration_seconds,
    database_errors_total,
    queue_depth,
    queue_processing_duration_seconds,
    redis_operations_total,
    redis_operation_duration_seconds,
    service_health,

    # Helper functions
    track_ai_call,
    track_tokens,
    track_cache,
    track_database_query,
    update_service_info,
    set_service_health,
    calculate_cost,
    track_ai_call_with_cost,
)

from .logging_config import (
    setup_logging,
    StructuredLogger,
    generate_correlation_id,
    set_correlation_id,
    get_correlation_id,
    with_correlation_id,
    log_request,
    log_response,
    log_ai_call,
    log_database_query,
    log_business_event,
    log_health_check,
    log_error,
    track_performance,
    mask_sensitive_data,
)

from .alerting import (
    AlertManager,
    Alert,
    Severity,
    Threshold,
    EmailChannel,
    SlackChannel,
    PagerDutyChannel,
    setup_alerting_from_env,
)

__all__ = [
    # Version
    '__version__',

    # Metrics
    'http_requests_total',
    'http_request_duration_seconds',
    'http_request_size_bytes',
    'http_response_size_bytes',
    'http_exceptions_total',
    'ai_api_calls_total',
    'ai_api_tokens_total',
    'ai_api_cost_total',
    'ai_api_duration_seconds',
    'ai_api_errors_total',
    'ai_cache_hits_total',
    'ai_cache_misses_total',
    'campaigns_created_total',
    'ads_published_total',
    'prediction_accuracy',
    'roas_value',
    'video_generation_total',
    'video_processing_duration_seconds',
    'database_connections',
    'database_query_duration_seconds',
    'database_errors_total',
    'queue_depth',
    'queue_processing_duration_seconds',
    'redis_operations_total',
    'redis_operation_duration_seconds',
    'service_health',
    'track_ai_call',
    'track_tokens',
    'track_cache',
    'track_database_query',
    'update_service_info',
    'set_service_health',
    'calculate_cost',
    'track_ai_call_with_cost',

    # Logging
    'setup_logging',
    'StructuredLogger',
    'generate_correlation_id',
    'set_correlation_id',
    'get_correlation_id',
    'with_correlation_id',
    'log_request',
    'log_response',
    'log_ai_call',
    'log_database_query',
    'log_business_event',
    'log_health_check',
    'log_error',
    'track_performance',
    'mask_sensitive_data',

    # Alerting
    'AlertManager',
    'Alert',
    'Severity',
    'Threshold',
    'EmailChannel',
    'SlackChannel',
    'PagerDutyChannel',
    'setup_alerting_from_env',
]
