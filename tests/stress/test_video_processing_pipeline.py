"""
Stress Test: Video Processing Pipeline
Tests complete video processing from ingestion to rendering
Covers: Drive Intel → Scene Detection → Feature Extraction → Video Agent → Pro Modules
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

GATEWAY_URL = "http://localhost:8000"
VIDEO_AGENT_URL = "http://localhost:8002"
DRIVE_INTEL_URL = "http://localhost:8001"


class VideoProcessingPipelineTester:
    """Test video processing pipeline"""
    
    async def test_video_ingestion(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test video ingestion"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{GATEWAY_URL}/api/ingest/local/folder",
                json={"folder_path": f"/test/videos/batch_{uuid.uuid4()}"},
                timeout=60.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "step": "ingestion",
                "success": response.status_code in [200, 202],
                "asset_id": response.json().get("asset_id") if response.status_code in [200, 202] else None,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "step": "ingestion",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_scene_detection(self, client: httpx.AsyncClient, asset_id: str) -> Dict[str, Any]:
        """Test scene detection"""
        start_time = time.time()
        
        try:
            # Wait for scene detection
            max_wait = 120
            wait_interval = 3
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
                            "step": "scene_detection",
                            "success": True,
                            "clips_count": len(clips),
                            "duration_ms": duration
                        }
                
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval
            
            return {
                "step": "scene_detection",
                "success": False,
                "error": "Timeout",
                "duration_ms": (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            return {
                "step": "scene_detection",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_feature_extraction(self, client: httpx.AsyncClient, asset_id: str) -> Dict[str, Any]:
        """Test feature extraction (YOLO, OCR, Whisper)"""
        start_time = time.time()
        
        try:
            response = await client.get(
                f"{GATEWAY_URL}/api/assets/{asset_id}/clips?features=true",
                timeout=30.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                clips = response.json().get("clips", [])
                features_count = sum(1 for clip in clips if clip.get("features"))
                
                return {
                    "step": "feature_extraction",
                    "success": True,
                    "clips_with_features": features_count,
                    "total_clips": len(clips),
                    "duration_ms": duration
                }
            else:
                return {
                    "step": "feature_extraction",
                    "success": False,
                    "error": f"Status {response.status_code}",
                    "duration_ms": duration
                }
        
        except Exception as e:
            return {
                "step": "feature_extraction",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_pro_caption_generation(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Pro module: Auto Captions"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{VIDEO_AGENT_URL}/api/pro/caption",
                json={
                    "video_path": "/test/video.mp4",
                    "style": random.choice(["instagram", "youtube", "tiktok"]),
                    "language": "en",
                    "word_level": True
                },
                timeout=120.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "step": "pro_captions",
                "success": response.status_code in [200, 202],
                "status_code": response.status_code,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "step": "pro_captions",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_pro_color_grading(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Pro module: Color Grading"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{VIDEO_AGENT_URL}/api/pro/color-grade",
                json={
                    "video_path": "/test/video.mp4",
                    "preset": random.choice(["cinematic", "vintage", "high_contrast", "fitness_energy"]),
                    "intensity": 1.0
                },
                timeout=120.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "step": "pro_color_grading",
                "success": response.status_code in [200, 202],
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "step": "pro_color_grading",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_pro_smart_crop(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Pro module: Smart Crop"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{VIDEO_AGENT_URL}/api/pro/smart-crop",
                json={
                    "video_path": "/test/video.mp4",
                    "target_aspect": random.choice(["9:16", "1:1", "4:5", "16:9"]),
                    "track_faces": True,
                    "smooth_motion": True
                },
                timeout=120.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "step": "pro_smart_crop",
                "success": response.status_code in [200, 202],
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "step": "pro_smart_crop",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_pro_audio_mixing(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Pro module: Audio Mixer"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{VIDEO_AGENT_URL}/api/pro/audio-mix",
                json={
                    "video_path": "/test/video.mp4",
                    "music_path": "/test/music.mp3",
                    "auto_duck": True,
                    "normalization": "social_media",
                    "voice_enhance": True
                },
                timeout=120.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "step": "pro_audio_mixing",
                "success": response.status_code in [200, 202],
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "step": "pro_audio_mixing",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_pro_winning_ad_generation(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test Pro module: Winning Ad Generator"""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{VIDEO_AGENT_URL}/api/pro/render-winning-ad",
                json={
                    "video_clips": ["/test/clip1.mp4", "/test/clip2.mp4"],
                    "template": random.choice(["fitness_transformation", "testimonial", "problem_solution"]),
                    "platform": "instagram",
                    "hook_text": "Transform Your Life",
                    "cta_text": "Start Now",
                    "duration_target": 30
                },
                timeout=300.0
            )
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "step": "pro_winning_ad",
                "success": response.status_code in [200, 202],
                "job_id": response.json().get("job_id") if response.status_code in [200, 202] else None,
                "duration_ms": duration
            }
        
        except Exception as e:
            return {
                "step": "pro_winning_ad",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }


