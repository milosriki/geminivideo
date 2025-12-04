# Visual Pattern Extractor - Quick Reference

## Quick Start

```python
from services.visual_patterns import VisualPatternExtractor
import cv2

# Initialize
extractor = VisualPatternExtractor()

# Load frame
frame = cv2.imread('frame.jpg')

# Extract features (2048-dim)
features = extractor.extract_features(frame)

# Classify pattern
result = extractor.classify_visual_pattern(frame)
print(f"{result.primary_pattern}: {result.confidence:.2%}")
```

## 10 Visual Patterns

1. **face_closeup** - Close-up shots of faces/people
2. **before_after** - Before/after comparisons
3. **text_heavy** - Heavy text overlays
4. **product_focus** - Product-focused shots
5. **action_motion** - High-energy action
6. **testimonial** - Speaking-to-camera
7. **lifestyle** - Lifestyle/ambient shots
8. **tutorial_demo** - Tutorial demonstrations
9. **ugc_style** - User-generated content
10. **professional_studio** - Professional production

## Main Methods

### Extract Features
```python
features = extractor.extract_features(frame)
# Returns: np.ndarray (2048,)
```

### Classify Pattern
```python
result = extractor.classify_visual_pattern(frame)
# Returns: VisualPatternResult
#   - primary_pattern: str
#   - confidence: float
#   - all_scores: Dict[str, float]
#   - visual_energy: float
#   - feature_vector: np.ndarray
```

### Analyze Sequence
```python
analysis = extractor.analyze_video_sequence(frames, sample_rate=5)
# Returns: VideoSequenceAnalysis
#   - dominant_pattern: str
#   - pattern_distribution: Dict[str, float]
#   - average_confidence: float
#   - average_visual_energy: float
#   - pattern_transitions: List[Dict]
#   - temporal_consistency: float
```

### Batch Processing
```python
features_batch = extractor.extract_features_batch(frames)
# Returns: np.ndarray (N, 2048)
```

### Detailed Analysis
```python
details = extractor.analyze_single_frame_detailed(frame)
# Returns: Dict with top_3_patterns, descriptions, etc.
```

## Integration with FeatureExtractorService

```python
from services.feature_extractor import FeatureExtractorService

service = FeatureExtractorService()

# Automatic visual pattern extraction
features = service.extract_features('video.mp4', 0.0, 5.0)

# Access visual pattern data
print(features.visual_pattern)      # e.g., 'face_closeup'
print(features.visual_confidence)   # e.g., 0.87
print(features.visual_energy)       # e.g., 0.64

# Detailed sequence analysis
analysis = service.extract_visual_sequence_analysis(
    'video.mp4', 0.0, 30.0, sample_rate=5
)
```

## Common Use Cases

### 1. Single Frame Classification
```python
frame = cv2.imread('frame.jpg')
result = extractor.classify_visual_pattern(frame)
pattern = result.primary_pattern
confidence = result.confidence
```

### 2. Video Sequence Analysis
```python
cap = cv2.VideoCapture('video.mp4')
frames = []
for _ in range(100):
    ret, frame = cap.read()
    if ret:
        frames.append(frame)
cap.release()

analysis = extractor.analyze_video_sequence(frames, sample_rate=5)
dominant = analysis.dominant_pattern
```

### 3. Pattern Transitions
```python
analysis = extractor.analyze_video_sequence(frames)
for t in analysis.pattern_transitions:
    print(f"Frame {t['frame_index']}: "
          f"{t['from_pattern']} → {t['to_pattern']}")
```

### 4. Batch Feature Extraction
```python
frames = [cv2.imread(f'frame_{i}.jpg') for i in range(50)]
features = extractor.extract_features_batch(frames)
# Process all features at once
```

## Performance Tips

1. **Use Batch Processing** for multiple frames
2. **Sample Frames** for long videos (sample_rate parameter)
3. **GPU Acceleration** automatically used if available
4. **Lazy Loading** - model loads on first use

## Device Support

- **CUDA**: Automatic GPU acceleration
- **MPS**: Apple Silicon GPU support
- **CPU**: Fallback (slower but compatible)

## Typical Performance

- GPU: ~50ms per frame
- CPU: ~200ms per frame
- Batch (32 frames, GPU): ~30ms per frame

## File Locations

- **Main**: `/home/user/geminivideo/services/drive-intel/services/visual_patterns.py`
- **Tests**: `/home/user/geminivideo/services/drive-intel/services/test_visual_patterns.py`
- **Integration**: `/home/user/geminivideo/services/drive-intel/services/feature_extractor.py`
- **Model**: `/home/user/geminivideo/services/drive-intel/models/asset.py`

## Testing

```bash
cd /home/user/geminivideo/services/drive-intel/services
python test_visual_patterns.py
```

---

**Quick Reference Version 1.0** | Agent 3 Implementation
