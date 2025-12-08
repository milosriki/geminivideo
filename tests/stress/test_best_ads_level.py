"""
Stress Test: Best Ads Level Performance
Tests system at production scale with best-performing ad patterns
"""
import asyncio
import time
import random
import numpy as np
from typing import List, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

# Best ads level configuration
BEST_ADS_CTR = 0.05  # 5% CTR
BEST_ADS_ROAS = 4.0  # 4x ROAS
BEST_ADS_PIPELINE_ROAS = 5.0  # 5x Pipeline ROAS
BEST_ADS_SPEND = 10000  # $10k spend
BEST_ADS_IMPRESSIONS = 200000  # 200k impressions


class BestAdsSimulator:
    """Simulate best-performing ads for stress testing"""
    
    @staticmethod
    def generate_best_ad_state(ad_id: str) -> Dict[str, Any]:
        """Generate ad state matching best ads performance"""
        return {
            "ad_id": ad_id,
            "impressions": BEST_ADS_IMPRESSIONS + random.randint(-10000, 10000),
            "clicks": int(BEST_ADS_IMPRESSIONS * BEST_ADS_CTR) + random.randint(-500, 500),
            "spend": BEST_ADS_SPEND + random.uniform(-500, 500),
            "pipeline_value": BEST_ADS_SPEND * BEST_ADS_PIPELINE_ROAS + random.uniform(-1000, 1000),
            "cash_revenue": BEST_ADS_SPEND * BEST_ADS_ROAS + random.uniform(-1000, 1000),
            "age_hours": random.uniform(72, 720),  # 3-30 days
            "hook_type": random.choice(["testimonial", "transformation", "problem_solution"]),
            "visual_style": random.choice(["ugc", "professional", "before_after"]),
            "emotion": random.choice(["desire", "belonging", "fear"]),
            "ctr": BEST_ADS_CTR + random.uniform(-0.01, 0.01),
            "pipeline_roas": BEST_ADS_PIPELINE_ROAS + random.uniform(-0.5, 0.5)
        }
    
    @staticmethod
    def generate_best_ads_batch(count: int) -> List[Dict[str, Any]]:
        """Generate batch of best-performing ads"""
        return [BestAdsSimulator.generate_best_ad_state(f"best-ad-{i}") for i in range(count)]


async def stress_test_best_ads_budget_allocation(
    concurrent: int = 50,
    total_ads: int = 500
) -> Dict[str, Any]:
    """Stress test budget allocation with best-performing ads"""
    
    logger.info(f"Testing budget allocation with {total_ads} best-performing ads")
    
    simulator = BestAdsSimulator()
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Generate best ads
        ads = simulator.generate_best_ads_batch(total_ads)
        
        # Test budget allocation in batches
        batch_size = concurrent
        total_budget = 50000  # $50k total budget
        
        for i in range(0, total_ads, batch_size):
            batch_ads = ads[i:i + batch_size]
            
            async def allocate_budget(ad_batch):
                try:
                    start = time.time()
                    response = await client.post(
                        f"http://localhost:8003/api/ml/battle-hardened/select",
                        json={
                            "ad_states": ad_batch,
                            "total_budget": total_budget / (total_ads / len(ad_batch)),
                            "creative_dna_scores": {
                                ad["ad_id"]: random.uniform(0.7, 1.0)
                                for ad in ad_batch
                            }
                        },
                        timeout=30.0
                    )
                    duration = (time.time() - start) * 1000
                    
                    return {
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "duration_ms": duration,
                        "ads_count": len(ad_batch),
                        "recommendations_count": len(response.json().get("recommendations", [])) if response.status_code == 200 else 0
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "ads_count": len(ad_batch)
                    }
            
            batch_results = await asyncio.gather(
                *[allocate_budget([ad]) for ad in batch_ads],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_ads + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in results if not (isinstance(r, dict) and r.get("success"))]
    
    durations = [r["duration_ms"] for r in successful if "duration_ms" in r]
    
    return {
        "total_ads": total_ads,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_ads if total_ads > 0 else 0,
        "total_duration_seconds": total_duration,
        "ads_per_second": total_ads / total_duration if total_duration > 0 else 0,
        "avg_duration_ms": np.mean(durations) if durations else 0,
        "p95_duration_ms": np.percentile(durations, 95) if durations else 0,
        "p99_duration_ms": np.percentile(durations, 99) if durations else 0
    }


