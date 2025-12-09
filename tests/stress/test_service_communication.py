"""
Stress Test: Service-to-Service Communication
Tests all inter-service API calls and integrations
Covers: Gateway → ML Service, Gateway → Titan-Core, Gateway → Video Agent, etc.
"""
import asyncio
import time
import random
import numpy as np
from typing import List, Dict, Any
import httpx
import logging
import uuid

logger = logging.getLogger(__name__)

GATEWAY_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8004"
TITAN_CORE_URL = "http://localhost:8005"
VIDEO_AGENT_URL = "http://localhost:8002"
DRIVE_INTEL_URL = "http://localhost:8001"
META_PUBLISHER_URL = "http://localhost:8003"


class ServiceCommunicationTester:
    """Test service-to-service communication"""
    
    async def test_gateway_to_ml_service(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Gateway API → ML Service communication"""
        start_time = time.time()
        
        try:
            # Test CTR prediction endpoint
            response = await client.post(
                f"{GATEWAY_URL}/api/ml/predict-ctr",
                json={
                    "scenes": [
                        {
                            "features": {
                                "hook_strength": random.uniform(0.5, 1.0),
                                "motion_score": random.uniform(0.3, 0.9),
                                "emotion_score": random.uniform(0.4, 0.95)
                            }
                        }
                    ]
                },
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "service_pair": "gateway_to_ml",
                "endpoint": "/api/ml/predict-ctr",
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "service_pair": "gateway_to_ml",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_gateway_to_titan_core(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Gateway API → Titan-Core communication"""
        start_time = time.time()
        
        try:
            # Test AI Council endpoint
            response = await client.post(
                f"{TITAN_CORE_URL}/council/evaluate",
                json={
                    "campaign_id": str(uuid.uuid4()),
                    "asset_id": str(uuid.uuid4()),
                    "variations_count": 3
                },
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "service_pair": "gateway_to_titan_core",
                "endpoint": "/council/evaluate",
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "service_pair": "gateway_to_titan_core",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_gateway_to_video_agent(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Gateway API → Video Agent communication"""
        start_time = time.time()
        
        try:
            # Test render endpoint
            response = await client.post(
                f"{VIDEO_AGENT_URL}/api/render/remix",
                json={
                    "scenes": [],
                    "variant": "reels",
                    "platform": "instagram"
                },
                timeout=120.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "service_pair": "gateway_to_video_agent",
                "endpoint": "/api/render/remix",
                "success": response.status_code in [200, 202],
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "service_pair": "gateway_to_video_agent",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_gateway_to_drive_intel(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Gateway API → Drive Intel communication"""
        start_time = time.time()
        
        try:
            # Test ingest endpoint
            response = await client.post(
                f"{GATEWAY_URL}/api/ingest/local/folder",
                json={"folder_path": "/test/videos"},
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "service_pair": "gateway_to_drive_intel",
                "endpoint": "/api/ingest/local/folder",
                "success": response.status_code in [200, 202],
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "service_pair": "gateway_to_drive_intel",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_ml_service_to_meta_publisher(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test ML Service → Meta Publisher (via queue)"""
        start_time = time.time()
        
        try:
            # Test queue ad change
            response = await client.post(
                f"{GATEWAY_URL}/api/pending-ad-changes",
                json={
                    "ad_id": f"ad_{uuid.uuid4()}",
                    "change_type": "BUDGET_INCREASE",
                    "new_budget": 100.50,
                    "reasoning": "Test change"
                },
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "service_pair": "ml_service_to_meta_publisher",
                "endpoint": "/api/pending-ad-changes",
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "service_pair": "ml_service_to_meta_publisher",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_hubspot_to_ml_service(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test HubSpot Webhook → ML Service"""
        start_time = time.time()
        
        try:
            # Test webhook endpoint
            response = await client.post(
                f"{GATEWAY_URL}/api/webhook/hubspot",
                json={
                    "ad_id": f"ad_{uuid.uuid4()}",
                    "deal_id": f"deal_{uuid.uuid4()}",
                    "stage": "Closed Won",
                    "deal_value": 10000.0
                },
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "service_pair": "hubspot_to_ml_service",
                "endpoint": "/api/webhook/hubspot",
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "service_pair": "hubspot_to_ml_service",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_circuit_breaker(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test circuit breaker pattern on service failures"""
        start_time = time.time()
        
        try:
            # Try to call non-existent endpoint multiple times
            failures = 0
            for _ in range(5):
                try:
                    response = await client.get(
                        f"{ML_SERVICE_URL}/api/non-existent-endpoint",
                        timeout=5.0
                    )
                    if response.status_code >= 500:
                        failures += 1
                except:
                    failures += 1
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "test": "circuit_breaker",
                "success": True,
                "failures_detected": failures,
                "circuit_breaker_works": failures >= 3,  # Should trigger after 3 failures
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "test": "circuit_breaker",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_retry_with_backoff(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test retry with exponential backoff"""
        start_time = time.time()
        
        try:
            # Simulate retry logic
            max_retries = 3
            base_delay = 0.1
            attempt = 0
            
            while attempt < max_retries:
                try:
                    response = await client.get(
                        f"{GATEWAY_URL}/api/health",
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        break
                except:
                    pass
                
                attempt += 1
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "test": "retry_with_backoff",
                "success": True,
                "attempts": attempt + 1,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "test": "retry_with_backoff",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }


async def stress_test_service_communication(
    concurrent: int = 50,
    total_requests: int = 500
) -> Dict[str, Any]:
    """Run stress test for service-to-service communication"""
    
    logger.info(f"Starting service communication stress test: {concurrent} concurrent, {total_requests} total")
    
    tester = ServiceCommunicationTester()
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Test all service pairs
        service_tests = [
            tester.test_gateway_to_ml_service(client),
            tester.test_gateway_to_titan_core(client),
            tester.test_gateway_to_video_agent(client),
            tester.test_gateway_to_drive_intel(client),
            tester.test_ml_service_to_meta_publisher(client),
            tester.test_hubspot_to_ml_service(client),
            tester.test_circuit_breaker(client),
            tester.test_retry_with_backoff(client)
        ]
        
        # Run initial tests
        initial_results = await asyncio.gather(*service_tests, return_exceptions=True)
        results.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in initial_results])
        
        # Stress test specific endpoints
        stress_tests = []
        for _ in range(total_requests):
            test_func = random.choice([
                tester.test_gateway_to_ml_service,
                tester.test_gateway_to_drive_intel,
                tester.test_hubspot_to_ml_service
            ])
            stress_tests.append(test_func(client))
        
        # Process in batches
        batch_size = concurrent
        for i in range(0, len(stress_tests), batch_size):
            batch = stress_tests[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in batch_results])
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(len(stress_tests) + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Service pair analysis
    service_stats = {}
    for result in results:
        service_pair = result.get("service_pair") or result.get("test", "unknown")
        if service_pair not in service_stats:
            service_stats[service_pair] = {"total": 0, "successful": 0, "durations": []}
        
        service_stats[service_pair]["total"] += 1
        if result.get("success"):
            service_stats[service_pair]["successful"] += 1
            if "duration_ms" in result:
                service_stats[service_pair]["durations"].append(result["duration_ms"])
    
    service_analysis = {}
    for service_pair, stats in service_stats.items():
        service_analysis[service_pair] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0
        }
    
    return {
        "total_requests": total_requests,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / len(results) if results else 0,
        "total_duration_seconds": total_duration,
        "requests_per_second": len(results) / total_duration if total_duration > 0 else 0,
        "service_analysis": service_analysis
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_service_communication(concurrent=20, total_requests=100))

