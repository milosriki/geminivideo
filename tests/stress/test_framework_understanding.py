"""
Stress Test: Framework Understanding (Not Hardcoded)
Tests if system truly understands framework details vs hardcoding
"""
import asyncio
import json
from typing import Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)


async def test_framework_understanding_variations(
    base_scenario: Dict[str, Any],
    variations: List[Dict[str, Any]],
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """
    Test if system adapts to variations (proves understanding, not hardcoding)
    """
    results = []
    
    for variation in variations:
        scenario = {**base_scenario, **variation}
        
        try:
            response = await client.post(
                "http://localhost:8084/api/titan/director/create-battle-plan",
                json={
                    **scenario,
                    "framework": "training_video_framework_2025",
                    "test_understanding": True  # Signal to show reasoning
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for understanding indicators
                has_reasoning = "reasoning" in result or "framework_application" in result
                adapts_to_variation = variation.get("key_change") in str(result)
                shows_understanding = has_reasoning and adapts_to_variation
                
                results.append({
                    "variation": variation,
                    "success": True,
                    "shows_understanding": shows_understanding,
                    "has_reasoning": has_reasoning,
                    "adapts": adapts_to_variation
                })
            else:
                results.append({
                    "variation": variation,
                    "success": False,
                    "status_code": response.status_code
                })
        
        except Exception as e:
            results.append({
                "variation": variation,
                "success": False,
                "error": str(e)
            })
    
    understanding_rate = sum(
        1 for r in results 
        if r.get("shows_understanding", False)
    ) / len(results) if results else 0
    
    return {
        "total_variations": len(variations),
        "successful": sum(1 for r in results if r.get("success")),
        "shows_understanding": sum(1 for r in results if r.get("shows_understanding")),
        "understanding_rate": understanding_rate,
        "results": results
    }


async def test_dynamic_hook_generation(
    context: Dict[str, Any],
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Test if system generates hooks dynamically based on context"""
    
    try:
        response = await client.post(
            "http://localhost:8084/api/titan/creative/generate-hook",
            json={
                "context": context,
                "framework": "training_video_framework_2025",
                "phase": "pattern_interrupt",
                "must_adapt": True  # Not hardcoded
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if hook adapts to context
            hook_text = result.get("hook_text", "")
            context_keywords = [
                context.get("industry", ""),
                context.get("pain_point", ""),
                context.get("target_audience", "")
            ]
            
            adapts_to_context = any(
                keyword.lower() in hook_text.lower() 
                for keyword in context_keywords 
                if keyword
            )
            
            has_framework_elements = any(
                element in result.get("elements", [])
                for element in [
                    "human_face_with_emotion",
                    "direct_eye_contact",
                    "pattern_interrupt"
                ]
            )
            
            return {
                "success": True,
                "adapts_to_context": adapts_to_context,
                "has_framework_elements": has_framework_elements,
                "not_hardcoded": adapts_to_context and has_framework_elements,
                "hook_text": hook_text[:100]  # First 100 chars
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


async def test_transition_understanding(
    phase_1_content: Dict[str, Any],
    phase_2_requirements: Dict[str, Any],
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Test if system understands how to transition between phases"""
    
    try:
        response = await client.post(
            "http://localhost:8084/api/titan/creative/create-transition",
            json={
                "from_content": phase_1_content,
                "to_requirements": phase_2_requirements,
                "framework": "training_video_framework_2025",
                "must_understand_flow": True
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if transition makes logical sense
            has_timing = "timing_seconds" in result
            connects_content = "connects_to_phase_1" in result.get("reasoning", "")
            sets_up_phase_2 = "sets_up_phase_2" in result.get("reasoning", "")
            
            understands_flow = has_timing and (connects_content or sets_up_phase_2)
            
            return {
                "success": True,
                "understands_flow": understands_flow,
                "has_timing": has_timing,
                "connects_content": connects_content,
                "sets_up_next": sets_up_phase_2
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


async def main():
    """Run framework understanding tests"""
    print("=" * 80)
    print("FRAMEWORK UNDERSTANDING TEST")
    print("Testing if system understands vs hardcodes")
    print("=" * 80)
    
    base_scenario = {
        "industry": "fitness",
        "product": "Weight Loss Program",
        "target_audience": "Busy professionals 30-45"
    }
    
    variations = [
        {"industry": "finance", "key_change": "finance"},
        {"industry": "real_estate", "key_change": "real_estate"},
        {"target_audience": "Seniors 60+", "key_change": "seniors"},
        {"product": "Luxury Service", "key_change": "luxury"},
        {"pain_point": "Time constraint", "key_change": "time"}
    ]
    
    async with httpx.AsyncClient() as client:
        # Test 1: Variation understanding
        print("\n1. Testing Variation Understanding...")
        variation_results = await test_framework_understanding_variations(
            base_scenario,
            variations,
            client
        )
        
        print(f"  Variations Tested: {variation_results['total_variations']}")
        print(f"  Shows Understanding: {variation_results['shows_understanding']}")
        print(f"  Understanding Rate: {variation_results['understanding_rate']*100:.1f}%")
        
        # Test 2: Dynamic hook generation
        print("\n2. Testing Dynamic Hook Generation...")
        contexts = [
            {"industry": "fitness", "pain_point": "lack of time", "target_audience": "busy professionals"},
            {"industry": "finance", "pain_point": "debt", "target_audience": "young adults"},
            {"industry": "healthcare", "pain_point": "chronic pain", "target_audience": "middle-aged"}
        ]
        
        hook_results = await asyncio.gather(
            *[test_dynamic_hook_generation(ctx, client) for ctx in contexts],
            return_exceptions=True
        )
        
        successful_hooks = [r for r in hook_results if isinstance(r, dict) and r.get("success")]
        adapts_to_context = [r for r in successful_hooks if r.get("adapts_to_context")]
        not_hardcoded = [r for r in successful_hooks if r.get("not_hardcoded")]
        
        print(f"  Contexts Tested: {len(contexts)}")
        print(f"  Successful: {len(successful_hooks)}")
        print(f"  Adapts to Context: {len(adapts_to_context)}")
        print(f"  Not Hardcoded: {len(not_hardcoded)}")
        
        # Test 3: Transition understanding
        print("\n3. Testing Transition Understanding...")
        phase_1 = {
            "pattern_type": "impossible_result",
            "content": "Shows dramatic transformation"
        }
        phase_2_req = {
            "must_connect": True,
            "must_setup_solution": True
        }
        
        transition_result = await test_transition_understanding(phase_1, phase_2_req, client)
        
        print(f"  Success: {transition_result.get('success')}")
        print(f"  Understands Flow: {transition_result.get('understands_flow')}")
        
        # Summary
        print("\n" + "=" * 80)
        print("UNDERSTANDING TEST SUMMARY")
        print("=" * 80)
        print(f"Variation Understanding: {variation_results['understanding_rate']*100:.1f}%")
        print(f"Dynamic Hook Generation: {len(not_hardcoded)}/{len(successful_hooks)}")
        print(f"Transition Understanding: {transition_result.get('understands_flow', False)}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

