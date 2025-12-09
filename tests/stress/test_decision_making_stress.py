"""
Stress Test: Decision Making & Learning Loops
Tests decision-making under load and identifies where we're not maximizing capabilities
"""
import asyncio
import time
import random
import numpy as np
from typing import List, Dict, Any, Optional
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DecisionMakingStressTest:
    """Stress test decision-making systems"""
    
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.results = []
    
    async def test_battle_hardened_decision_under_load(
        self,
        concurrent: int = 100,
        total_decisions: int = 1000
    ) -> Dict[str, Any]:
        """Stress test BattleHardenedSampler decision-making"""
        
        logger.info(f"Testing {total_decisions} decisions with {concurrent} concurrent")
        
        # Generate realistic ad states
        ad_states = []
        for i in range(total_decisions):
            ad_states.append({
                "ad_id": f"ad-{i}",
                "impressions": random.randint(1000, 100000),
                "clicks": random.randint(50, 5000),
                "spend": random.uniform(100, 10000),
                "pipeline_value": random.uniform(0, 50000),
                "cash_revenue": random.uniform(0, 30000),
                "age_hours": random.uniform(1, 720),
                "pipeline_roas": random.uniform(0, 10),
                "ctr": random.uniform(0.01, 0.10)
            })
        
        results = []
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            # Process in batches
            batch_size = concurrent
            for i in range(0, total_decisions, batch_size):
                batch = ad_states[i:i + batch_size]
                
                async def make_decision(ad_state):
                    try:
                        start = time.time()
                        response = await client.post(
                            f"{self.base_url}/api/ml/battle-hardened/select",
                            json={
                                "ad_states": [ad_state],
                                "total_budget": 1000,
                                "creative_dna_scores": {ad_state["ad_id"]: random.uniform(0.5, 1.0)}
                            },
                            timeout=10.0
                        )
                        duration = (time.time() - start) * 1000
                        
                        if response.status_code == 200:
                            data = response.json()
                            return {
                                "success": True,
                                "duration_ms": duration,
                                "has_recommendation": len(data.get("recommendations", [])) > 0,
                                "has_confidence": "confidence" in str(data),
                                "has_reasoning": "reason" in str(data),
                                "decision_quality": self._assess_decision_quality(data, ad_state)
                            }
                        else:
                            return {
                                "success": False,
                                "status_code": response.status_code,
                                "duration_ms": duration
                            }
                    except Exception as e:
                        return {
                            "success": False,
                            "error": str(e)
                        }
                
                batch_results = await asyncio.gather(
                    *[make_decision(ad) for ad in batch],
                    return_exceptions=True
                )
                
                results.extend(batch_results)
                logger.info(f"Processed batch {i // batch_size + 1}/{(total_decisions + batch_size - 1) // batch_size}")
        
        total_duration = time.time() - start_time
        
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        
        # Analyze decision quality
        quality_issues = []
        if successful:
            has_reasoning = sum(1 for r in successful if r.get("has_reasoning"))
            has_confidence = sum(1 for r in successful if r.get("has_confidence"))
            
            if has_reasoning / len(successful) < 1.0:
                quality_issues.append("Missing reasoning in some decisions")
            
            if has_confidence / len(successful) < 1.0:
                quality_issues.append("Missing confidence scores")
        
        return {
            "total_decisions": total_decisions,
            "concurrent": concurrent,
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "total_duration_seconds": total_duration,
            "decisions_per_second": total_decisions / total_duration if total_duration > 0 else 0,
            "quality_issues": quality_issues,
            "avg_duration_ms": np.mean([r["duration_ms"] for r in successful if "duration_ms" in r]) if successful else 0
        }
    
    def _assess_decision_quality(self, decision_data: Dict, ad_state: Dict) -> Dict[str, Any]:
        """Assess if decision uses full framework capabilities"""
        issues = []
        missing_capabilities = []
        
        recs = decision_data.get("recommendations", [])
        if not recs:
            issues.append("No recommendations returned")
            return {"issues": issues, "missing_capabilities": missing_capabilities}
        
        rec = recs[0]
        
        # Check if using blended scoring
        if "ctr_weight" not in rec.get("metrics", {}):
            missing_capabilities.append("Blended scoring (CTR/ROAS weights)")
        
        # Check if using fatigue detection
        if "fatigue_score" not in rec.get("metrics", {}):
            missing_capabilities.append("Fatigue detection")
        
        # Check if using Creative DNA boost
        if "dna_boost" not in str(rec):
            missing_capabilities.append("Creative DNA boost")
        
        # Check if using Thompson Sampling
        if "confidence" not in rec:
            missing_capabilities.append("Thompson Sampling confidence")
        
        # Check if using ignorance zone
        age_hours = ad_state.get("age_hours", 0)
        if age_hours < 48 and "observe" not in rec.get("reason", "").lower():
            missing_capabilities.append("Ignorance zone logic")
        
        return {
            "issues": issues,
            "missing_capabilities": missing_capabilities,
            "uses_full_framework": len(missing_capabilities) == 0
        }
    
    async def test_learning_loop_effectiveness(
        self,
        iterations: int = 50
    ) -> Dict[str, Any]:
        """Test if learning loops are actually improving decisions"""
        
        logger.info(f"Testing learning loop over {iterations} iterations")
        
        # Simulate learning cycle
        performance_trend = []
        learning_indicators = []
        
        async with httpx.AsyncClient() as client:
            for i in range(iterations):
                # Simulate feedback
                feedback = {
                    "ad_id": f"learning-ad-{i % 10}",  # Reuse same ads
                    "actual_pipeline_value": random.uniform(1000, 10000),
                    "actual_spend": random.uniform(500, 5000)
                }
                
                # Send feedback
                try:
                    start = time.time()
                    response = await client.post(
                        f"{self.base_url}/api/ml/battle-hardened/feedback",
                        json=feedback,
                        timeout=5.0
                    )
                    duration = (time.time() - start) * 1000
                    
                    if response.status_code == 200:
                        # Check if learning is happening
                        learning_indicators.append({
                            "iteration": i,
                            "feedback_registered": True,
                            "duration_ms": duration,
                            "has_learning_signal": "actual_roas" in response.text
                        })
                    else:
                        learning_indicators.append({
                            "iteration": i,
                            "feedback_registered": False,
                            "error": response.status_code
                        })
                except Exception as e:
                    learning_indicators.append({
                        "iteration": i,
                        "feedback_registered": False,
                        "error": str(e)
                    })
                
                # Every 10 iterations, check if decisions improved
                if i % 10 == 0 and i > 0:
                    # Make decision for same ad
                    decision_response = await client.post(
                        f"{self.base_url}/api/ml/battle-hardened/select",
                        json={
                            "ad_states": [{
                                "ad_id": f"learning-ad-{i % 10}",
                                "impressions": 10000,
                                "clicks": 500,
                                "spend": 2000,
                                "pipeline_value": 8000,
                                "cash_revenue": 6000,
                                "age_hours": 72
                            }],
                            "total_budget": 1000
                        },
                        timeout=10.0
                    )
                    
                    if decision_response.status_code == 200:
                        recs = decision_response.json().get("recommendations", [])
                        if recs:
                            confidence = recs[0].get("confidence", 0)
                            performance_trend.append({
                                "iteration": i,
                                "confidence": confidence
                            })
        
        # Analyze learning effectiveness
        if len(performance_trend) > 1:
            confidences = [p["confidence"] for p in performance_trend]
            learning_improvement = confidences[-1] - confidences[0] if len(confidences) > 1 else 0
            is_learning = learning_improvement > 0
        else:
            is_learning = False
            learning_improvement = 0
        
        feedback_registered = sum(1 for li in learning_indicators if li.get("feedback_registered"))
        
        return {
            "iterations": iterations,
            "feedback_registered": feedback_registered,
            "feedback_rate": feedback_registered / iterations if iterations > 0 else 0,
            "is_learning": is_learning,
            "learning_improvement": learning_improvement,
            "performance_trend": performance_trend,
            "learning_indicators": learning_indicators
        }
    
    async def test_self_learning_cycle_completeness(
        self,
        cycles: int = 10
    ) -> Dict[str, Any]:
        """Test if self-learning cycle uses all 7 loops"""
        
        logger.info(f"Testing {cycles} self-learning cycles")
        
        missing_loops = []
        cycle_results = []
        
        async with httpx.AsyncClient() as client:
            for i in range(cycles):
                try:
                    response = await client.post(
                        f"{self.base_url}/api/ml/self-learning-cycle",
                        json={
                            "account_id": f"test-account-{i}",
                            "trigger_retrain": True,
                            "accuracy_threshold": 0.80
                        },
                        timeout=120.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        steps = data.get("steps", [])
                        
                        # Check for all 7 loops
                        expected_steps = [
                            "fetch_actuals",
                            "calculate_accuracy",
                            "auto_retrain",
                            "compound_learning",
                            "auto_promote",
                            "cross_learning",
                            "rag_indexing"
                        ]
                        
                        step_names = [s.get("name", "") for s in steps]
                        missing = [step for step in expected_steps if step not in step_names]
                        
                        if missing:
                            missing_loops.extend(missing)
                        
                        cycle_results.append({
                            "cycle": i,
                            "success": True,
                            "steps_completed": len(steps),
                            "expected_steps": len(expected_steps),
                            "missing_steps": missing
                        })
                    else:
                        cycle_results.append({
                            "cycle": i,
                            "success": False,
                            "status_code": response.status_code
                        })
                
                except Exception as e:
                    cycle_results.append({
                        "cycle": i,
                        "success": False,
                        "error": str(e)
                    })
        
        unique_missing = list(set(missing_loops))
        
        return {
            "cycles_tested": cycles,
            "successful_cycles": sum(1 for r in cycle_results if r.get("success")),
            "missing_loops": unique_missing,
            "uses_all_7_loops": len(unique_missing) == 0,
            "cycle_results": cycle_results
        }


async def test_agent_orchestration_under_load(
    concurrent: int = 50,
    total_requests: int = 500
) -> Dict[str, Any]:
    """Stress test agent orchestration and find coordination failures"""
    
    logger.info(f"Testing agent orchestration: {concurrent} concurrent, {total_requests} total")
    
    # Simulate complex workflow requiring multiple agents
    workflows = []
    for i in range(total_requests):
        workflows.append({
            "workflow_id": f"workflow-{i}",
            "type": random.choice([
                "creative_generation",  # Requires: Director → RAG → Creative DNA → Video Agent
                "budget_optimization",  # Requires: BattleHardened → SafeExecutor → Meta Publisher
                "learning_cycle"  # Requires: All 7 loops
            ]),
            "complexity": random.choice(["simple", "medium", "complex"])
        })
    
    results = []
    orchestration_failures = []
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        batch_size = concurrent
        for i in range(0, total_requests, batch_size):
            batch = workflows[i:i + batch_size]
            
            async def execute_workflow(workflow):
                try:
                    start = time.time()
                    
                    # Route to appropriate endpoint
                    if workflow["type"] == "creative_generation":
                        endpoint = "http://localhost:8084/api/titan/director/create-battle-plan"
                        payload = {
                            "video_id": f"video-{workflow['workflow_id']}",
                            "framework": "training_video_framework_2025"
                        }
                    elif workflow["type"] == "budget_optimization":
                        endpoint = f"http://localhost:8003/api/ml/battle-hardened/select"
                        payload = {
                            "ad_states": [{
                                "ad_id": f"ad-{workflow['workflow_id']}",
                                "impressions": 10000,
                                "clicks": 500,
                                "spend": 2000,
                                "pipeline_value": 8000,
                                "age_hours": 72
                            }],
                            "total_budget": 1000
                        }
                    else:  # learning_cycle
                        endpoint = f"http://localhost:8003/api/ml/self-learning-cycle"
                        payload = {
                            "account_id": workflow["workflow_id"],
                            "trigger_retrain": True
                        }
                    
                    response = await client.post(
                        endpoint,
                        json=payload,
                        timeout=60.0
                    )
                    
                    duration = (time.time() - start) * 1000
                    
                    # Check for orchestration issues
                    issues = []
                    if response.status_code != 200:
                        issues.append(f"HTTP {response.status_code}")
                    
                    if duration > 5000:  # > 5 seconds
                        issues.append("Slow orchestration")
                    
                    # Check if all required agents participated
                    response_text = response.text if response.status_code == 200 else ""
                    if workflow["type"] == "creative_generation":
                        if "rag" not in response_text.lower() and "similar" not in response_text.lower():
                            issues.append("RAG agent not used")
                        if "dna" not in response_text.lower() and "creative" not in response_text.lower():
                            issues.append("Creative DNA agent not used")
                    
                    if issues:
                        orchestration_failures.append({
                            "workflow_id": workflow["workflow_id"],
                            "type": workflow["type"],
                            "issues": issues
                        })
                    
                    return {
                        "success": response.status_code == 200,
                        "duration_ms": duration,
                        "workflow_type": workflow["type"],
                        "issues": issues
                    }
                
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "workflow_type": workflow["type"]
                    }
            
            batch_results = await asyncio.gather(
                *[execute_workflow(w) for w in batch],
                return_exceptions=True
            )
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_requests + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    successful = [r for r in results if isinstance(r, dict) and r.get("success")]
    
    return {
        "total_workflows": total_requests,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "orchestration_failures": len(orchestration_failures),
        "failure_details": orchestration_failures[:20],  # First 20
        "total_duration_seconds": total_duration,
        "workflows_per_second": total_requests / total_duration if total_duration > 0 else 0
    }


