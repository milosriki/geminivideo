# Agent 2: ML Engineer - Video Processing

## Your Mission
Implement real scene detection and emotion recognition using PySceneDetect and DeepFace.

## Priority: HIGH

## Tasks

### 1. Install Dependencies
Update `services/drive-intel/requirements.txt`:
```
# Existing...
deepface==0.0.79
opencv-python-headless==4.8.1.78
scenedetect[opencv]==0.6.3
tf-keras==2.16.0  # For DeepFace
```

### 2. Real Scene Detection
Update `services/drive-intel/src/main.py`:
```python
from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector
import cv2

async def process_asset(asset_id: str, db: Session):
    """Real scene detection using PySceneDetect"""
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()

    # Open video
    video = open_video(asset.path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=30.0))

    # Detect scenes
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    clips = []
    for i, scene in enumerate(scene_list):
        start_time = scene[0].get_seconds()
        end_time = scene[1].get_seconds()

        # Extract middle frame for emotion analysis
        video.seek(start_time + (end_time - start_time) / 2)
        frame = video.read()

        # Analyze emotion (next step)
        emotion_data = analyze_emotion(frame)

        clip = Clip(
            asset_id=asset_id,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            emotion_data=emotion_data,
            scene_score=0.5  # Will be calculated later
        )
        clips.append(clip)

    db.bulk_save_objects(clips)
    db.commit()

    # Update asset status
    asset.status = 'completed'
    db.commit()
```

### 3. Emotion Recognition
Add to `services/drive-intel/src/features/emotion.py`:
```python
from deepface import DeepFace
import numpy as np
import cv2

def analyze_emotion(frame: np.ndarray) -> dict:
    """
    Analyze emotion in video frame using DeepFace
    Returns emotion data with scores
    """
    try:
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Analyze with DeepFace
        analysis = DeepFace.analyze(
            rgb_frame,
            actions=['emotion'],
            enforce_detection=False,  # Don't fail if no face
            detector_backend='opencv'
        )

        if isinstance(analysis, list):
            analysis = analysis[0]

        emotions = analysis['emotion']
        dominant = analysis['dominant_emotion']

        # Prioritize positive emotions for ads
        priority_score = (
            emotions.get('happy', 0) * 1.0 +
            emotions.get('surprise', 0) * 0.8 +
            emotions.get('neutral', 0) * 0.3
        ) / 100.0

        return {
            'emotions': emotions,
            'dominant': dominant,
            'priority_score': priority_score,
            'has_face': True
        }
    except Exception as e:
        print(f"Emotion analysis failed: {e}")
        return {
            'emotions': {},
            'dominant': 'unknown',
            'priority_score': 0.0,
            'has_face': False
        }

def filter_clips_by_emotion(clips: list, min_priority: float = 0.5) -> list:
    """Filter clips to only those with positive emotions"""
    return [
        clip for clip in clips
        if clip.emotion_data.get('priority_score', 0) >= min_priority
    ]
```

### 4. Update Scoring
Modify `services/gateway-api/src/scoring.ts` to use emotion:
```python
# Add emotion boost to composite score
def calculate_composite_with_emotion(clip):
    emotion_boost = clip.emotion_data.get('priority_score', 0) * 0.15

    composite = (
        psychology_score * 0.35 +
        hook_strength * 0.30 +
        novelty_score * 0.20 +
        emotion_boost * 0.15
    )
    return composite
```

### 5. Add Endpoint
Add to `services/drive-intel/src/main.py`:
```python
@app.get("/assets/{asset_id}/clips/emotional")
async def get_emotional_clips(
    asset_id: str,
    min_emotion_score: float = 0.5,
    db: Session = Depends(get_db)
):
    """Get clips filtered by positive emotions"""
    clips = db.query(Clip).filter(
        Clip.asset_id == asset_id,
        Clip.emotion_data['priority_score'].astext.cast(Float) >= min_emotion_score
    ).order_by(Clip.emotion_data['priority_score'].desc()).all()

    return {"clips": clips, "count": len(clips)}
```

### 6. Testing
Create `tests/test_emotion.py`:
```python
import pytest
from services.drive_intel.src.features.emotion import analyze_emotion
import cv2
import numpy as np

def test_emotion_detection():
    # Load test image
    frame = cv2.imread('tests/fixtures/happy_face.jpg')
    result = analyze_emotion(frame)

    assert result['has_face'] == True
    assert 'happy' in result['emotions']
    assert result['priority_score'] > 0

def test_no_face_handling():
    # Blank frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = analyze_emotion(frame)

    assert result['has_face'] == False
    assert result['priority_score'] == 0.0
```

## Dependencies
- `pip install deepface scenedetect opencv-python-headless tf-keras`

## Deliverables
- [ ] Real PySceneDetect integration working
- [ ] DeepFace emotion recognition working
- [ ] Emotion-filtered clips endpoint
- [ ] Tests for emotion detection
- [ ] Documentation updated

## Branch
`agent-2-video-ml-emotion`

## Blockers
None (uses existing video files)

## Who Depends On You
- Agent 4 (needs emotion data for rendering)
- Agent 3 (emotion features for prediction)
