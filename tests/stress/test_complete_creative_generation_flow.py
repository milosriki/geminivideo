"""
Stress Test: Complete Creative Generation Flow
Tests the full orchestration from video upload to Meta publishing
Covers: Drive Intel → ML Service → AI Council → Video Agent → Meta Publisher → SafeExecutor
"""
import asyncio
import time
import random
import numpy as np
from typing import List, Dict, Any, Optional
import httpx
import logging
import uuid

logger = logging.getLogger(__name__)

# Service URLs
GATEWAY_URL = "http://localhost:8000"
DRIVE_INTEL_URL = "http://localhost:8001"
VIDEO_AGENT_URL = "http://localhost:8002"
META_PUBLISHER_URL = "http://localhost:8003"
ML_SERVICE_URL = "http://localhost:8004"
TITAN_CORE_URL = "http://localhost:8005"


class CreativeGenerationFlowTester:
    """Test complete creative generation orchestration"""
    
    def __init__(self):
        self.results = []
        self.video_ids = []
        self.campaign_ids = []
        self.blueprint_ids = []
        self.render_job_ids = []
        self.ad_ids = []
    
    async def test_step_1_video_upload(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Step 1: Upload video to Drive Intel"""
        start_time = time.time()
        
        try:
            # Simulate video upload
            video_data = {
                "video_path": f"/test/videos/test_video_{uuid.uuid4()}.mp4",
                "folder_path": "/test/videos",
                "metadata": {
                    "title": f"Test Video {uuid.uuid4()}",
                    "duration": random.uniform(15, 60),
                    "resolution": random.choice(["1080p", "720p", "4K"])
                }
            }
            
            response = await client.post(
                f"{GATEWAY_URL}/api/ingest/local/folder",
                json={"folder_path": video_data["folder_path"]},
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                asset_id = response.json().get("asset_id") or str(uuid.uuid4())
                self.video_ids.append(asset_id)
                
                return {
                    "step": "video_upload",
                    "success": True,
                    "asset_id": asset_id,
                    "duration_ms": duration,
                    "status_code": response.status_code
                }
            else:
                return {
                    "step": "video_upload",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "step": "video_upload",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_step_2_scene_extraction(self, client: httpx.AsyncClient, asset_id: str) -> Dict[str, Any]:
        """Step 2: Drive Intel scene extraction"""
        start_time = time.time()
        
        try:
            # Wait for scene extraction
            max_wait = 60
            wait_interval = 2
            elapsed = 0
            
            while elapsed < max_wait:
                response = await client.get(
                    f"{GATEWAY_URL}/api/assets/{asset_id}/clips",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    clips = response.json().get("clips", [])
                    if len(clips) > 0:
                        duration = (time.time() - start_time) * 1000
                        return {
                            "step": "scene_extraction",
                            "success": True,
                            "clips_count": len(clips),
                            "duration_ms": duration
                        }
                
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval
            
            return {
                "step": "scene_extraction",
                "success": False,
                "error": "Timeout waiting for scene extraction",
                "duration_ms": (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            return {
                "step": "scene_extraction",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_step_3_ctr_prediction(self, client: httpx.AsyncClient, asset_id: str) -> Dict[str, Any]:
        """Step 3: ML Service CTR prediction"""
        start_time = time.time()
        
        try:
            # Get clips first
            clips_response = await client.get(
                f"{GATEWAY_URL}/api/assets/{asset_id}/clips?ranked=true&top=10",
                timeout=10.0
            )
            
            if clips_response.status_code != 200:
                return {
                    "step": "ctr_prediction",
                    "success": False,
                    "error": "Failed to get clips",
                    "duration_ms": (time.time() - start_time) * 1000
                }
            
            clips = clips_response.json().get("clips", [])[:5]  # Top 5
            
            # Score storyboard
            storyboard = {
                "scenes": [
                    {
                        "clip_id": clip.get("id"),
                        "features": clip.get("features", {}),
                        "duration": clip.get("duration", 3.0)
                    }
                    for clip in clips
                ],
                "metadata": {
                    "platform": "instagram",
                    "target_audience": "fitness_enthusiasts"
                }
            }
            
            response = await client.post(
                f"{GATEWAY_URL}/api/score/storyboard",
                json=storyboard,
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                scores = response.json()
                return {
                    "step": "ctr_prediction",
                    "success": True,
                    "predictions_count": len(clips),
                    "avg_ctr": scores.get("composite_score", 0),
                    "duration_ms": duration
                }
            else:
                return {
                    "step": "ctr_prediction",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "step": "ctr_prediction",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_step_4_ai_council(self, client: httpx.AsyncClient, asset_id: str) -> Dict[str, Any]:
        """Step 4: AI Council evaluation"""
        start_time = time.time()
        
        try:
            # Create campaign for AI Council
            campaign_data = {
                "product_name": f"Test Product {uuid.uuid4()}",
                "offer": "50% Off Limited Time",
                "target_avatar": "fitness_enthusiast",
                "pain_points": ["lack of motivation", "time constraints"],
                "desires": ["quick results", "expert guidance"]
            }
            
            campaign_response = await client.post(
                f"{GATEWAY_URL}/api/campaigns",
                json=campaign_data,
                timeout=10.0
            )
            
            if campaign_response.status_code != 200:
                return {
                    "step": "ai_council",
                    "success": False,
                    "error": "Failed to create campaign",
                    "duration_ms": (time.time() - start_time) * 1000
                }
            
            campaign_id = campaign_response.json().get("id")
            self.campaign_ids.append(campaign_id)
            
            # Get AI Council evaluation
            council_data = {
                "campaign_id": campaign_id,
                "asset_id": asset_id,
                "variations_count": 5
            }
            
            response = await client.post(
                f"{TITAN_CORE_URL}/council/evaluate",
                json=council_data,
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                blueprints = result.get("blueprints", [])
                approved = [b for b in blueprints if b.get("verdict") == "APPROVED"]
                
                for blueprint in approved:
                    self.blueprint_ids.append(blueprint.get("id"))
                
                return {
                    "step": "ai_council",
                    "success": True,
                    "total_variations": len(blueprints),
                    "approved_count": len(approved),
                    "approval_rate": len(approved) / len(blueprints) if blueprints else 0,
                    "duration_ms": duration
                }
            else:
                return {
                    "step": "ai_council",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "step": "ai_council",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_step_5_video_rendering(self, client: httpx.AsyncClient, blueprint_id: str) -> Dict[str, Any]:
        """Step 5: Video Agent rendering"""
        start_time = time.time()
        
        try:
            render_data = {
                "blueprint_id": blueprint_id,
                "platform": "instagram",
                "quality": "high",
                "variations": ["reels", "story"]
            }
            
            response = await client.post(
                f"{VIDEO_AGENT_URL}/api/render/remix",
                json=render_data,
                timeout=120.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                job_id = response.json().get("job_id")
                if job_id:
                    self.render_job_ids.append(job_id)
                
                return {
                    "step": "video_rendering",
                    "success": True,
                    "job_id": job_id,
                    "duration_ms": duration
                }
            else:
                return {
                    "step": "video_rendering",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "step": "video_rendering",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_step_6_meta_queue(self, client: httpx.AsyncClient, render_job_id: str) -> Dict[str, Any]:
        """Step 6: Meta Publisher queue"""
        start_time = time.time()
        
        try:
            # Check if job is queued to Meta
            response = await client.get(
                f"{GATEWAY_URL}/api/render/jobs/{render_job_id}",
                timeout=10.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                job = response.json()
                status = job.get("status", "unknown")
                
                # Check pending_ad_changes table
                pending_response = await client.get(
                    f"{GATEWAY_URL}/api/pending-ad-changes",
                    params={"render_job_id": render_job_id},
                    timeout=10.0
                )
                
                pending_count = 0
                if pending_response.status_code == 200:
                    pending_count = len(pending_response.json().get("changes", []))
                
                return {
                    "step": "meta_queue",
                    "success": True,
                    "job_status": status,
                    "pending_changes": pending_count,
                    "duration_ms": duration
                }
            else:
                return {
                    "step": "meta_queue",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "step": "meta_queue",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_complete_flow(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test complete creative generation flow"""
        flow_start = time.time()
        steps = []
        
        # Step 1: Video Upload
        step1 = await self.test_step_1_video_upload(client)
        steps.append(step1)
        if not step1["success"]:
            return {"success": False, "steps": steps, "failed_at": "step_1"}
        
        asset_id = step1["asset_id"]
        await asyncio.sleep(2)  # Brief pause between steps
        
        # Step 2: Scene Extraction
        step2 = await self.test_step_2_scene_extraction(client, asset_id)
        steps.append(step2)
        if not step2["success"]:
            return {"success": False, "steps": steps, "failed_at": "step_2"}
        
        await asyncio.sleep(1)
        
        # Step 3: CTR Prediction
        step3 = await self.test_step_3_ctr_prediction(client, asset_id)
        steps.append(step3)
        if not step3["success"]:
            return {"success": False, "steps": steps, "failed_at": "step_3"}
        
        await asyncio.sleep(1)
        
        # Step 4: AI Council
        step4 = await self.test_step_4_ai_council(client, asset_id)
        steps.append(step4)
        if not step4["success"]:
            return {"success": False, "steps": steps, "failed_at": "step_4"}
        
        if not self.blueprint_ids:
            return {"success": False, "steps": steps, "failed_at": "step_4_no_approvals"}
        
        await asyncio.sleep(1)
        
        # Step 5: Video Rendering (test first approved blueprint)
        step5 = await self.test_step_5_video_rendering(client, self.blueprint_ids[0])
        steps.append(step5)
        if not step5["success"]:
            return {"success": False, "steps": steps, "failed_at": "step_5"}
        
        render_job_id = step5.get("job_id")
        if render_job_id:
            await asyncio.sleep(2)
            
            # Step 6: Meta Queue
            step6 = await self.test_step_6_meta_queue(client, render_job_id)
            steps.append(step6)
        
        total_duration = (time.time() - flow_start) * 1000
        
        successful_steps = sum(1 for s in steps if s.get("success"))
        
        return {
            "success": successful_steps == len(steps),
            "steps": steps,
            "total_steps": len(steps),
            "successful_steps": successful_steps,
            "total_duration_ms": total_duration,
            "asset_id": asset_id,
            "campaign_ids": self.campaign_ids,
            "blueprint_ids": self.blueprint_ids,
            "render_job_ids": self.render_job_ids
        }


async def stress_test_complete_creative_generation_flow(
    concurrent: int = 10,
    total_flows: int = 50
) -> Dict[str, Any]:
    """Run stress test for complete creative generation flow"""
    
    logger.info(f"Starting complete creative generation flow stress test: {concurrent} concurrent, {total_flows} total")
    
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Process in batches
        batch_size = concurrent
        for i in range(0, total_flows, batch_size):
            batch_count = min(batch_size, total_flows - i)
            
            async def run_flow():
                tester = CreativeGenerationFlowTester()
                return await tester.test_complete_flow(client)
            
            batch_results = await asyncio.gather(
                *[run_flow() for _ in range(batch_count)],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result),
                        "steps": []
                    })
                else:
                    results.append(result)
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_flows + batch_size - 1) // batch_size}")
    
    total_duration = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    # Step-level analysis
    step_stats = {}
    for result in results:
        for step in result.get("steps", []):
            step_name = step.get("step", "unknown")
            if step_name not in step_stats:
                step_stats[step_name] = {"total": 0, "successful": 0, "durations": []}
            
            step_stats[step_name]["total"] += 1
            if step.get("success"):
                step_stats[step_name]["successful"] += 1
                if "duration_ms" in step:
                    step_stats[step_name]["durations"].append(step["duration_ms"])
    
    # Calculate step success rates and durations
    step_analysis = {}
    for step_name, stats in step_stats.items():
        step_analysis[step_name] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0
        }
    
    return {
        "total_flows": total_flows,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_flows if total_flows > 0 else 0,
        "total_duration_seconds": total_duration,
        "flows_per_second": total_flows / total_duration if total_duration > 0 else 0,
        "step_analysis": step_analysis,
        "avg_flow_duration_ms": np.mean([r.get("total_duration_ms", 0) for r in successful]) if successful else 0,
        "p95_flow_duration_ms": np.percentile([r.get("total_duration_ms", 0) for r in successful], 95) if successful else 0,
        "failure_points": {
            step: sum(1 for r in failed if r.get("failed_at") == step)
            for step in ["step_1", "step_2", "step_3", "step_4", "step_5", "step_6"]
        }
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_complete_creative_generation_flow(concurrent=5, total_flows=20))

