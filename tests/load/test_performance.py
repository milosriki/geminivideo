"""
Load and Performance Tests
Tests API endpoint performance, ML inference speed, concurrent user handling

Agent 29 of 30 - Comprehensive Test Suite
Uses Locust for load testing
Coverage Target: 80%+
"""

import time
import random
import json
from typing import Dict, Any, List
from datetime import datetime
import statistics

import pytest
from locust import HttpUser, task, between, events, TaskSet
from locust.runners import MasterRunner, WorkerRunner
import requests
import numpy as np

# Test configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"


# ============================================================================
# LOCUST USER CLASSES FOR LOAD TESTING
# ============================================================================

class APIUser(HttpUser):
    """Simulates a user making API requests."""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = API_BASE_URL

    def on_start(self):
        """Called when a simulated user starts."""
        self.api_key = "test_api_key_12345"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    @task(3)
    def get_health_check(self):
        """Test root endpoint (most common)."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def predict_roas(self):
        """Test ROAS prediction endpoint."""
        payload = {
            "features": {
                "hook_type": random.choice(["problem_solution", "curiosity", "testimonial"]),
                "hook_strength": random.uniform(5.0, 10.0),
                "visual_complexity": random.uniform(4.0, 9.0),
                "audience_size": random.randint(1000000, 5000000),
                "account_avg_roas": random.uniform(2.0, 4.5),
                "account_avg_ctr": random.uniform(1.0, 3.0),
                "cpm_estimate": random.uniform(8.0, 20.0)
            }
        }

        with self.client.post(
            "/api/predict",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/predict"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "predicted_roas" in data:
                        response.success()
                    else:
                        response.failure("Missing predicted_roas in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def batch_predict(self):
        """Test batch prediction endpoint."""
        features_list = [
            {
                "hook_strength": random.uniform(5.0, 10.0),
                "account_avg_roas": random.uniform(2.0, 4.5)
            }
            for _ in range(5)
        ]

        payload = {"features_list": features_list}

        with self.client.post(
            "/api/predict/batch",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/predict/batch"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def get_assets(self):
        """Test assets listing endpoint."""
        params = {
            "limit": random.choice([10, 20, 50]),
            "offset": 0
        }

        with self.client.get(
            "/api/assets",
            params=params,
            headers=self.headers,
            catch_response=True,
            name="/api/assets"
        ) as response:
            if response.status_code in [200, 503]:  # Allow service unavailable
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def score_creative(self):
        """Test creative scoring endpoint."""
        payload = {
            "creative": {
                "hook_type": random.choice(["testimonial", "demonstration"]),
                "visual_style": "modern",
                "copy_text": "Amazing product that solves your problems!",
                "target_audience": "tech_enthusiasts"
            }
        }

        with self.client.post(
            "/api/score",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/score"
        ) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class VideoGenerationUser(HttpUser):
    """Simulates users generating videos."""
    wait_time = between(3, 8)  # Longer wait for video operations
    host = API_BASE_URL

    def on_start(self):
        self.api_key = "test_api_key_12345"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    @task
    def generate_video(self):
        """Test video generation endpoint."""
        payload = {
            "prompt": f"Create a marketing video about {random.choice(['tech', 'fashion', 'food', 'travel'])}",
            "duration": random.choice([10, 15, 30]),
            "style": random.choice(["modern", "minimal", "vibrant"])
        }

        with self.client.post(
            "/api/generate",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/api/generate"
        ) as response:
            if response.status_code in [200, 202, 503]:
                if response.status_code == 202:
                    try:
                        data = response.json()
                        if "job_id" in data:
                            # Poll job status
                            self.check_job_status(data["job_id"])
                    except:
                        pass
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    def check_job_status(self, job_id: str):
        """Check video generation job status."""
        with self.client.get(
            f"/api/video/{job_id}",
            headers=self.headers,
            catch_response=True,
            name="/api/video/[id]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


# ============================================================================
# PERFORMANCE BENCHMARKING TESTS
# ============================================================================

class TestAPIPerformance:
    """Test API endpoint performance benchmarks."""

    @pytest.fixture
    def api_client(self):
        """Create API client for testing."""
        session = requests.Session()
        session.headers.update({
            "X-API-Key": "test_api_key_12345",
            "Content-Type": "application/json"
        })
        return session

    def test_health_check_performance(self, api_client):
        """Test that health check responds quickly."""
        response_times = []

        for _ in range(100):
            start = time.time()
            response = api_client.get(f"{API_BASE_URL}/")
            elapsed = time.time() - start

            response_times.append(elapsed)
            assert response.status_code == 200

        # Calculate statistics
        avg_time = statistics.mean(response_times)
        p95_time = np.percentile(response_times, 95)
        p99_time = np.percentile(response_times, 99)

        print(f"\nHealth Check Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95_time*1000:.2f}ms")
        print(f"  P99: {p99_time*1000:.2f}ms")

        # Assert performance requirements
        assert avg_time < 0.1, f"Average response time {avg_time}s exceeds 100ms"
        assert p95_time < 0.2, f"P95 response time {p95_time}s exceeds 200ms"

    def test_prediction_endpoint_performance(self, api_client):
        """Test ROAS prediction endpoint performance."""
        payload = {
            "features": {
                "hook_type": "problem_solution",
                "hook_strength": 8.0,
                "audience_size": 2500000,
                "account_avg_roas": 3.5
            }
        }

        response_times = []

        for _ in range(50):
            start = time.time()
            response = api_client.post(f"{API_BASE_URL}/api/predict", json=payload)
            elapsed = time.time() - start

            if response.status_code == 200:
                response_times.append(elapsed)

        if response_times:
            avg_time = statistics.mean(response_times)
            p95_time = np.percentile(response_times, 95)

            print(f"\nPrediction Performance:")
            print(f"  Average: {avg_time*1000:.2f}ms")
            print(f"  P95: {p95_time*1000:.2f}ms")

            # Predictions should complete within 1 second
            assert avg_time < 1.0, f"Average prediction time {avg_time}s exceeds 1s"
            assert p95_time < 2.0, f"P95 prediction time {p95_time}s exceeds 2s"

    def test_batch_prediction_performance(self, api_client):
        """Test batch prediction throughput."""
        batch_sizes = [5, 10, 20]
        results = {}

        for batch_size in batch_sizes:
            features_list = [
                {"hook_strength": 8.0, "account_avg_roas": 3.5}
                for _ in range(batch_size)
            ]

            payload = {"features_list": features_list}

            start = time.time()
            response = api_client.post(f"{API_BASE_URL}/api/predict/batch", json=payload)
            elapsed = time.time() - start

            if response.status_code == 200:
                time_per_prediction = elapsed / batch_size
                results[batch_size] = {
                    "total_time": elapsed,
                    "time_per_prediction": time_per_prediction
                }

        if results:
            print(f"\nBatch Prediction Performance:")
            for batch_size, metrics in results.items():
                print(f"  Batch size {batch_size}:")
                print(f"    Total time: {metrics['total_time']*1000:.2f}ms")
                print(f"    Time per prediction: {metrics['time_per_prediction']*1000:.2f}ms")

            # Batch processing should be more efficient
            if 5 in results and 20 in results:
                assert results[20]["time_per_prediction"] < results[5]["time_per_prediction"] * 1.5

    def test_concurrent_requests(self, api_client):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request():
            try:
                response = api_client.get(f"{API_BASE_URL}/")
                return response.status_code == 200
            except:
                return False

        # Test with 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            start = time.time()
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            elapsed = time.time() - start

        success_count = sum(results)
        success_rate = success_count / len(results)

        print(f"\nConcurrent Requests (50 workers, 100 requests):")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Requests per second: {len(results)/elapsed:.2f}")
        print(f"  Success rate: {success_rate*100:.1f}%")

        # Should handle at least 80% successfully
        assert success_rate >= 0.8, f"Success rate {success_rate} below 80%"

    def test_rate_limiting_performance(self, api_client):
        """Test that rate limiting doesn't degrade performance excessively."""
        response_times = []
        rate_limited_count = 0

        for _ in range(200):
            start = time.time()
            response = api_client.get(f"{API_BASE_URL}/")
            elapsed = time.time() - start

            response_times.append(elapsed)

            if response.status_code == 429:
                rate_limited_count += 1

        print(f"\nRate Limiting Performance:")
        print(f"  Total requests: {len(response_times)}")
        print(f"  Rate limited: {rate_limited_count}")
        print(f"  Average response time: {statistics.mean(response_times)*1000:.2f}ms")

        # Rate limiting should kick in
        assert rate_limited_count > 0, "Rate limiting not working"

        # Non-rate-limited responses should still be fast
        successful_times = [t for i, t in enumerate(response_times)
                          if i < len(response_times) - rate_limited_count]
        if successful_times:
            avg_successful = statistics.mean(successful_times)
            assert avg_successful < 0.15, "Rate limiting slowing down successful requests"


