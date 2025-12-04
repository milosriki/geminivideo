"""
Feature extraction from video clips
Motion, objects (YOLO), text (OCR), transcript (Whisper), embeddings, visual patterns (CNN)
"""
import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from models.asset import ClipFeatures
from services.transcription import TranscriptionService
from services.visual_patterns import VisualPatternExtractor

logger = logging.getLogger(__name__)


class FeatureExtractorService:
    """
    Extract features from video clips:
    - Motion score (frame differencing)
    - Objects (YOLOv8n stub)
    - Text (PaddleOCR stub)
    - Transcript (Whisper stub)
    - Embeddings (sentence-transformers)
    - Visual patterns (ResNet-50 CNN)
    """

    def __init__(self):
        self.yolo_model = None
        self.ocr_model = None
        self.transcription_service = None
        self.embedding_model = None
        self.visual_pattern_extractor = None
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

        try:
            # Whisper transcription service (lazy loading of model)
            self.transcription_service = TranscriptionService(model_size='base')
            logger.info("Transcription service initialized")
        except Exception as e:
            logger.warning(f"Warning: Could not initialize transcription service: {e}")

        try:
            # Visual pattern extractor with CNN (lazy loading of ResNet-50)
            self.visual_pattern_extractor = VisualPatternExtractor()
            logger.info("Visual pattern extractor initialized")
        except Exception as e:
            logger.warning(f"Warning: Could not initialize visual pattern extractor: {e}")
    
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

            # Visual pattern extraction (CNN-based)
            visual_pattern_data = self._extract_visual_patterns(middle_frame)
            if visual_pattern_data:
                features.visual_pattern = visual_pattern_data.get('primary_pattern')
                features.visual_confidence = visual_pattern_data.get('primary_confidence')
                features.visual_energy = visual_pattern_data.get('visual_energy')
        
        # Transcript extraction with Whisper
        transcript_data = self._extract_transcript(video_path, start_time, end_time)
        features.transcript = transcript_data.get('text', '')

        # Store additional transcript metadata in features if needed
        # (Could extend ClipFeatures model to include keywords, segments, etc.)
        if 'keywords' in transcript_data:
            # For now, we'll include keywords in the embedding
            keywords_text = " ".join(transcript_data['keywords'])
            text_for_embedding = " ".join(
                features.text_detected +
                [features.transcript, keywords_text]
            )
        else:
            text_for_embedding = " ".join(
                features.text_detected +
                [features.transcript]
            )

        # Generate embedding from available text
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
    ) -> Dict:
        """
        Extract audio transcript using Whisper

        Returns:
            Dictionary with transcript data including text, segments, keywords
        """
        if self.transcription_service is None:
            logger.warning("Transcription service not available")
            return {'text': '', 'keywords': [], 'success': False}

        try:
            # Extract transcript with word-level timestamps
            result = self.transcription_service.extract_transcript(
                video_path,
                start_time,
                end_time
            )

            if result.get('success'):
                logger.info(f"Transcribed segment: {len(result['text'])} chars, "
                          f"{len(result.get('keywords', []))} keywords")
            else:
                logger.warning(f"Transcription failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"Error in transcript extraction: {e}")
            return {'text': '', 'keywords': [], 'success': False, 'error': str(e)}
    
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

    def _extract_visual_patterns(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Extract visual patterns using CNN-based classification

        Args:
            frame: Input frame as numpy array

        Returns:
            Dictionary with visual pattern data or None if extraction fails
        """
        if self.visual_pattern_extractor is None:
            logger.warning("Visual pattern extractor not available")
            return None

        try:
            # Analyze single frame in detail
            result = self.visual_pattern_extractor.analyze_single_frame_detailed(frame)
            logger.info(f"Visual pattern detected: {result['primary_pattern']} "
                       f"(confidence: {result['primary_confidence']:.2f})")
            return result

        except Exception as e:
            logger.error(f"Error extracting visual patterns: {e}")
            return None

    def extract_visual_sequence_analysis(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        sample_rate: int = 5
    ) -> Optional[Dict]:
        """
        Extract visual pattern analysis for entire video sequence

        Args:
            video_path: Path to video file
            start_time: Start time in seconds
            end_time: End time in seconds
            sample_rate: Sample every Nth frame (default: 5)

        Returns:
            Dictionary with sequence analysis or None if extraction fails
        """
        if self.visual_pattern_extractor is None:
            logger.warning("Visual pattern extractor not available")
            return None

        try:
            # Extract frames from video sequence
            frames = self._extract_frames_sequence(
                video_path, start_time, end_time, sample_rate
            )

            if not frames:
                logger.warning("No frames extracted for visual sequence analysis")
                return None

            # Analyze sequence
            analysis = self.visual_pattern_extractor.analyze_video_sequence(
                frames, sample_rate=1  # Already sampled in extraction
            )

            logger.info(f"Sequence analysis: {analysis.frame_count} frames, "
                       f"dominant pattern: {analysis.dominant_pattern}, "
                       f"consistency: {analysis.temporal_consistency:.2f}")

            # Convert to dictionary
            return {
                'dominant_pattern': analysis.dominant_pattern,
                'pattern_distribution': analysis.pattern_distribution,
                'average_confidence': analysis.average_confidence,
                'average_visual_energy': analysis.average_visual_energy,
                'pattern_transitions': analysis.pattern_transitions,
                'temporal_consistency': analysis.temporal_consistency,
                'frame_count': analysis.frame_count
            }

        except Exception as e:
            logger.error(f"Error in visual sequence analysis: {e}")
            return None

    def _extract_frames_sequence(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        sample_rate: int = 5
    ) -> List[np.ndarray]:
        """
        Extract a sequence of frames from video

        Args:
            video_path: Path to video file
            start_time: Start time in seconds
            end_time: End time in seconds
            sample_rate: Extract every Nth frame

        Returns:
            List of frames as numpy arrays
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        frames = []
        frame_count = 0

        while cap.get(cv2.CAP_PROP_POS_FRAMES) < end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            # Sample frames based on sample_rate
            if frame_count % sample_rate == 0:
                frames.append(frame)

            frame_count += 1

            # Limit maximum frames to prevent memory issues
            if len(frames) >= 100:
                break

        cap.release()
        logger.info(f"Extracted {len(frames)} frames from video sequence")

        return frames
