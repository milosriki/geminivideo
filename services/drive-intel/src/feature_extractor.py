import logging
from typing import List, Dict, Any
import numpy as np
from ultralytics import YOLO
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """
    Extracts visual and semantic features from video frames/scenes.
    - Object Detection: YOLOv8
    - Semantic Embeddings: SentenceTransformer
    """
    
    def __init__(self):
        logger.info("Initializing FeatureExtractor...")
        # Load YOLO model (nano for speed, or small/medium for accuracy)
        self.yolo = YOLO('yolov8n.pt') 
        
        # Load Sentence Transformer
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("FeatureExtractor initialized.")

    def detect_objects(self, image_path: str) -> List[str]:
        """
        Detect objects in an image frame.
        Returns a list of unique object names detected.
        """
        try:
            results = self.yolo(image_path, verbose=False)
            detected_objects = set()
            
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.yolo.names[class_id]
                    detected_objects.add(class_name)
            
            return list(detected_objects)
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []

    def detect_objects_at_timestamp(self, video_path: str, timestamp: float) -> List[str]:
        """
        Extract frame at timestamp and detect objects.
        """
        import cv2
        try:
            cap = cv2.VideoCapture(video_path)
            # Set position (milliseconds)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            success, frame = cap.read()
            cap.release()
            
            if not success:
                logger.warning(f"Failed to extract frame at {timestamp}s")
                return []
                
            # Run YOLO on the frame (numpy array)
            results = self.yolo(frame, verbose=False)
            detected_objects = set()
            
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.yolo.names[class_id]
                    detected_objects.add(class_name)
            
            return list(detected_objects)
        except Exception as e:
            logger.error(f"Frame object detection failed: {e}")
            return []

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate semantic embedding vector for text.
        Returns a list of floats (vector).
        """
        try:
            if not text:
                return [0.0] * 384 # Dimension of all-MiniLM-L6-v2
                
            embedding = self.embedder.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [0.0] * 384

# Global instance
feature_extractor = None

def get_feature_extractor():
    global feature_extractor
    if feature_extractor is None:
        feature_extractor = FeatureExtractor()
    return feature_extractor
