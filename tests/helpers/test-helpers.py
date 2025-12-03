"""
Test Helper Functions (Python)
Agent 29 of 30
"""

import random
import string
import time
from typing import Any, Callable, Dict, List
from functools import wraps


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """
    Wait for a condition to become true.

    Args:
        condition: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds

    Returns:
        True if condition met, False if timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(interval)

    return False


def generate_random_string(length: int = 10) -> str:
    """Generate random alphanumeric string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    """Generate random test email address."""
    return f"test-{generate_random_string()}@example.com"


def create_mock_features() -> Dict[str, Any]:
    """Create mock feature set for ML predictions."""
    return {
        'hook_type': random.choice(['problem_solution', 'curiosity', 'testimonial']),
        'hook_strength': random.uniform(5.0, 10.0),
        'visual_complexity': random.uniform(4.0, 9.0),
        'audience_size': random.randint(1000000, 5000000),
        'account_avg_roas': random.uniform(2.0, 4.5),
        'account_avg_ctr': random.uniform(1.0, 3.0),
        'cpm_estimate': random.uniform(8.0, 20.0)
    }


def assert_response_time(response_time: float, max_time: float, message: str = None):
    """
    Assert that response time is within acceptable limit.

    Args:
        response_time: Actual response time in seconds
        max_time: Maximum acceptable time in seconds
        message: Optional custom error message
    """
    if message is None:
        message = f"Response time {response_time:.3f}s exceeds limit of {max_time}s"

    assert response_time <= max_time, message


def measure_execution_time(func: Callable) -> tuple:
    """
    Measure execution time of a function.

    Returns:
        Tuple of (result, execution_time_seconds)
    """
    start_time = time.time()
    result = func()
    execution_time = time.time() - start_time

    return result, execution_time


class PerformanceMonitor:
    """Monitor and record performance metrics."""

    def __init__(self):
        self.measurements: List[float] = []

    def record(self, duration: float):
        """Record a measurement."""
        self.measurements.append(duration)

    def get_stats(self) -> Dict[str, float]:
        """Get statistical summary of measurements."""
        if not self.measurements:
            return {}

        import statistics
        return {
            'count': len(self.measurements),
            'mean': statistics.mean(self.measurements),
            'median': statistics.median(self.measurements),
            'min': min(self.measurements),
            'max': max(self.measurements),
            'stdev': statistics.stdev(self.measurements) if len(self.measurements) > 1 else 0
        }

    def reset(self):
        """Reset all measurements."""
        self.measurements.clear()
