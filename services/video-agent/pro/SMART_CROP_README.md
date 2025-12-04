# Smart Crop System - Pro-Grade Video Ads

Complete intelligent video cropping system with face/object tracking for creating professional social media content.

## Features

### Core Detection & Tracking
- **Face Detection**: OpenCV DNN (Caffe ResNet-based) with Haar Cascade fallback
- **Face Tracking**: Multi-face handling with center-of-mass tracking
- **Object Detection**: YOLO (v3/v4, tiny variants)
- **Motion Detection**: Optical flow and frame differencing
- **Speaker Focus**: Audio-aware speaker tracking

### Smart Cropping
- **Auto-Reframe**: Convert between aspect ratios intelligently
  - 16:9 → 9:16 (YouTube to TikTok/Reels)
  - 16:9 → 1:1 (YouTube to Instagram feed)
  - 16:9 → 4:5 (Instagram Reels)
  - Any custom aspect ratio
- **Smooth Panning**: No jerky movements with easing functions
- **Safe Zone Awareness**: Keep subjects centered
- **Ken Burns Effect**: Cinematic pan and zoom on images

### Production-Ready
- **Real OpenCV Code**: No mock data, production-grade implementation
- **FFmpeg Integration**: Generate optimized crop/scale filters
- **Performance Optimized**: Frame sampling and efficient processing
- **Batch Processing**: Multi-format conversion in one pass

---

## Installation

### 1. Install Dependencies

```bash
pip install opencv-python opencv-contrib-python numpy
```

### 2. Download Detection Models

```bash
# Download face detection models (required)
python download_models.py

# Download YOLO models (optional, for object detection)
python download_models.py --yolo-model yolov3-tiny
```

**Model Files**:
- Face Detection: `models/face_detection/deploy.prototxt` + `res10_300x300_ssd_iter_140000.caffemodel`
- YOLO: `models/yolo/yolov3-tiny.{weights,cfg}` + `coco.names`

### 3. Verify Installation

```bash
python smart_crop.py
```

---

## Quick Start

### Example 1: YouTube to TikTok

Convert 16:9 landscape video to 9:16 portrait with face tracking:

```python
from smart_crop import create_smart_crop_pipeline, AspectRatio

ffmpeg_cmd = create_smart_crop_pipeline(
    video_path="input.mp4",
    output_path="output_tiktok.mp4",
    target_aspect=AspectRatio.PORTRAIT_9_16,
    output_resolution=(1080, 1920),
    detect_faces=True,
    detect_motion=True
)

# Execute FFmpeg command
import subprocess
subprocess.run(ffmpeg_cmd, shell=True)
```

### Example 2: YouTube to Instagram Square

```python
ffmpeg_cmd = create_smart_crop_pipeline(
    video_path="input.mp4",
    output_path="output_instagram.mp4",
    target_aspect=AspectRatio.SQUARE_1_1,
    output_resolution=(1080, 1080),
    detect_faces=True,
    detect_motion=True
)
```

### Example 3: Custom Processing

For maximum control, process frames directly:

```python
from smart_crop import SmartCropTracker, AspectRatio
import cv2

# Initialize tracker
tracker = SmartCropTracker(
    target_aspect=AspectRatio.PORTRAIT_9_16,
    smoothing_window=15,
    safe_zone_ratio=0.8
)
tracker.initialize()

# Open video
cap = cv2.VideoCapture("input.mp4")
crop_regions = []

frame_number = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Process frame
    crop_region = tracker.process_frame(
        frame,
        frame_number,
        detect_faces=True,
        detect_objects=False,
        detect_motion=True
    )

    crop_regions.append(crop_region)
    frame_number += 1

cap.release()

# Generate FFmpeg filter
filter_str = tracker.generate_simple_crop_filter(
    crop_regions,
    output_width=1080,
    output_height=1920
)

print(f"FFmpeg filter: {filter_str}")
```

---