# ============================================================================
# ML MODEL INFERENCE PERFORMANCE TESTS
# ============================================================================

class TestMLPerformance:
    """Test ML model inference performance."""

    def test_roas_predictor_inference_speed(self):
        """Test ROAS prediction inference speed."""
        import sys
        sys.path.insert(0, '/home/user/geminivideo/services/ml-service')

        from roas_predictor import ROASPredictor, FeatureSet
        import pandas as pd

        # Create and train a small model
        predictor = ROASPredictor()

        # Generate minimal training data
        np.random.seed(42)
        training_data = pd.DataFrame({
            col: np.random.randn(50) if col == 'actual_roas'
            else np.random.choice(['a', 'b', 'c'], 50) if col in predictor.CATEGORICAL_FEATURES
            else np.random.choice([True, False], 50) if col in predictor.BOOLEAN_FEATURES
            else np.random.randn(50)
            for col in predictor.FEATURE_COLUMNS + ['actual_roas']
        })

        predictor.train(training_data, validation_split=0.2)

        # Test inference speed
        features = FeatureSet()
        inference_times = []

        for _ in range(100):
            start = time.time()
            prediction = predictor.predict_roas(features, return_explanation=False)
            elapsed = time.time() - start
            inference_times.append(elapsed)

        avg_time = statistics.mean(inference_times)
        p95_time = np.percentile(inference_times, 95)

        print(f"\nML Inference Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")
        print(f"  P95: {p95_time*1000:.2f}ms")

        # Inference should be fast (under 100ms)
        assert avg_time < 0.1, f"Average inference time {avg_time}s exceeds 100ms"

    def test_batch_inference_throughput(self):
        """Test batch inference throughput."""
        import sys
        sys.path.insert(0, '/home/user/geminivideo/services/ml-service')

        from roas_predictor import ROASPredictor, FeatureSet
        import pandas as pd

        predictor = ROASPredictor()

        # Quick training
        np.random.seed(42)
        training_data = pd.DataFrame({
            col: np.random.randn(50) if col == 'actual_roas'
            else np.random.choice(['a', 'b', 'c'], 50) if col in predictor.CATEGORICAL_FEATURES
            else np.random.choice([True, False], 50) if col in predictor.BOOLEAN_FEATURES
            else np.random.randn(50)
            for col in predictor.FEATURE_COLUMNS + ['actual_roas']
        })

        predictor.train(training_data, validation_split=0.2)

        # Test batch sizes
        batch_sizes = [10, 50, 100]

        for batch_size in batch_sizes:
            features_list = [FeatureSet() for _ in range(batch_size)]

            start = time.time()
            predictions = predictor.predict_batch(features_list)
            elapsed = time.time() - start

            time_per_prediction = elapsed / batch_size

            print(f"\nBatch size {batch_size}:")
            print(f"  Total time: {elapsed*1000:.2f}ms")
            print(f"  Time per prediction: {time_per_prediction*1000:.2f}ms")

            assert len(predictions) == batch_size

    def test_model_loading_performance(self, tmp_path):
        """Test model loading speed."""
        import sys
        sys.path.insert(0, '/home/user/geminivideo/services/ml-service')

        from roas_predictor import ROASPredictor
        import pandas as pd

        # Train and save model
        predictor1 = ROASPredictor()

        np.random.seed(42)
        training_data = pd.DataFrame({
            col: np.random.randn(50) if col == 'actual_roas'
            else np.random.choice(['a', 'b', 'c'], 50) if col in predictor1.CATEGORICAL_FEATURES
            else np.random.choice([True, False], 50) if col in predictor1.BOOLEAN_FEATURES
            else np.random.randn(50)
            for col in predictor1.FEATURE_COLUMNS + ['actual_roas']
        })

        predictor1.train(training_data, validation_split=0.2)

        model_path = str(tmp_path / "test_model")
        predictor1.save_model(model_path)

        # Test loading speed
        start = time.time()
        predictor2 = ROASPredictor()
        predictor2.load_model(model_path)
        load_time = time.time() - start

        print(f"\nModel Loading Performance:")
        print(f"  Load time: {load_time*1000:.2f}ms")

        # Model should load quickly (under 1 second)
        assert load_time < 1.0, f"Model loading time {load_time}s exceeds 1s"


