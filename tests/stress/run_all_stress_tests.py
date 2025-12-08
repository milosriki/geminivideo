#!/usr/bin/env python3
"""
Run All Stress Tests
Comprehensive stress testing suite for pattern prediction and video editing
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.stress.test_pattern_prediction_stress import (
    stress_test_pattern_prediction,
    stress_test_video_editing
)
from tests.stress.test_best_ads_level import (
    stress_test_best_ads_budget_allocation,
    stress_test_best_ads_rag_search,
    stress_test_best_ads_feedback_loop
)


async def run_all_stress_tests():
    """Run complete stress test suite"""
    print("=" * 80)
    print("COMPREHENSIVE STRESS TEST SUITE")
    print("=" * 80)
    
    results = {}
    
    # Pattern Prediction Tests
    print("\n" + "=" * 80)
    print("PART 1: PATTERN PREDICTION STRESS TESTS")
    print("=" * 80)
    
    print("\n1.1 Random Dynamic Questions (1000 requests, 100 concurrent)...")
    results["pattern_prediction"] = await stress_test_pattern_prediction(
        concurrent=100,
        total=1000
    )
    
    print("\n1.2 Video Editing at Best Ads Level (200 requests, 50 concurrent)...")
    results["video_editing"] = await stress_test_video_editing(
        concurrent=50,
        total=200
    )
    
    # Best Ads Level Tests
    print("\n" + "=" * 80)
    print("PART 2: BEST ADS LEVEL STRESS TESTS")
    print("=" * 80)
    
    print("\n2.1 Budget Allocation (500 ads, 50 concurrent)...")
    results["budget_allocation"] = await stress_test_best_ads_budget_allocation(
        concurrent=50,
        total_ads=500
    )
    
    print("\n2.2 RAG Search (1000 searches, 100 concurrent)...")
    results["rag_search"] = await stress_test_best_ads_rag_search(
        concurrent=100,
        total_searches=1000
    )
    
    print("\n2.3 Feedback Loop (2000 feedbacks, 200 concurrent)...")
    results["feedback_loop"] = await stress_test_best_ads_feedback_loop(
        concurrent=200,
        total_feedbacks=2000
    )
    
    # Summary Report
    print("\n" + "=" * 80)
    print("STRESS TEST SUMMARY REPORT")
    print("=" * 80)
    
    for test_name, result in results.items():
        if isinstance(result, dict) and "success_rate" in result:
            print(f"\n{test_name.upper().replace('_', ' ')}:")
            print(f"  Success Rate: {result['success_rate']*100:.1f}%")
            if "avg_duration_ms" in result:
                print(f"  Avg Duration: {result['avg_duration_ms']:.2f}ms")
            if "p95_duration_ms" in result:
                print(f"  P95 Duration: {result['p95_duration_ms']:.2f}ms")
            if "p99_duration_ms" in result:
                print(f"  P99 Duration: {result['p99_duration_ms']:.2f}ms")
    
    print("\n" + "=" * 80)
    print("ALL STRESS TESTS COMPLETE")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_stress_tests())