## Aspect Ratios

Supported aspect ratios with optimal resolutions:

| Platform | Aspect Ratio | Resolution | Usage |
|----------|--------------|------------|-------|
| TikTok | 9:16 | 1080x1920 | Vertical video |
| Instagram Reels | 9:16 | 1080x1920 | Vertical video |
| Instagram Feed | 1:1 | 1080x1080 | Square posts |
| Instagram Portrait | 4:5 | 1080x1350 | Portrait posts |
| YouTube | 16:9 | 1920x1080 | Landscape video |
| YouTube Shorts | 9:16 | 1080x1920 | Vertical shorts |

### Custom Aspect Ratios

```python
from smart_crop import AspectRatio

# Built-in ratios
AspectRatio.PORTRAIT_9_16   # 9:16 (0.5625)
AspectRatio.SQUARE_1_1      # 1:1 (1.0)
AspectRatio.PORTRAIT_4_5    # 4:5 (0.8)
AspectRatio.LANDSCAPE_16_9  # 16:9 (1.778)
AspectRatio.LANDSCAPE_21_9  # 21:9 (2.333)
```

---

## Detection Features

### Face Detection

**Priority**: Highest (primary subject)

**Configuration**:
```python
face_detector = FaceDetector()
face_detector.load_model()
face_detector.confidence_threshold = 0.5  # Adjust sensitivity

faces = face_detector.detect(frame)
```

**Multi-Face Handling**:
- Single face: Center on face
- Multiple faces: Center on center-of-mass of all faces
- Prioritizes largest/most prominent face

### Object Detection (YOLO)

**Priority**: Medium (when no faces detected)

**Configuration**:
```python
object_detector = ObjectDetector("yolov3-tiny")
object_detector.load_model()
object_detector.confidence_threshold = 0.5
object_detector.nms_threshold = 0.4

# Detect specific objects
objects = object_detector.detect(
    frame,
    target_classes=["person", "bottle", "laptop", "cell phone"]
)
```

**COCO Classes** (80 objects): person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, traffic light, fire hydrant, stop sign, parking meter, bench, bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket, bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant, bed, dining table, toilet, tv, laptop, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors, teddy bear, hair drier, toothbrush.

### Motion Detection

**Priority**: Low (fallback when no faces/objects)

**Configuration**:
```python
motion_detector = MotionDetector(history_size=10)
motion_detector.motion_threshold = 25  # Sensitivity

motion_score, motion_bbox = motion_detector.detect_motion(frame)
```

---

## Smoothing & Easing

### Smoothing Window

Control how many frames are used for smoothing camera movement:

```python
tracker = SmartCropTracker(
    smoothing_window=15  # More frames = smoother but slower response
)
```

- **Small (5-10)**: Fast response, good for action/sports
- **Medium (10-20)**: Balanced, good for interviews/talking heads
- **Large (20-30)**: Very smooth, good for slow-moving subjects

### Easing Functions

Control the interpolation curve:

```python
from smart_crop import SmoothingFilter, EasingFunction

smoother = SmoothingFilter(
    window_size=15,
    easing=EasingFunction.EASE_IN_OUT  # Smooth acceleration/deceleration
)
```

**Available Easing**:
- `LINEAR`: Constant speed
- `EASE_IN`: Slow start, fast end
- `EASE_OUT`: Fast start, slow end
- `EASE_IN_OUT`: Smooth start and end (recommended)
- `SMOOTH`: Smoothstep function

---

## Advanced Features

### Ken Burns Effect

Create cinematic pan and zoom on static images:

```python
from smart_crop import KenBurnsEffect

kb = KenBurnsEffect(duration=5.0, fps=30.0)

filter_str = kb.generate_effect(
    image_width=1920,
    image_height=1080,
    target_width=1080,
    target_height=1920,
    zoom_start=1.0,      # Starting zoom level
    zoom_end=1.3,        # Ending zoom (1.3 = 30% zoom in)
    pan_start=(0.3, 0.3),  # Start position (0-1, 0-1)
    pan_end=(0.7, 0.7)     # End position
)

# FFmpeg command
ffmpeg_cmd = f"ffmpeg -loop 1 -i image.jpg -vf '{filter_str}' -t 5 output.mp4"
```