async def stress_test_video_processing_pipeline(
    concurrent: int = 10,
    total_pipelines: int = 50
) -> Dict[str, Any]:
    """Run stress test for video processing pipeline"""
    
    logger.info(f"Starting video processing pipeline stress test: {concurrent} concurrent, {total_pipelines} total")
    
    tester = VideoProcessingPipelineTester()
    results = []
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        # Process in batches
        batch_size = concurrent
        for i in range(0, total_pipelines, batch_size):
            batch_count = min(batch_size, total_pipelines - i)
            
            async def run_pipeline():
                pipeline_steps = []
                
                # Step 1: Ingestion
                step1 = await tester.test_video_ingestion(client)
                pipeline_steps.append(step1)
                if not step1["success"]:
                    return {"success": False, "steps": pipeline_steps}
                
                asset_id = step1.get("asset_id")
                if not asset_id:
                    return {"success": False, "steps": pipeline_steps}
                
                await asyncio.sleep(2)
                
                # Step 2: Scene Detection
                step2 = await tester.test_scene_detection(client, asset_id)
                pipeline_steps.append(step2)
                
                await asyncio.sleep(1)
                
                # Step 3: Feature Extraction
                step3 = await tester.test_feature_extraction(client, asset_id)
                pipeline_steps.append(step3)
                
                # Test Pro modules (can run in parallel)
                pro_tests = [
                    tester.test_pro_caption_generation(client),
                    tester.test_pro_color_grading(client),
                    tester.test_pro_smart_crop(client),
                    tester.test_pro_audio_mixing(client)
                ]
                
                pro_results = await asyncio.gather(*pro_tests, return_exceptions=True)
                pipeline_steps.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in pro_results])
                
                successful_steps = sum(1 for s in pipeline_steps if s.get("success"))
                
                return {
                    "success": successful_steps >= 3,  # At least 3 steps must succeed
                    "steps": pipeline_steps,
                    "total_steps": len(pipeline_steps),
                    "successful_steps": successful_steps
                }
            
            batch_results = await asyncio.gather(
                *[run_pipeline() for _ in range(batch_count)],
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
            
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_pipelines + batch_size - 1) // batch_size}")
    
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
    
    step_analysis = {}
    for step_name, stats in step_stats.items():
        step_analysis[step_name] = {
            "success_rate": stats["successful"] / stats["total"] if stats["total"] > 0 else 0,
            "avg_duration_ms": np.mean(stats["durations"]) if stats["durations"] else 0,
            "p95_duration_ms": np.percentile(stats["durations"], 95) if stats["durations"] else 0
        }
    
    return {
        "total_pipelines": total_pipelines,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / total_pipelines if total_pipelines > 0 else 0,
        "total_duration_seconds": total_duration,
        "pipelines_per_second": total_pipelines / total_duration if total_duration > 0 else 0,
        "step_analysis": step_analysis
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(stress_test_video_processing_pipeline(concurrent=5, total_pipelines=20))

