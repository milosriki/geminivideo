"""
Stress Test: AI Council Orchestration
Tests AI Council components working together
Covers: Director Agent → Oracle Agent → Council of Titans → Veo Director → Ultimate Pipeline
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

TITAN_CORE_URL = "http://localhost:8005"
GATEWAY_URL = "http://localhost:8000"


class AICouncilOrchestrationTester:
    """Test AI Council orchestration"""
    
    async def test_director_agent(self, client: httpx.AsyncClient, campaign_id: str) -> Dict[str, Any]:
        """Test Director Agent: Battle Plan Generation"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{TITAN_CORE_URL}/director/generate",
                json={
                    "campaign_id": campaign_id,
                    "asset_id": str(uuid.uuid4()),
                    "target_variations": 5
                },
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "component": "director_agent",
                    "success": True,
                    "battle_plan": result.get("battle_plan"),
                    "variations_count": result.get("variations_count", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "component": "director_agent",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "component": "director_agent",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_oracle_agent(self, client: httpx.AsyncClient, blueprint_id: str) -> Dict[str, Any]:
        """Test Oracle Agent: Performance Prediction"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{TITAN_CORE_URL}/oracle/predict",
                json={
                    "blueprint_id": blueprint_id,
                    "creative_dna": {
                        "hook_type": "testimonial",
                        "visual_style": "ugc",
                        "emotion": "desire"
                    }
                },
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "component": "oracle_agent",
                    "success": True,
                    "predicted_roas": result.get("predicted_roas", 0),
                    "confidence": result.get("confidence", 0),
                    "verdict": result.get("verdict", "UNKNOWN"),
                    "duration_ms": duration
                }
            else:
                return {
                    "component": "oracle_agent",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "component": "oracle_agent",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_council_of_titans(self, client: httpx.AsyncClient, blueprints: List[Dict]) -> Dict[str, Any]:
        """Test Council of Titans: Quality Evaluation"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{TITAN_CORE_URL}/council/evaluate",
                json={
                    "blueprints": blueprints,
                    "approval_threshold": 0.85
                },
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                evaluations = result.get("evaluations", [])
                approved = [e for e in evaluations if e.get("verdict") == "APPROVED"]
                
                return {
                    "component": "council_of_titans",
                    "success": True,
                    "total_evaluated": len(evaluations),
                    "approved_count": len(approved),
                    "approval_rate": len(approved) / len(evaluations) if evaluations else 0,
                    "avg_council_score": np.mean([e.get("council_score", 0) for e in evaluations]) if evaluations else 0,
                    "duration_ms": duration
                }
            else:
                return {
                    "component": "council_of_titans",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "component": "council_of_titans",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_veo_director(self, client: httpx.AsyncClient, blueprint_id: str) -> Dict[str, Any]:
        """Test Veo Director: Video Generation"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{TITAN_CORE_URL}/veo/generate",
                json={
                    "blueprint_id": blueprint_id,
                    "style": random.choice(["cinematic", "social", "ugc"]),
                    "duration_seconds": 30
                },
                timeout=300.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 202]:
                result = response.json()
                return {
                    "component": "veo_director",
                    "success": True,
                    "video_id": result.get("video_id"),
                    "status": result.get("status", "processing"),
                    "duration_ms": duration
                }
            else:
                return {
                    "component": "veo_director",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "component": "veo_director",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_ultimate_pipeline(self, client: httpx.AsyncClient, campaign_id: str) -> Dict[str, Any]:
        """Test Ultimate Pipeline: Complete Processing"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{TITAN_CORE_URL}/pipeline/process",
                json={
                    "campaign_id": campaign_id,
                    "asset_id": str(uuid.uuid4()),
                    "variations_count": 5,
                    "platform": "instagram"
                },
                timeout=600.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 202]:
                result = response.json()
                return {
                    "component": "ultimate_pipeline",
                    "success": True,
                    "pipeline_id": result.get("pipeline_id"),
                    "blueprints_created": result.get("blueprints_created", 0),
                    "approved_count": result.get("approved_count", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "component": "ultimate_pipeline",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "component": "ultimate_pipeline",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_complete_orchestration(self, client: httpx.AsyncClient, campaign_id: str) -> Dict[str, Any]:
        """Test complete AI Council orchestration"""
        orchestration_start = time.time()
        components = []
        
        # Step 1: Director Agent
        step1 = await self.test_director_agent(client, campaign_id)
        components.append(step1)
        await asyncio.sleep(1)
        
        # Step 2: Generate blueprints (simulated)
        blueprint_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        # Step 3: Oracle Agent (test on first blueprint)
        if blueprint_ids:
            step3 = await self.test_oracle_agent(client, blueprint_ids[0])
            components.append(step3)
            await asyncio.sleep(1)
        
        # Step 4: Council of Titans
        blueprints = [
            {
                "id": bid,
                "hook_text": f"Hook {i}",
                "council_score": random.uniform(0.7, 0.95)
            }
            for i, bid in enumerate(blueprint_ids)
        ]
        step4 = await self.test_council_of_titans(client, blueprints)
        components.append(step4)
        await asyncio.sleep(1)
        
        # Step 5: Ultimate Pipeline
        step5 = await self.test_ultimate_pipeline(client, campaign_id)
        components.append(step5)
        
        total_duration = (time.time() - orchestration_start) * 1000
        
        successful_components = sum(1 for c in components if c.get("success"))
        
        return {
            "success": successful_components >= 3,  # At least 3 components must succeed
            "components": components,
            "total_components": len(components),
            "successful_components": successful_components,
            "total_duration_ms": total_duration,
            "campaign_id": campaign_id
        }


async def stress_test_ai_council_orchestration(
    concurrent: int = 10,
    total_orchestrations: int = 50
) -> Dict[str, Any]:
    """Run stress test for AI Council orchestration"""
    
    logger.info(f"Starting AI Council orchestration stress test: {concurrent} concurrent, {total_orchestrations} total")
    
    tester = AICouncilOrchestrationTester()
    results = []
    start_time = time.time()
    
    # Create test campaigns
    campaign_ids = [str(uuid.uuid4()) for _ in range(total_orchestrations)]
    
    async with httpx.AsyncClient(timeout=900.0) as client:
        # Process in batches
        batch_size = concurrent
        for i in range(0, total_orchestrations, batch_size):
            batch_campaign_ids = campaign_ids[i:i + batch_size]
            
            async def run_orchestration(campaign_id):
                return await tester.test_complete_orchestration(client, campaign_id)
            
            batch_results = await asyncio.gather(
                *[run_orchestration(cid) for cid in batch_campaign_ids],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result),
                        "components": []
                    })
                else:
                    results.append(result)
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_orchestrations + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Component-level analysis
    component_stats = {}
    for result in results:
        for component in result.get("components", []):
            component_name = component.get("component", "unknown")
            if component_name not in component_stats:
                component_stats[component_name] = {"total": 0, "successful": 0, "durations": []}
            
            component_stats[component_name]["total"] += 1
            if component.get("success"):
                component_stats[component_name]["successful"] += 1
                if "duration_ms" in component:
                    component_stats[component_name]["durations"].append(component["duration_ms"])
    
    component_analysis = {}
    for component_name, stats in component_stats.items():
        component_analysis[component_name] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0
        }
    
    return {
        "total_orchestrations": total_orchestrations,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_orchestrations if total_orchestrations > 0 else 0,
        "total_duration_seconds": total_duration,
        "orchestrations_per_second": total_orchestrations / total_duration if total_duration > 0 else 0,
        "component_analysis": component_analysis,
        "avg_orchestration_duration_ms": np.mean([r.get("total_duration_ms", 0) for r in successful]) if successful else 0,
        "p95_orchestration_duration_ms": np.percentile([r.get("total_duration_ms", 0) for r in successful], 95) if successful else 0
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_ai_council_orchestration(concurrent=5, total_orchestrations=20))