### Speaker Focus

Track the speaking person using audio energy:

```python
from smart_crop import SpeakerFocusTracker

speaker_tracker = SpeakerFocusTracker(audio_threshold=0.01)

# For each frame
speaker_face = speaker_tracker.detect_speaker(
    faces=detected_faces,
    audio_energy=current_audio_energy,  # 0.0-1.0
    frame_number=frame_num
)
```

### Safe Zone

Keep subjects in the center area of the frame:

```python
tracker = SmartCropTracker(
    safe_zone_ratio=0.8  # Keep subject in center 80% of frame
)
```

- **0.5**: Very loose, subject can move to edges
- **0.8**: Balanced, recommended for most content
- **0.95**: Very tight, subject always centered

---

## Performance Optimization

### Frame Sampling

Process every Nth frame to improve speed:

```python
ffmpeg_cmd = create_smart_crop_pipeline(
    video_path="input.mp4",
    output_path="output.mp4",
    sample_interval=5  # Process every 5th frame
)
```

**Recommendations**:
- High quality: `sample_interval=1` (every frame)
- Balanced: `sample_interval=3-5`
- Fast preview: `sample_interval=10`

### Model Selection

Choose faster models for real-time processing:

```python
# Fast: Haar Cascade (built-in, no download needed)
face_detector = FaceDetector()
face_detector.load_model()  # Falls back to Haar if DNN not available

# Medium: OpenCV DNN (ResNet-based)
# Requires model download

# Fast object detection: YOLO-tiny
object_detector = ObjectDetector("yolov3-tiny")

# Accurate but slower: Full YOLO
object_detector = ObjectDetector("yolov3")
```

### Benchmarking

Test performance on your hardware:

```bash
python smart_crop_examples.py benchmark
```

---

## Use Cases

### 1. Social Media Content Creation

**Scenario**: Convert long-form YouTube videos to short-form TikTok/Reels

```python
ffmpeg_cmd = create_smart_crop_pipeline(
    video_path="youtube_video.mp4",
    output_path="tiktok_version.mp4",
    target_aspect=AspectRatio.PORTRAIT_9_16,
    output_resolution=(1080, 1920),
    detect_faces=True,
    detect_motion=True,
    sample_interval=3
)
```

### 2. Product Showcase Videos

**Scenario**: Track products in advertising videos

```python
tracker = SmartCropTracker(target_aspect=AspectRatio.PORTRAIT_9_16)
tracker.initialize()

# Process with object detection
crop_region = tracker.process_frame(
    frame,
    frame_number,
    detect_faces=False,
    detect_objects=True,
    target_objects=["bottle", "laptop", "cell phone", "handbag"]
)
```

### 3. Interview/Talking Head

**Scenario**: Keep speaker centered during interview

```python
tracker = SmartCropTracker(
    target_aspect=AspectRatio.PORTRAIT_9_16,
    smoothing_window=20,  # Very smooth
    safe_zone_ratio=0.85   # Keep face centered
)
```

### 4. Sports/Action Highlights

**Scenario**: Follow fast-moving action

```python
tracker = SmartCropTracker(
    target_aspect=AspectRatio.PORTRAIT_9_16,
    smoothing_window=8,   # Fast response
    safe_zone_ratio=0.7    # Allow more movement
)

crop_region = tracker.process_frame(
    frame,
    frame_number,
    detect_faces=False,
    detect_objects=False,
    detect_motion=True  # Focus on motion
)
```

### 5. Batch Multi-Platform Export

**Scenario**: Convert one video to all platform formats

