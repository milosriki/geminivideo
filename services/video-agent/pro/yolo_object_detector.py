"""
YOLOv8 Object Detection for Ad Scene Understanding

Detects products, backgrounds, actions, and context in video ads.
Critical for:
- Product visibility tracking
- Scene composition analysis
- Brand safety checks
- Context-aware editing
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
import cv2
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("ultralytics not installed. Run: pip install ultralytics")

# COCO class names (80 classes)
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
    'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
    'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

# Categories relevant for ads
AD_RELEVANT_CATEGORIES = {
    'person': 'human_presence',
    'bottle': 'product',
    'cup': 'product',
    'cell phone': 'product',
    'laptop': 'product',
    'tv': 'product',
    'car': 'vehicle',
    'motorcycle': 'vehicle',
    'dog': 'pet',
    'cat': 'pet',
    'couch': 'lifestyle',
    'bed': 'lifestyle',
    'dining table': 'lifestyle',
    'sports ball': 'sports',
    'skateboard': 'sports',
    'surfboard': 'sports'
}

@dataclass
class ObjectDetection:
    """A detected object"""
    class_name: str
    class_id: int
    confidence: float
    x: int
    y: int
    width: int
    height: int
    category: str  # human, product, vehicle, etc.

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        return self.width * self.height

class YOLOObjectDetector:
    """
    Scene understanding through object detection.

    Use cases:
    - Track product visibility over time
    - Detect scene types (indoor, outdoor, lifestyle)
    - Brand safety (detect inappropriate content)
    - Composition analysis
    """

    def __init__(self,
                 model_size: str = 'n',  # n, s, m, l, x
                 confidence_threshold: float = 0.4,
                 device: str = None):
        """
        Initialize YOLOv8 object detector.

        Args:
            model_size: Model size (n=nano, s=small, m=medium, l=large, x=xlarge)
            confidence_threshold: Minimum detection confidence
            device: 'cuda', 'cpu', or None for auto
        """
        self.confidence_threshold = confidence_threshold
        self.device = device

        if not YOLO_AVAILABLE:
            logger.error("YOLOv8 not available. Install: pip install ultralytics")
            self.model = None
            return

        model_name = f"yolov8{model_size}.pt"
        try:
            self.model = YOLO(model_name)
            logger.info(f"Loaded YOLOv8 model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def detect_objects(self, frame: np.ndarray) -> List[ObjectDetection]:
        """Detect all objects in a frame"""
        if self.model is None:
            return []

        results = self.model(frame, verbose=False, conf=self.confidence_threshold)

        detections = []
        for result in results:
            boxes = result.boxes

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = COCO_CLASSES[class_id] if class_id < len(COCO_CLASSES) else 'unknown'

                category = AD_RELEVANT_CATEGORIES.get(class_name, 'other')

                detection = ObjectDetection(
                    class_name=class_name,
                    class_id=class_id,
                    confidence=confidence,
                    x=int(x1),
                    y=int(y1),
                    width=int(x2 - x1),
                    height=int(y2 - y1),
                    category=category
                )
                detections.append(detection)

        return detections

    def analyze_video_objects(self, video_path: str, sample_rate: int = 5) -> Dict:
        """
        Analyze objects throughout a video.

        Returns comprehensive object presence analysis.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        object_timeline = []
        object_counts = defaultdict(int)
        category_counts = defaultdict(int)
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_rate == 0:
                detections = self.detect_objects(frame)
                timestamp = frame_idx / fps

                frame_objects = {}
                for det in detections:
                    object_counts[det.class_name] += 1
                    category_counts[det.category] += 1

                    if det.class_name not in frame_objects:
                        frame_objects[det.class_name] = {
                            'count': 0,
                            'max_confidence': 0,
                            'total_area': 0
                        }
                    frame_objects[det.class_name]['count'] += 1
                    frame_objects[det.class_name]['max_confidence'] = max(
                        frame_objects[det.class_name]['max_confidence'],
                        det.confidence
                    )
                    frame_objects[det.class_name]['total_area'] += det.area

                object_timeline.append({
                    'frame': frame_idx,
                    'timestamp': timestamp,
                    'objects': frame_objects,
                    'total_objects': len(detections),
                    'has_person': any(d.class_name == 'person' for d in detections),
                    'has_product': any(d.category == 'product' for d in detections)
                })

            frame_idx += 1

        cap.release()

        processed_frames = frame_idx // sample_rate

        return {
            'video_path': video_path,
            'total_frames': total_frames,
            'processed_frames': processed_frames,
            'fps': fps,
            'duration': total_frames / fps,
            'object_summary': dict(object_counts),
            'category_summary': dict(category_counts),
            'most_common_objects': sorted(object_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'timeline': object_timeline,
            'scene_analysis': self._analyze_scene_type(dict(object_counts), dict(category_counts)),
            'product_visibility': self._calculate_product_visibility(object_timeline)
        }

    def _analyze_scene_type(self, object_counts: Dict, category_counts: Dict) -> Dict:
        """Determine scene type from detected objects"""
        total = sum(object_counts.values()) or 1

        scene_scores = {
            'lifestyle': 0,
            'outdoor': 0,
            'tech': 0,
            'food': 0,
            'sports': 0,
            'studio': 0
        }

        # Lifestyle indicators
        for obj in ['couch', 'bed', 'dining table', 'chair', 'potted plant']:
            scene_scores['lifestyle'] += object_counts.get(obj, 0)

        # Outdoor indicators
        for obj in ['car', 'bicycle', 'motorcycle', 'bird', 'tree', 'dog']:
            scene_scores['outdoor'] += object_counts.get(obj, 0)

        # Tech indicators
        for obj in ['laptop', 'cell phone', 'tv', 'keyboard', 'mouse']:
            scene_scores['tech'] += object_counts.get(obj, 0)

        # Food indicators
        for obj in ['pizza', 'banana', 'apple', 'cup', 'bowl', 'fork', 'knife']:
            scene_scores['food'] += object_counts.get(obj, 0)

        # Sports indicators
        for obj in ['sports ball', 'skateboard', 'surfboard', 'tennis racket']:
            scene_scores['sports'] += object_counts.get(obj, 0)

        # Normalize and find primary scene type
        max_score = max(scene_scores.values()) or 1
        normalized = {k: v/max_score for k, v in scene_scores.items()}
        primary_scene = max(scene_scores, key=scene_scores.get)

        return {
            'primary_scene_type': primary_scene,
            'scene_scores': normalized,
            'has_humans': category_counts.get('human_presence', 0) > 0,
            'has_products': category_counts.get('product', 0) > 0
        }

    def _calculate_product_visibility(self, timeline: List[Dict]) -> Dict:
        """Calculate product visibility metrics"""
        frames_with_product = sum(1 for f in timeline if f.get('has_product', False))
        total_frames = len(timeline) or 1

        # Find longest streak of product visibility
        max_streak = 0
        current_streak = 0
        for f in timeline:
            if f.get('has_product', False):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return {
            'product_presence_ratio': frames_with_product / total_frames,
            'frames_with_product': frames_with_product,
            'longest_product_visibility_streak': max_streak,
            'recommendation': self._get_product_recommendation(frames_with_product / total_frames)
        }

    def _get_product_recommendation(self, ratio: float) -> str:
        if ratio >= 0.5:
            return "Good product visibility - product shown in majority of video"
        elif ratio >= 0.3:
            return "Moderate product visibility - consider adding more product shots"
        elif ratio >= 0.1:
            return "Low product visibility - product may be overshadowed"
        else:
            return "Very low product visibility - increase product screen time significantly"
