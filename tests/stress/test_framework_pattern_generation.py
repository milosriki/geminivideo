"""
Stress Test: Framework Pattern Generation
Tests if system can produce ads matching TRAINING VIDEO FRAMEWORK.pdf patterns
without hardcoding - must understand and apply the details
"""
import asyncio
import time
import random
import json
from typing import List, Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

# Framework specifications from PDF
FRAMEWORK_SPECS = {
    "phase_1_pattern_interrupt": {
        "duration_seconds": 0.8,
        "requirements": [
            "human_face_with_emotion",
            "direct_eye_contact",
            "lateral_movement_or_15pct_zoom",
            "high_contrast_4_5_1",
            "max_5_words_text",
            "no_branding_first_0_8s",
            "asymmetrical_composition_15_20pct"
        ],
        "pattern_types": [
            "impossible_result",
            "mid_action_freeze",
            "expectation_violation",
            "emotional_extreme",
            "visual_metaphor_interrupt"
        ]
    },
    "phase_2_value_proposition": {
        "duration_seconds": 2.1,  # 0.9-3.0s total
        "requirements": [
            "problem_statement_0_9_1_5s",
            "solution_tease_1_6_3_0s",
            "specific_number_statistic",
            "visual_contrast_split_screen",
            "color_shift_cool_to_warm",
            "text_animation_slide",
            "camera_zoom_in_27pct_retention"
        ]
    },
    "phase_3_validation": {
        "duration_seconds": 32,  # 3.1-35s
        "requirements": [
            "proof_stacking_3_part",
            "testimonials_2_3_quick_cuts",
            "before_after_metrics",
            "objection_handling_top_3",
            "jump_cuts_2_4_seconds",
            "motion_design_sync"
        ]
    },
    "phase_4_cta": {
        "duration_seconds": 15,  # 46-60s
        "requirements": [
            "lead_magnet_presentation",
            "clear_specific_benefit",
            "scarcity_urgency_element",
            "direct_command_language",
            "value_focused_button_text",
            "low_friction_language"
        ]
    },
    "life_force_8_triggers": [
        "survival_life_extension",
        "food_beverage_enjoyment",
        "freedom_from_fear_pain",
        "sexual_companionship",
        "comfortable_living",
        "status_superiority",
        "protection_loved_ones",
        "social_approval"
    ],
    "thumbnail_specs": {
        "resolution_primary": "1080x1920",
        "resolution_secondary": "1080x1350",
        "text_size": "8pct_vertical_height",
        "contrast_ratio": "4.5_1_minimum",
        "face_position": "top_or_center_third",
        "eye_direction": "direct_contact",
        "highlight_effect": "yellow_orange_glow"
    }
}