```python
from smart_crop_examples import example_7_multi_format_batch

commands = example_7_multi_format_batch(
    input_video="master_video.mp4",
    output_dir="exports"
)

# Generates: tiktok, reels, instagram, youtube versions
```

---

## FFmpeg Filter Generation

### Simple Crop Filter

Average crop position (fastest):

```python
filter_str = tracker.generate_simple_crop_filter(
    crop_regions,
    output_width=1080,
    output_height=1920
)
# Output: "crop=606:1080:657:0,scale=1080:1920"
```

### Animated Crop Filter

Smooth interpolation between positions:

```python
filter_str = tracker.generate_ffmpeg_filter(
    crop_regions,
    fps=30.0,
    output_width=1080,
    output_height=1920
)
# Output: Complex expression with temporal interpolation
```

---

## Troubleshooting

### Models Not Found

**Error**: `Face detection model not found`

**Solution**:
```bash
python download_models.py
```

The system will fall back to Haar Cascade if DNN models are unavailable.

### Slow Performance

**Solutions**:
1. Increase `sample_interval` (process fewer frames)
2. Use YOLO-tiny instead of full YOLO
3. Disable object detection if not needed
4. Reduce `smoothing_window`
5. Lower input video resolution

### Poor Tracking

**Solutions**:
1. Adjust `confidence_threshold` for detectors
2. Increase `smoothing_window` for smoother tracking
3. Adjust `safe_zone_ratio` to control centering
4. Enable multiple detection methods (faces + motion)
5. Check lighting and image quality

### Memory Issues

**Solutions**:
1. Process video in chunks
2. Increase `sample_interval`
3. Use smaller input resolution
4. Free crop_regions list periodically

---

## API Reference

### SmartCropTracker

Main class for smart cropping.

**Constructor**:
```python
SmartCropTracker(
    target_aspect: AspectRatio = AspectRatio.PORTRAIT_9_16,
    smoothing_window: int = 15,
    safe_zone_ratio: float = 0.8
)
```

**Methods**:
- `initialize()`: Load detection models
- `process_frame()`: Process single frame
- `generate_ffmpeg_filter()`: Generate animated crop filter
- `generate_simple_crop_filter()`: Generate static crop filter

### FaceDetector

Face detection with OpenCV DNN.

**Constructor**:
```python
FaceDetector(
    model_path: Optional[str] = None,
    config_path: Optional[str] = None
)
```

**Methods**:
- `load_model()`: Load detection model
- `detect(frame)`: Detect faces in frame

### ObjectDetector

YOLO object detection.

**Constructor**:
```python
ObjectDetector(model_type: str = "yolov3-tiny")
```

**Methods**:
- `load_model()`: Load YOLO model
- `detect(frame, target_classes)`: Detect objects

### KenBurnsEffect

Create pan and zoom effects.

**Constructor**:
```python
KenBurnsEffect(duration: float = 5.0, fps: float = 30.0)
```

**Methods**:
- `generate_effect()`: Generate zoompan filter

---

## Examples

See `smart_crop_examples.py` for 10 complete examples:

```bash
python smart_crop_examples.py
```

1. YouTube to TikTok
2. YouTube to Instagram Square
3. YouTube to Instagram Reels
4. Custom Face Tracking
5. Object Tracking for Products
6. Ken Burns Effect
7. Multi-Format Batch
8. Action/Sports Tracking
9. Visualize Tracking
10. Performance Benchmark

---

## License

MIT License

---

## Credits

- OpenCV: Face detection and video processing
- YOLO: Object detection (Joseph Redmon)
- FFmpeg: Video encoding and filtering

---

## Support

For issues, questions, or feature requests, see the main project repository.

**System Requirements**:
- Python 3.7+
- OpenCV 4.x
- NumPy
- FFmpeg (for video encoding)

**Tested Platforms**:
- Linux (Ubuntu 20.04+)
- macOS (10.15+)
- Windows 10+
