"""
Scene Detector - Real video analysis
Uses PySceneDetect to find actual cuts and scenes in video files
"""
import logging
from typing import List, Dict, Any
from scenedetect import open_video, SceneManager, ContentDetector

logger = logging.getLogger(__name__)

class SceneDetector:
    """Real scene detection using PySceneDetect"""
    
    def detect_scenes(self, video_path: str, threshold: float = 27.0) -> List[Dict[str, Any]]:
        """
        Detect scenes in a video file
        
        Args:
            video_path: Path to video file
            threshold: Threshold for content detector (default 27.0)
            
        Returns:
            List of detected scenes with start/end times
        """
        try:
            video = open_video(video_path)
            scene_manager = SceneManager()
            
            # Add ContentDetector algorithm (detects fast cuts)
            scene_manager.add_detector(ContentDetector(threshold=threshold))
            
            # Detect scenes
            scene_manager.detect_scenes(video, show_progress=False)
            
            # Get scene list
            scene_list = scene_manager.get_scene_list()
            
            scenes = []
            for i, scene in enumerate(scene_list):
                start, end = scene
                
                # Calculate simple complexity score based on duration (shorter = higher energy)
                duration = end.get_seconds() - start.get_seconds()
                energy_score = min(1.0, 3.0 / duration) if duration > 0 else 0
                
                scenes.append({
                    "clip_id": f"scene_{i+1}",
                    "start_time": start.get_seconds(),
                    "end_time": end.get_seconds(),
                    "duration": duration,
                    "scene_score": 0.5 + (energy_score * 0.5), # Base score + energy bonus
                    "features": {
                        "scene_index": i,
                        "frame_start": start.get_frames(),
                        "frame_end": end.get_frames(),
                        "energy_level": "high" if energy_score > 0.7 else "normal"
                    }
                })
                
            logger.info(f"✅ Detected {len(scenes)} scenes in {video_path}")
            return scenes
            
        except Exception as e:
            logger.error(f"Scene detection failed: {e}")
            # Fallback to single scene if detection fails
            return [{
                "clip_id": "scene_1",
                "start_time": 0.0,
                "end_time": 10.0, # Placeholder
                "duration": 10.0,
                "scene_score": 0.5,
                "features": {"error": str(e)}
            }]

# Global instance
scene_detector = SceneDetector()
