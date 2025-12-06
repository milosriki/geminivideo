# GeminiVideo AI Components Documentation

Comprehensive technical documentation for all 11 AI subsystems powering the GeminiVideo platform.

---

## Table of Contents

### Video Analysis Subsystem
1. [Motion Moment SDK](#1-motion-moment-sdk)
2. [Face-Weighted Analyzer](#2-face-weighted-analyzer)
3. [Precision AV Sync](#3-precision-av-sync)
4. [Psychological Timing](#4-psychological-timing)
5. [YOLO Face Detector](#5-yolo-face-detector)
6. [YOLO Object Detector](#6-yolo-object-detector)
7. [Motion Energy Calculator](#7-motion-energy-calculator)
8. [Hook Optimizer](#8-hook-optimizer)
9. [CTA Optimizer](#9-cta-optimizer)

### ML Optimization Subsystem
10. [Variation Generator](#10-variation-generator)
11. [Budget Optimizer](#11-budget-optimizer)
12. [Loser Kill Switch](#12-loser-kill-switch)
13. [Cross-Campaign Learning](#13-cross-campaign-learning)
14. [CAPI Feedback Loop](#14-capi-feedback-loop)
15. [Prediction Accuracy Tracker](#15-prediction-accuracy-tracker)
16. [Auto-Retrain Pipeline](#16-auto-retrain-pipeline)

### Data Intelligence Subsystem
17. [Winning Patterns Database](#17-winning-patterns-database)

### AI Generation Subsystem
18. [Runway Gen-3 Integration](#18-runway-gen-3-integration)
19. [ElevenLabs Voice Integration](#19-elevenlabs-voice-integration)

---

## Video Analysis Subsystem

### 1. Motion Moment SDK

**File:** `/home/user/geminivideo/services/video-agent/pro/motion_moment_sdk.py`

#### Purpose
Analyzes temporal dynamics of video ads by detecting precise micro-moments where attention peaks. Processes 30-frame windows (1 second at 30fps) to identify optimal moments for hooks, CTAs, and transitions.

#### Key Constants
- `WINDOW_SIZE = 30` - Analysis window size (1 second at 30fps)
- `FACE_WEIGHT = 3.2` - Multiplier for face regions (based on eye-tracking research)

#### Main Classes and Methods

**MotionMoment** (dataclass)
- `frame_start: int` - Start frame of moment
- `frame_end: int` - End frame of moment
- `timestamp_start: float` - Start timestamp in seconds
- `motion_energy: float` - Energy level of moment
- `peak_frame: int` - Frame with peak energy
- `moment_type: str` - 'hook', 'transition', 'cta', 'emotional'
- `face_present: bool` - Whether face detected
- `face_weight: float` - Weight applied (3.2x if face present)

**MotionMomentSDK**
- `__init__(fps: float = 30.0)` - Initialize with video FPS
- `calculate_motion_energy(frame1, frame2) -> float` - Calculate optical flow energy
- `analyze_temporal_window(frames, face_detections) -> TemporalWindow` - Analyze 30-frame window
- `detect_motion_moments(video_path) -> List[MotionMoment]` - Detect all moments in video
- `find_optimal_cut_points(moments) -> List[float]` - Find optimal cut timestamps
- `get_attention_curve(video_path) -> Dict` - Generate attention prediction curve

#### Input/Output
- **Input:** Video file path (MP4, AVI, etc.)
- **Output:** List of MotionMoment objects with timestamps, energy levels, and classifications

#### Dependencies
- OpenCV (`cv2`) - Video processing and optical flow
- NumPy - Numerical operations
- SciPy (optional) - Gaussian smoothing

#### Usage Example
```python
from motion_moment_sdk import MotionMomentSDK

sdk = MotionMomentSDK(fps=30.0)
moments = sdk.detect_motion_moments("video.mp4")

for moment in moments:
    print(f"Type: {moment.moment_type}")
    print(f"Time: {moment.timestamp_start:.2f}s")
    print(f"Energy: {moment.motion_energy:.2f}")
    print(f"Face present: {moment.face_present}")

# Get attention curve
curve = sdk.get_attention_curve("video.mp4")
print(f"Timeline: {curve['timeline']}")
print(f"Attention: {curve['attention']}")
```

---

### 2. Face-Weighted Analyzer

**File:** `/home/user/geminivideo/services/video-agent/pro/face_weighted_analyzer.py`

#### Purpose
Applies 3.2x weight to human face regions in motion analysis. Based on eye-tracking research showing viewers pay 3.2x more attention to faces than background elements.

#### Key Constants
- `FACE_WEIGHT = 3.2` - Scientific multiplier based on eye-tracking studies
- Optical flow parameters: `pyr_scale=0.5`, `levels=3`, `winsize=15`

#### Main Classes and Methods

**FaceRegion** (dataclass)
- `x, y, width, height: int` - Bounding box coordinates
- `confidence: float` - Detection confidence
- `motion_energy: float` - Raw motion energy in region
- `weighted_energy: float` - Energy × 3.2

**FrameAnalysis** (dataclass)
- `frame_idx: int` - Frame number
- `timestamp: float` - Time in seconds
- `faces: List[FaceRegion]` - Detected faces
- `background_motion: float` - Motion outside faces
- `face_motion: float` - Weighted face motion
- `total_weighted_motion: float` - Combined weighted motion
- `face_ratio: float` - Percentage of frame covered by faces

**FaceWeightedAnalyzer**
- `__init__(use_yolo: bool = False)` - Initialize with YOLO or Haar Cascade
- `detect_faces(frame) -> List[FaceRegion]` - Detect faces in frame
- `calculate_weighted_motion(frame1, frame2) -> FrameAnalysis` - Calculate with 3.2x weighting
- `analyze_video(video_path) -> Dict` - Full video analysis
- `_find_peak_face_moments(analyses, top_n=5) -> List[Dict]` - Find best face moments

#### Input/Output
- **Input:** Video file path or frame pairs
- **Output:** Dictionary with face motion metrics, peak moments, and recommendations

#### Dependencies
- OpenCV - Video processing, Haar Cascade detection
- NumPy - Array operations
- Ultralytics YOLO (optional) - Advanced face detection

#### Usage Example
```python
from face_weighted_analyzer import FaceWeightedAnalyzer

analyzer = FaceWeightedAnalyzer(use_yolo=False)
results = analyzer.analyze_video("ad.mp4")

print(f"Total face motion (3.2x weighted): {results['total_face_motion_weighted']:.2f}")
print(f"Face to background ratio: {results['face_to_background_ratio']:.2f}")
print(f"Average face coverage: {results['average_face_coverage']:.2%}")

for moment in results['peak_face_moments']:
    print(f"Peak at {moment['timestamp']:.2f}s - {moment['face_count']} faces")
```

---

### 3. Precision AV Sync

**File:** `/home/user/geminivideo/services/video-agent/pro/precision_av_sync.py`

#### Purpose
Ensures audio beats align with visual peaks within 0.1 second tolerance. Critical for professional ad quality - beat-synced cuts increase watch time by 23%.

#### Key Constants
- `SYNC_TOLERANCE = 0.1` - 100ms precision requirement
- Audio sample rate: `sr = 22050` Hz

#### Main Classes and Methods

**AudioPeak** (dataclass)
- `timestamp: float` - When peak occurs
- `energy: float` - Peak energy level
- `peak_type: str` - 'beat', 'onset', 'vocal', 'drop'

**VisualPeak** (dataclass)
- `timestamp: float` - When peak occurs
- `motion_energy: float` - Visual energy level
- `peak_type: str` - 'cut', 'motion', 'face_appear', 'transition'

**SyncPoint** (dataclass)
- `audio_peak: AudioPeak` - Audio peak
- `visual_peak: VisualPeak` - Matched visual peak
- `offset: float` - Time offset in seconds
- `is_synced: bool` - Within 0.1s tolerance
- `sync_score: float` - Sync quality (0-1)

**PrecisionAVSync**
- `__init__(sr: int = 22050)` - Initialize with sample rate
- `extract_audio_peaks(audio_path) -> List[AudioPeak]` - Find beats, onsets, drops
- `extract_visual_peaks(video_path) -> List[VisualPeak]` - Find cuts, motion spikes
- `find_sync_points(audio_peaks, visual_peaks) -> List[SyncPoint]` - Match peaks
- `analyze_sync_quality(video_path) -> Dict` - Overall sync analysis
- `suggest_cut_adjustments(sync_points) -> List[Dict]` - Fix recommendations

#### Input/Output
- **Input:** Video file path (extracts audio) or separate video + audio paths
- **Output:** Sync analysis with percentage synced, average offset, and recommendations

#### Dependencies
- Librosa - Audio analysis, beat detection
- OpenCV - Video processing
- SciPy - Peak finding
- FFmpeg - Audio extraction

#### Usage Example
```python
from precision_av_sync import PrecisionAVSync

sync = PrecisionAVSync(sr=22050)
analysis = sync.analyze_sync_quality("ad_video.mp4")

print(f"Sync percentage: {analysis['sync_percentage']:.1f}%")
print(f"Average offset: {analysis['average_offset_seconds']:.3f}s")
print(f"Recommendation: {analysis['recommendation']}")

# Get cut adjustments
audio_peaks = sync.extract_audio_peaks("audio.wav")
visual_peaks = sync.extract_visual_peaks("video.mp4")
sync_points = sync.find_sync_points(audio_peaks, visual_peaks)
adjustments = sync.suggest_cut_adjustments(sync_points)

for adj in adjustments[:5]:
    print(f"Cut at {adj['current_visual_time']:.2f}s")
    print(f"Should be at {adj['target_audio_time']:.2f}s")
    print(f"Shift {adj['direction']} by {abs(adj['adjustment_needed']):.3f}s")
```

---

### 4. Psychological Timing

**File:** `/home/user/geminivideo/services/video-agent/pro/psychological_timing.py`

#### Purpose
Optimizes placement of psychological triggers (pain points, urgency, social proof) based on motion analysis. Low-motion moments = higher cognitive bandwidth for message absorption.

#### Key Constants
**Trigger Configurations** (min/max duration, ideal motion level):
- `PAIN_POINT`: 2-5s, low motion, face present
- `AGITATION`: 3-8s, medium motion, face present
- `SOLUTION`: 5-15s, high motion, product focus
- `SOCIAL_PROOF`: 3-10s, low motion, face present
- `URGENCY`: 2-5s, high motion, no face needed
- `CTA`: 2-4s, low motion, button focus
- `HOOK`: 1-3s, high motion, face present

#### Main Classes and Methods

**TriggerType** (Enum)
- `PAIN_POINT, AGITATION, SOLUTION, SOCIAL_PROOF, URGENCY, SCARCITY, CTA, HOOK, TRANSFORMATION`

**PsychologicalTrigger** (dataclass)
- `trigger_type: TriggerType`
- `ideal_motion_level: str` - 'low', 'medium', 'high'
- `ideal_face_present: bool`
- `min_duration, max_duration: float`
- `position_preference: str` - 'early', 'middle', 'late'

**TriggerWindow** (dataclass)
- `start_time, end_time: float`
- `motion_level: float`
- `has_face: bool`
- `recommended_triggers: List[TriggerType]`
- `absorption_score: float` - How well viewers absorb messages (0-1)

**PsychologicalTimingOptimizer**
- `__init__()` - Initialize with trigger configs
- `analyze_motion_windows(motion_data) -> List[TriggerWindow]` - Find optimal windows
- `optimize_trigger_placement(video_analysis) -> Dict` - Generate recommendations
- `_score_trigger_fit(config, level, has_face, duration, position) -> float` - Score fit (0-1)

#### Input/Output
- **Input:** Motion data as list of (timestamp, motion_energy, has_face) tuples
- **Output:** List of TriggerWindow objects with recommended triggers and absorption scores

#### Dependencies
- NumPy - Statistical calculations
- Enum - Trigger type definitions

#### Usage Example
```python
from psychological_timing import PsychologicalTimingOptimizer, TriggerType

optimizer = PsychologicalTimingOptimizer()

# Motion data: (timestamp, energy, has_face)
motion_data = [
    (0.0, 15.2, True),
    (0.5, 12.1, True),
    (1.0, 3.4, False),
    # ... more data
]

windows = optimizer.analyze_motion_windows(motion_data)

for window in windows:
    print(f"Window: {window.start_time:.1f}s - {window.end_time:.1f}s")
    print(f"Motion: {window.motion_level}, Face: {window.has_face}")
    print(f"Absorption score: {window.absorption_score:.2f}")
    print(f"Recommended: {[t.value for t in window.recommended_triggers]}")
```

---

### 5. YOLO Face Detector

**File:** `/home/user/geminivideo/services/video-agent/pro/yolo_face_detector.py`

#### Purpose
Production-grade face detection using YOLOv8. Achieves 98% accuracy vs 75% with Haar Cascade. Works on profile faces, occluded faces, and diverse demographics.

#### Key Constants
- `DEFAULT_MODEL = "yolov8n-face.pt"` - Face-specific model
- `FALLBACK_MODEL = "yolov8n.pt"` - General COCO model
- `confidence_threshold = 0.5` - Default minimum confidence

#### Main Classes and Methods

**FaceDetection** (dataclass)
- `x, y, width, height: int` - Bounding box
- `confidence: float` - Detection confidence
- `landmarks: Optional[Dict]` - Eyes, nose, mouth positions
- `emotion: Optional[str]` - Detected emotion
- `age_estimate: Optional[int]` - Estimated age
- `center: Tuple[int, int]` - Center coordinates (property)
- `area: int` - Face area in pixels (property)

**YOLOFaceDetector**
- `__init__(model_path=None, confidence_threshold=0.5, device=None)` - Initialize YOLO
- `detect_faces(frame) -> List[FaceDetection]` - Detect in single frame
- `detect_faces_video(video_path, sample_rate=1) -> Dict` - Full video analysis
- `find_best_face_moments(video_path, top_n=5) -> List[Dict]` - Find clearest faces
- `_fallback_detect(frame)` - Use Haar Cascade if YOLO unavailable

#### Input/Output
- **Input:** Video path or NumPy array (BGR image)
- **Output:** List of FaceDetection objects or video analysis dict

#### Dependencies
- Ultralytics YOLO - YOLOv8 models
- OpenCV - Image processing
- NumPy - Array operations

#### Usage Example
```python
from yolo_face_detector import YOLOFaceDetector

detector = YOLOFaceDetector(confidence_threshold=0.5)

# Single frame detection
import cv2
frame = cv2.imread("frame.jpg")
faces = detector.detect_faces(frame)

for face in faces:
    print(f"Face at ({face.x}, {face.y}) - {face.width}x{face.height}")
    print(f"Confidence: {face.confidence:.2f}")
    print(f"Area: {face.area} pixels")

# Video analysis
analysis = detector.detect_faces_video("video.mp4", sample_rate=3)
print(f"Face presence ratio: {analysis['face_presence_ratio']:.2%}")
print(f"Average faces per frame: {analysis['average_faces_per_frame']:.2f}")

# Best face moments
best = detector.find_best_face_moments("video.mp4", top_n=3)
for moment in best:
    print(f"{moment['timestamp']:.2f}s - {moment['recommendation']}")
```

---

### 6. YOLO Object Detector

**File:** `/home/user/geminivideo/services/video-agent/pro/yolo_object_detector.py`

#### Purpose
Scene understanding through object detection. Tracks product visibility, analyzes composition, detects scene types, and ensures brand safety.

#### Key Constants
- `COCO_CLASSES` - List of 80 object classes (person, car, bottle, etc.)
- `AD_RELEVANT_CATEGORIES` - Mapping to ad categories (product, lifestyle, sports, etc.)
- Default model: `yolov8n.pt` (nano - fastest)

#### Main Classes and Methods

**ObjectDetection** (dataclass)
- `class_name: str` - Object class
- `class_id: int` - COCO class ID
- `confidence: float` - Detection confidence
- `x, y, width, height: int` - Bounding box
- `category: str` - Ad-relevant category
- `center: Tuple[int, int]` - Center point (property)
- `area: int` - Object area (property)

**YOLOObjectDetector**
- `__init__(model_size='n', confidence_threshold=0.4, device=None)` - Initialize
- `detect_objects(frame) -> List[ObjectDetection]` - Detect in frame
- `analyze_video_objects(video_path, sample_rate=5) -> Dict` - Full video analysis
- `_analyze_scene_type(object_counts, category_counts) -> Dict` - Determine scene type
- `_calculate_product_visibility(timeline) -> Dict` - Product visibility metrics

#### Input/Output
- **Input:** Video path or frame array
- **Output:** Dict with object counts, scene analysis, product visibility

#### Dependencies
- Ultralytics YOLO - YOLOv8 models
- OpenCV - Video processing
- Collections - Default dict

#### Usage Example
```python
from yolo_object_detector import YOLOObjectDetector

detector = YOLOObjectDetector(model_size='n', confidence_threshold=0.4)

# Analyze video
analysis = detector.analyze_video_objects("ad.mp4", sample_rate=5)

print(f"Total objects detected: {analysis['object_summary']}")
print(f"Scene type: {analysis['scene_analysis']['primary_scene_type']}")
print(f"Product visibility: {analysis['product_visibility']['product_presence_ratio']:.2%}")
print(f"Recommendation: {analysis['product_visibility']['recommendation']}")

# Most common objects
for obj, count in analysis['most_common_objects'][:5]:
    print(f"{obj}: {count} detections")
```

---

### 7. Motion Energy Calculator

**File:** `/home/user/geminivideo/services/video-agent/pro/motion_energy.py`

#### Purpose
Calculates motion energy using optical flow, frame differencing, and block matching. Foundation for cut timing, attention prediction, beat sync, and trigger placement.

#### Key Constants
- `STATIC_THRESHOLD = 1.0` - Below this = static
- `SMOOTH_THRESHOLD = 5.0` - Below this = smooth motion
- `FAST_THRESHOLD = 15.0` - Above this = fast/chaotic motion

#### Main Classes and Methods

**MotionMethod** (Enum)
- `OPTICAL_FLOW, FRAME_DIFF, BLOCK_MATCHING, HYBRID`

**MotionFrame** (dataclass)
- `frame_idx: int, timestamp: float`
- `total_energy, mean_energy, max_energy: float`
- `horizontal_motion, vertical_motion: float`
- `dominant_direction: str` - 'left', 'right', 'up', 'down', 'mixed'
- `center_energy, edge_energy: float` - Spatial distribution
- `energy_distribution: str` - 'centered', 'peripheral', 'uniform'
- `motion_type: str` - 'static', 'smooth', 'fast', 'chaotic'

**MotionSegment** (dataclass)
- `start_frame, end_frame: int`
- `start_time, end_time: float`
- `avg_energy: float`
- `motion_type: str`

**MotionEnergyCalculator**
- `__init__(method=MotionMethod.OPTICAL_FLOW)` - Choose calculation method
- `calculate_optical_flow_energy(frame1, frame2) -> Dict` - Farneback optical flow
- `calculate_frame_diff_energy(frame1, frame2) -> Dict` - Frame differencing
- `classify_motion(mean_energy) -> str` - Classify motion type
- `analyze_frame_pair(frame1, frame2, frame_idx, fps) -> MotionFrame` - Full analysis
- `analyze_video(video_path, sample_rate=1) -> Dict` - Complete video analysis
- `find_cut_points(video_path, num_cuts=5) -> List[Dict]` - Optimal cut points

#### Input/Output
- **Input:** Video path or frame pairs
- **Output:** Dict with energy stats, motion distribution, segments, timeline, recommendations

#### Dependencies
- OpenCV - Optical flow, frame differencing
- NumPy - Array operations
- SciPy - Peak finding

#### Usage Example
```python
from motion_energy import MotionEnergyCalculator, MotionMethod

calculator = MotionEnergyCalculator(method=MotionMethod.OPTICAL_FLOW)

# Analyze video
analysis = calculator.analyze_video("video.mp4", sample_rate=1)

print(f"Energy stats: {analysis['energy_stats']}")
print(f"Motion distribution: {analysis['motion_distribution']}")
print(f"Segments: {len(analysis['segments'])}")

# Get recommendations
for rec in analysis['recommendations']:
    print(f"{rec['type']} at {rec.get('timestamp', rec.get('start_time'))}s")
    print(f"Reason: {rec['reason']}")

# Find cut points
cuts = calculator.find_cut_points("video.mp4", num_cuts=5)
for cut in cuts:
    print(f"Cut at {cut['timestamp']:.2f}s - {cut['motion_type']}")
```

---

### 8. Hook Optimizer

**File:** `/home/user/geminivideo/services/video-agent/pro/hook_optimizer.py`

#### Purpose
Analyzes and optimizes the first 3 seconds of video ads. Research shows 65% of viewers decide to watch or skip in first 3 seconds. Hooks with motion + face + text in first 1.5s have 2.3x higher view rate.

#### Key Constants
- `HOOK_DURATION = 3.0` - First 3 seconds
- `LEARNING_PERIOD_HOURS = 24` - Data collection period

#### Main Classes and Methods

**HookType** (Enum)
- `FACE_HOOK, MOTION_HOOK, TEXT_HOOK, AUDIO_HOOK, PATTERN_INTERRUPT, TRANSFORMATION, QUESTION`

**HookAnalysis** (dataclass)
- `hook_type: HookType`
- `effectiveness_score: float` - 0-100 score
- `first_face_time: Optional[float]` - When first face appears
- `first_motion_peak: Optional[float]` - First high motion
- `attention_curve: List[float]` - Frame-by-frame attention prediction
- `pattern_interrupt_score: float` - Unexpectedness (0-1)
- `improvements: List[str]` - Specific recommendations
- `optimal_cut_time: float` - Suggested first cut

**HookTemplate** (dataclass)
- `name: str` - Template name
- `hook_type: HookType`
- `structure: List[Dict]` - Timeline of elements
- `avg_performance: float` - Historical score
- `best_for: List[str]` - Industries/use cases

**HOOK_TEMPLATES** - 5 proven templates:
- Direct Address (85% avg) - Face speaks to camera
- Pattern Interrupt (78% avg) - Unexpected opening
- Motion Grab (82% avg) - Fast movement + beat
- Transformation (91% avg) - Before/after in 3s
- Question Hook (87% avg) - Direct question

**HookOptimizer**
- `__init__()` - Initialize with templates
- `analyze_hook(video_path, audio_path=None) -> HookAnalysis` - Analyze first 3s
- `_calculate_effectiveness(...) -> float` - Score 0-100
- `_predict_attention(motion_energies, face_frames) -> List[float]` - Attention curve
- `_generate_improvements(...) -> List[str]` - Specific fixes
- `get_best_template(industry) -> HookTemplate` - Industry-specific template
- `generate_hook_script(product, pain_point, template) -> Dict` - Create hook script

#### Input/Output
- **Input:** Video path, optional audio path
- **Output:** HookAnalysis with score, improvements, and attention prediction

#### Dependencies
- OpenCV - Video processing
- NumPy - Statistics

#### Usage Example
```python
from hook_optimizer import HookOptimizer, HookType

optimizer = HookOptimizer()

# Analyze existing hook
analysis = optimizer.analyze_hook("ad.mp4")
print(f"Hook type: {analysis.hook_type.value}")
print(f"Effectiveness: {analysis.effectiveness_score}/100")
print(f"First face: {analysis.first_face_time}s")
print(f"First motion peak: {analysis.first_motion_peak}s")

for improvement in analysis.improvements:
    print(f"- {improvement}")

# Get best template for industry
template = optimizer.get_best_template("fitness")
print(f"Best template: {template.name} ({template.avg_performance}% avg)")

# Generate hook script
script = optimizer.generate_hook_script(
    product="Protein Powder",
    pain_point="muscle recovery",
    template=template
)
for element in script['structure']:
    print(f"{element['time']}: {element['action']}")
```

---

### 9. CTA Optimizer

**File:** `/home/user/geminivideo/services/video-agent/pro/cta_optimizer.py`

#### Purpose
Optimizes CTA placement and presentation for maximum conversion. Research shows: CTA after urgency = 2.1x clicks, CTA during low motion = 1.8x better focus.

#### Key Constants
**Best CTA Configs** by industry:
- `ecommerce`: "Shop Now - Limited Stock" (4s, red button, urgency)
- `saas`: "Start Free Trial" (5s, green button, "Free for 14 days")
- `leadgen`: "Get Your Free Guide" (4s, blue button)
- `app`: "Download Free" (4s, green button, "4.9★ Rating")

#### Main Classes and Methods

**CTAType** (Enum)
- `BUTTON, SWIPE_UP, LINK_BIO, SHOP_NOW, LEARN_MORE, SIGN_UP, DOWNLOAD, CALL_NOW, COUNTDOWN, CUSTOM`

**CTAPosition** (Enum)
- `END` - Last 3-5 seconds
- `MID_END` - 70-85% of video
- `REPEATED` - Multiple throughout
- `EARLY_END` - 50% + end

**CTAConfig** (dataclass)
- `cta_type: CTAType`
- `text: str` - Button text
- `position: CTAPosition`
- `duration: float` - How long shown
- `urgency_text: Optional[str]` - Urgency message
- `countdown_seconds: Optional[int]`
- `button_color: str` - Default "#FF0000" (red converts best)
- `animation: str` - Default "pulse"

**CTAPlacement** (dataclass)
- `start_time, end_time: float`
- `cta_config: CTAConfig`
- `confidence_score: float`
- `reason: str` - Why this placement
- `pre_cta_sequence: List[str]` - What should happen before

**CTAOptimizer**
- `__init__()` - Initialize with configs
- `analyze_cta_timing(video_analysis) -> CTAPlacement` - Find optimal placement
- `generate_cta_sequence(video_duration, industry) -> Dict` - Full sequence
- `score_existing_cta(video_path) -> Dict` - Score current CTA
- `get_best_cta_for_goal(goal) -> CTAConfig` - Goal-specific config
- `generate_cta_variations(base_cta, count=5) -> List[str]` - A/B test variations

#### Input/Output
- **Input:** Video duration or analysis dict
- **Output:** CTAPlacement or sequence dict with timing and config

#### Dependencies
- NumPy - Statistics

#### Usage Example
```python
from cta_optimizer import CTAOptimizer

optimizer = CTAOptimizer()

# Generate CTA sequence
sequence = optimizer.generate_cta_sequence(
    video_duration=30.0,
    industry="ecommerce"
)

print(f"Sequence for {sequence['video_duration']}s video:")
for element in sequence['sequence']:
    print(f"{element['start']:.1f}s - {element['end']:.1f}s: {element['type']}")
    print(f"  Content: {element['content']}")

# Get goal-specific CTA
cta = optimizer.get_best_cta_for_goal("sales")
print(f"CTA: {cta.text}")
print(f"Color: {cta.button_color}")
print(f"Duration: {cta.duration}s")

# Generate variations
variations = optimizer.generate_cta_variations("Shop Now", count=5)
for var in variations:
    print(f"- {var}")
```

---

## ML Optimization Subsystem

### 10. Variation Generator

**File:** `/home/user/geminivideo/services/ml-service/src/variation_generator.py`

#### Purpose
Generates 50 creative variations from one concept. AI beats humans through volume and speed - testing 50 variations finds winners 10x faster than testing 5.

#### Key Constants
- `TARGET_VARIATIONS = 50` - Default variation count

#### Main Classes and Methods

**VariationType** (Enum)
- `HOOK, CTA, HEADLINE, COLOR, MUSIC, VOICE, PACING, DURATION, FORMAT`

**CreativeConcept** (dataclass)
- `id, name, description: str`
- `target_audience, industry, objective: str`
- `product, key_benefit, pain_point, social_proof: str`
- `brand_colors: List[str]`
- `tone: str` - energetic, calm, urgent, professional
- `hook_script, main_script, cta_text: str`

**CreativeVariation** (dataclass)
- `id, concept_id: str`
- `variation_number: int`
- `variations_applied: Dict[str, str]` - What changed
- `hook, headline, cta: str`
- `color_scheme: List[str]`
- `pacing: str` - fast, medium, slow
- `duration: int` - 15, 30, or 60 seconds
- `predicted_performance: float` - ML prediction
- `variation_hash: str` - Deduplication

**VariationGenerator**
- `__init__()` - Initialize with templates
- `generate_variations(concept, count=50) -> List[CreativeVariation]` - Generate variations
- `_generate_hook_variations(concept, count=10) -> List[str]` - Hook variations
- `_generate_cta_variations(concept, count=10) -> List[str]` - CTA variations
- `_generate_headline_variations(concept, count=10) -> List[str]` - Headline variations
- `_generate_color_variations(concept, count=5) -> List[List[str]]` - Color schemes
- `rank_variations(variations) -> List[CreativeVariation]` - Sort by predicted performance
- `get_top_variations(variations, count=10) -> List` - Get best N
- `export_variations(variations) -> List[Dict]` - Export for rendering

**Variation Strategies:**
1. Hook variations (10)
2. CTA variations (10)
3. Headline variations (10)
4. Color variations (5)
5. Pacing/duration combinations (9)
6. Cross-combinations (remaining to reach 50)

#### Input/Output
- **Input:** CreativeConcept object
- **Output:** List of 50 CreativeVariation objects

#### Dependencies
- Itertools - Combinations
- Hashlib - Variation hashing

#### Usage Example
```python
from variation_generator import VariationGenerator, CreativeConcept

generator = VariationGenerator()

concept = CreativeConcept(
    id="concept_001",
    name="Fitness Product Launch",
    description="New protein powder",
    target_audience="fitness enthusiasts",
    industry="health",
    objective="conversions",
    product="ProGain Protein",
    key_benefit="faster muscle recovery",
    pain_point="slow recovery after workouts",
    social_proof="10,000+ athletes",
    brand_colors=["#FF6B6B", "#4ECDC4"],
    tone="energetic",
    hook_script="Tired of slow recovery?",
    main_script="ProGain delivers 30g protein...",
    cta_text="Get 20% Off Today"
)

variations = generator.generate_variations(concept, count=50)
print(f"Generated {len(variations)} variations")

# Get top 10 by predicted performance
top = generator.get_top_variations(variations, count=10)
for var in top:
    print(f"#{var.variation_number}: {var.predicted_performance:.2f}")
    print(f"  Hook: {var.hook}")
    print(f"  CTA: {var.cta}")
    print(f"  Changes: {var.variations_applied}")
```

---

### 11. Budget Optimizer

**File:** `/home/user/geminivideo/services/ml-service/src/budget_optimizer.py`

#### Purpose
Automatically shifts budget from underperforming ads to winners. Checks hourly and makes optimal micro-adjustments vs weekly manual changes.

#### Key Constants
- `MIN_SPEND_FOR_DECISION = 50` - Minimum spend before changes
- `MIN_CONVERSIONS_FOR_DECISION = 5` - Minimum conversions needed
- `LEARNING_PERIOD_HOURS = 24` - Learning phase duration
- `MAX_BUDGET_INCREASE_PERCENT = 50` - Max 50% increase per shift
- `MAX_BUDGET_DECREASE_PERCENT = 50` - Max 50% decrease per shift
- `MIN_BUDGET = 10` - Minimum daily budget
- `TARGET_ROAS = 2.0` - Default target
- `MIN_ROAS_THRESHOLD = 1.0` - Below this = loser
- `SCALE_ROAS_THRESHOLD = 3.0` - Above this = scale aggressively

#### Main Classes and Methods

**AdStatus** (Enum)
- `LEARNING, SCALING, MAINTAINING, DECLINING, PAUSED`

**AdPerformance** (dataclass)
- `ad_id, campaign_id, creative_id: str`
- `spend, daily_budget: float`
- `impressions, clicks, conversions: int`
- `revenue: float`
- `ctr, cvr, cpa, roas: float` - Calculated metrics
- `hours_active: int`
- `status: AdStatus`
- `confidence: float`

**BudgetRecommendation** (dataclass)
- `ad_id: str`
- `current_budget, recommended_budget: float`
- `change_amount, change_percent: float`
- `reason: str` - Why change recommended
- `confidence: float`
- `priority: int` - 1 = highest

**BudgetShiftResult** (dataclass)
- `successful: bool`
- `changes_made: List[Dict]`
- `total_budget_shifted: float`
- `expected_impact: Dict`
- `execution_time: datetime`

**BudgetOptimizer**
- `__init__(target_roas=2.0)` - Initialize with target
- `analyze_ads(ads) -> Dict[str, List[AdPerformance]]` - Categorize ads
- `generate_recommendations(ads, total_budget=None) -> List[BudgetRecommendation]` - Generate shifts
- `execute_budget_shifts(recommendations, platform_client) -> BudgetShiftResult` - Execute changes
- `get_optimization_report(ads) -> Dict` - Performance report
- `simulate_optimization(ads, days=7) -> Dict` - Simulate impact

#### Input/Output
- **Input:** List of AdPerformance objects
- **Output:** List of BudgetRecommendation or BudgetShiftResult

#### Dependencies
- NumPy - Statistics
- AsyncIO - Async execution

#### Usage Example
```python
from budget_optimizer import BudgetOptimizer, AdPerformance

optimizer = BudgetOptimizer(target_roas=2.5)

# Example ad data
ads = [
    AdPerformance(
        ad_id="ad_001", campaign_id="camp_1", creative_id="creative_1",
        spend=100, daily_budget=50,
        impressions=10000, clicks=200, conversions=10, revenue=500,
        ctr=0.02, cvr=0.05, cpa=10, roas=5.0,
        hours_active=48, status=AdStatus.SCALING, confidence=0.9
    ),
    # ... more ads
]

# Analyze and categorize
categories = optimizer.analyze_ads(ads)
print(f"Winners: {len(categories['winners'])}")
print(f"Losers: {len(categories['losers'])}")

# Generate recommendations
recs = optimizer.generate_recommendations(ads)
for rec in recs:
    print(f"Ad {rec.ad_id}: ${rec.current_budget} -> ${rec.recommended_budget}")
    print(f"  Change: {rec.change_percent:+.1f}%")
    print(f"  Reason: {rec.reason}")

# Get report
report = optimizer.get_optimization_report(ads)
print(f"Overall ROAS: {report['overall_roas']:.2f}")
print(f"Potential savings: ${report['potential_savings']:.2f}")
```

---

### 12. Loser Kill Switch

**File:** `/home/user/geminivideo/services/ml-service/src/loser_kill_switch.py`

#### Purpose
Automatically pauses ads that waste money. Kills after $50 of confirmed waste vs $500 with manual approach.

#### Key Constants
- `MIN_CTR = 0.005` (0.5%) - Kill if CTR below this after 1000 impressions
- `MIN_CVR = 0.005` (0.5%) - Kill if CVR below this after 100 clicks
- `MAX_CPA_MULTIPLIER = 3.0` - Kill if CPA is 3x target after 3 conversions
- `MIN_ROAS = 0.5` - Kill if ROAS below 0.5 after $100 spend
- `NO_CONVERSION_SPEND_LIMIT = 100` - Kill if no conversions after $100

#### Main Classes and Methods

**KillReason** (Enum)
- `LOW_CTR, LOW_CVR, HIGH_CPA, NEGATIVE_ROAS, NO_CONVERSIONS, DECLINING_PERFORMANCE, BUDGET_EXHAUSTED, MANUAL`

**AdMetrics** (dataclass)
- `ad_id, campaign_id: str`
- `spend, budget: float`
- `impressions, clicks, conversions: int`
- `revenue: float`
- `ctr, cvr, cpa, roas: float`
- `hours_running: int`
- `last_conversion: Optional[datetime]`

**KillDecision** (dataclass)
- `ad_id: str`
- `should_kill: bool`
- `reason: KillReason`
- `confidence: float`
- `waste_prevented: float` - Money saved
- `recommendation: str`
- `metrics_at_kill: Dict`

**LoserKillSwitch**
- `__init__(target_cpa=50.0, target_roas=2.0)` - Initialize thresholds
- `evaluate_ad(metrics) -> KillDecision` - Evaluate single ad
- `_check_ctr(metrics) -> KillDecision` - CTR check
- `_check_cvr(metrics) -> KillDecision` - CVR check
- `_check_cpa(metrics) -> KillDecision` - CPA check
- `_check_roas(metrics) -> KillDecision` - ROAS check
- `_check_no_conversions(metrics) -> KillDecision` - Zero conversions check
- `execute_kill(decision, platform_client) -> Dict` - Execute pause
- `batch_evaluate(ads) -> List[KillDecision]` - Evaluate multiple ads
- `get_kill_report(decisions) -> Dict` - Summary report

#### Input/Output
- **Input:** AdMetrics object
- **Output:** KillDecision with should_kill boolean and reason

#### Dependencies
- AsyncIO - Async execution
- Datetime - Time tracking

#### Usage Example
```python
from loser_kill_switch import LoserKillSwitch, AdMetrics, KillReason

kill_switch = LoserKillSwitch(target_cpa=50.0, target_roas=2.0)

# Evaluate ad
metrics = AdMetrics(
    ad_id="ad_bad_001",
    campaign_id="camp_1",
    spend=120,
    budget=200,
    impressions=15000,
    clicks=30,
    conversions=0,
    revenue=0,
    ctr=0.002,
    cvr=0.0,
    cpa=0,
    roas=0,
    hours_running=72,
    last_conversion=None
)

decision = kill_switch.evaluate_ad(metrics)
if decision.should_kill:
    print(f"KILL AD {decision.ad_id}")
    print(f"Reason: {decision.reason.value}")
    print(f"Recommendation: {decision.recommendation}")
    print(f"Waste prevented: ${decision.waste_prevented:.2f}")

    # Execute kill (would call platform API)
    # result = await kill_switch.execute_kill(decision, platform_client)

# Batch evaluate
ads_to_check = [metrics1, metrics2, metrics3]
decisions = kill_switch.batch_evaluate(ads_to_check)
report = kill_switch.get_kill_report(decisions)
print(f"Total to kill: {report['total_ads_to_kill']}")
print(f"Total waste prevented: ${report['total_waste_prevented']:.2f}")
```

---

### 13. Cross-Campaign Learning

**File:** `/home/user/geminivideo/services/ml-service/src/cross_campaign_learning.py`

#### Purpose
Learns from ALL campaigns across ALL accounts. Every new campaign benefits from all previous learnings - compound knowledge vs starting from scratch.

#### Key Constants
None explicitly defined (configurable storage path)

#### Main Classes and Methods

**CampaignLearning** (dataclass)
- `campaign_id, account_id, industry, objective: str`
- `winning_patterns, failed_patterns: List[Dict]`
- `winning_hooks, failed_hooks: List[str]`
- `winning_ctas: List[str]`
- `best_audiences, best_times: List[Dict]`
- `best_roas, best_ctr, best_cpa: float`
- `total_spend: float`
- `confidence_score: float`
- `data_points: int`

**IndustryInsight** (dataclass)
- `industry: str`
- `sample_size: int`
- `avg_roas, avg_ctr, avg_cpa: float` - Benchmarks
- `top_hook_types, top_cta_types: List[Tuple[str, float]]`
- `best_video_duration: Tuple[int, int]`
- `best_posting_times: List[Dict]`
- `best_age_ranges, best_interests: List[str]`
- `confidence: float`

**CrossCampaignLearner**
- `__init__(storage_path=None)` - Initialize database
- `add_campaign_learning(learning)` - Add new learning
- `get_recommendations_for_campaign(industry, objective, target_audience) -> Dict` - Get recommendations
- `_find_similar_campaigns(industry, objective) -> List[CampaignLearning]` - Find similar
- `_aggregate_winning_hooks(campaigns) -> List[Dict]` - Aggregate hooks
- `_aggregate_winning_ctas(campaigns) -> List[Dict]` - Aggregate CTAs
- `get_learning_stats() -> Dict` - Statistics
- `export_knowledge_base() -> Dict` - Export all learnings

#### Input/Output
- **Input:** CampaignLearning objects
- **Output:** Recommendations dict with benchmarks, hooks, CTAs, patterns

#### Dependencies
- NumPy - Statistics
- Collections - Default dict
- JSON - Export/import

#### Usage Example
```python
from cross_campaign_learning import CrossCampaignLearner, CampaignLearning

learner = CrossCampaignLearner()

# Add learning from successful campaign
learning = CampaignLearning(
    campaign_id="camp_001",
    account_id="acc_1",
    industry="ecommerce",
    objective="conversions",
    winning_patterns=[{"type": "transformation", "performance": 4.2}],
    winning_hooks=["Stop scrolling! Transform your..."],
    winning_ctas=["Shop Now - 50% Off"],
    best_audiences=[{"age": "25-34", "interest": "fitness"}],
    best_times=[{"hour": 19, "day": "weekday"}],
    best_roas=4.2,
    best_ctr=0.032,
    best_cpa=12.5,
    total_spend=50000,
    total_conversions=4000,
    confidence_score=0.92,
    data_points=1000,
    extracted_at=datetime.now(),
    campaign_duration_days=30
)

learner.add_campaign_learning(learning)

# Get recommendations for new campaign
recs = learner.get_recommendations_for_campaign(
    industry="ecommerce",
    objective="conversions"
)

print(f"Expected ROAS: {recs['industry_benchmarks']['expected_roas']:.2f}")
print(f"Confidence: {recs['industry_benchmarks']['confidence']:.2f}")
print("\nRecommended hooks:")
for hook in recs['recommended_hooks'][:3]:
    print(f"  {hook['hook']} (ROAS: {hook['avg_roas']:.2f})")

# Get stats
stats = learner.get_learning_stats()
print(f"\nTotal campaigns learned: {stats['total_campaigns_learned']}")
print(f"Total spend analyzed: ${stats['total_spend_analyzed']:,.2f}")
```

---

### 14. CAPI Feedback Loop

**File:** `/home/user/geminivideo/services/ml-service/src/capi_feedback_loop.py`

#### Purpose
Wires Meta Conversion API results to model retraining. Real conversion data → prediction matching → daily retraining → continuously improving system.

#### Key Constants
- `RETRAIN_THRESHOLD = 100` - Minimum data points before retraining
- `RETRAIN_INTERVAL_HOURS = 24` - Minimum hours between retrains

#### Main Classes and Methods

**CAPIConversionEvent** (dataclass)
- `event_id, event_name: str` - Purchase, Lead, AddToCart
- `event_time: int` - Unix timestamp
- `user_data, custom_data: Dict` - Event data
- `event_source_url: str`
- `value: float` - Conversion value (property)
- `currency: str` - Currency code (property)

**PredictionActualPair** (dataclass)
- `prediction_id, campaign_id, creative_id: str`
- `predicted_ctr, predicted_roas, predicted_conversions: float/int` - Predictions
- `actual_ctr, actual_roas, actual_conversions: float/int` - Actuals from CAPI
- `actual_revenue, actual_spend: float`
- `ctr_error, roas_error, conversion_error: float` - Prediction errors

**CAPIFeedbackLoop**
- `__init__(db_session)` - Initialize with database
- `process_capi_event(event_data) -> Dict` - Process incoming webhook
- `match_predictions_to_actuals() -> List[PredictionActualPair]` - Match predictions to outcomes
- `should_retrain() -> bool` - Check if retraining needed
- `trigger_retrain() -> Dict` - Execute model retraining
- `get_feedback_metrics() -> Dict` - Get loop health metrics

**Scheduled Job:**
- `daily_retrain_job(db_session)` - Run daily retraining

#### Input/Output
- **Input:** CAPI webhook events (dict)
- **Output:** Processing result, retrain result with accuracy improvements

#### Dependencies
- SQLAlchemy - Database ORM
- AsyncIO - Async processing

#### Usage Example
```python
from capi_feedback_loop import CAPIFeedbackLoop, CAPIConversionEvent

loop = CAPIFeedbackLoop(db_session)

# Process CAPI event
event_data = {
    "event_id": "evt_123",
    "event_name": "Purchase",
    "event_time": 1234567890,
    "custom_data": {
        "value": 99.99,
        "currency": "USD",
        "campaign_id": "camp_001"
    }
}

result = await loop.process_capi_event(event_data)
print(f"Processed: {result['processed']}")
print(f"Campaign: {result['campaign_id']}")

# Check if retraining needed
if await loop.should_retrain():
    print("Triggering retraining...")
    retrain_result = await loop.trigger_retrain()
    print(f"Samples used: {retrain_result['samples_used']}")
    print(f"Avg CTR error before: {retrain_result['avg_ctr_error_before']:.4f}")

# Get metrics
metrics = loop.get_feedback_metrics()
print(f"Pending events: {metrics['pending_events']}")
```

---

### 15. Prediction Accuracy Tracker

**File:** `/home/user/geminivideo/services/ml-service/src/prediction_accuracy_tracker.py`

#### Purpose
Tracks prediction accuracy over time to detect model drift, trigger retraining when accuracy drops, and build confidence in predictions.

#### Key Constants
**Acceptable Error Percentages:**
- `CTR: 0.25` (25% error acceptable)
- `CVR: 0.30` (30% error acceptable)
- `CPA: 0.35` (35% error acceptable)
- `ROAS: 0.30` (30% error acceptable)
- `CONVERSIONS: 0.40` (40% error acceptable)

**Thresholds:**
- `RETRAIN_ACCURACY_THRESHOLD = 0.6` - Retrain if accuracy below 60%
- `MIN_SAMPLES_FOR_REPORT = 20` - Minimum samples needed

#### Main Classes and Methods

**MetricType** (Enum)
- `CTR, CVR, CPA, ROAS, CONVERSIONS`

**PredictionRecord** (dataclass)
- `prediction_id, model_type, model_version: str`
- `predicted_value: float`
- `confidence: float`
- `actual_value: Optional[float]` - Filled later
- `campaign_id, creative_id: str`
- `metric_type: MetricType`
- `error, error_percent: Optional[float]`
- `is_accurate: Optional[bool]` - Within acceptable range

**AccuracyReport** (dataclass)
- `model_type, model_version: str`
- `period_start, period_end: datetime`
- `total_predictions, predictions_with_actuals, accurate_predictions: int`
- `accuracy_rate: float` - % within acceptable range
- `mean_absolute_error, mean_absolute_percentage_error, root_mean_squared_error: float`
- `accuracy_trend: str` - 'improving', 'stable', 'declining'
- `needs_retraining: bool`
- `confidence_adjustment: float` - How much to adjust

**PredictionAccuracyTracker**
- `__init__()` - Initialize tracker
- `record_prediction(prediction_id, model_type, model_version, predicted_value, confidence, metric_type, ...)` - Record prediction
- `record_actual(prediction_id, actual_value)` - Record outcome
- `get_accuracy_report(model_type=None, model_version=None, days=7) -> AccuracyReport` - Generate report
- `should_retrain(model_type) -> Tuple[bool, str]` - Check if retraining needed
- `get_dashboard_metrics() -> Dict` - Dashboard metrics

#### Input/Output
- **Input:** Predictions and actuals
- **Output:** AccuracyReport with metrics and retraining recommendations

#### Dependencies
- NumPy - Statistics
- Datetime - Time tracking

#### Usage Example
```python
from prediction_accuracy_tracker import PredictionAccuracyTracker, MetricType

tracker = PredictionAccuracyTracker()

# Record prediction
tracker.record_prediction(
    prediction_id="pred_001",
    model_type="roas_predictor",
    model_version="v2024_01",
    predicted_value=3.5,
    confidence=0.85,
    metric_type=MetricType.ROAS,
    campaign_id="camp_001"
)

# Later, record actual
tracker.record_actual("pred_001", actual_value=3.2)

# Get report
report = tracker.get_accuracy_report(model_type="roas_predictor", days=7)
print(f"Accuracy rate: {report.accuracy_rate:.2%}")
print(f"MAPE: {report.mean_absolute_percentage_error:.2%}")
print(f"Trend: {report.accuracy_trend}")
print(f"Needs retraining: {report.needs_retraining}")

# Check if should retrain
should, reason = tracker.should_retrain("roas_predictor")
if should:
    print(f"Retrain recommended: {reason}")

# Dashboard
metrics = tracker.get_dashboard_metrics()
print(f"Total predictions: {metrics['total_predictions']}")
print(f"Overall accuracy: {metrics['overall_accuracy']:.2%}")
```

---

### 16. Auto-Retrain Pipeline

**File:** `/home/user/geminivideo/services/ml-service/src/auto_retrain_pipeline.py`

#### Purpose
Automatically retrains ML models when accuracy drops, enough data accumulated, or on schedule. Makes the system smarter every day.

#### Key Constants (RetrainConfig)
- `min_accuracy_threshold = 0.6` - Trigger if below 60%
- `min_samples_for_retrain = 100` - Need 100 new samples
- `max_samples_per_retrain = 10000` - Cap at 10k
- `daily_retrain_hour = 2` - 2 AM daily check
- `validation_split = 0.2` - 20% validation
- `min_improvement_threshold = 0.01` - Require 1% improvement
- `enable_auto_rollback = True` - Rollback if worse
- `rollback_accuracy_threshold = 0.5` - Rollback if below 50%

#### Main Classes and Methods

**RetrainTrigger** (Enum)
- `SCHEDULED, ACCURACY_DROP, DATA_THRESHOLD, DRIFT_DETECTED, MANUAL`

**RetrainStatus** (Enum)
- `PENDING, RUNNING, COMPLETED, FAILED`

**RetrainJob** (dataclass)
- `job_id, model_type: str`
- `trigger: RetrainTrigger`
- `status: RetrainStatus`
- `training_samples, validation_samples: int`
- `old_accuracy, new_accuracy, improvement: float`
- `created_at, started_at, completed_at: datetime`
- `error: Optional[str]`

**RetrainConfig** (dataclass)
- Configuration class with all thresholds

**AutoRetrainPipeline**
- `__init__(config=None)` - Initialize with config
- `check_retrain_needed(model_type, accuracy_tracker) -> Tuple[bool, RetrainTrigger, str]` - Check if needed
- `start_retrain(model_type, trigger, config) -> RetrainJob` - Start job
- `_execute_retrain(job)` - Execute pipeline
- `get_job_status(job_id) -> Optional[RetrainJob]` - Check status
- `get_training_history(model_type=None, limit=10) -> List[Dict]` - History
- `get_current_versions() -> Dict[str, str]` - Current model versions
- `run_scheduled_check()` - Check all models
- `get_pipeline_status() -> Dict` - Overall status

**Scheduled Runner:**
- `run_daily_retrain()` - Daily check function

#### Input/Output
- **Input:** Model type, accuracy tracker
- **Output:** RetrainJob with old/new accuracy and improvement

#### Dependencies
- AsyncIO - Async execution
- Datetime - Time tracking

#### Usage Example
```python
from auto_retrain_pipeline import AutoRetrainPipeline, RetrainConfig, RetrainTrigger

config = RetrainConfig(
    min_accuracy_threshold=0.6,
    min_samples_for_retrain=100,
    daily_retrain_hour=2
)

pipeline = AutoRetrainPipeline(config)

# Check if retraining needed
should_retrain, trigger, reason = await pipeline.check_retrain_needed(
    model_type="ctr_predictor",
    accuracy_tracker=accuracy_tracker
)

if should_retrain:
    print(f"Retraining triggered: {trigger.value}")
    print(f"Reason: {reason}")

    # Start retraining
    job = await pipeline.start_retrain("ctr_predictor", trigger)
    print(f"Job started: {job.job_id}")

    # Check status later
    job = pipeline.get_job_status(job.job_id)
    print(f"Status: {job.status.value}")
    if job.status == RetrainStatus.COMPLETED:
        print(f"Old accuracy: {job.old_accuracy:.2%}")
        print(f"New accuracy: {job.new_accuracy:.2%}")
        print(f"Improvement: {job.improvement:+.2%}")

# Get training history
history = pipeline.get_training_history(model_type="ctr_predictor", limit=5)
for record in history:
    print(f"{record['job_id']}: {record['new_accuracy']:.2%} ({record['trigger']})")

# Run scheduled check for all models
await pipeline.run_scheduled_check()
```

---

## Data Intelligence Subsystem

### 17. Winning Patterns Database

**File:** `/home/user/geminivideo/services/drive-intel/services/winning_patterns_db.py`

#### Purpose
Stores patterns extracted from high-performing ads to train models and generate winning variations. This is the KNOWLEDGE that makes the AI smart.

#### Key Constants
- `COCO_CLASSES` - 80 object classes
- `AD_RELEVANT_CATEGORIES` - Mapping to ad categories

#### Main Classes and Methods

**AdPlatform** (Enum)
- `META, GOOGLE, TIKTOK, YOUTUBE, LINKEDIN`

**AdFormat** (Enum)
- `VIDEO, IMAGE, CAROUSEL, STORIES, REELS`

**AdObjective** (Enum)
- `CONVERSIONS, TRAFFIC, AWARENESS, LEADS, SALES, APP_INSTALLS`

**HookPattern** (dataclass)
- `hook_type: str` - face, motion, text, question, transformation
- `first_element: str` - What appears first
- `timing: Dict[str, float]` - Element timing
- `text_used, emotion, motion_level: str`

**VisualPattern** (dataclass)
- `color_palette, dominant_colors: List[str]`
- `composition: str` - centered, rule-of-thirds, dynamic
- `face_ratio: float` - % time faces shown
- `text_overlay_style, transitions: str/List`
- `aspect_ratio: str`

**AudioPattern** (dataclass)
- `has_music, has_voiceover: bool`
- `music_genre, voice_gender, voice_energy: str`
- `beat_sync: bool`
- `audio_hooks: List[str]`

**CTAPattern** (dataclass)
- `cta_type, cta_text: str`
- `cta_timing: float` - % into video
- `urgency_used, scarcity_used: bool`
- `button_color, animation: str`

**WinningAdPattern** (dataclass)
- `id, industry: str`
- `source_platform: AdPlatform`
- `ad_format: AdFormat`
- `objective: AdObjective`
- `estimated_spend, estimated_impressions: float/int`
- `estimated_ctr, estimated_roas: float`
- `hook_pattern: HookPattern`
- `visual_pattern: VisualPattern`
- `audio_pattern: AudioPattern`
- `cta_pattern: CTAPattern`
- `duration_seconds: float`
- `confidence_score: float`
- `tags: List[str]`

**WinningPatternsDB**
- `__init__(storage_path=None)` - Initialize database
- `add_pattern(pattern) -> str` - Add winning pattern
- `get_pattern(pattern_id) -> Optional[WinningAdPattern]` - Get by ID
- `find_patterns(industry, platform, objective, hook_type, min_roas, limit) -> List` - Search
- `get_top_performers(limit=10) -> List` - Top by ROAS
- `get_hook_statistics() -> Dict` - Hook type performance
- `get_industry_benchmarks(industry) -> Dict` - Industry metrics
- `extract_creative_dna(patterns) -> Dict` - Common DNA from patterns
- `seed_with_examples()` - Seed with example patterns

#### Input/Output
- **Input:** WinningAdPattern objects
- **Output:** Pattern lists, benchmarks, statistics

#### Dependencies
- JSON - Storage
- Collections - Indexing
- Hashlib - ID generation

#### Usage Example
```python
from winning_patterns_db import (
    WinningPatternsDB, WinningAdPattern, AdPlatform, AdFormat,
    AdObjective, HookPattern, VisualPattern, AudioPattern, CTAPattern
)

db = WinningPatternsDB()

# Add a winning pattern
pattern = WinningAdPattern(
    id="",
    source_platform=AdPlatform.META,
    ad_format=AdFormat.REELS,
    objective=AdObjective.SALES,
    industry="ecommerce",
    estimated_spend=50000,
    estimated_impressions=2000000,
    estimated_ctr=0.032,
    estimated_roas=4.2,
    hook_pattern=HookPattern(
        hook_type="transformation",
        first_element="before_state",
        timing={"before": 0.0, "transition": 1.5, "after": 2.0},
        text_used="Watch this transformation",
        emotion="surprise",
        motion_level="high"
    ),
    visual_pattern=VisualPattern(
        color_palette=["#FF6B6B", "#4ECDC4"],
        dominant_colors=["red", "teal"],
        composition="centered",
        face_ratio=0.4,
        text_overlay_style="bold_center",
        transitions=["swipe", "zoom"],
        aspect_ratio="9:16"
    ),
    audio_pattern=AudioPattern(
        has_music=True,
        music_genre="upbeat_pop",
        has_voiceover=True,
        voice_gender="female",
        voice_energy="excited",
        beat_sync=True,
        audio_hooks=["beat_drop"]
    ),
    cta_pattern=CTAPattern(
        cta_type="shop_now",
        cta_text="Shop Now - 50% Off",
        cta_timing=0.85,
        urgency_used=True,
        scarcity_used=True,
        button_color="#FF4444",
        animation="pulse"
    ),
    duration_seconds=15,
    extracted_at=datetime.now(),
    confidence_score=0.92,
    tags=["transformation", "ecommerce", "high_roas"]
)

pattern_id = db.add_pattern(pattern)

# Find patterns
patterns = db.find_patterns(
    industry="ecommerce",
    platform=AdPlatform.META,
    min_roas=3.0,
    limit=10
)

# Get benchmarks
benchmarks = db.get_industry_benchmarks("ecommerce")
print(f"Average ROAS: {benchmarks['roas']['avg']:.2f}")
print(f"Top hook types: {benchmarks['top_hook_types']}")

# Extract creative DNA
dna = db.extract_creative_dna(patterns)
print(f"Dominant hook: {dna['dominant_hook']}")
print(f"Common colors: {dna['common_colors']}")
```

---

## AI Generation Subsystem

### 18. Runway Gen-3 Integration

**File:** `/home/user/geminivideo/services/titan-core/integrations/runway_gen3.py`

#### Purpose
Generate AI video from text prompts or images using Runway Gen-3 Alpha. Enables creating product shots, lifestyle scenes, and B-roll without filming.

#### Key Constants
- `RUNWAY_API_URL = "https://api.runwayml.com/v1"`
- `RUNWAY_API_KEY` - From environment variable

#### Main Classes and Methods

**RunwayModel** (Enum)
- `GEN3_ALPHA, GEN3_ALPHA_TURBO, GEN2`

**VideoAspectRatio** (Enum)
- `LANDSCAPE = "16:9"`
- `PORTRAIT = "9:16"`
- `SQUARE = "1:1"`
- `WIDESCREEN = "21:9"`

**GenerationRequest** (dataclass)
- `prompt: str` - Text description
- `model: RunwayModel` - Default GEN3_ALPHA_TURBO
- `duration: int` - 5 or 10 seconds
- `aspect_ratio: VideoAspectRatio` - Default PORTRAIT
- `seed: Optional[int]` - Reproducibility
- `image_url: Optional[str]` - For image-to-video
- `style_reference: Optional[str]` - Style guide

**GenerationResult** (dataclass)
- `task_id: str` - Generation task ID
- `status: str` - pending, processing, completed, failed
- `video_url: Optional[str]` - URL to generated video
- `duration, generation_time: float`
- `cost_credits: float` - Estimated cost
- `prompt_used: str`
- `error: Optional[str]`

**RunwayGen3Client**
- `__init__(api_key=None)` - Initialize with API key
- `generate_video(request) -> GenerationResult` - Generate video
- `generate_product_shot(product_image, scene_description) -> GenerationResult` - Product video
- `generate_lifestyle_scene(description, mood) -> GenerationResult` - Lifestyle B-roll
- `generate_variations(base_prompt, count=3) -> List[GenerationResult]` - Multiple variations
- `_poll_for_completion(client, task_id, headers, max_wait=300)` - Poll API
- `_calculate_credits(duration, model) -> float` - Estimate cost

**Moods for lifestyle scenes:**
- `energetic` - Dynamic, vibrant, fast-paced
- `calm` - Slow motion, soft lighting, peaceful
- `luxury` - Elegant, golden lighting, premium
- `playful` - Bouncy, bright colors, fun

#### Input/Output
- **Input:** GenerationRequest with prompt, duration, aspect ratio
- **Output:** GenerationResult with video URL or error

#### Dependencies
- httpx - Async HTTP client
- AsyncIO - Async operations

#### Usage Example
```python
from runway_gen3 import RunwayGen3Client, GenerationRequest, VideoAspectRatio

client = RunwayGen3Client()

# Generate from text
request = GenerationRequest(
    prompt="Professional product showcase of sleek water bottle, "
           "rotating on white background, studio lighting, 4k quality",
    duration=5,
    aspect_ratio=VideoAspectRatio.PORTRAIT
)

result = await client.generate_video(request)
if result.status == "completed":
    print(f"Video URL: {result.video_url}")
    print(f"Generation time: {result.generation_time:.1f}s")
    print(f"Cost: {result.cost_credits:.4f} credits")

# Generate product shot from image
product_result = await client.generate_product_shot(
    product_image="https://example.com/bottle.jpg",
    scene_description="Rotating smoothly on marble surface with morning sunlight"
)

# Generate lifestyle scene
lifestyle_result = await client.generate_lifestyle_scene(
    description="Person jogging through park at sunrise",
    mood="energetic"
)

# Generate variations
variations = await client.generate_variations(
    base_prompt="Modern office workspace with laptop",
    count=3
)
for i, var in enumerate(variations):
    print(f"Variation {i+1}: {var.video_url}")
```

---

### 19. ElevenLabs Voice Integration

**File:** `/home/user/geminivideo/services/titan-core/integrations/elevenlabs_voice.py`

#### Purpose
Professional voiceovers and voice cloning for video ads. Enables generating voiceovers from scripts, cloning voices for brand consistency, and multilingual voiceovers.

#### Key Constants
- `ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"`
- `ELEVENLABS_API_KEY` - From environment variable

**Voice Presets:**
- `adam` - Deep male voice
- `rachel` - Calm female voice
- `domi` - Young female, energetic
- `bella` - Soft female voice
- `elli` - Young female, American
- `josh` - Deep male, American
- `arnold` - Strong male voice
- `sam` - Young male, American

#### Main Classes and Methods

**VoiceModel** (Enum)
- `ELEVEN_TURBO_V2` - Fast, good quality
- `ELEVEN_MULTILINGUAL_V2` - Best for languages
- `ELEVEN_MONOLINGUAL_V1` - English optimized

**VoiceStyle** (Enum)
- `CONVERSATIONAL, NARRATIVE, NEWS, PROMOTIONAL, EXCITED, CALM`

**VoiceSettings** (dataclass)
- `stability: float = 0.5` - 0-1, higher = more consistent
- `similarity_boost: float = 0.75` - 0-1, match to original
- `style: float = 0.5` - 0-1, style exaggeration
- `use_speaker_boost: bool = True`

**VoiceOverRequest** (dataclass)
- `text: str` - Script to narrate
- `voice_id: str` - ElevenLabs voice ID
- `model: VoiceModel` - Default ELEVEN_TURBO_V2
- `settings: VoiceSettings` - Optional custom settings
- `output_format: str` - Default "mp3_44100_128"

**VoiceOverResult** (dataclass)
- `audio_data: bytes` - Generated audio
- `audio_url: Optional[str]` - URL if uploaded
- `duration_seconds: float` - Estimated duration
- `characters_used: int` - Character count
- `generation_time: float` - API time
- `error: Optional[str]`

**ElevenLabsClient**
- `__init__(api_key=None)` - Initialize with API key
- `generate_voiceover(request) -> VoiceOverResult` - Generate audio
- `get_available_voices() -> List[Dict]` - List available voices
- `clone_voice(name, audio_files, description) -> Optional[str]` - Clone voice
- `generate_ad_voiceover(script, voice_type) -> VoiceOverResult` - Optimized for ads
- `generate_multilingual(text, voice_id, language) -> VoiceOverResult` - Multi-language
- `estimate_cost(text) -> Dict` - Cost estimation

**Voice Types for Ads:**
- `energetic_male, energetic_female`
- `calm_male, calm_female`
- `young_female, young_male`
- `authoritative`

#### Input/Output
- **Input:** VoiceOverRequest with text and voice settings
- **Output:** VoiceOverResult with audio bytes or error

#### Dependencies
- httpx - Async HTTP client
- AsyncIO - Async operations
- Base64 - Audio encoding

#### Usage Example
```python
from elevenlabs_voice import ElevenLabsClient, VoiceOverRequest, VoiceSettings, VOICE_PRESETS

client = ElevenLabsClient()

# Generate voiceover
request = VoiceOverRequest(
    text="Transform your fitness journey with ProGain Protein. "
         "Get 30 grams of pure protein in every delicious shake. "
         "Shop now and save 20 percent.",
    voice_id=VOICE_PRESETS["josh"],
    settings=VoiceSettings(
        stability=0.6,
        similarity_boost=0.8,
        style=0.7
    )
)

result = await client.generate_voiceover(request)
if result.error is None:
    # Save audio
    with open("voiceover.mp3", "wb") as f:
        f.write(result.audio_data)
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Characters: {result.characters_used}")

# Generate ad-optimized voiceover
ad_result = await client.generate_ad_voiceover(
    script="Stop scrolling! Tired of slow muscle recovery? "
           "ProGain delivers results in half the time. Limited offer!",
    voice_type="energetic_male"
)

# Clone a voice
with open("sample1.mp3", "rb") as f1, open("sample2.mp3", "rb") as f2:
    voice_id = await client.clone_voice(
        name="Brand Voice",
        audio_files=[f1.read(), f2.read()],
        description="Official brand spokesperson voice"
    )
    if voice_id:
        print(f"Voice cloned: {voice_id}")

# Estimate cost
estimate = client.estimate_cost("This is a test script for cost estimation.")
print(f"Characters: {estimate['characters']}")
print(f"Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
```

---

## Integration Architecture

### How Components Work Together

1. **Video Analysis Pipeline**
   - Motion Moment SDK → Face-Weighted Analyzer → Motion Energy
   - Precision AV Sync ← Audio analysis
   - YOLO Face/Object Detectors → Scene understanding
   - Psychological Timing ← Motion data
   - Hook/CTA Optimizers ← All analysis data

2. **ML Optimization Loop**
   - Variation Generator → Creates 50 variations
   - Budget Optimizer → Shifts spend to winners
   - Loser Kill Switch → Stops waste
   - CAPI Feedback → Real conversion data
   - Prediction Tracker → Monitors accuracy
   - Auto-Retrain → Improves models
   - Cross-Campaign Learning → Compounds knowledge

3. **Data Flow**
   - Winning Patterns DB ← Stores successful patterns
   - All ML components → Query patterns for predictions
   - CAPI events → Feedback Loop → Retrain Pipeline
   - Predictions → Accuracy Tracker → Retrain decisions

4. **AI Generation**
   - Runway Gen-3 ← Creates video scenes
   - ElevenLabs ← Generates voiceovers
   - Both → Feed into video assembly pipeline

---

## Performance Characteristics

### Video Analysis (Real-time capable)
- Motion Moment SDK: ~1-2x real-time (30s video in 30-60s)
- Face Detection (YOLO): 60+ FPS on GPU
- Object Detection (YOLO): 30+ FPS on GPU
- Motion Energy: ~1x real-time
- AV Sync: ~2-3x real-time

### ML Optimization (Background/scheduled)
- Variation Generation: <1s for 50 variations
- Budget Optimization: <100ms for 100 ads
- Kill Switch Evaluation: <10ms per ad
- CAPI Processing: <50ms per event
- Model Retraining: 1-4 hours (scheduled daily)

### AI Generation (API-dependent)
- Runway Gen-3: 60-120s for 5s video
- ElevenLabs: 1-3s for 30s audio

---

## Configuration & Environment Variables

### Required Environment Variables
```bash
# Runway Gen-3
export RUNWAY_API_KEY="your_runway_key"

# ElevenLabs
export ELEVENLABS_API_KEY="your_elevenlabs_key"

# Meta CAPI (for feedback loop)
export META_ACCESS_TOKEN="your_meta_token"
export META_PIXEL_ID="your_pixel_id"
```

### Optional Configurations
```python
# Video Analysis
MOTION_WINDOW_SIZE = 30  # frames
FACE_DETECTION_CONFIDENCE = 0.5
SYNC_TOLERANCE = 0.1  # seconds

# ML Optimization
TARGET_ROAS = 2.0
MIN_BUDGET = 10
RETRAIN_THRESHOLD = 100  # samples

# Storage
PATTERNS_DB_PATH = "/data/patterns"
```

---

## Error Handling & Logging

All components use Python's `logging` module:

```python
import logging
logger = logging.getLogger(__name__)

# Set log level
logging.basicConfig(level=logging.INFO)

# Each component logs:
logger.info("...")    # Normal operations
logger.warning("...")  # Issues that don't stop execution
logger.error("...")    # Failures
```

---

## Testing & Validation

### Unit Tests
Each component should have tests for:
- Core functionality
- Edge cases
- Error handling
- Performance benchmarks

### Integration Tests
- End-to-end video analysis
- ML pipeline (variation → budget → kill → retrain)
- CAPI feedback loop
- AI generation pipeline

### Performance Tests
- Video processing speed
- Prediction latency
- API response times
- Database query performance

---

## Maintenance & Updates

### Model Updates
- YOLO models: Update when new YOLOv8 versions released
- ML predictors: Auto-retrain daily via pipeline
- Pattern database: Continuous learning from campaigns

### API Integrations
- Runway: Check API updates monthly
- ElevenLabs: Monitor voice model improvements
- Meta CAPI: Track API version changes

### Performance Monitoring
- Track processing times
- Monitor prediction accuracy
- Watch API costs
- Alert on anomalies

---

## Troubleshooting Guide

### Common Issues

**Video Processing Slow**
- Check if GPU is being used: `torch.cuda.is_available()`
- Reduce sample_rate in video analysis
- Use smaller YOLO models (n vs s/m/l)

**YOLO Models Not Loading**
- Ensure ultralytics installed: `pip install ultralytics`
- Download models: Models auto-download on first use
- Check disk space for model cache

**API Errors (Runway/ElevenLabs)**
- Verify API keys set in environment
- Check API quota/credits
- Monitor rate limits
- Use mock clients for testing

**Prediction Accuracy Low**
- Check if enough training data (>100 samples)
- Trigger manual retrain
- Verify CAPI feedback loop working
- Review feature quality

**Budget Optimizer Not Shifting**
- Verify ads have enough spend/conversions
- Check learning period passed (24h)
- Review ROAS thresholds
- Ensure platform API connected

---

## Support & Resources

### Documentation
- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [Runway API Docs](https://docs.runwayml.com/)
- [ElevenLabs API Docs](https://docs.elevenlabs.io/)
- [Meta CAPI Docs](https://developers.facebook.com/docs/marketing-api/conversions-api/)

### Internal Resources
- Architecture diagrams: `/docs/architecture/`
- API examples: `/examples/`
- Performance benchmarks: `/docs/benchmarks/`

---

**Document Version:** 1.0
**Last Updated:** 2025-12-06
**Total Components Documented:** 19
**Total Lines of Code Analyzed:** ~7,500+
