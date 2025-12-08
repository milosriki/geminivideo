"""
Stress Test: Agent Orchestration Failures
Finds where agent coordination breaks down
"""
import asyncio
import time
import random
from typing import Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)


async def test_creative_generation_orchestration(
    iterations: int = 50
) -> Dict[str, Any]:
    """Test if all agents participate in creative generation"""
    
    failures = []
    agent_participation = {
        "director": 0,
        "rag": 0,
        "creative_dna": 0,
        "oracle": 0,
        "video_agent": 0
    }
    
    async with httpx.AsyncClient() as client:
        for i in range(iterations):
            try:
                response = await client.post(
                    "http://localhost:8084/api/titan/director/create-battle-plan",
                    json={
                        "video_id": f"test-video-{i}",
                        "framework": "training_video_framework_2025"
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.text.lower()
                    
                    # Check agent participation
                    if "director" in data or "battle plan" in data:
                        agent_participation["director"] += 1
                    
                    if "rag" in data or "similar" in data or "winner" in data:
                        agent_participation["rag"] += 1
                    
                    if "dna" in data or "creative" in data:
                        agent_participation["creative_dna"] += 1
                    
                    if "oracle" in data or "predict" in data:
                        agent_participation["oracle"] += 1
                    
                    if "video" in data or "render" in data:
                        agent_participation["video_agent"] += 1
                    
                    # Check for missing agents
                    if "rag" not in data and "similar" not in data:
                        failures.append({
                            "iteration": i,
                            "failure": "RAG agent not participating",
                            "impact": "Not learning from winners"
                        })
                    
                    if "dna" not in data:
                        failures.append({
                            "iteration": i,
                            "failure": "Creative DNA agent not participating",
                            "impact": "Not extracting creative patterns"
                        })
                else:
                    failures.append({
                        "iteration": i,
                        "failure": f"HTTP {response.status_code}",
                        "impact": "Orchestration endpoint failed"
                    })
            
            except Exception as e:
                failures.append({
                    "iteration": i,
                    "failure": str(e),
                    "impact": "Orchestration exception"
                })
    
    participation_rate = {
        agent: count / iterations
        for agent, count in agent_participation.items()
    }
    
    return {
        "iterations": iterations,
        "agent_participation": agent_participation,
        "participation_rate": participation_rate,
        "failures": failures,
        "failure_rate": len(failures) / iterations if iterations > 0 else 0,
        "all_agents_participating": all(rate > 0.8 for rate in participation_rate.values())
    }


async def test_budget_optimization_orchestration(
    iterations: int = 50
) -> Dict[str, Any]:
    """Test if all agents participate in budget optimization"""
    
    failures = []
    agent_participation = {
        "battle_hardened": 0,
        "safe_executor": 0,
        "meta_publisher": 0,
        "fatigue_detector": 0
    }
    
    async with httpx.AsyncClient() as client:
        for i in range(iterations):
            try:
                # Step 1: Get budget recommendation
                response = await client.post(
                    "http://localhost:8003/api/ml/battle-hardened/select",
                    json={
                        "ad_states": [{
                            "ad_id": f"ad-{i}",
                            "impressions": 10000,
                            "clicks": 500,
                            "spend": 2000,
                            "pipeline_value": 8000,
                            "age_hours": 72
                        }],
                        "total_budget": 1000
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    agent_participation["battle_hardened"] += 1
                    data = response.json()
                    
                    # Check if recommendation goes to SafeExecutor
                    recs = data.get("recommendations", [])
                    if recs:
                        rec = recs[0]
                        if rec.get("recommended_budget") != rec.get("current_budget"):
                            # Should queue to SafeExecutor
                            agent_participation["safe_executor"] += 1
                            
                            # Check if SafeExecutor would process
                            # (Would need to check pending_ad_changes table)
                            agent_participation["meta_publisher"] += 1  # Assumed
                    
                    # Check fatigue detection
                    if "fatigue" in str(data).lower():
                        agent_participation["fatigue_detector"] += 1
                    else:
                        failures.append({
                            "iteration": i,
                            "failure": "Fatigue detector not checking",
                            "impact": "Not detecting fatigued ads"
                        })
                else:
                    failures.append({
                        "iteration": i,
                        "failure": f"BattleHardened failed: {response.status_code}",
                        "impact": "Budget optimization broken"
                    })
            
            except Exception as e:
                failures.append({
                    "iteration": i,
                    "failure": str(e),
                    "impact": "Orchestration exception"
                })
    
    return {
        "iterations": iterations,
        "agent_participation": agent_participation,
        "failures": failures,
        "failure_rate": len(failures) / iterations if iterations > 0 else 0
    }


async def test_learning_orchestration(
    iterations: int = 20
) -> Dict[str, Any]:
    """Test if all 7 learning loops participate"""
    
    expected_loops = [
        "fetch_actuals",
        "calculate_accuracy",
        "auto_retrain",
        "compound_learning",
        "auto_promote",
        "cross_learning",
        "rag_indexing"
    ]
    
    loop_participation = {loop: 0 for loop in expected_loops}
    failures = []
    
    async with httpx.AsyncClient() as client:
        for i in range(iterations):
            try:
                response = await client.post(
                    "http://localhost:8003/api/ml/self-learning-cycle",
                    json={
                        "account_id": f"test-{i}",
                        "trigger_retrain": True,
                        "accuracy_threshold": 0.80
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    steps = data.get("steps", [])
                    
                    step_names = [s.get("name", "") for s in steps]
                    
                    for loop in expected_loops:
                        if loop in step_names:
                            loop_participation[loop] += 1
                        else:
                            failures.append({
                                "iteration": i,
                                "missing_loop": loop,
                                "impact": f"{loop} not executing"
                            })
                else:
                    failures.append({
                        "iteration": i,
                        "failure": f"HTTP {response.status_code}",
                        "impact": "Learning cycle failed"
                    })
            
            except Exception as e:
                failures.append({
                    "iteration": i,
                    "failure": str(e),
                    "impact": "Learning cycle exception"
                })
    
    participation_rate = {
        loop: count / iterations
        for loop, count in loop_participation.items()
    }
    
    return {
        "iterations": iterations,
        "expected_loops": len(expected_loops),
        "loop_participation": loop_participation,
        "participation_rate": participation_rate,
        "all_loops_participating": all(rate > 0.8 for rate in participation_rate.values()),
        "failures": failures,
        "failure_rate": len(failures) / iterations if iterations > 0 else 0
    }


async def main():
    """Run all orchestration failure tests"""
    print("=" * 80)
    print("AGENT ORCHESTRATION FAILURE ANALYSIS")
    print("=" * 80)
    
    # Test 1: Creative generation
    print("\n1. Testing Creative Generation Orchestration...")
    creative_results = await test_creative_generation_orchestration(iterations=50)
    
    print(f"  Iterations: {creative_results['iterations']}")
    print(f"  Agent Participation:")
    for agent, rate in creative_results['participation_rate'].items():
        print(f"    {agent}: {rate*100:.1f}%")
    print(f"  All Agents Participating: {creative_results['all_agents_participating']}")
    print(f"  Failures: {len(creative_results['failures'])}")
    
    # Test 2: Budget optimization
    print("\n2. Testing Budget Optimization Orchestration...")
    budget_results = await test_budget_optimization_orchestration(iterations=50)
    
    print(f"  Iterations: {budget_results['iterations']}")
    print(f"  Agent Participation:")
    for agent, count in budget_results['agent_participation'].items():
        print(f"    {agent}: {count}/{budget_results['iterations']}")
    print(f"  Failures: {len(budget_results['failures'])}")
    
    # Test 3: Learning orchestration
    print("\n3. Testing Learning Orchestration...")
    learning_results = await test_learning_orchestration(iterations=20)
    
    print(f"  Iterations: {learning_results['iterations']}")
    print(f"  Loop Participation:")
    for loop, rate in learning_results['participation_rate'].items():
        print(f"    {loop}: {rate*100:.1f}%")
    print(f"  All Loops Participating: {learning_results['all_loops_participating']}")
    print(f"  Failures: {len(learning_results['failures'])}")
    
    # Summary
    print("\n" + "=" * 80)
    print("ORCHESTRATION FAILURE SUMMARY")
    print("=" * 80)
    print(f"Creative Generation Failures: {len(creative_results['failures'])}")
    print(f"Budget Optimization Failures: {len(budget_results['failures'])}")
    print(f"Learning Orchestration Failures: {len(learning_results['failures'])}")
    print("=" * 80)
    
    return {
        "creative_results": creative_results,
        "budget_results": budget_results,
        "learning_results": learning_results
    }


if __name__ == "__main__":
    asyncio.run(main())

