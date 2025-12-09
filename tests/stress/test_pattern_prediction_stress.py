"""
Stress Test: Pattern Prediction with Random Dynamic Questions
Tests the system's ability to handle high load and dynamic queries
"""
import asyncio
import time
import random
import numpy as np
from typing import List, Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8003"
ML_SERVICE_URL = f"{BASE_URL}/api/ml"
CONCURRENT_REQUESTS = 100
TOTAL_REQUESTS = 1000
QUESTION_TYPES = [
    "top_campaigns",
    "winning_ads",
    "synthetic_revenue",
    "oracle_prediction",
    "creative_doctor",
    "fatigue_monitoring",
    "pattern_extractor",
    "market_trends",
    "federated_learning"
]


class DynamicQuestionGenerator:
    """Generate random dynamic questions for stress testing"""
    
    @staticmethod
    def generate_top_campaigns_question() -> Dict[str, Any]:
        """Generate dynamic top campaigns question"""
        quarters = ["Q1", "Q2", "Q3", "Q4", "last_quarter", "last_month", "last_week"]
        metrics = ["ROAS", "CTR", "pipeline_value", "conversions", "spend"]
        segments = ["audience_segment", "platform", "hook_type", "visual_style"]
        
        return {
            "type": "top_campaigns",
            "question": f"What were our top {random.randint(3, 10)} performing ad campaigns {random.choice(quarters)} in terms of {random.choice(metrics)}, and what was the primary {random.choice(segments)} for each?",
            "params": {
                "top_k": random.randint(3, 10),
                "time_period": random.choice(quarters),
                "metric": random.choice(metrics),
                "group_by": random.choice(segments)
            }
        }
    
    @staticmethod
    def generate_winning_ads_question() -> Dict[str, Any]:
        """Generate dynamic winning ads question"""
        hook_types = ["testimonial", "problem_solution", "transformation", "before_after", "urgency"]
        metrics = ["CTR", "ROAS", "pipeline_roas", "conversions"]
        thresholds = [0.02, 0.03, 0.04, 0.05, 2.0, 3.0, 4.0, 5.0]
        
        return {
            "type": "winning_ads",
            "question": f"Show me {random.randint(3, 10)} winning video ads from our database that used a '{random.choice(hook_types)}' style hook and had a {random.choice(metrics)} above {random.choice(thresholds)}.",
            "params": {
                "top_k": random.randint(3, 10),
                "hook_type": random.choice(hook_types),
                "metric": random.choice(metrics),
                "threshold": random.choice(thresholds)
            }
        }
    
    @staticmethod
    def generate_synthetic_revenue_question() -> Dict[str, Any]:
        """Generate dynamic synthetic revenue question"""
        campaigns = ["Summer Promo", "Black Friday", "New Year", "Spring Sale", "Holiday Special"]
        stages = ["Proposal Sent", "Assessment Done", "Contract Sent", "Closed Won", "Appointment Booked"]
        values = [10000, 15000, 20000, 25000, 30000, 50000]
        
        return {
            "type": "synthetic_revenue",
            "question": f"A lead from the '{random.choice(campaigns)}' campaign just moved to the '{random.choice(stages)}' stage in HubSpot with a deal value of ${random.choice(values):,}. What is the calculated synthetic revenue for this event?",
            "params": {
                "campaign": random.choice(campaigns),
                "stage": random.choice(stages),
                "deal_value": random.choice(values)
            }
        }
    
    @staticmethod
    def generate_oracle_prediction_question() -> Dict[str, Any]:
        """Generate dynamic Oracle prediction question"""
        creative_ids = [f"xyz-{random.randint(100, 999)}" for _ in range(5)]
        
        return {
            "type": "oracle_prediction",
            "question": f"I'm about to launch a new video creative (ID: '{random.choice(creative_ids)}'). Analyze its creative DNA and predict its potential performance. Should I proceed with the launch, and what is your confidence level?",
            "params": {
                "creative_id": random.choice(creative_ids),
                "action": "predict"
            }
        }
    
    @staticmethod
    def generate_creative_doctor_question() -> Dict[str, Any]:
        """Generate dynamic Creative Doctor question"""
        creative_ids = [f"xyz-{random.randint(100, 999)}" for _ in range(5)]
        issues = ["slow hook pacing", "weak CTA", "low emotional appeal", "poor visual flow", "unclear value prop"]
        
        return {
            "type": "creative_doctor",
            "question": f"The Oracle Agent rejected creative '{random.choice(creative_ids)}' due to '{random.choice(issues)}.' Generate {random.randint(2, 5)} new variations of the first {random.randint(2, 5)} seconds of this video that are optimized to improve the hook rate.",
            "params": {
                "creative_id": random.choice(creative_ids),
                "issue": random.choice(issues),
                "variations": random.randint(2, 5),
                "duration": random.randint(2, 5)
            }
        }
    
    @staticmethod
    def generate_fatigue_monitoring_question() -> Dict[str, Any]:
        """Generate dynamic fatigue monitoring question"""
        return {
            "type": "fatigue_monitoring",
            "question": "Which active ads are currently showing signs of creative fatigue, and what auto-remediation actions have been queued for them in the SafeExecutor?",
            "params": {
                "status": "active",
                "include_remediation": True
            }
        }
    
    @staticmethod
    def generate_pattern_extractor_question() -> Dict[str, Any]:
        """Generate dynamic Pattern Extractor question"""
        time_periods = ["last_month", "last_quarter", "last_week", "last_90_days"]
        top_n = random.randint(5, 20)
        
        return {
            "type": "pattern_extractor",
            "question": f"Analyze the top {top_n} winning ads from {random.choice(time_periods)}. Instead of showing me the ads, tell me the underlying principles of why they succeeded. What were the dominant hook patterns, visual styles, and emotional appeals that we should use as a blueprint for our next campaign?",
            "params": {
                "top_n": top_n,
                "time_period": random.choice(time_periods),
                "analysis_type": "principles"
            }
        }
    
    @staticmethod
    def generate_market_trend_question() -> Dict[str, Any]:
        """Generate dynamic Market Trend question"""
        industries = ["fitness", "healthcare", "finance", "education", "ecommerce", "saas"]
        trends_count = random.randint(2, 5)
        
        return {
            "type": "market_trend",
            "question": f"Analyze the latest creative trends on the TikTok Creative Center for the '{random.choice(industries)}' industry. Identify {trends_count} emerging visual styles or audio trends that we are not currently using. Based on these trends, generate a concept for a new, experimental ad campaign.",
            "params": {
                "industry": random.choice(industries),
                "trends_count": trends_count,
                "platform": "tiktok"
            }
        }
    
    @staticmethod
    def generate_federated_learning_question() -> Dict[str, Any]:
        """Generate dynamic Federated Learning question"""
        business_types = ["service-based", "ecommerce", "saas", "healthcare", "fitness"]
        time_periods = ["last_30_days", "last_90_days", "last_quarter"]
        
        return {
            "type": "federated_learning",
            "question": f"Based on the aggregated (and anonymized) model updates from all client accounts, what is the single most effective creative element that has the highest positive correlation with ROAS across all {random.choice(business_types)} businesses in the {random.choice(time_periods)}?",
            "params": {
                "business_type": random.choice(business_types),
                "time_period": random.choice(time_periods),
                "metric": "ROAS"
            }
        }
    
    @classmethod
    def generate_random_question(cls) -> Dict[str, Any]:
        """Generate a random question of any type"""
        generators = [
            cls.generate_top_campaigns_question,
            cls.generate_winning_ads_question,
            cls.generate_synthetic_revenue_question,
            cls.generate_oracle_prediction_question,
            cls.generate_creative_doctor_question,
            cls.generate_fatigue_monitoring_question,
            cls.generate_pattern_extractor_question,
            cls.generate_market_trend_question,
            cls.generate_federated_learning_question
        ]
        
        return random.choice(generators)()