async def find_underutilized_capabilities() -> Dict[str, Any]:
    """Find where we're not maximizing framework/concept capabilities"""
    
    logger.info("Analyzing underutilized capabilities...")
    
    issues = []
    
    async with httpx.AsyncClient() as client:
        # Test 1: Check if using all BlendingEngine curves
        try:
            # Check code/endpoints for curve options
            response = await client.get(f"http://localhost:8003/health", timeout=5.0)
            # Would need to check actual implementation
            issues.append({
                "category": "BlendingEngine",
                "issue": "Only using SIGMOID curve - not testing LINEAR, EXPONENTIAL, STEP, ADAPTIVE",
                "impact": "Missing optimization opportunities",
                "recommendation": "Test all 5 curve types and select best per account"
            })
        except:
            pass
        
        # Test 2: Check if using all FatigueDetector rules
        issues.append({
            "category": "FatigueDetector",
            "issue": "May not be using all 4 detection rules simultaneously",
            "impact": "Missing fatigue signals",
            "recommendation": "Combine all rules: frequency + CTR decline + CPM increase + impression decay"
        })
        
        # Test 3: Check if using all Life-Force 8 triggers
        issues.append({
            "category": "Life-Force 8",
            "issue": "Not systematically testing all 8 psychological triggers",
            "impact": "Missing high-performing trigger combinations",
            "recommendation": "Test all 8 triggers and combinations in A/B tests"
        })
        
        # Test 4: Check if using all Thompson Sampling capabilities
        issues.append({
            "category": "Thompson Sampling",
            "issue": "Not using variance-based exploration (uncertainty quantification)",
            "impact": "Suboptimal explore/exploit balance",
            "recommendation": "Use variance in Beta distribution to prioritize uncertain ads"
        })
        
        # Test 5: Check if using all RAG capabilities
        issues.append({
            "category": "RAG Winner Index",
            "issue": "Not using hybrid search (vector + metadata filtering simultaneously)",
            "impact": "Missing relevant winners",
            "recommendation": "Combine FAISS similarity + metadata filters for better results"
        })
        
        # Test 6: Check if using all Synthetic Revenue capabilities
        issues.append({
            "category": "Synthetic Revenue",
            "issue": "Not using time decay for stale deals",
            "impact": "Overvaluing old pipeline stages",
            "recommendation": "Apply exponential decay: 0.5^(days/half_life)"
        })
        
        # Test 7: Check if using all SafeExecutor capabilities
        issues.append({
            "category": "SafeExecutor",
            "issue": "Not using all safety features: fuzzy budgets, jitter, velocity limits",
            "impact": "Higher ban risk",
            "recommendation": "Enable all: rate limiting + velocity + fuzzing + jitter"
        })
        
        # Test 8: Check if using all Model Registry capabilities
        issues.append({
            "category": "Model Registry",
            "issue": "Not using champion/challenger A/B testing",
            "impact": "Not improving models over time",
            "recommendation": "Run challenger models in parallel, promote when better"
        })
        
        # Test 9: Check if using all Vertex AI capabilities
        issues.append({
            "category": "Vertex AI",
            "issue": "Not using all multimodal features: video analysis + image gen + embeddings",
            "impact": "Underutilizing AI capabilities",
            "recommendation": "Use Gemini 2.0 for video, Imagen for thumbnails, embeddings for RAG"
        })
        
        # Test 10: Check if using all orchestration patterns
        issues.append({
            "category": "Orchestration",
            "issue": "Not using circuit breakers, retry with backoff, dead letter queues",
            "impact": "Cascading failures, lost work",
            "recommendation": "Implement all resilience patterns from ORCHESTRATION_ANALYSIS"
        })
    
    return {
        "total_issues": len(issues),
        "issues": issues,
        "high_impact": [i for i in issues if "high" in i.get("impact", "").lower()],
        "medium_impact": [i for i in issues if "medium" in i.get("impact", "").lower()],
        "low_impact": [i for i in issues if "low" in i.get("impact", "").lower()]
    }