async def stress_test_best_ads_rag_search(
    concurrent: int = 100,
    total_searches: int = 1000
) -> Dict[str, Any]:
    """Stress test RAG search with best ads patterns"""
    
    logger.info(f"Testing RAG search: {concurrent} concurrent, {total_searches} total")
    
    hook_types = ["testimonial", "transformation", "problem_solution", "before_after", "urgency"]
    visual_styles = ["ugc", "professional", "before_after", "lifestyle"]
    emotions = ["desire", "belonging", "fear", "curiosity"]
    
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Generate random search queries
        queries = []
        for i in range(total_searches):
            queries.append({
                "query_embedding": np.random.rand(768).tolist(),  # Simulated embedding
                "top_k": random.randint(3, 10),
                "hook_type": random.choice(hook_types),
                "min_roas": random.uniform(2.0, 5.0)
            })
        
        # Process in batches
        batch_size = concurrent
        for i in range(0, total_searches, batch_size):
            batch = queries[i:i + batch_size]
            
            async def search_rag(query):
                try:
                    start = time.time()
                    response = await client.post(
                        f"http://localhost:8003/api/ml/rag/search-winners",
                        json=query,
                        timeout=10.0
                    )
                    duration = (time.time() - start) * 1000
                    
                    return {
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "duration_ms": duration,
                        "results_count": len(response.json().get("matches", [])) if response.status_code == 200 else 0
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e)
                    }
            
            batch_results = await asyncio.gather(
                *[search_rag(q) for q in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_searches + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in results if not (isinstance(r, dict) and r.get("success"))]
    
    durations = [r["duration_ms"] for r in successful if "duration_ms" in r]
    
    return {
        "total_searches": total_searches,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_searches if total_searches > 0 else 0,
        "total_duration_seconds": total_duration,
        "searches_per_second": total_searches / total_duration if total_duration > 0 else 0,
        "avg_duration_ms": np.mean(durations) if durations else 0,
        "p95_duration_ms": np.percentile(durations, 95) if durations else 0,
        "p99_duration_ms": np.percentile(durations, 99) if durations else 0
    }


async def stress_test_best_ads_feedback_loop(
    concurrent: int = 200,
    total_feedbacks: int = 2000
) -> Dict[str, Any]:
    """Stress test feedback loop with best ads performance data"""
    
    logger.info(f"Testing feedback loop: {concurrent} concurrent, {total_feedbacks} total")
    
    simulator = BestAdsSimulator()
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Generate feedback data
        feedbacks = []
        for i in range(total_feedbacks):
            ad = simulator.generate_best_ad_state(f"feedback-ad-{i}")
            feedbacks.append({
                "ad_id": ad["ad_id"],
                "actual_pipeline_value": ad["pipeline_value"],
                "actual_spend": ad["spend"]
            })
        
        # Process in batches
        batch_size = concurrent
        for i in range(0, total_feedbacks, batch_size):
            batch = feedbacks[i:i + batch_size]
            
            async def send_feedback(feedback):
                try:
                    start = time.time()
                    response = await client.post(
                        f"http://localhost:8003/api/ml/battle-hardened/feedback",
                        json=feedback,
                        timeout=5.0
                    )
                    duration = (time.time() - start) * 1000
                    
                    return {
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "duration_ms": duration
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e)
                    }
            
            batch_results = await asyncio.gather(
                *[send_feedback(f) for f in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_feedbacks + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in results if not (isinstance(r, dict) and r.get("success"))]
    
    durations = [r["duration_ms"] for r in successful if "duration_ms" in r]
    
    return {
        "total_feedbacks": total_feedbacks,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_feedbacks if total_feedbacks > 0 else 0,
        "total_duration_seconds": total_duration,
        "feedbacks_per_second": total_feedbacks / total_duration if total_duration > 0 else 0,
        "avg_duration_ms": np.mean(durations) if durations else 0,
        "p95_duration_ms": np.percentile(durations, 95) if durations else 0,
        "p99_duration_ms": np.percentile(durations, 99) if durations else 0
    }


async def main():
    """Run all best ads level stress tests"""
    print("=" * 80)
    print("STRESS TEST: BEST ADS LEVEL PERFORMANCE")
    print("=" * 80)
    
    # Test 1: Budget Allocation
    print("\n1. Testing Budget Allocation with Best Ads...")
    budget_results = await stress_test_best_ads_budget_allocation(
        concurrent=50,
        total_ads=500
    )
    print(f"  Success Rate: {budget_results['success_rate']*100:.1f}%")
    print(f"  Avg Duration: {budget_results['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {budget_results['p95_duration_ms']:.2f}ms")
    
    # Test 2: RAG Search
    print("\n2. Testing RAG Search with Best Ads Patterns...")
    rag_results = await stress_test_best_ads_rag_search(
        concurrent=100,
        total_searches=1000
    )
    print(f"  Success Rate: {rag_results['success_rate']*100:.1f}%")
    print(f"  Avg Duration: {rag_results['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {rag_results['p95_duration_ms']:.2f}ms")
    
    # Test 3: Feedback Loop
    print("\n3. Testing Feedback Loop with Best Ads Data...")
    feedback_results = await stress_test_best_ads_feedback_loop(
        concurrent=200,
        total_feedbacks=2000
    )
    print(f"  Success Rate: {feedback_results['success_rate']*100:.1f}%")
    print(f"  Avg Duration: {feedback_results['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {feedback_results['p95_duration_ms']:.2f}ms")
    
    print("\n" + "=" * 80)
    print("BEST ADS LEVEL STRESS TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

