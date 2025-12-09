"""
Stress Test: Final Product Production
Tests if system can produce complete, production-ready ads matching framework
"""
import asyncio
import json
from typing import Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)


async def test_complete_ad_production(
    scenario: Dict[str, Any],
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Test production of complete, framework-compliant ad"""
    
    try:
        response = await client.post(
            "http://localhost:8084/api/titan/director/generate-complete-ad",
            json={
                **scenario,
                "framework": "training_video_framework_2025",
                "output_format": "production_ready",
                "include_all_specs": True,
                "must_understand": True
            },
            timeout=120.0
        )
        
        if response.status_code == 200:
            product = response.json()
            
            # Check completeness
            completeness_checks = {
                "has_thumbnail_specs": "thumbnail" in product and "specifications" in product.get("thumbnail", {}),
                "has_4_phases": all(f"phase_{i}" in product for i in range(1, 5)),
                "has_timing_specs": all(
                    "timing_seconds" in product.get(f"phase_{i}", {})
                    for i in range(1, 5)
                ),
                "has_visual_requirements": "visual_requirements" in product,
                "has_audio_requirements": "audio_requirements" in product,
                "has_psychological_triggers": "life_force_8_triggers" in product,
                "has_production_notes": "production_notes" in product,
                "has_script": "script" in product or all(
                    "script" in product.get(f"phase_{i}", {})
                    for i in range(1, 5)
                )
            }
            
            completeness_score = sum(completeness_checks.values()) / len(completeness_checks)
            
            # Check framework compliance
            from tests.stress.test_framework_pattern_generation import FrameworkPatternValidator
            validator = FrameworkPatternValidator()
            validation = validator.validate_complete_ad(product)
            
            return {
                "success": True,
                "completeness_score": completeness_score,
                "completeness_checks": completeness_checks,
                "framework_compliant": validation["framework_compliant"],
                "framework_score": validation["overall_score"],
                "is_production_ready": completeness_score >= 0.9 and validation["framework_compliant"],
                "product_size": len(json.dumps(product))
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def stress_test_production(
    concurrent: int = 10,
    total: int = 50
) -> Dict[str, Any]:
    """Stress test complete ad production"""
    
    scenarios = [
        {
            "industry": "fitness",
            "product": "6-Week Transformation Program",
            "target_audience": "Busy professionals 30-45",
            "pain_points": ["lack of time", "tried everything", "no results"],
            "unique_value": "15-min daily workouts"
        },
        {
            "industry": "finance",
            "product": "Investment Mastery Course",
            "target_audience": "Entrepreneurs 25-40",
            "pain_points": ["don't know where to start", "afraid of losing money"],
            "unique_value": "Step-by-step system"
        },
        {
            "industry": "real_estate",
            "product": "Real Estate Investing Blueprint",
            "target_audience": "First-time investors 28-50",
            "pain_points": ["don't have capital", "too risky"],
            "unique_value": "No money down strategies"
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Generate test cases
        test_cases = []
        for i in range(total):
            base = random.choice(scenarios)
            test_cases.append(base)
        
        # Process in batches
        batch_size = concurrent
        for i in range(0, total, batch_size):
            batch = test_cases[i:i + batch_size]
            
            batch_results = await asyncio.gather(
                *[test_complete_ad_production(scenario, client) for scenario in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}")
    
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    production_ready = [r for r in successful if r.get("is_production_ready")]
    framework_compliant = [r for r in successful if r.get("framework_compliant")]
    
    completeness_scores = [r.get("completeness_score", 0) for r in successful]
    framework_scores = [r.get("framework_score", 0) for r in successful]
    
    return {
        "total_tests": total,
        "concurrent": concurrent,
        "successful": len(successful),
        "production_ready": len(production_ready),
        "framework_compliant": len(framework_compliant),
        "production_ready_rate": len(production_ready) / len(successful) if successful else 0,
        "avg_completeness": sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0,
        "avg_framework_score": sum(framework_scores) / len(framework_scores) if framework_scores else 0
    }


async def main():
    """Run production stress tests"""
    print("=" * 80)
    print("FINAL PRODUCT PRODUCTION STRESS TEST")
    print("Testing if system can produce complete, framework-compliant ads")
    print("=" * 80)
    
    results = await stress_test_production(
        concurrent=10,
        total=50
    )
    
    print(f"\nProduction Results:")
    print(f"  Total Tests: {results['total_tests']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Production Ready: {results['production_ready']}")
    print(f"  Framework Compliant: {results['framework_compliant']}")
    print(f"  Production Ready Rate: {results['production_ready_rate']*100:.1f}%")
    print(f"  Avg Completeness: {results['avg_completeness']*100:.1f}%")
    print(f"  Avg Framework Score: {results['avg_framework_score']*100:.1f}%")
    
    print("\n" + "=" * 80)
    print("PRODUCTION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    import random
    asyncio.run(main())