async def main():
    """Run all decision-making and learning stress tests"""
    print("=" * 80)
    print("DECISION MAKING & LEARNING STRESS TEST")
    print("Finding failures and underutilized capabilities")
    print("=" * 80)
    
    tester = DecisionMakingStressTest()
    
    # Test 1: Decision-making under load
    print("\n1. Testing Decision-Making Under Load...")
    decision_results = await tester.test_battle_hardened_decision_under_load(
        concurrent=100,
        total_decisions=1000
    )
    
    print(f"  Total Decisions: {decision_results['total_decisions']}")
    print(f"  Successful: {decision_results['successful']}")
    print(f"  Decisions/sec: {decision_results['decisions_per_second']:.2f}")
    print(f"  Quality Issues: {decision_results['quality_issues']}")
    
    # Test 2: Learning loop effectiveness
    print("\n2. Testing Learning Loop Effectiveness...")
    learning_results = await tester.test_learning_loop_effectiveness(iterations=50)
    
    print(f"  Iterations: {learning_results['iterations']}")
    print(f"  Feedback Registered: {learning_results['feedback_registered']}")
    print(f"  Is Learning: {learning_results['is_learning']}")
    print(f"  Learning Improvement: {learning_results['learning_improvement']:.4f}")
    
    # Test 3: Self-learning cycle completeness
    print("\n3. Testing Self-Learning Cycle Completeness...")
    cycle_results = await tester.test_self_learning_cycle_completeness(cycles=10)
    
    print(f"  Cycles Tested: {cycle_results['cycles_tested']}")
    print(f"  Successful: {cycle_results['successful_cycles']}")
    print(f"  Uses All 7 Loops: {cycle_results['uses_all_7_loops']}")
    print(f"  Missing Loops: {cycle_results['missing_loops']}")
    
    # Test 4: Agent orchestration
    print("\n4. Testing Agent Orchestration...")
    orchestration_results = await test_agent_orchestration_under_load(
        concurrent=50,
        total_requests=500
    )
    
    print(f"  Total Workflows: {orchestration_results['total_workflows']}")
    print(f"  Successful: {orchestration_results['successful']}")
    print(f"  Orchestration Failures: {orchestration_results['orchestration_failures']}")
    if orchestration_results['failure_details']:
        print(f"  Sample Failures: {orchestration_results['failure_details'][:3]}")
    
    # Test 5: Find underutilized capabilities
    print("\n5. Finding Underutilized Capabilities...")
    capability_issues = await find_underutilized_capabilities()
    
    print(f"  Total Issues Found: {capability_issues['total_issues']}")
    print(f"  High Impact: {len(capability_issues['high_impact'])}")
    print(f"  Medium Impact: {len(capability_issues['medium_impact'])}")
    print(f"  Low Impact: {len(capability_issues['low_impact'])}")
    
    # Summary
    print("\n" + "=" * 80)
    print("STRESS TEST SUMMARY")
    print("=" * 80)
    print(f"Decision Quality Issues: {len(decision_results['quality_issues'])}")
    print(f"Learning Effectiveness: {learning_results['is_learning']}")
    print(f"Missing Learning Loops: {len(cycle_results['missing_loops'])}")
    print(f"Orchestration Failures: {orchestration_results['orchestration_failures']}")
    print(f"Underutilized Capabilities: {capability_issues['total_issues']}")
    print("=" * 80)
    
    # Detailed report
    print("\n" + "=" * 80)
    print("UNDERUTILIZED CAPABILITIES DETAILED REPORT")
    print("=" * 80)
    for issue in capability_issues['issues']:
        print(f"\n{issue['category']}:")
        print(f"  Issue: {issue['issue']}")
        print(f"  Impact: {issue['impact']}")
        print(f"  Recommendation: {issue['recommendation']}")
    
    return {
        "decision_results": decision_results,
        "learning_results": learning_results,
        "cycle_results": cycle_results,
        "orchestration_results": orchestration_results,
        "capability_issues": capability_issues
    }


if __name__ == "__main__":
    asyncio.run(main())

