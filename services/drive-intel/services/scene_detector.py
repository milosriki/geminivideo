"""
Scene detection service using PySceneDetect.
"""
import logging
from typing import List, Dict, Any
import os
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector

logger = logging.getLogger(__name__)

class SceneDetectorService:
    """Service for detecting scenes in videos."""
    
    def __init__(self):
        self.threshold = float(os.getenv("SCENE_DETECT_THRESHOLD", "27.0"))
        logger.info(f"Scene detector initialized (threshold: {self.threshold})")
    
    async def detect_scenes(self, video_path: str) -> List[Dict[str, Any]]:
        """Detect scenes in a video."""
        try:
            logger.info(f"Detecting scenes in: {video_path}")
            
            video = open_video(video_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=self.threshold))
            
            # Detect scenes
            scene_manager.detect_scenes(video, show_progress=False)
            scene_list = scene_manager.get_scene_list()
            
            # Convert to our format
            scenes = []
            for i, (start_time, end_time) in enumerate(scene_list):
                scene = {
                    "start": start_time.get_seconds(),
                    "end": end_time.get_seconds(),
                    "duration": (end_time - start_time).get_seconds()
                }
                scenes.append(scene)
            
            logger.info(f"Detected {len(scenes)} scenes")
            return scenes
        except Exception as e:
            logger.error(f"Scene detection failed: {e}", exc_info=True)
            # Return a fallback single scene for the entire video
            return [{
                "start": 0.0,
                "end": 30.0,  # Default assumption
                "duration": 30.0
            }]