async def test_pattern_prediction_single(question: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
    """Test a single pattern prediction query"""
    start_time = time.time()
    
    try:
        # Route to appropriate endpoint based on question type
        endpoint_map = {
            "top_campaigns": f"{ML_SERVICE_URL}/analytics/top-campaigns",
            "winning_ads": f"{ML_SERVICE_URL}/rag/search-winners",
            "synthetic_revenue": f"{ML_SERVICE_URL}/synthetic-revenue/calculate",
            "oracle_prediction": f"{ML_SERVICE_URL}/oracle/predict",
            "creative_doctor": f"{ML_SERVICE_URL}/creative-doctor/generate",
            "fatigue_monitoring": f"{ML_SERVICE_URL}/fatigue/monitor",
            "pattern_extractor": f"{ML_SERVICE_URL}/pattern-extractor/analyze",
            "market_trend": f"{ML_SERVICE_URL}/market-trend/analyze",
            "federated_learning": f"{ML_SERVICE_URL}/federated-learning/query"
        }
        
        endpoint = endpoint_map.get(question["type"], f"{ML_SERVICE_URL}/query")
        
        response = await client.post(
            endpoint,
            json=question["params"],
            timeout=30.0
        )
        
        duration = time.time() - start_time
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "question_type": question["type"],
            "response_size": len(response.text) if response.status_code == 200 else 0
        }
    
    except Exception as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "error": str(e),
            "duration_ms": duration * 1000,
            "question_type": question["type"]
        }


