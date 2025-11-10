"""
Scene detection using PySceneDetect
"""
from scenedetect import detect, ContentDetector, split_video_ffmpeg
from typing import List, Tuple
import cv2
import os


class SceneDetectorService:
    """
    Shot/scene detection service using PySceneDetect ContentDetector
    """
    
    def __init__(self, threshold: float = 27.0):
        """
        Initialize scene detector
        
        Args:
            threshold: Content detection threshold (default 27.0)
                      Lower = more sensitive, more scenes detected
        """
        self.threshold = threshold
    
    def detect_scenes(self, video_path: str) -> List[Tuple[float, float]]:
        """
        Detect scenes in a video
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of (start_time, end_time) tuples in seconds
        """
        try:
            # Detect scenes using ContentDetector
            scene_list = detect(video_path, ContentDetector(threshold=self.threshold))
            
            # Convert to list of (start, end) tuples in seconds
            scenes = []
            for scene in scene_list:
                start_time = scene[0].get_seconds()
                end_time = scene[1].get_seconds()
                scenes.append((start_time, end_time))
            
            # If no scenes detected, return the whole video as one scene
            if not scenes:
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                cap.release()
                scenes = [(0.0, duration)]
            
            return scenes
            
        except Exception as e:
            print(f"Error detecting scenes: {e}")
            # Fallback: return whole video as one scene
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            return [(0.0, duration)]
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Extract basic video information
        
        Returns:
            dict with duration, resolution, fps, file_size
        """
        cap = cv2.VideoCapture(video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
        
        return {
            "duration": duration,
            "resolution": (width, height),
            "fps": fps,
            "file_size": file_size
        }
