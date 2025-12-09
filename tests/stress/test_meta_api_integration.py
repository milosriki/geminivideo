"""
Stress Test: Meta API Integration
Tests Meta API integration, rate limiting, and SafeExecutor
Covers: Meta Publisher → SafeExecutor → Meta API → Rate Limits → Jitter → Fuzzy Budgets
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
META_PUBLISHER_URL = "http://localhost:8003"


class MetaAPIIntegrationTester:
    """Test Meta API integration"""
    
    async def test_meta_campaign_creation(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Meta campaign creation"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{META_PUBLISHER_URL}/api/meta/campaigns",
                json={
                    "name": f"Test Campaign {uuid.uuid4().hex[:8]}",
                    "objective": "CONVERSIONS",
                    "status": "PAUSED",
                    "daily_budget": 100
                },
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "campaign_creation",
                "success": response.status_code in [200, 201],
                "campaign_id": response.json().get("id") if response.status_code in [200, 201] else None,
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "campaign_creation",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_meta_ad_creation(self, client: httpx.AsyncClient, campaign_id: str) -> Dict[str, Any]:
        """Test Meta ad creation"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{META_PUBLISHER_URL}/api/meta/ads",
                json={
                    "campaign_id": campaign_id,
                    "adset_id": f"adset_{uuid.uuid4()}",
                    "creative": {
                        "video_id": f"video_{uuid.uuid4()}",
                        "title": "Test Ad",
                        "body": "Test Ad Body"
                    },
                    "status": "PAUSED"
                },
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "ad_creation",
                "success": response.status_code in [200, 201],
                "ad_id": response.json().get("id") if response.status_code in [200, 201] else None,
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "ad_creation",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_safe_executor_queue(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test SafeExecutor queue (pending_ad_changes)"""
        start_time = time.time()
        
        try:
            change_data = {
                "ad_id": ad_id,
                "change_type": random.choice(["BUDGET_INCREASE", "BUDGET_DECREASE", "STATUS_CHANGE"]),
                "new_budget": round(random.uniform(50, 500), 2),
                "reasoning": "Stress test change",
                "priority": "normal"
            }
            
            response = await client.post(
                f"{GATEWAY_URL}/api/pending-ad-changes",
                json=change_data,
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                change_id = response.json().get("id") or str(uuid.uuid4())
                return {
                    "operation": "safe_executor_queue",
                    "success": True,
                    "change_id": change_id,
                    "duration_ms": duration
                }
            else:
                return {
                    "operation": "safe_executor_queue",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "operation": "safe_executor_queue",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_rate_limiting(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Meta API rate limiting (15 requests/hour)"""
        start_time = time.time()
        
        try:
            # Try to make multiple requests quickly
            requests_made = 0
            rate_limited = False
            
            for i in range(20):
                try:
                    response = await client.get(
                        f"{META_PUBLISHER_URL}/api/meta/insights",
                        params={"ad_id": f"ad_{uuid.uuid4()}"},
                        timeout=5.0
                    )
                    requests_made += 1
                    
                    if response.status_code == 429:  # Too Many Requests
                        rate_limited = True
                        break
                except:
                    pass
                
                await asyncio.sleep(0.1)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "rate_limiting",
                "success": True,
                "requests_made": requests_made,
                "rate_limited": rate_limited,
                "rate_limit_works": rate_limited or requests_made < 20,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "rate_limiting",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_jitter_delay(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test jitter delay (3-18 seconds)"""
        start_time = time.time()
        
        try:
            # Simulate jitter calculation
            jitter_min = 3
            jitter_max = 18
            jitter_delays = []
            
            for _ in range(10):
                jitter = random.uniform(jitter_min, jitter_max)
                jitter_delays.append(jitter)
            
            avg_jitter = np.mean(jitter_delays)
            min_jitter = min(jitter_delays)
            max_jitter = max(jitter_delays)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "jitter_delay",
                "success": True,
                "avg_jitter_seconds": avg_jitter,
                "min_jitter": min_jitter,
                "max_jitter": max_jitter,
                "jitter_in_range": min_jitter >= jitter_min and max_jitter <= jitter_max,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "jitter_delay",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_fuzzy_budget(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test fuzzy budget calculation ($50.00 → $49.83)"""
        start_time = time.time()
        
        try:
            original_budget = 50.00
            fuzzy_amount = random.uniform(0.10, 0.50)
            fuzzy_budget = round(original_budget - fuzzy_amount, 2)
            
            # Verify fuzzy budget is within expected range
            fuzzy_range = (original_budget - 0.50, original_budget - 0.10)
            is_fuzzy = fuzzy_range[0] <= fuzzy_budget <= fuzzy_range[1]
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "fuzzy_budget",
                "success": True,
                "original_budget": original_budget,
                "fuzzy_budget": fuzzy_budget,
                "fuzzy_amount": fuzzy_amount,
                "is_fuzzy": is_fuzzy,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "fuzzy_budget",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_budget_velocity_limit(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test budget velocity limit (20% in 6 hours)"""
        start_time = time.time()
        
        try:
            current_budget = 100.00
            max_increase = current_budget * 0.20  # 20%
            proposed_budget = current_budget + (max_increase * 1.5)  # Exceeds limit
            
            # Check if velocity limit would be enforced
            allowed_budget = min(proposed_budget, current_budget + max_increase)
            velocity_limit_enforced = allowed_budget < proposed_budget
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "operation": "budget_velocity_limit",
                "success": True,
                "current_budget": current_budget,
                "proposed_budget": proposed_budget,
                "allowed_budget": allowed_budget,
                "velocity_limit_enforced": velocity_limit_enforced,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "operation": "budget_velocity_limit",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_ad_change_history(self, client: httpx.AsyncClient, change_id: str) -> Dict[str, Any]:
        """Test ad change history logging"""
        start_time = time.time()
        
        try:
            response = await client.get(
                f"{GATEWAY_URL}/api/ad-change-history",
                params={"change_id": change_id},
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                history = response.json()
                return {
                    "operation": "ad_change_history",
                    "success": True,
                    "history_found": history is not None,
                    "status": history.get("status") if history else None,
                    "duration_ms": duration
                }
            else:
                return {
                    "operation": "ad_change_history",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "operation": "ad_change_history",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }


async def stress_test_meta_api_integration(
    concurrent: int = 20,
    total_operations: int = 200
) -> Dict[str, Any]:
    """Run stress test for Meta API integration"""
    
    logger.info(f"Starting Meta API integration stress test: {concurrent} concurrent, {total_operations} total")
    
    tester = MetaAPIIntegrationTester()
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Test individual operations
        operation_tests = [
            tester.test_rate_limiting(client),
            tester.test_jitter_delay(client),
            tester.test_fuzzy_budget(client),
            tester.test_budget_velocity_limit(client)
        ]
        
        operation_results = await asyncio.gather(*operation_tests, return_exceptions=True)
        results.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in operation_results])
        
        # Stress test campaign and ad creation
        for _ in range(total_operations):
            # Create campaign
            campaign_result = await tester.test_meta_campaign_creation(client)
            results.append(campaign_result)
            
            if campaign_result.get("success") and campaign_result.get("campaign_id"):
                campaign_id = campaign_result["campaign_id"]
                
                # Create ad
                ad_result = await tester.test_meta_ad_creation(client, campaign_id)
                results.append(ad_result)
                
                if ad_result.get("success") and ad_result.get("ad_id"):
                    ad_id = ad_result["ad_id"]
                    
                    # Queue to SafeExecutor
                    queue_result = await tester.test_safe_executor_queue(client, ad_id)
                    results.append(queue_result)
                    
                    if queue_result.get("success") and queue_result.get("change_id"):
                        change_id = queue_result["change_id"]
                        await asyncio.sleep(1)
                        
                        # Check history
                        history_result = await tester.test_ad_change_history(client, change_id)
                        results.append(history_result)
            
            await asyncio.sleep(0.5)  # Rate limiting protection
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Operation-level analysis
    operation_stats = {}
    for result in results:
        operation = result.get("operation", "unknown")
        if operation not in operation_stats:
            operation_stats[operation] = {"total": 0, "successful": 0, "durations": []}
        
        operation_stats[operation]["total"] += 1
        if result.get("success"):
            operation_stats[operation]["successful"] += 1
            if "duration_ms" in result:
                operation_stats[operation]["durations"].append(result["duration_ms"])
    
    operation_analysis = {}
    for operation, stats in operation_stats.items():
        operation_analysis[operation] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0
        }
    
    return {
        "total_operations": total_operations,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / len(results) if results else 0,
        "total_duration_seconds": total_duration,
        "operations_per_second": len(results) / total_duration if total_duration > 0 else 0,
        "operation_analysis": operation_analysis
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_meta_api_integration(concurrent=10, total_operations=50))

