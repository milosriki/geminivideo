"""
Stress Test: Real-time Feedback Loops
Tests real-time feedback processing and learning
Covers: Meta Insights → HubSpot Webhooks → Feedback Processing → Model Updates → Auto-Promotion
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


class RealtimeFeedbackLoopsTester:
    """Test real-time feedback loops"""
    
    async def test_meta_insights_feedback(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test Meta insights feedback ingestion"""
        start_time = time.time()
        
        try:
            insights = {
                "ad_id": ad_id,
                "impressions": random.randint(1000, 100000),
                "clicks": random.randint(50, 5000),
                "spend": round(random.uniform(100, 10000), 2),
                "conversions": random.randint(0, 100),
                "ctr": random.uniform(0.01, 0.10),
                "cpc": round(random.uniform(0.50, 5.00), 2),
                "timestamp": time.time()
            }
            
            response = await client.post(
                f"{GATEWAY_URL}/api/meta/insights",
                json=insights,
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "feedback_type": "meta_insights",
                "success": response.status_code in [200, 201],
                "ad_id": ad_id,
                "impressions": insights["impressions"],
                "spend": insights["spend"],
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "feedback_type": "meta_insights",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_hubspot_webhook_feedback(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test HubSpot webhook feedback (synthetic revenue)"""
        start_time = time.time()
        
        try:
            webhook_data = {
                "ad_id": ad_id,
                "deal_id": f"deal_{uuid.uuid4()}",
                "stage": random.choice([
                    "Proposal Sent",
                    "Assessment Done",
                    "Contract Sent",
                    "Closed Won",
                    "Appointment Booked"
                ]),
                "deal_value": round(random.uniform(5000, 50000), 2),
                "timestamp": time.time()
            }
            
            response = await client.post(
                f"{GATEWAY_URL}/api/webhook/hubspot",
                json=webhook_data,
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "feedback_type": "hubspot_webhook",
                    "success": True,
                    "ad_id": ad_id,
                    "synthetic_revenue": result.get("synthetic_revenue", 0),
                    "pipeline_roas": result.get("pipeline_roas", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "feedback_type": "hubspot_webhook",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "feedback_type": "hubspot_webhook",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_feedback_processing(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test feedback processing and model update"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/battle-hardened/feedback",
                json={
                    "ad_id": ad_id,
                    "actual_pipeline_value": round(random.uniform(500, 50000), 2),
                    "actual_spend": round(random.uniform(100, 10000), 2),
                    "timestamp": time.time()
                },
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "feedback_type": "feedback_processing",
                    "success": True,
                    "ad_id": ad_id,
                    "model_updated": result.get("model_updated", False),
                    "sampler_updated": result.get("sampler_updated", False),
                    "duration_ms": duration
                }
            else:
                return {
                    "feedback_type": "feedback_processing",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "feedback_type": "feedback_processing",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_auto_promotion_trigger(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test auto-promotion trigger based on feedback"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/auto-promote/check",
                json={"ad_id": ad_id},
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "feedback_type": "auto_promotion",
                    "success": True,
                    "ad_id": ad_id,
                    "promoted": result.get("promoted", False),
                    "action": result.get("action", "none"),
                    "budget_increase": result.get("budget_increase", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "feedback_type": "auto_promotion",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "feedback_type": "auto_promotion",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_dual_signal_feedback(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test dual-signal feedback (Meta + HubSpot)"""
        start_time = time.time()
        
        try:
            # Send both signals
            meta_result = await self.test_meta_insights_feedback(client, ad_id)
            await asyncio.sleep(0.5)
            hubspot_result = await self.test_hubspot_webhook_feedback(client, ad_id)
            await asyncio.sleep(1)
            
            # Check if both processed
            processing_result = await self.test_feedback_processing(client, ad_id)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "feedback_type": "dual_signal",
                "success": meta_result.get("success") and hubspot_result.get("success") and processing_result.get("success"),
                "ad_id": ad_id,
                "meta_success": meta_result.get("success"),
                "hubspot_success": hubspot_result.get("success"),
                "processing_success": processing_result.get("success"),
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "feedback_type": "dual_signal",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_feedback_latency(self, client: httpx.AsyncClient, ad_id: str) -> Dict[str, Any]:
        """Test feedback processing latency"""
        start_time = time.time()
        
        try:
            # Send feedback
            feedback_sent = time.time()
            response = await client.post(
                f"{GATEWAY_URL}/api/meta/insights",
                json={
                    "ad_id": ad_id,
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": 100.0
                },
                timeout=10.0
            )
            
            feedback_received = time.time()
            latency = (feedback_received - feedback_sent) * 1000
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "feedback_type": "latency_test",
                "success": response.status_code in [200, 201],
                "ad_id": ad_id,
                "latency_ms": latency,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "feedback_type": "latency_test",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }


async def stress_test_realtime_feedback_loops(
    concurrent: int = 50,
    total_feedbacks: int = 500
) -> Dict[str, Any]:
    """Run stress test for real-time feedback loops"""
    
    logger.info(f"Starting real-time feedback loops stress test: {concurrent} concurrent, {total_feedbacks} total")
    
    tester = RealtimeFeedbackLoopsTester()
    results = []
    start_time = time.time()
    
    # Generate test ad IDs
    ad_ids = [f"ad_{uuid.uuid4()}" for _ in range(total_feedbacks)]
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Process in batches
        batch_size = concurrent
        for i in range(0, total_feedbacks, batch_size):
            batch_ad_ids = ad_ids[i:i + batch_size]
            
            async def process_feedback(ad_id):
                # Randomly choose feedback type
                feedback_type = random.choice([
                    "meta_insights",
                    "hubspot_webhook",
                    "dual_signal"
                ])
                
                if feedback_type == "meta_insights":
                    return await tester.test_meta_insights_feedback(client, ad_id)
                elif feedback_type == "hubspot_webhook":
                    return await tester.test_hubspot_webhook_feedback(client, ad_id)
                else:
                    return await tester.test_dual_signal_feedback(client, ad_id)
            
            batch_results = await asyncio.gather(
                *[process_feedback(ad_id) for ad_id in batch_ad_ids],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result)
                    })
                else:
                    results.append(result)
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_feedbacks + batch_size - 1) // batch_size}")
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.5)
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Feedback type analysis
    feedback_stats = {}
    for result in results:
        feedback_type = result.get("feedback_type", "unknown")
        if feedback_type not in feedback_stats:
            feedback_stats[feedback_type] = {"total": 0, "successful": 0, "durations": [], "latencies": []}
        
        feedback_stats[feedback_type]["total"] += 1
        if result.get("success"):
            feedback_stats[feedback_type]["successful"] += 1
            if "duration_ms" in result:
                feedback_stats[feedback_type]["durations"].append(result["duration_ms"])
            if "latency_ms" in result:
                feedback_stats[feedback_type]["latencies"].append(result["latency_ms"])
    
    feedback_analysis = {}
    for feedback_type, stats in feedback_stats.items():
        feedback_analysis[feedback_type] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0,
            "avg_latency_ms": np.mean(stats["latencies"]) if stats["latencies"] else 0
        }
    
    return {
        "total_feedbacks": total_feedbacks,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_feedbacks if total_feedbacks > 0 else 0,
        "total_duration_seconds": total_duration,
        "feedbacks_per_second": total_feedbacks / total_duration if total_duration > 0 else 0,
        "feedback_analysis": feedback_analysis
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_realtime_feedback_loops(concurrent=25, total_feedbacks=100))