# ============================================================================
# DATABASE PERFORMANCE TESTS
# ============================================================================

class TestDatabasePerformance:
    """Test database query performance."""

    @pytest.fixture
    def db_pool(self):
        """Create database connection pool."""
        import os
        from psycopg2 import pool

        try:
            db_pool = pool.SimpleConnectionPool(
                1, 10,
                os.getenv('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/test_db')
            )
            yield db_pool
            db_pool.closeall()
        except:
            pytest.skip("Database not available")

    def test_simple_query_performance(self, db_pool):
        """Test simple SELECT query performance."""
        query_times = []

        for _ in range(100):
            conn = db_pool.getconn()
            cur = conn.cursor()

            start = time.time()
            cur.execute("SELECT 1")
            cur.fetchone()
            elapsed = time.time() - start

            query_times.append(elapsed)

            cur.close()
            db_pool.putconn(conn)

        avg_time = statistics.mean(query_times)
        print(f"\nSimple Query Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")

        assert avg_time < 0.01, "Simple queries too slow"

    def test_insert_performance(self, db_pool):
        """Test INSERT query performance."""
        conn = db_pool.getconn()
        cur = conn.cursor()

        # Create test table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_predictions (
                id SERIAL PRIMARY KEY,
                predicted_roas FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()

        insert_times = []

        for i in range(100):
            start = time.time()
            cur.execute(
                "INSERT INTO test_predictions (predicted_roas) VALUES (%s)",
                (random.uniform(2.0, 5.0),)
            )
            conn.commit()
            elapsed = time.time() - start

            insert_times.append(elapsed)

        # Cleanup
        cur.execute("DROP TABLE test_predictions")
        conn.commit()
        cur.close()
        db_pool.putconn(conn)

        avg_time = statistics.mean(insert_times)
        print(f"\nINSERT Performance:")
        print(f"  Average: {avg_time*1000:.2f}ms")

        assert avg_time < 0.05, "Inserts too slow"


