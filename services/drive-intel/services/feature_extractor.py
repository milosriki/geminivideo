"""
Feature extraction from video clips
Motion, objects (YOLO), text (OCR), transcript (Whisper), embeddings
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple
import os
from models.asset import ClipFeatures


class FeatureExtractorService:
    """
    Extract features from video clips:
    - Motion score (frame differencing)
    - Objects (YOLOv8n stub)
    - Text (PaddleOCR stub)
    - Transcript (Whisper stub)
    - Embeddings (sentence-transformers)
    """
    
    def __init__(self):
        self.yolo_model = None
        self.ocr_model = None
        self.whisper_model = None
        self.embedding_model = None
        self._init_models()
    
    def _init_models(self):
        """Initialize ML models lazily"""
        try:
            # YOLOv8n for object detection
            from ultralytics import YOLO
            self.yolo_model = YOLO('yolov8n.pt')  # Lightweight model
        except Exception as e:
            print(f"Warning: Could not load YOLO model: {e}")
        
        try:
            # PaddleOCR for text detection
            from paddleocr import PaddleOCR
            self.ocr_model = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        except Exception as e:
            print(f"Warning: Could not load OCR model: {e}")
        
        try:
            # Sentence transformer for embeddings
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
        
        # Whisper is optional for MVP
        # try:
        #     from faster_whisper import WhisperModel
        #     self.whisper_model = WhisperModel("base", device="cpu")
        # except Exception as e:
        #     print(f"Warning: Could not load Whisper model: {e}")
    
    def extract_features(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float
    ) -> ClipFeatures:
        """
        Extract all features from a video clip
        
        Args:
            video_path: Path to video file
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            ClipFeatures object with all extracted features
        """
        features = ClipFeatures()
        
        # Extract motion score
        features.motion_score = self._calculate_motion_score(video_path, start_time, end_time)
        
        # Extract middle frame for object detection and OCR
        middle_frame = self._extract_frame(video_path, (start_time + end_time) / 2)
        
        if middle_frame is not None:
            # Object detection
            objects, object_counts = self._detect_objects(middle_frame)
            features.objects = objects
            features.object_counts = object_counts
            
            # OCR text detection
            features.text_detected = self._detect_text(middle_frame)
            
            # Technical quality (simple estimate based on resolution and sharpness)
            features.technical_quality = self._estimate_quality(middle_frame)
        
        # Transcript extraction (stub for MVP)
        features.transcript = self._extract_transcript(video_path, start_time, end_time)
        
        # Generate embedding from available text
        text_for_embedding = " ".join(features.text_detected + [features.transcript])
        if text_for_embedding.strip():
            features.embedding = self._generate_embedding(text_for_embedding)
        
        return features
    
    def _calculate_motion_score(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float
    ) -> float:
        """Calculate motion score using frame differencing"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        motion_scores = []
        prev_frame = None
        
        for _ in range(min(end_frame - start_frame, 30)):  # Sample up to 30 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                diff = cv2.absdiff(prev_frame, gray)
                motion_score = np.mean(diff) / 255.0
                motion_scores.append(motion_score)
            
            prev_frame = gray
        
        cap.release()
        
        return np.mean(motion_scores) if motion_scores else 0.0
    
    def _extract_frame(self, video_path: str, time_sec: float) -> np.ndarray:
        """Extract a single frame at specified time"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_num = int(time_sec * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    def _detect_objects(self, frame: np.ndarray) -> Tuple[List[str], Dict[str, int]]:
        """Detect objects in frame using YOLO"""
        if self.yolo_model is None:
            return [], {}
        
        try:
            results = self.yolo_model(frame, verbose=False)
            
            objects = []
            object_counts = {}
            
            for result in results:
                if hasattr(result, 'boxes'):
                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id]
                        objects.append(class_name)
                        object_counts[class_name] = object_counts.get(class_name, 0) + 1
            
            return list(set(objects)), object_counts
        except Exception as e:
            print(f"Error in object detection: {e}")
            return [], {}
    
    def _detect_text(self, frame: np.ndarray) -> List[str]:
        """Detect text in frame using OCR"""
        if self.ocr_model is None:
            return []
        
        try:
            result = self.ocr_model.ocr(frame, cls=True)
            
            texts = []
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text = line[1][0]
                        confidence = line[1][1]
                        if confidence > 0.5:  # Only high confidence text
                            texts.append(text)
            
            return texts
        except Exception as e:
            print(f"Error in text detection: {e}")
            return []
    
    def _extract_transcript(
        self, 
        video_path: str, 
        start_time: float, 
        end_time: float
    ) -> str:
        """Extract audio transcript (stub for MVP)"""
        # Whisper integration is optional for MVP
        # For now, return empty string
        return ""
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate sentence embedding"""
        if self.embedding_model is None or not text.strip():
            return None
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def _estimate_quality(self, frame: np.ndarray) -> float:
        """Estimate technical quality of frame"""
        if frame is None:
            return 0.0
        
        # Calculate sharpness using Laplacian variance
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize to 0-1 range (empirical threshold ~100 for sharp images)
        sharpness_score = min(laplacian_var / 100.0, 1.0)
        
        # Resolution score (normalized by 1080p)
        height = frame.shape[0]
        resolution_score = min(height / 1080.0, 1.0)
        
        return (sharpness_score * 0.6 + resolution_score * 0.4)
