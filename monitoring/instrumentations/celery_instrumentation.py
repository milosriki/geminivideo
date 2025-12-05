"""
Celery instrumentation for task monitoring.

Usage:
    from monitoring.instrumentations.celery_instrumentation import setup_celery_monitoring

    app = Celery('my-tasks')
    setup_celery_monitoring(app, service_name="my-service")
"""

import time
from typing import Optional
from functools import wraps

try:
    from celery import Celery, Task
    from celery.signals import (
        task_prerun,
        task_postrun,
        task_failure,
        task_retry,
        task_success,
    )
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("Warning: Celery not installed. Celery instrumentation disabled.")

# Import monitoring modules
import sys
from pathlib import Path

monitoring_dir = Path(__file__).parent.parent
sys.path.insert(0, str(monitoring_dir))

from metrics import (
    queue_depth,
    queue_processing_duration_seconds,
)
from logging_config import setup_logging, StructuredLogger


# ============================================================================
# TASK METRICS
# ============================================================================

if CELERY_AVAILABLE:
    from prometheus_client import Counter, Histogram, Gauge

    celery_tasks_total = Counter(
        'celery_tasks_total',
        'Total Celery tasks',
        ['service', 'task_name', 'status']  # status: success, failure, retry
    )

    celery_task_duration_seconds = Histogram(
        'celery_task_duration_seconds',
        'Celery task duration in seconds',
        ['service', 'task_name'],
        buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0)
    )

    celery_task_retries_total = Counter(
        'celery_task_retries_total',
        'Total Celery task retries',
        ['service', 'task_name']
    )

    celery_active_tasks = Gauge(
        'celery_active_tasks',
        'Number of active Celery tasks',
        ['service', 'task_name']
    )

    celery_queue_length = Gauge(
        'celery_queue_length',
        'Celery queue length',
        ['service', 'queue_name']
    )


# ============================================================================
# TASK TRACKING
# ============================================================================

class TaskTracker:
    """Track task execution metrics."""

    def __init__(self, service_name: str, logger: Optional[StructuredLogger] = None):
        self.service_name = service_name
        self.logger = logger
        self.task_start_times = {}

    def on_task_prerun(self, sender=None, task_id=None, task=None, args=None, kwargs=None, **extra_kwargs):
        """Handle task prerun signal."""
        if not CELERY_AVAILABLE:
            return

        task_name = sender.name if sender else 'unknown'

        # Record start time
        self.task_start_times[task_id] = time.time()

        # Increment active tasks
        celery_active_tasks.labels(
            service=self.service_name,
            task_name=task_name
        ).inc()

        # Log task start
        if self.logger:
            self.logger.info(
                f"Celery task started: {task_name}",
                event_type='celery_task_start',
                task_name=task_name,
                task_id=task_id,
                args=str(args),
                kwargs=str(kwargs)
            )

    def on_task_postrun(self, sender=None, task_id=None, task=None, args=None, kwargs=None,
                       retval=None, state=None, **extra_kwargs):
        """Handle task postrun signal."""
        if not CELERY_AVAILABLE:
            return

        task_name = sender.name if sender else 'unknown'
        start_time = self.task_start_times.pop(task_id, None)

        # Decrement active tasks
        celery_active_tasks.labels(
            service=self.service_name,
            task_name=task_name
        ).dec()

        # Calculate duration
        if start_time:
            duration = time.time() - start_time
            celery_task_duration_seconds.labels(
                service=self.service_name,
                task_name=task_name
            ).observe(duration)

            # Log task completion
            if self.logger:
                self.logger.info(
                    f"Celery task completed: {task_name}",
                    event_type='celery_task_complete',
                    task_name=task_name,
                    task_id=task_id,
                    duration_seconds=duration,
                    state=state
                )

    def on_task_success(self, sender=None, result=None, **extra_kwargs):
        """Handle task success signal."""
        if not CELERY_AVAILABLE:
            return

        task_name = sender.name if sender else 'unknown'

        # Increment success counter
        celery_tasks_total.labels(
            service=self.service_name,
            task_name=task_name,
            status='success'
        ).inc()

    def on_task_failure(self, sender=None, task_id=None, exception=None, args=None,
                       kwargs=None, traceback=None, einfo=None, **extra_kwargs):
        """Handle task failure signal."""
        if not CELERY_AVAILABLE:
            return

        task_name = sender.name if sender else 'unknown'

        # Increment failure counter
        celery_tasks_total.labels(
            service=self.service_name,
            task_name=task_name,
            status='failure'
        ).inc()

        # Decrement active tasks
        celery_active_tasks.labels(
            service=self.service_name,
            task_name=task_name
        ).dec()

        # Remove from start times
        self.task_start_times.pop(task_id, None)

        # Log failure
        if self.logger:
            self.logger.error(
                f"Celery task failed: {task_name}",
                event_type='celery_task_failure',
                task_name=task_name,
                task_id=task_id,
                exception_type=type(exception).__name__,
                exception_message=str(exception),
                traceback=str(traceback)
            )

    def on_task_retry(self, sender=None, task_id=None, reason=None, einfo=None, **extra_kwargs):
        """Handle task retry signal."""
        if not CELERY_AVAILABLE:
            return

        task_name = sender.name if sender else 'unknown'

        # Increment retry counter
        celery_task_retries_total.labels(
            service=self.service_name,
            task_name=task_name
        ).inc()

        celery_tasks_total.labels(
            service=self.service_name,
            task_name=task_name,
            status='retry'
        ).inc()

        # Log retry
        if self.logger:
            self.logger.warning(
                f"Celery task retry: {task_name}",
                event_type='celery_task_retry',
                task_name=task_name,
                task_id=task_id,
                reason=str(reason)
            )