class FrameworkPatternValidator:
    """Validate generated ads match framework specifications"""
    
    @staticmethod
    def validate_phase_1(ad_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Phase 1: Pattern Interrupt (0-0.8s)"""
        phase_1 = ad_structure.get("phase_1", {})
        requirements = FRAMEWORK_SPECS["phase_1_pattern_interrupt"]["requirements"]
        
        validation = {
            "phase": "pattern_interrupt",
            "duration_check": phase_1.get("duration_seconds", 0) <= 0.8,
            "requirements_met": [],
            "requirements_missing": [],
            "pattern_type": phase_1.get("pattern_type"),
            "score": 0
        }
        
        for req in requirements:
            if req in phase_1.get("elements", []):
                validation["requirements_met"].append(req)
            else:
                validation["requirements_missing"].append(req)
        
        validation["score"] = len(validation["requirements_met"]) / len(requirements)
        return validation
    
    @staticmethod
    def validate_phase_2(ad_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Phase 2: Value Proposition (0.9-3.0s)"""
        phase_2 = ad_structure.get("phase_2", {})
        requirements = FRAMEWORK_SPECS["phase_2_value_proposition"]["requirements"]
        
        validation = {
            "phase": "value_proposition",
            "duration_check": 2.1 <= phase_2.get("duration_seconds", 0) <= 3.0,
            "requirements_met": [],
            "requirements_missing": [],
            "has_specific_number": phase_2.get("has_specific_number", False),
            "score": 0
        }
        
        for req in requirements:
            if req in phase_2.get("elements", []):
                validation["requirements_met"].append(req)
            else:
                validation["requirements_missing"].append(req)
        
        validation["score"] = len(validation["requirements_met"]) / len(requirements)
        return validation
    
    @staticmethod
    def validate_phase_3(ad_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Phase 3: Validation Block (3.1-35s)"""
        phase_3 = ad_structure.get("phase_3", {})
        requirements = FRAMEWORK_SPECS["phase_3_validation"]["requirements"]
        
        validation = {
            "phase": "validation_block",
            "duration_check": 3.1 <= phase_3.get("duration_seconds", 0) <= 35.0,
            "requirements_met": [],
            "requirements_missing": [],
            "testimonials_count": phase_3.get("testimonials_count", 0),
            "objections_handled": phase_3.get("objections_handled", 0),
            "score": 0
        }
        
        for req in requirements:
            if req in phase_3.get("elements", []):
                validation["requirements_met"].append(req)
            else:
                validation["requirements_missing"].append(req)
        
        validation["score"] = len(validation["requirements_met"]) / len(requirements)
        return validation
    
    @staticmethod
    def validate_phase_4(ad_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Phase 4: CTA (46-60s)"""
        phase_4 = ad_structure.get("phase_4", {})
        requirements = FRAMEWORK_SPECS["phase_4_cta"]["requirements"]
        
        validation = {
            "phase": "cta",
            "duration_check": 14 <= phase_4.get("duration_seconds", 0) <= 15,
            "requirements_met": [],
            "requirements_missing": [],
            "has_scarcity": phase_4.get("has_scarcity", False),
            "has_urgency": phase_4.get("has_urgency", False),
            "score": 0
        }
        
        for req in requirements:
            if req in phase_4.get("elements", []):
                validation["requirements_met"].append(req)
            else:
                validation["requirements_missing"].append(req)
        
        validation["score"] = len(validation["requirements_met"]) / len(requirements)
        return validation
    
    @staticmethod
    def validate_life_force_8(ad_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Life-Force 8 psychological triggers"""
        triggers_used = ad_structure.get("life_force_8_triggers", [])
        available_triggers = FRAMEWORK_SPECS["life_force_8_triggers"]
        
        return {
            "triggers_used": triggers_used,
            "triggers_available": available_triggers,
            "coverage": len(set(triggers_used) & set(available_triggers)) / len(available_triggers),
            "score": len(triggers_used) / len(available_triggers) if triggers_used else 0
        }
    
    @staticmethod
    def validate_thumbnail(ad_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate thumbnail specifications"""
        thumbnail = ad_structure.get("thumbnail", {})
        specs = FRAMEWORK_SPECS["thumbnail_specs"]
        
        validation = {
            "resolution_check": thumbnail.get("resolution") in [specs["resolution_primary"], specs["resolution_secondary"]],
            "has_face": thumbnail.get("has_face", False),
            "has_direct_eye_contact": thumbnail.get("has_direct_eye_contact", False),
            "contrast_ratio": thumbnail.get("contrast_ratio", 0) >= 4.5,
            "score": 0
        }
        
        checks = [
            validation["resolution_check"],
            validation["has_face"],
            validation["has_direct_eye_contact"],
            validation["contrast_ratio"]
        ]
        
        validation["score"] = sum(checks) / len(checks)
        return validation
    
    @classmethod
    def validate_complete_ad(cls, ad_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete ad against framework"""
        validations = {
            "phase_1": cls.validate_phase_1(ad_structure),
            "phase_2": cls.validate_phase_2(ad_structure),
            "phase_3": cls.validate_phase_3(ad_structure),
            "phase_4": cls.validate_phase_4(ad_structure),
            "life_force_8": cls.validate_life_force_8(ad_structure),
            "thumbnail": cls.validate_thumbnail(ad_structure)
        }
        
        overall_score = sum(v.get("score", 0) for v in validations.values()) / len(validations)
        
        return {
            "validations": validations,
            "overall_score": overall_score,
            "framework_compliant": overall_score >= 0.8,
            "total_requirements": sum(len(v.get("requirements_met", [])) for v in validations.values() if "requirements_met" in v),
            "total_missing": sum(len(v.get("requirements_missing", [])) for v in validations.values() if "requirements_missing" in v)
        }


async def test_framework_ad_generation(
    industry: str,
    product: str,
    target_audience: str,
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Test if system can generate framework-compliant ad"""
    
    start_time = time.time()
    
    try:
        # Request ad generation from Director Agent
        response = await client.post(
            "http://localhost:8084/api/titan/director/create-battle-plan",
            json={
                "industry": industry,
                "product": product,
                "target_audience": target_audience,
                "framework": "training_video_framework_2025",
                "requirements": {
                    "must_follow_4_phase_structure": True,
                    "must_include_pattern_interrupt": True,
                    "must_include_life_force_8": True,
                    "must_include_thumbnail_specs": True,
                    "must_understand_details": True  # Not hardcoded
                }
            },
            timeout=60.0
        )
        
        duration = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            ad_structure = response.json()
            
            # Validate against framework
            validator = FrameworkPatternValidator()
            validation = validator.validate_complete_ad(ad_structure)
            
            return {
                "success": True,
                "duration_ms": duration,
                "framework_compliant": validation["framework_compliant"],
                "overall_score": validation["overall_score"],
                "validation": validation,
                "ad_structure": ad_structure
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "duration_ms": duration,
                "error": response.text
            }
    
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        return {
            "success": False,
            "error": str(e),
            "duration_ms": duration
        }


async def stress_test_framework_generation(
    concurrent: int = 20,
    total: int = 100
) -> Dict[str, Any]:
    """Stress test framework-compliant ad generation"""
    
    logger.info(f"Testing framework generation: {concurrent} concurrent, {total} total")
    
    # Test scenarios
    scenarios = [
        {
            "industry": "fitness",
            "product": "Personal Training Program",
            "target_audience": "Busy professionals 30-45, want to lose weight"
        },
        {
            "industry": "finance",
            "product": "Investment Course",
            "target_audience": "Entrepreneurs 25-40, want financial freedom"
        },
        {
            "industry": "real_estate",
            "product": "Real Estate Investing Course",
            "target_audience": "First-time investors 28-50, want passive income"
        },
        {
            "industry": "ecommerce",
            "product": "Dropshipping Course",
            "target_audience": "Aspiring entrepreneurs 20-35, want online business"
        },
        {
            "industry": "healthcare",
            "product": "Wellness Program",
            "target_audience": "Health-conscious individuals 35-55, want longevity"
        }
    ]
    
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Generate test cases
        test_cases = []
        for i in range(total):
            scenario = random.choice(scenarios)
            test_cases.append(scenario)
        
        # Process in batches
        batch_size = concurrent
        for i in range(0, total, batch_size):
            batch = test_cases[i:i + batch_size]
            
            batch_results = await asyncio.gather(
                *[test_framework_ad_generation(**scenario, client=client) for scenario in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    framework_compliant = [r for r in successful if r.get("framework_compliant", False)]
    
    scores = [r.get("overall_score", 0) for r in successful if "overall_score" in r]
    
    return {
        "total_tests": total,
        "concurrent": concurrent,
        "successful": len(successful),
        "framework_compliant": len(framework_compliant),
        "compliance_rate": len(framework_compliant) / len(successful) if successful else 0,
        "avg_framework_score": sum(scores) / len(scores) if scores else 0,
        "total_duration_seconds": total_duration,
        "tests_per_second": total / total_duration if total_duration > 0 else 0,
        "detailed_results": results[:10]  # First 10 for inspection
    }


async def test_pattern_interrupt_generation(
    pattern_type: str,
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Test if system can generate specific pattern interrupt types"""
    
    try:
        response = await client.post(
            "http://localhost:8084/api/titan/creative/pattern-interrupt",
            json={
                "pattern_type": pattern_type,
                "framework_specs": FRAMEWORK_SPECS["phase_1_pattern_interrupt"],
                "must_understand": True  # Not hardcoded
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if it understands the pattern type
            understands = result.get("pattern_type") == pattern_type
            has_requirements = all(
                req in result.get("elements", [])
                for req in FRAMEWORK_SPECS["phase_1_pattern_interrupt"]["requirements"][:3]
            )
            
            return {
                "success": True,
                "pattern_type": pattern_type,
                "understands_pattern": understands,
                "has_requirements": has_requirements,
                "not_hardcoded": result.get("reasoning") is not None  # Shows understanding
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


async def test_transition_generation(
    from_phase: str,
    to_phase: str,
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Test if system can generate smooth transitions between phases"""
    
    try:
        response = await client.post(
            "http://localhost:8084/api/titan/creative/transition",
            json={
                "from_phase": from_phase,
                "to_phase": to_phase,
                "framework_specs": FRAMEWORK_SPECS,
                "must_understand": True
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if transition makes sense
            has_timing = "timing_seconds" in result
            has_visual_flow = "visual_flow" in result
            has_psychological_continuity = "psychological_continuity" in result
            
            return {
                "success": True,
                "from_phase": from_phase,
                "to_phase": to_phase,
                "has_timing": has_timing,
                "has_visual_flow": has_visual_flow,
                "has_psychological_continuity": has_psychological_continuity,
                "understands_transition": all([has_timing, has_visual_flow, has_psychological_continuity])
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


async def test_final_product_generation(
    industry: str,
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Test if system can produce final product matching framework"""
    
    try:
        response = await client.post(
            "http://localhost:8084/api/titan/director/generate-complete-ad",
            json={
                "industry": industry,
                "framework": "training_video_framework_2025",
                "output_format": "complete_production_ready",
                "include": [
                    "thumbnail_specs",
                    "4_phase_script",
                    "visual_requirements",
                    "audio_requirements",
                    "timing_specifications",
                    "psychological_triggers",
                    "production_notes"
                ],
                "must_understand": True  # Not hardcoded
            },
            timeout=120.0
        )
        
        if response.status_code == 200:
            product = response.json()
            
            # Validate it's a complete product
            has_all_phases = all(
                f"phase_{i}" in product for i in range(1, 5)
            )
            has_thumbnail = "thumbnail" in product
            has_specs = "specifications" in product
            has_production_notes = "production_notes" in product
            shows_understanding = "reasoning" in product or "framework_application" in product
            
            validator = FrameworkPatternValidator()
            validation = validator.validate_complete_ad(product)
            
            return {
                "success": True,
                "has_all_phases": has_all_phases,
                "has_thumbnail": has_thumbnail,
                "has_specs": has_specs,
                "has_production_notes": has_production_notes,
                "shows_understanding": shows_understanding,
                "framework_compliant": validation["framework_compliant"],
                "overall_score": validation["overall_score"],
                "is_complete_product": all([
                    has_all_phases,
                    has_thumbnail,
                    has_specs,
                    has_production_notes
                ])
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
    """Run all framework pattern generation tests"""
    print("=" * 80)
    print("FRAMEWORK PATTERN GENERATION STRESS TEST")
    print("Testing if system can produce TRAINING VIDEO FRAMEWORK.pdf patterns")
    print("=" * 80)
    
    # Test 1: Framework-compliant ad generation
    print("\n1. Testing Framework-Compliant Ad Generation...")
    framework_results = await stress_test_framework_generation(
        concurrent=20,
        total=100
    )
    
    print(f"\nFramework Generation Results:")
    print(f"  Total Tests: {framework_results['total_tests']}")
    print(f"  Successful: {framework_results['successful']}")
    print(f"  Framework Compliant: {framework_results['framework_compliant']}")
    print(f"  Compliance Rate: {framework_results['compliance_rate']*100:.1f}%")
    print(f"  Avg Framework Score: {framework_results['avg_framework_score']*100:.1f}%")
    
    # Test 2: Pattern interrupt generation
    print("\n2. Testing Pattern Interrupt Generation...")
    pattern_types = FRAMEWORK_SPECS["phase_1_pattern_interrupt"]["pattern_types"]
    
    async with httpx.AsyncClient() as client:
        pattern_results = await asyncio.gather(
            *[test_pattern_interrupt_generation(pt, client) for pt in pattern_types],
            return_exceptions=True
        )
    
    successful_patterns = [r for r in pattern_results if isinstance(r, dict) and r.get("success")]
    understands_patterns = [r for r in successful_patterns if r.get("understands_pattern")]
    
    print(f"  Pattern Types Tested: {len(pattern_types)}")
    print(f"  Successful: {len(successful_patterns)}")
    print(f"  Understands Pattern: {len(understands_patterns)}")
    print(f"  Understanding Rate: {len(understands_patterns)/len(successful_patterns)*100:.1f}%" if successful_patterns else "N/A")
    
    # Test 3: Transition generation
    print("\n3. Testing Transition Generation...")
    transitions = [
        ("phase_1", "phase_2"),
        ("phase_2", "phase_3"),
        ("phase_3", "phase_4")
    ]
    
    async with httpx.AsyncClient() as client:
        transition_results = await asyncio.gather(
            *[test_transition_generation(f, t, client) for f, t in transitions],
            return_exceptions=True
        )
    
    successful_transitions = [r for r in transition_results if isinstance(r, dict) and r.get("success")]
    understands_transitions = [r for r in successful_transitions if r.get("understands_transition")]
    
    print(f"  Transitions Tested: {len(transitions)}")
    print(f"  Successful: {len(successful_transitions)}")
    print(f"  Understands Transition: {len(understands_transitions)}")
    
    # Test 4: Final product generation
    print("\n4. Testing Final Product Generation...")
    industries = ["fitness", "finance", "real_estate", "ecommerce", "healthcare"]
    
    async with httpx.AsyncClient() as client:
        product_results = await asyncio.gather(
            *[test_final_product_generation(ind, client) for ind in industries],
            return_exceptions=True
        )
    
    successful_products = [r for r in product_results if isinstance(r, dict) and r.get("success")]
    complete_products = [r for r in successful_products if r.get("is_complete_product")]
    framework_compliant_products = [r for r in successful_products if r.get("framework_compliant")]
    
    print(f"  Industries Tested: {len(industries)}")
    print(f"  Successful: {len(successful_products)}")
    print(f"  Complete Products: {len(complete_products)}")
    print(f"  Framework Compliant: {len(framework_compliant_products)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("FRAMEWORK PATTERN GENERATION SUMMARY")
    print("=" * 80)
    print(f"Framework Compliance: {framework_results['compliance_rate']*100:.1f}%")
    print(f"Pattern Understanding: {len(understands_patterns)/len(successful_patterns)*100:.1f}%" if successful_patterns else "N/A")
    print(f"Transition Understanding: {len(understands_transitions)/len(successful_transitions)*100:.1f}%" if successful_transitions else "N/A")
    print(f"Complete Products: {len(complete_products)}/{len(industries)}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

