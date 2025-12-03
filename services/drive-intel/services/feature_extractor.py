"""
Feature extraction from video clips
Motion, objects (YOLO), text (OCR), transcript (Whisper), embeddings

ZERO SILENT FAILURES - All errors are tracked and reported
"""
import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from models.asset import ClipFeatures

# Configure logging - NO SILENT FAILURES
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class ModelLoadError(Exception):
    """Raised when a required model fails to load"""
    pass


class FeatureExtractionError(Exception):
    """Raised when feature extraction fails"""
    pass


class FeatureExtractorService:
    """
    Extract features from video clips:
    - Motion score (frame differencing)
    - Objects (YOLOv8n)
    - Text (PaddleOCR)
    - Transcript (Whisper)
    - Embeddings (sentence-transformers)

    ZERO SILENT FAILURES:
    - All model loading errors are tracked
    - get_status() returns which models are available
    - Feature extraction includes warnings for degraded features
    """

    def __init__(self, strict_mode: bool = False):
        """
        Args:
            strict_mode: If True, raise exception if any model fails to load
        """
        self.yolo_model = None
        self.ocr_model = None
        self.whisper_model = None
        self.embedding_model = None
        self.strict_mode = strict_mode

        # Track loading errors - NO SILENT FAILURES
        self.model_errors: Dict[str, str] = {}
        self.models_available: Dict[str, bool] = {
            'yolo': False,
            'ocr': False,
            'whisper': False,
            'embedding': False
        }

        self._init_models()

    def _init_models(self):
        """Initialize ML models with explicit error tracking"""

        # YOLOv8n for object detection
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO('yolov8n.pt')
            self.models_available['yolo'] = True
            logger.info("✅ YOLO model loaded successfully")
        except ImportError as e:
            error_msg = f"ultralytics not installed: {e}"
            self.model_errors['yolo'] = error_msg
            logger.error(f"❌ YOLO FAILED: {error_msg}")
            if self.strict_mode:
                raise ModelLoadError(error_msg)
        except Exception as e:
            error_msg = f"YOLO load failed: {e}"
            self.model_errors['yolo'] = error_msg
            logger.error(f"❌ YOLO FAILED: {error_msg}")
            if self.strict_mode:
                raise ModelLoadError(error_msg)

        # PaddleOCR for text detection
        try:
            from paddleocr import PaddleOCR
            self.ocr_model = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            self.models_available['ocr'] = True
            logger.info("✅ PaddleOCR model loaded successfully")
        except ImportError as e:
            error_msg = f"paddleocr not installed: {e}. Run: pip install paddleocr paddlepaddle"
            self.model_errors['ocr'] = error_msg
            logger.error(f"❌ OCR FAILED: {error_msg}")
            if self.strict_mode:
                raise ModelLoadError(error_msg)
        except Exception as e:
            error_msg = f"OCR load failed: {e}"
            self.model_errors['ocr'] = error_msg
            logger.error(f"❌ OCR FAILED: {error_msg}")
            if self.strict_mode:
                raise ModelLoadError(error_msg)

        # Sentence transformer for embeddings
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.models_available['embedding'] = True
            logger.info("✅ Embedding model loaded successfully")
        except ImportError as e:
            error_msg = f"sentence-transformers not installed: {e}"
            self.model_errors['embedding'] = error_msg
            logger.error(f"❌ EMBEDDING FAILED: {error_msg}")
            if self.strict_mode:
                raise ModelLoadError(error_msg)
        except Exception as e:
            error_msg = f"Embedding load failed: {e}"
            self.model_errors['embedding'] = error_msg
            logger.error(f"❌ EMBEDDING FAILED: {error_msg}")
            if self.strict_mode:
                raise ModelLoadError(error_msg)

    def get_status(self) -> Dict:
        """
        Get model availability status - NEVER LIE ABOUT CAPABILITIES

        Returns:
            Dict with model status and any errors
        """
        available_count = sum(1 for v in self.models_available.values() if v)
        total_models = len(self.models_available)

        return {
            'models_available': self.models_available,
            'models_failed': self.model_errors,
            'status': 'fully_operational' if available_count == total_models
                      else 'degraded' if available_count > 0
                      else 'non_operational',
            'available_count': f"{available_count}/{total_models}",
            'capabilities': {
                'object_detection': self.models_available['yolo'],
                'text_extraction': self.models_available['ocr'],
                'semantic_search': self.models_available['embedding'],
                'transcription': self.models_available['whisper']
            }
        }

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

        Note: Features from unavailable models will be empty but extraction_warnings
              will explain what's missing
        """
        features = ClipFeatures()
        extraction_warnings = []

        # Track which features are degraded
        if not self.models_available['yolo']:
            extraction_warnings.append(f"YOLO unavailable: {self.model_errors.get('yolo', 'unknown')}")
        if not self.models_available['ocr']:
            extraction_warnings.append(f"OCR unavailable: {self.model_errors.get('ocr', 'unknown')}")
        if not self.models_available['embedding']:
            extraction_warnings.append(f"Embedding unavailable: {self.model_errors.get('embedding', 'unknown')}")

        # Extract motion score (always available - uses OpenCV only)
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
        else:
            extraction_warnings.append("Could not extract frame from video")

        # Transcript extraction (stub for MVP)
        features.transcript = self._extract_transcript(video_path, start_time, end_time)

        # Generate embedding from available text
        text_for_embedding = " ".join(features.text_detected + [features.transcript])
        if text_for_embedding.strip():
            features.embedding = self._generate_embedding(text_for_embedding)

        # Log warnings instead of silently failing
        if extraction_warnings:
            logger.warning(f"Feature extraction degraded for {video_path}: {'; '.join(extraction_warnings)}")

        # Attach warnings to features for upstream consumers
        features.extraction_warnings = extraction_warnings

        return features

    def _calculate_motion_score(
        self,
        video_path: str,
        start_time: float,
        end_time: float
    ) -> float:
        """Calculate motion score using frame differencing"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            raise FeatureExtractionError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            cap.release()
            logger.error(f"Invalid FPS for video: {video_path}")
            raise FeatureExtractionError(f"Invalid FPS for video: {video_path}")

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

    def _extract_frame(self, video_path: str, time_sec: float) -> Optional[np.ndarray]:
        """Extract a single frame at specified time"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video for frame extraction: {video_path}")
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            cap.release()
            return None

        frame_num = int(time_sec * fps)

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            logger.warning(f"Could not read frame {frame_num} from {video_path}")

        return frame if ret else None

    def _detect_objects(self, frame: np.ndarray) -> Tuple[List[str], Dict[str, int]]:
        """Detect objects in frame using YOLO"""
        if self.yolo_model is None:
            # Log warning but don't crash - feature is degraded
            logger.debug("Object detection skipped - YOLO model not available")
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
            # Log error with full context
            logger.error(f"Object detection failed: {e}", exc_info=True)
            return [], {}

    def _detect_text(self, frame: np.ndarray) -> List[str]:
        """Detect text in frame using OCR"""
        if self.ocr_model is None:
            logger.debug("Text detection skipped - OCR model not available")
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
            logger.error(f"Text detection failed: {e}", exc_info=True)
            return []

    def _extract_transcript(
        self,
        video_path: str,
        start_time: float,
        end_time: float
    ) -> str:
        """Extract audio transcript (not implemented yet)"""
        # Whisper integration is planned but not implemented
        # Return empty string but log that this feature is unavailable
        if not self.models_available.get('whisper'):
            logger.debug("Transcript extraction skipped - Whisper not implemented")
        return ""

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate sentence embedding"""
        if self.embedding_model is None:
            logger.debug("Embedding skipped - model not available")
            return None

        if not text.strip():
            return None

        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}", exc_info=True)
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