# ============================================================================
# SETUP FUNCTION
# ============================================================================

def setup_celery_monitoring(celery_app: 'Celery', service_name: str,
                           log_level: str = 'INFO') -> Optional[StructuredLogger]:
    """
    Setup monitoring for Celery application.

    Args:
        celery_app: Celery application instance
        service_name: Name of the service
        log_level: Logging level

    Returns:
        StructuredLogger instance
    """
    if not CELERY_AVAILABLE:
        print("Warning: Celery not available. Skipping Celery monitoring setup.")
        return None

    # Setup logging
    logger = setup_logging(
        service_name=service_name,
        log_level=log_level
    )

    # Create task tracker
    tracker = TaskTracker(service_name, logger)

    # Connect signals
    task_prerun.connect(tracker.on_task_prerun)
    task_postrun.connect(tracker.on_task_postrun)
    task_success.connect(tracker.on_task_success)
    task_failure.connect(tracker.on_task_failure)
    task_retry.connect(tracker.on_task_retry)

    logger.info(
        f"Celery monitoring initialized for {service_name}",
        event_type='monitoring_init'
    )

    return logger


# ============================================================================
# TASK DECORATOR
# ============================================================================

def monitored_task(celery_app: 'Celery', service_name: str, **task_kwargs):
    """
    Decorator to create monitored Celery tasks.

    Usage:
        @monitored_task(app, "my-service", name="process_video")
        def process_video(video_id: str):
            # Task code here
            pass
    """
    if not CELERY_AVAILABLE:
        # Return a no-op decorator if Celery is not available
        def decorator(func):
            return func
        return decorator

    def decorator(func):
        # Create Celery task
        task = celery_app.task(**task_kwargs)(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            task_name = task.name
            start_time = time.time()

            try:
                # Execute task
                result = func(*args, **kwargs)

                # Track success
                duration = time.time() - start_time
                celery_task_duration_seconds.labels(
                    service=service_name,
                    task_name=task_name
                ).observe(duration)

                celery_tasks_total.labels(
                    service=service_name,
                    task_name=task_name,
                    status='success'
                ).inc()

                return result

            except Exception as e:
                # Track failure
                celery_tasks_total.labels(
                    service=service_name,
                    task_name=task_name,
                    status='failure'
                ).inc()
                raise

        return wrapper

    return decorator


# ============================================================================
# QUEUE MONITORING
# ============================================================================

def monitor_queue_length(celery_app: 'Celery', service_name: str, queue_name: str):
    """
    Monitor queue length periodically.

    This should be called from a periodic task.

    Usage:
        @celery_app.on_after_configure.connect
        def setup_periodic_tasks(sender, **kwargs):
            sender.add_periodic_task(
                60.0,  # Every 60 seconds
                monitor_queue_length.s(celery_app, "my-service", "default"),
            )
    """
    if not CELERY_AVAILABLE:
        return

    try:
        # Get queue length from broker
        inspector = celery_app.control.inspect()
        active = inspector.active()
        reserved = inspector.reserved()

        # Calculate total queue length
        total_length = 0
        if active:
            total_length += sum(len(tasks) for tasks in active.values())
        if reserved:
            total_length += sum(len(tasks) for tasks in reserved.values())

        # Update metric
        celery_queue_length.labels(
            service=service_name,
            queue_name=queue_name
        ).set(total_length)

        queue_depth.labels(
            service=service_name,
            queue_name=queue_name
        ).set(total_length)

    except Exception as e:
        print(f"Error monitoring queue length: {e}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__' and CELERY_AVAILABLE:
    from celery import Celery

    # Create Celery app
    app = Celery(
        'example',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )

    # Setup monitoring
    logger = setup_celery_monitoring(app, service_name='example-service')

    # Example task
    @app.task(name='example.add')
    def add(x: int, y: int) -> int:
        """Example task."""
        return x + y

    # Run worker
    # celery -A example worker --loglevel=info