async def stress_test_pattern_prediction(
    concurrent: int = CONCURRENT_REQUESTS,
    total: int = TOTAL_REQUESTS
) -> Dict[str, Any]:
    """Run stress test with concurrent pattern prediction queries"""
    
    logger.info(f"Starting stress test: {concurrent} concurrent, {total} total requests")
    
    generator = DynamicQuestionGenerator()
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Generate all questions upfront
        questions = [generator.generate_random_question() for _ in range(total)]
        
        # Process in batches
        batch_size = concurrent
        for i in range(0, total, batch_size):
            batch = questions[i:i + batch_size]
            
            # Run batch concurrently
            batch_results = await asyncio.gather(
                *[test_pattern_prediction_single(q, client) for q in batch],
                return_exceptions=True
            )
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result),
                        "duration_ms": 0
                    })
                else:
                    results.append(result)
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    durations = [r["duration_ms"] for r in successful]
    
    return {
        "total_requests": total,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total if total > 0 else 0,
        "total_duration_seconds": total_duration,
        "requests_per_second": total / total_duration if total_duration > 0 else 0,
        "avg_duration_ms": np.mean(durations) if durations else 0,
        "p50_duration_ms": np.percentile(durations, 50) if durations else 0,
        "p95_duration_ms": np.percentile(durations, 95) if durations else 0,
        "p99_duration_ms": np.percentile(durations, 99) if durations else 0,
        "max_duration_ms": np.max(durations) if durations else 0,
        "min_duration_ms": np.min(durations) if durations else 0,
        "errors": [r.get("error") for r in failed[:10]]  # First 10 errors
    }


async def stress_test_video_editing(
    concurrent: int = 50,
    total: int = 200
) -> Dict[str, Any]:
    """Stress test video editing/processing at best ads level"""
    
    logger.info(f"Starting video editing stress test: {concurrent} concurrent, {total} total")
    
    # Simulate video editing requests
    video_requests = []
    for i in range(total):
        video_requests.append({
            "video_id": f"test-video-{i}",
            "operation": random.choice([
                "analyze",
                "generate_variations",
                "optimize_hook",
                "extract_dna",
                "create_battle_plan"
            ]),
            "params": {
                "duration_seconds": random.randint(15, 60),
                "hook_type": random.choice(["testimonial", "problem_solution", "transformation"]),
                "quality": "best_ads_level"
            }
        })
    
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Process in batches
        batch_size = concurrent
        for i in range(0, total, batch_size):
            batch = video_requests[i:i + batch_size]
            
            async def process_video(req):
                try:
                    start = time.time()
                    # Simulate video processing endpoint
                    response = await client.post(
                        f"{BASE_URL}/api/video/process",
                        json=req,
                        timeout=60.0
                    )
                    duration = (time.time() - start) * 1000
                    
                    return {
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "duration_ms": duration,
                        "video_id": req["video_id"],
                        "operation": req["operation"]
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "video_id": req["video_id"]
                    }
            
            batch_results = await asyncio.gather(
                *[process_video(req) for req in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            logger.info(f"Processed video batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in results if not (isinstance(r, dict) and r.get("success"))]
    
    durations = [r["duration_ms"] for r in successful if "duration_ms" in r]
    
    return {
        "total_requests": total,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total if total > 0 else 0,
        "total_duration_seconds": total_duration,
        "requests_per_second": total / total_duration if total_duration > 0 else 0,
        "avg_duration_ms": np.mean(durations) if durations else 0,
        "p95_duration_ms": np.percentile(durations, 95) if durations else 0,
        "p99_duration_ms": np.percentile(durations, 99) if durations else 0
    }


async def main():
    """Run all stress tests"""
    print("=" * 80)
    print("STRESS TEST SUITE: Pattern Prediction & Video Editing")
    print("=" * 80)
    
    # Test 1: Pattern Prediction
    print("\n1. Testing Pattern Prediction with Random Dynamic Questions...")
    pattern_results = await stress_test_pattern_prediction(
        concurrent=CONCURRENT_REQUESTS,
        total=TOTAL_REQUESTS
    )
    
    print(f"\nPattern Prediction Results:")
    print(f"  Total Requests: {pattern_results['total_requests']}")
    print(f"  Successful: {pattern_results['successful']} ({pattern_results['success_rate']*100:.1f}%)")
    print(f"  Failed: {pattern_results['failed']}")
    print(f"  Requests/sec: {pattern_results['requests_per_second']:.2f}")
    print(f"  Avg Duration: {pattern_results['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {pattern_results['p95_duration_ms']:.2f}ms")
    print(f"  P99 Duration: {pattern_results['p99_duration_ms']:.2f}ms")
    
    # Test 2: Video Editing
    print("\n2. Testing Video Editing at Best Ads Level...")
    video_results = await stress_test_video_editing(
        concurrent=50,
        total=200
    )
    
    print(f"\nVideo Editing Results:")
    print(f"  Total Requests: {video_results['total_requests']}")
    print(f"  Successful: {video_results['successful']} ({video_results['success_rate']*100:.1f}%)")
    print(f"  Failed: {video_results['failed']}")
    print(f"  Requests/sec: {video_results['requests_per_second']:.2f}")
    print(f"  Avg Duration: {video_results['avg_duration_ms']:.2f}ms")
    print(f"  P95 Duration: {video_results['p95_duration_ms']:.2f}ms")
    
    # Summary
    print("\n" + "=" * 80)
    print("STRESS TEST SUMMARY")
    print("=" * 80)
    print(f"Pattern Prediction: {pattern_results['success_rate']*100:.1f}% success")
    print(f"Video Editing: {video_results['success_rate']*100:.1f}% success")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

