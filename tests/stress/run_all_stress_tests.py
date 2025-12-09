#!/usr/bin/env python3
"""
Run All Stress Tests
Comprehensive stress testing suite covering all orchestration flows and functionality
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
from tests.stress.test_complete_creative_generation_flow import (
    stress_test_complete_creative_generation_flow
)
from tests.stress.test_budget_optimization_flow import (
    stress_test_budget_optimization_flow
)
from tests.stress.test_self_learning_cycle import (
    stress_test_self_learning_cycle
)
from tests.stress.test_database_operations import (
    stress_test_database_operations
)
from tests.stress.test_service_communication import (
    stress_test_service_communication
)
from tests.stress.test_video_processing_pipeline import (
    stress_test_video_processing_pipeline
)
from tests.stress.test_ai_council_orchestration import (
    stress_test_ai_council_orchestration
)
from tests.stress.test_meta_api_integration import (
    stress_test_meta_api_integration
)
from tests.stress.test_rag_search_indexing import (
    stress_test_rag_search_indexing
)
from tests.stress.test_realtime_feedback_loops import (
    stress_test_realtime_feedback_loops
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
    
    # New Orchestrated Tests
    print("\n" + "=" * 80)
    print("PART 3: COMPLETE ORCHESTRATION FLOW TESTS")
    print("=" * 80)
    
    print("\n3.1 Complete Creative Generation Flow (50 flows, 10 concurrent)...")
    results["creative_generation_flow"] = await stress_test_complete_creative_generation_flow(
        concurrent=10,
        total_flows=50
    )
    
    print("\n3.2 Budget Optimization Flow (200 flows, 20 concurrent)...")
    results["budget_optimization_flow"] = await stress_test_budget_optimization_flow(
        concurrent=20,
        total_flows=200
    )
    
    print("\n3.3 Self-Learning Cycle (20 cycles, 5 concurrent)...")
    results["self_learning_cycle"] = await stress_test_self_learning_cycle(
        concurrent=5,
        total_cycles=20
    )
    
    print("\n" + "=" * 80)
    print("PART 4: INFRASTRUCTURE & SERVICE TESTS")
    print("=" * 80)
    
    print("\n4.1 Database Operations (200 operations, 20 concurrent)...")
    results["database_operations"] = await stress_test_database_operations(
        concurrent=20,
        total_operations=200
    )
    
    print("\n4.2 Service Communication (500 requests, 50 concurrent)...")
    results["service_communication"] = await stress_test_service_communication(
        concurrent=50,
        total_requests=500
    )
    
    print("\n" + "=" * 80)
    print("PART 5: VIDEO PROCESSING & AI COUNCIL TESTS")
    print("=" * 80)
    
    print("\n5.1 Video Processing Pipeline (50 pipelines, 10 concurrent)...")
    results["video_processing_pipeline"] = await stress_test_video_processing_pipeline(
        concurrent=10,
        total_pipelines=50
    )
    
    print("\n5.2 AI Council Orchestration (50 orchestrations, 10 concurrent)...")
    results["ai_council_orchestration"] = await stress_test_ai_council_orchestration(
        concurrent=10,
        total_orchestrations=50
    )
    
    print("\n" + "=" * 80)
    print("PART 6: INTEGRATION & FEEDBACK TESTS")
    print("=" * 80)
    
    print("\n6.1 Meta API Integration (200 operations, 20 concurrent)...")
    results["meta_api_integration"] = await stress_test_meta_api_integration(
        concurrent=20,
        total_operations=200
    )
    
    print("\n6.2 RAG Search and Indexing (300 operations, 30 concurrent)...")
    results["rag_search_indexing"] = await stress_test_rag_search_indexing(
        concurrent=30,
        total_operations=300
    )
    
    print("\n6.3 Real-time Feedback Loops (500 feedbacks, 50 concurrent)...")
    results["realtime_feedback_loops"] = await stress_test_realtime_feedback_loops(
        concurrent=50,
        total_feedbacks=500
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

