"""
Feature extraction service for video clips.
"""
import logging
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class FeatureExtractorService:
    """Service for extracting features from video clips."""
    
    def __init__(self):
        self.yolo_model = None
        self.ocr_reader = None
        self.whisper_model = None
        self.sentence_model = None
        
        self._init_models()
        logger.info("Feature extractor initialized")
    
    def _init_models(self):
        """Initialize ML models."""
        try:
            # Initialize YOLO for object detection
            from ultralytics import YOLO
            self.yolo_model = YOLO('yolov8n.pt')  # Nano model for speed
            logger.info("YOLO model loaded")
        except Exception as e:
            logger.warning(f"Failed to load YOLO model: {e}")
        
        try:
            # Initialize PaddleOCR
            from paddleocr import PaddleOCR
            self.ocr_reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("PaddleOCR loaded")
        except Exception as e:
            logger.warning(f"Failed to load OCR model: {e}")
        
        try:
            # Initialize SentenceTransformers for embeddings
            from sentence_transformers import SentenceTransformer
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer loaded")
        except Exception as e:
            logger.warning(f"Failed to load sentence transformer: {e}")
    
    async def extract_features(
        self,
        video_path: str,
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """Extract all features for a clip."""
        try:
            # Open video
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Calculate frame numbers
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            
            # Extract features
            motion_score = await self._calculate_motion(cap, start_frame, end_frame, fps)
            objects = await self._detect_objects(cap, start_frame, end_frame, fps)
            ocr_tokens = await self._extract_ocr(cap, start_frame, end_frame, fps)
            transcript = await self._extract_transcript(video_path, start_time, end_time)
            
            # Generate embedding for text features
            text_content = " ".join(ocr_tokens)
            if transcript:
                text_content += " " + transcript
            
            embedding_id = None
            if text_content and self.sentence_model:
                embedding_id = f"emb_{hash(text_content)}"
            
            cap.release()
            
            return {
                "objects": objects,
                "ocr_tokens": ocr_tokens,
                "motion_score": motion_score,
                "transcript_excerpt": transcript,
                "embeddingVectorId": embedding_id,
                "rankScore": 0.0  # Will be calculated by ranking service
            }
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}", exc_info=True)
            return {
                "objects": [],
                "ocr_tokens": [],
                "motion_score": 0.0,
                "transcript_excerpt": None,
                "embeddingVectorId": None,
                "rankScore": 0.0
            }
    
    async def _calculate_motion(
        self,
        cap: cv2.VideoCapture,
        start_frame: int,
        end_frame: int,
        fps: float
    ) -> float:
        """Calculate motion score using frame differencing."""
        try:
            # Sample frames
            sample_frames = []
            step = max(1, (end_frame - start_frame) // 10)  # Sample ~10 frames
            
            for frame_num in range(start_frame, end_frame, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    sample_frames.append(gray)
                if len(sample_frames) >= 10:
                    break
            
            if len(sample_frames) < 2:
                return 0.0
            
            # Calculate frame differences
            diffs = []
            for i in range(len(sample_frames) - 1):
                diff = cv2.absdiff(sample_frames[i], sample_frames[i + 1])
                diffs.append(np.mean(diff) / 255.0)
            
            # Average motion score
            motion_score = np.mean(diffs) if diffs else 0.0
            return float(motion_score)
        except Exception as e:
            logger.error(f"Motion calculation failed: {e}")
            return 0.0
    
    async def _detect_objects(
        self,
        cap: cv2.VideoCapture,
        start_frame: int,
        end_frame: int,
        fps: float
    ) -> List[str]:
        """Detect objects using YOLO."""
        if not self.yolo_model:
            return []
        
        try:
            # Sample a representative frame (middle of the clip)
            mid_frame = (start_frame + end_frame) // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ret, frame = cap.read()
            
            if not ret:
                return []
            
            # Run YOLO detection
            results = self.yolo_model(frame, verbose=False)
            
            # Extract object names
            objects = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    if class_name not in objects:
                        objects.append(class_name)
            
            return objects
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    async def _extract_ocr(
        self,
        cap: cv2.VideoCapture,
        start_frame: int,
        end_frame: int,
        fps: float
    ) -> List[str]:
        """Extract text using OCR."""
        if not self.ocr_reader:
            return []
        
        try:
            # Sample a few frames
            tokens = set()
            sample_points = [
                start_frame,
                (start_frame + end_frame) // 2,
                end_frame - 1
            ]
            
            for frame_num in sample_points:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Run OCR
                result = self.ocr_reader.ocr(frame, cls=True)
                
                if result and result[0]:
                    for line in result[0]:
                        text = line[1][0]
                        # Clean and tokenize
                        words = text.lower().split()
                        tokens.update(words)
            
            return list(tokens)
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
    
    async def _extract_transcript(
        self,
        video_path: str,
        start_time: float,
        end_time: float
    ) -> Optional[str]:
        """Extract speech transcript using Whisper."""
        # Whisper integration is optional and can be expensive
        # For MVP, we'll return None and add this later
        return None
    
    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate text embedding."""
        if not self.sentence_model or not text:
            return None
        
        try:
            embedding = self.sentence_model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
