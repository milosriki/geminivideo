"""
Smart Crop Integration with Pro Video Agent System

Demonstrates how to integrate smart cropping with the larger video agent ecosystem

Author: Pro Video Agent
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from smart_crop import (
    SmartCropTracker,
    AspectRatio,
    create_smart_crop_pipeline,
    FaceDetector,
    ObjectDetector
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoAdProcessor:
    """
    Integrate smart cropping into video ad production pipeline

    Coordinates smart cropping with other video processing agents
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.smart_crop_enabled = self.config.get("smart_crop_enabled", True)
        self.supported_platforms = ["tiktok", "reels", "instagram", "youtube_shorts"]

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)

        # Default configuration
        return {
            "smart_crop_enabled": True,
            "detection_settings": {
                "faces": True,
                "objects": False,
                "motion": True
            },
            "tracking_settings": {
                "smoothing_window": 15,
                "safe_zone_ratio": 0.8
            },
            "performance": {
                "sample_interval": 3,
                "max_resolution": [1920, 1080]
            },
            "platforms": {
                "tiktok": {
                    "aspect_ratio": "9:16",
                    "resolution": [1080, 1920],
                    "priority": "faces"
                },
                "reels": {
                    "aspect_ratio": "9:16",
                    "resolution": [1080, 1920],
                    "priority": "faces"
                },
                "instagram": {
                    "aspect_ratio": "1:1",
                    "resolution": [1080, 1080],
                    "priority": "faces"
                },
                "youtube_shorts": {
                    "aspect_ratio": "9:16",
                    "resolution": [1080, 1920],
                    "priority": "action"
                }
            }
        }

    def process_video_for_platform(self,
                                   input_video: str,
                                   platform: str,
                                   output_dir: str = "output") -> Dict[str, Any]:
        """
        Process video for specific platform with smart cropping

        Args:
            input_video: Input video path
            platform: Target platform (tiktok, reels, instagram, etc.)
            output_dir: Output directory

        Returns:
            Processing results dictionary
        """
        if platform not in self.supported_platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        platform_config = self.config["platforms"][platform]
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        input_path = Path(input_video)
        output_file = output_path / f"{input_path.stem}_{platform}.mp4"

        logger.info(f"Processing video for {platform}")
        logger.info(f"Input: {input_video}")
        logger.info(f"Output: {output_file}")

        # Get aspect ratio
        aspect_str = platform_config["aspect_ratio"]
        aspect_map = {
            "9:16": AspectRatio.PORTRAIT_9_16,
            "1:1": AspectRatio.SQUARE_1_1,
            "4:5": AspectRatio.PORTRAIT_4_5,
            "16:9": AspectRatio.LANDSCAPE_16_9
        }
        target_aspect = aspect_map.get(aspect_str, AspectRatio.PORTRAIT_9_16)

        # Detection settings based on platform priority
        priority = platform_config.get("priority", "faces")
        detect_faces = priority in ["faces", "all"]
        detect_objects = priority in ["objects", "all"]
        detect_motion = priority in ["action", "motion", "all"]

        # Generate smart crop pipeline
        ffmpeg_cmd = create_smart_crop_pipeline(
            video_path=input_video,
            output_path=str(output_file),
            target_aspect=target_aspect,
            output_resolution=tuple(platform_config["resolution"]),
            detect_faces=detect_faces,
            detect_objects=detect_objects,
            detect_motion=detect_motion,
            sample_interval=self.config["performance"]["sample_interval"]
        )

        return {
            "platform": platform,
            "input": input_video,
            "output": str(output_file),
            "ffmpeg_command": ffmpeg_cmd,
            "aspect_ratio": aspect_str,
            "resolution": platform_config["resolution"],
            "status": "ready"
        }

    def process_video_multi_platform(self,
                                     input_video: str,
                                     platforms: List[str],
                                     output_dir: str = "output") -> List[Dict[str, Any]]:
        """
        Process video for multiple platforms

        Args:
            input_video: Input video path
            platforms: List of target platforms
            output_dir: Output directory

        Returns:
            List of processing results
        """
        results = []

        for platform in platforms:
            try:
                result = self.process_video_for_platform(
                    input_video,
                    platform,
                    output_dir
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process for {platform}: {e}")
                results.append({
                    "platform": platform,
                    "input": input_video,
                    "status": "failed",
                    "error": str(e)
                })

        return results

    def generate_processing_manifest(self,
                                    results: List[Dict[str, Any]],
                                    output_path: str = "manifest.json"):
        """Generate processing manifest for downstream agents"""
        manifest = {
            "version": "1.0",
            "smart_crop_enabled": self.smart_crop_enabled,
            "processing_results": results,
            "config": self.config
        }

        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Generated manifest: {output_path}")
        return manifest


class SmartCropAPI:
    """
    REST API-style interface for smart crop system

    Can be integrated with web services or other agents
    """

    def __init__(self):
        self.processor = VideoAdProcessor()

    def crop_video(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process crop request

        Request format:
        {
            "video_path": "input.mp4",
            "target_platform": "tiktok",
            "options": {
                "detect_faces": true,
                "detect_motion": true,
                "smoothing": 15
            }
        }
        """
        try:
            video_path = request["video_path"]
            platform = request["target_platform"]
            options = request.get("options", {})

            result = self.processor.process_video_for_platform(
                video_path,
                platform
            )

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"Crop request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def batch_crop(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process batch crop request

        Request format:
        {
            "video_path": "input.mp4",
            "platforms": ["tiktok", "instagram", "reels"],
            "output_dir": "output"
        }
        """
        try:
            video_path = request["video_path"]
            platforms = request["platforms"]
            output_dir = request.get("output_dir", "output")

            results = self.processor.process_video_multi_platform(
                video_path,
                platforms,
                output_dir
            )

            return {
                "success": True,
                "results": results,
                "total": len(results),
                "successful": len([r for r in results if r.get("status") == "ready"])
            }

        except Exception as e:
            logger.error(f"Batch crop request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class AgentIntegration:
    """
    Integration with multi-agent video production system

    Demonstrates how smart crop agent communicates with other agents
    """

    def __init__(self):
        self.processor = VideoAdProcessor()
        self.agent_name = "SmartCropAgent"
        self.agent_version = "1.0.0"

    def handle_agent_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle request from agent coordinator

        Request format:
        {
            "task": "crop_video",
            "video_id": "video_123",
            "video_path": "/path/to/video.mp4",
            "target_platforms": ["tiktok", "instagram"],
            "priority": "high"
        }
        """
        task = request.get("task")
        video_id = request.get("video_id")

        logger.info(f"[{self.agent_name}] Handling task: {task} for {video_id}")

        if task == "crop_video":
            return self._handle_crop_task(request)
        elif task == "analyze_video":
            return self._handle_analysis_task(request)
        elif task == "get_capabilities":
            return self._handle_capabilities_request()
        else:
            return {
                "agent": self.agent_name,
                "success": False,
                "error": f"Unknown task: {task}"
            }

    def _handle_crop_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle video cropping task"""
        video_path = request["video_path"]
        platforms = request.get("target_platforms", ["tiktok"])

        results = self.processor.process_video_multi_platform(
            video_path,
            platforms,
            output_dir=request.get("output_dir", "output")
        )

        return {
            "agent": self.agent_name,
            "task": "crop_video",
            "video_id": request.get("video_id"),
            "success": True,
            "results": results,
            "next_agent": "EncodingAgent"  # Suggest next agent in pipeline
        }

    def _handle_analysis_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze video for face/object content"""
        video_path = request["video_path"]

        # Initialize detectors
        face_detector = FaceDetector()
        face_detector.load_model()

        object_detector = ObjectDetector()
        has_yolo = object_detector.load_model()

        import cv2
        cap = cv2.VideoCapture(video_path)

        # Sample frames
        face_count = 0
        object_count = 0
        frames_analyzed = 0
        sample_frames = 30

        while frames_analyzed < sample_frames:
            ret, frame = cap.read()
            if not ret:
                break

            faces = face_detector.detect(frame)
            face_count += len(faces)

            if has_yolo:
                objects = object_detector.detect(frame)
                object_count += len(objects)

            frames_analyzed += 1

        cap.release()

        return {
            "agent": self.agent_name,
            "task": "analyze_video",
            "video_id": request.get("video_id"),
            "success": True,
            "analysis": {
                "frames_analyzed": frames_analyzed,
                "faces_detected": face_count,
                "objects_detected": object_count,
                "avg_faces_per_frame": face_count / max(frames_analyzed, 1),
                "avg_objects_per_frame": object_count / max(frames_analyzed, 1),
                "has_faces": face_count > 0,
                "has_objects": object_count > 0,
                "recommended_tracking": "faces" if face_count > object_count else "objects"
            }
        }

    def _handle_capabilities_request(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "agent": self.agent_name,
            "version": self.agent_version,
            "success": True,
            "capabilities": {
                "tasks": [
                    "crop_video",
                    "analyze_video",
                    "batch_crop",
                    "generate_manifest"
                ],
                "features": [
                    "face_detection",
                    "object_detection",
                    "motion_tracking",
                    "smooth_panning",
                    "ken_burns_effect",
                    "multi_platform_export"
                ],
                "supported_platforms": [
                    "tiktok",
                    "instagram",
                    "reels",
                    "youtube_shorts"
                ],
                "aspect_ratios": [
                    "9:16",
                    "1:1",
                    "4:5",
                    "16:9"
                ]
            }
        }


def example_integration_workflow():
    """
    Example: Complete workflow with agent integration

    Demonstrates how smart crop agent fits into larger pipeline
    """
    logger.info("\n" + "="*60)
    logger.info("Smart Crop Agent Integration Example")
    logger.info("="*60)

    # Initialize agent
    agent = AgentIntegration()

    # Step 1: Get agent capabilities
    logger.info("\n[Step 1] Query agent capabilities")
    capabilities = agent.handle_agent_request({
        "task": "get_capabilities"
    })
    logger.info(f"Agent: {capabilities['agent']}")
    logger.info(f"Version: {capabilities['version']}")
    logger.info(f"Tasks: {capabilities['capabilities']['tasks']}")

    # Step 2: Analyze video content
    logger.info("\n[Step 2] Analyze video content")
    analysis_request = {
        "task": "analyze_video",
        "video_id": "test_video_001",
        "video_path": "test_input.mp4"
    }
    # analysis_result = agent.handle_agent_request(analysis_request)
    # logger.info(f"Analysis: {analysis_result.get('analysis', {})}")

    # Step 3: Process video for multiple platforms
    logger.info("\n[Step 3] Process video for multiple platforms")
    crop_request = {
        "task": "crop_video",
        "video_id": "test_video_001",
        "video_path": "test_input.mp4",
        "target_platforms": ["tiktok", "instagram", "reels"],
        "output_dir": "output/smart_crop",
        "priority": "high"
    }
    crop_result = agent.handle_agent_request(crop_request)
    logger.info(f"Crop task completed: {crop_result.get('success')}")
    logger.info(f"Next agent: {crop_result.get('next_agent')}")

    # Step 4: Generate manifest for downstream agents
    logger.info("\n[Step 4] Generate processing manifest")
    processor = VideoAdProcessor()
    results = crop_result.get('results', [])
    if results:
        manifest = processor.generate_processing_manifest(
            results,
            output_path="output/smart_crop_manifest.json"
        )
        logger.info(f"Manifest generated with {len(results)} items")

    logger.info("\n" + "="*60)
    logger.info("Integration workflow complete!")
    logger.info("="*60)


def example_api_usage():
    """
    Example: API-style usage

    Can be exposed as REST API or gRPC service
    """
    logger.info("\n" + "="*60)
    logger.info("Smart Crop API Usage Example")
    logger.info("="*60)

    api = SmartCropAPI()

    # Single crop request
    logger.info("\n[API] Single crop request")
    single_request = {
        "video_path": "input.mp4",
        "target_platform": "tiktok",
        "options": {
            "detect_faces": True,
            "detect_motion": True,
            "smoothing": 15
        }
    }
    single_result = api.crop_video(single_request)
    logger.info(f"Success: {single_result['success']}")

    # Batch crop request
    logger.info("\n[API] Batch crop request")
    batch_request = {
        "video_path": "input.mp4",
        "platforms": ["tiktok", "instagram", "reels", "youtube_shorts"],
        "output_dir": "output/batch"
    }
    batch_result = api.batch_crop(batch_request)
    logger.info(f"Total: {batch_result.get('total', 0)}")
    logger.info(f"Successful: {batch_result.get('successful', 0)}")

    logger.info("\n" + "="*60)


if __name__ == "__main__":
    print("\nSmart Crop Integration Examples\n")
    print("1. Agent Integration Workflow")
    print("2. API Usage Examples")
    print("\nRun:")
    print("  python smart_crop_integration.py")

    # Run examples
    example_integration_workflow()
    example_api_usage()