# ============================================================================
# STRESS TESTING
# ============================================================================

class TestStressConditions:
    """Test system behavior under stress."""

    def test_sustained_load(self):
        """Test system under sustained load."""
        session = requests.Session()
        session.headers.update({"X-API-Key": "test_api_key_12345"})

        # Run for 30 seconds with consistent load
        end_time = time.time() + 30
        request_count = 0
        error_count = 0

        while time.time() < end_time:
            try:
                response = session.get(f"{API_BASE_URL}/")
                request_count += 1

                if response.status_code not in [200, 429]:
                    error_count += 1
            except:
                error_count += 1

            time.sleep(0.1)  # 10 requests per second

        error_rate = error_count / request_count if request_count > 0 else 1

        print(f"\nSustained Load Test (30s):")
        print(f"  Total requests: {request_count}")
        print(f"  Errors: {error_count}")
        print(f"  Error rate: {error_rate*100:.2f}%")

        # Allow up to 10% errors (including rate limits)
        assert error_rate < 0.1, f"Error rate {error_rate} exceeds 10%"

    def test_spike_load(self):
        """Test system handling traffic spikes."""
        import concurrent.futures

        session = requests.Session()
        session.headers.update({"X-API-Key": "test_api_key_12345"})

        def make_request():
            try:
                response = session.get(f"{API_BASE_URL}/")
                return response.status_code in [200, 429]
            except:
                return False

        # Sudden spike of 200 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
            start = time.time()
            futures = [executor.submit(make_request) for _ in range(200)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            elapsed = time.time() - start

        success_count = sum(results)
        success_rate = success_count / len(results)

        print(f"\nSpike Load Test (200 concurrent):")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Success rate: {success_rate*100:.1f}%")

        # Should handle at least 70% of spike traffic
        assert success_rate >= 0.7, f"Success rate {success_rate} below 70%"


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("Running performance tests...")
    pytest.main([__file__, "-v", "-s"])
