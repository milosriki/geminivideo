"""
FastAPI middleware for Prometheus metrics and structured logging.

Usage:
    from monitoring.middleware.fastapi_middleware import setup_monitoring

    app = FastAPI()
    setup_monitoring(app, service_name="my-service")
"""

import time
import os
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Import monitoring modules
import sys
from pathlib import Path

# Add parent directory to path for imports
monitoring_dir = Path(__file__).parent.parent
sys.path.insert(0, str(monitoring_dir))

from metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes,
    http_exceptions_total,
    get_metrics,
    get_content_type,
    update_service_info,
    set_service_health,
)
from logging_config import (
    setup_logging,
    set_correlation_id,
    get_correlation_id,
    generate_correlation_id,
    log_request,
    log_response,
    log_error,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP metrics."""

    def __init__(self, app: ASGIApp, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', generate_correlation_id())
        set_correlation_id(correlation_id)

        # Track request size
        content_length = request.headers.get('content-length', 0)
        try:
            request_size = int(content_length)
        except (ValueError, TypeError):
            request_size = 0

        # Start timer
        start_time = time.time()
        status_code = 500
        exception_type = None

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Track response size
            response_size = 0
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                try:
                    response_size = int(response.headers['content-length'])
                except (ValueError, TypeError):
                    pass

            # Add correlation ID to response
            response.headers['X-Correlation-ID'] = correlation_id

            return response

        except Exception as e:
            exception_type = type(e).__name__
            http_exceptions_total.labels(
                service=self.service_name,
                exception_type=exception_type
            ).inc()
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Get endpoint path
            endpoint = request.url.path
            method = request.method

            # Track metrics
            http_requests_total.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()

            http_request_duration_seconds.labels(
                service=self.service_name,
                method=method,
                endpoint=endpoint
            ).observe(duration)

            if request_size > 0:
                http_request_size_bytes.labels(
                    service=self.service_name,
                    method=method,
                    endpoint=endpoint
                ).observe(request_size)

            if 'response_size' in locals() and response_size > 0:
                http_response_size_bytes.labels(
                    service=self.service_name,
                    method=method,
                    endpoint=endpoint
                ).observe(response_size)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    def __init__(self, app: ASGIApp, logger, service_name: str):
        super().__init__(app)
        self.logger = logger
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get correlation ID
        correlation_id = get_correlation_id()

        # Log request
        log_request(
            self.logger,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=dict(request.headers),
            correlation_id=correlation_id
        )

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            log_response(
                self.logger,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                correlation_id=correlation_id
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            log_error(
                self.logger,
                error=e,
                context={
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'correlation_id': correlation_id
                }
            )
            raise


def setup_monitoring(
    app: FastAPI,
    service_name: str,
    environment: str = None,
    version: str = None,
    log_level: str = 'INFO'
) -> None:
    """
    Setup monitoring for FastAPI application.

    Args:
        app: FastAPI application instance
        service_name: Name of the service
        environment: Environment (production, staging, development)
        version: Service version
        log_level: Logging level
    """
    # Get environment from env var if not provided
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'production')

    # Get version from env var if not provided
    if version is None:
        version = os.getenv('SERVICE_VERSION', '1.0.0')

    # Setup logging
    logger = setup_logging(
        service_name=service_name,
        environment=environment,
        log_level=log_level,
        log_file=os.getenv('LOG_FILE'),
        retention_days=int(os.getenv('LOG_RETENTION_DAYS', '30'))
    )

    # Update service info
    update_service_info(service_name, version, environment)

    # Set service health to healthy
    set_service_health(service_name, healthy=True)

    # Add middleware (order matters - metrics first, then logging)
    app.add_middleware(MetricsMiddleware, service_name=service_name)
    app.add_middleware(LoggingMiddleware, logger=logger, service_name=service_name)

    # Add metrics endpoint
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(content=get_metrics(), media_type=get_content_type())

    # Add health endpoint
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "service": service_name}

    # Log startup
    logger.info(
        f"Monitoring initialized for {service_name}",
        version=version,
        environment=environment
    )


def track_background_task(service_name: str, task_name: str):
    """
    Decorator to track background task metrics.

    Usage:
        @track_background_task("my-service", "process_video")
        async def process_video(video_id: str):
            # Task code here
            pass
    """
    from functools import wraps
    from metrics import queue_processing_duration_seconds

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                queue_processing_duration_seconds.labels(
                    service=service_name,
                    queue_name='background_tasks',
                    message_type=task_name
                ).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                queue_processing_duration_seconds.labels(
                    service=service_name,
                    queue_name='background_tasks',
                    message_type=task_name
                ).observe(duration)

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Example usage
if __name__ == '__main__':
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="Example Service")

    # Setup monitoring
    setup_monitoring(
        app,
        service_name="example-service",
        environment="development",
        version="1.0.0"
    )

    # Example endpoint
    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.get("/error")
    async def error():
        raise ValueError("Example error")

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8000)
