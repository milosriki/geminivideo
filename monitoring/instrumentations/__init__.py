"""Instrumentation components for various frameworks."""

try:
    from .celery_instrumentation import (
        setup_celery_monitoring,
        monitored_task,
        monitor_queue_length
    )
    __all__ = ['setup_celery_monitoring', 'monitored_task', 'monitor_queue_length']
except ImportError:
    # Celery not available
    __all__ = []
