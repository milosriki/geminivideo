"""
Load Testing Script for Winner Ads Flow
Agent 18: Load Testing
Created: 2025-12-13

Uses Locust for distributed load testing of the GeminiVideo API.

Run with:
    locust -f winner_flow_load_test.py --host=http://localhost:8080

Or headless:
    locust -f winner_flow_load_test.py --host=http://localhost:8080 \
           --users 100 --spawn-rate 10 --run-time 5m --headless
"""

import os
import random
import json
import time
from typing import Dict, Any, List
from locust import HttpUser, task, between, tag, events
from locust.runners import MasterRunner, WorkerRunner

# ============================================================================
# Configuration
# ============================================================================

API_HOST = os.getenv("API_HOST", "http://localhost:8080")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "test-token")

# Test data
SAMPLE_AD_IDS = [f"ad_{i}" for i in range(1, 101)]
SAMPLE_CAMPAIGN_IDS = [f"campaign_{i}" for i in range(1, 21)]


# ============================================================================
# Event Hooks
# ============================================================================

@events.init.add_listener
def on_init(environment, **kwargs):
    """Initialize load test."""
    if isinstance(environment.runner, MasterRunner):
        print("🚀 Load test master starting...")
    elif isinstance(environment.runner, WorkerRunner):
        print(f"👷 Load test worker starting...")
    else:
        print("🔧 Load test local runner starting...")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("=" * 60)
    print("🎯 GeminiVideo Winner Flow Load Test")
    print(f"   Host: {API_HOST}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("=" * 60)
    print("✅ Load test completed")
    print("=" * 60)


# ============================================================================
# User Behavior Classes
# ============================================================================

class WinnerFlowUser(HttpUser):
    """
    Simulates a typical user interacting with the winner ads API.

    User journey:
    1. Check health
    2. Get recent winners
    3. View winner details
    4. Clone a winner
    5. Check budget reallocation
    6. View analytics
    """

    wait_time = between(1, 3)

    def on_start(self):
        """Called when user starts."""
        self.headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json",
            "X-Request-ID": f"load-test-{random.randint(1000, 9999)}"
        }
        self.cached_winners = []

    @task(1)
    @tag("health")
    def health_check(self):
        """Check API health."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Health degraded: {data.get('status')}")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(3)
    @tag("winners", "read")
    def get_recent_winners(self):
        """Get list of recent winners."""
        params = {
            "limit": random.choice([5, 10, 20]),
            "min_ctr": random.choice([0.02, 0.03, 0.04]),
            "min_roas": random.choice([1.5, 2.0, 2.5])
        }

        with self.client.get(
            "/api/winners/recent",
            params=params,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Cache winners for later use
                    self.cached_winners = [
                        w.get("ad_id") for w in data.get("winners", [])
                    ]
                    response.success()
                else:
                    response.failure("API returned success=false")
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    @tag("winners", "read")
    def get_winner_details(self):
        """Get details of a specific winner."""
        winner_id = random.choice(self.cached_winners or SAMPLE_AD_IDS)

        with self.client.get(
            f"/api/winners/{winner_id}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Expected for random IDs
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    @tag("winners", "write")
    def clone_winner(self):
        """Clone a winning ad."""
        winner_id = random.choice(self.cached_winners or SAMPLE_AD_IDS)

        payload = {
            "winner_ad_id": winner_id,
            "variations": random.randint(1, 5)
        }

        with self.client.post(
            "/api/winners/clone-winner",
            json=payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure("Clone failed")
            elif response.status_code == 400:
                # Validation error - still valid test
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    @tag("budget", "write")
    def reallocate_budget(self):
        """Trigger budget reallocation."""
        payload = {
            "account_id": "test_account",
            "max_reallocation_percent": random.randint(10, 30),
            "dry_run": True  # Always dry run for load tests
        }

        with self.client.post(
            "/api/winners/budget/reallocate",
            json=payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(2)
    @tag("analytics", "read")
    def get_winner_stats(self):
        """Get winner analytics."""
        with self.client.get(
            "/api/winners/stats",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    @tag("winners", "read")
    def find_similar_winners(self):
        """Find similar winners using RAG."""
        winner_id = random.choice(self.cached_winners or SAMPLE_AD_IDS)

        params = {
            "ad_id": winner_id,
            "k": random.choice([3, 5, 10])
        }

        with self.client.get(
            "/api/winners/similar",
            params=params,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class HighVolumeUser(HttpUser):
    """
    Simulates high-volume API consumer (e.g., internal service).
    Makes rapid requests to test system limits.
    """

    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

    @task(5)
    @tag("high-volume")
    def rapid_winner_fetch(self):
        """Rapidly fetch winners."""
        self.client.get(
            "/api/winners/recent",
            params={"limit": 10},
            headers=self.headers
        )

    @task(3)
    @tag("high-volume")
    def rapid_stats_fetch(self):
        """Rapidly fetch stats."""
        self.client.get("/api/winners/stats", headers=self.headers)

    @task(1)
    @tag("high-volume")
    def rapid_health_check(self):
        """Rapid health checks."""
        self.client.get("/health")


class BurstUser(HttpUser):
    """
    Simulates burst traffic patterns.
    Makes many requests quickly, then waits.
    """

    wait_time = between(5, 10)  # Long wait between bursts

    def on_start(self):
        self.headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

    @task
    @tag("burst")
    def burst_requests(self):
        """Send burst of requests."""
        # Make 10 rapid requests
        for _ in range(10):
            self.client.get(
                "/api/winners/recent",
                params={"limit": 5},
                headers=self.headers
            )
            time.sleep(0.05)  # 50ms between requests


# ============================================================================
# Custom Metrics Reporting
# ============================================================================

class MetricsReporter:
    """Custom metrics reporting for load tests."""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times: List[float] = []

    def record_request(self, response_time: float, success: bool):
        """Record a request."""
        self.request_count += 1
        self.response_times.append(response_time)
        if not success:
            self.error_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get summary metrics."""
        if not self.response_times:
            return {"error": "No data"}

        sorted_times = sorted(self.response_times)
        p50_idx = int(len(sorted_times) * 0.5)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)

        return {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1) * 100,
            "avg_response_time_ms": sum(self.response_times) / len(self.response_times),
            "p50_response_time_ms": sorted_times[p50_idx],
            "p95_response_time_ms": sorted_times[p95_idx],
            "p99_response_time_ms": sorted_times[p99_idx],
            "min_response_time_ms": min(self.response_times),
            "max_response_time_ms": max(self.response_times)
        }


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import subprocess
    import sys

    print("🚀 Starting GeminiVideo Load Test")
    print("=" * 60)
    print(f"Target: {API_HOST}")
    print("=" * 60)
    print()
    print("Run with Locust:")
    print(f"  locust -f {__file__} --host={API_HOST}")
    print()
    print("Or headless:")
    print(f"  locust -f {__file__} --host={API_HOST} --users 100 --spawn-rate 10 --run-time 5m --headless")
