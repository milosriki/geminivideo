# Agent 9: Testing Engineer

## Your Mission
Write comprehensive tests for all new features across all services.

## Priority: MEDIUM (Wait for other agents to finish)

## Tasks

### 1. Test Infrastructure
Update `tests/conftest.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.db import Base
from shared.models import *

# Test database
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/geminivideo_test"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_asset(db_session):
    asset = Asset(
        path="/test/video.mp4",
        filename="video.mp4",
        size_bytes=1048576,
        duration_seconds=30.0,
        resolution="1920x1080",
        format="mp4",
        status="completed"
    )
    db_session.add(asset)
    db_session.commit()
    return asset

@pytest.fixture
def sample_clip(db_session, sample_asset):
    clip = Clip(
        asset_id=sample_asset.asset_id,
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
        scene_score=0.75,
        emotion_data={'dominant': 'happy', 'priority_score': 0.8},
        composite_score=0.72
    )
    db_session.add(clip)
    db_session.commit()
    return clip
```

### 2. Database Tests
Create `tests/test_database.py`:
```python
def test_create_asset(db_session):
    asset = Asset(
        path="/test.mp4",
        filename="test.mp4",
        size_bytes=1024,
        duration_seconds=10.0
    )
    db_session.add(asset)
    db_session.commit()

    assert asset.asset_id is not None
    assert asset.status == "processing"

def test_create_clip_with_asset(db_session, sample_asset):
    clip = Clip(
        asset_id=sample_asset.asset_id,
        start_time=0.0,
        end_time=5.0,
        duration=5.0
    )
    db_session.add(clip)
    db_session.commit()

    assert clip.clip_id is not None
    assert clip.asset_id == sample_asset.asset_id

def test_prediction_linking(db_session, sample_clip):
    pred = Prediction(
        clip_id=sample_clip.clip_id,
        predicted_ctr=0.05,
        predicted_band='high'
    )
    db_session.add(pred)
    db_session.commit()

    assert pred.prediction_id is not None
    assert pred.actual_ctr is None  # Not yet measured
```

### 3. Emotion Recognition Tests
Create `tests/test_emotion.py`:
```python
import pytest
import numpy as np
import cv2
from services.drive_intel.src.features.emotion import analyze_emotion, filter_clips_by_emotion

def test_emotion_detection_with_face():
    # Load test image with happy face
    frame = cv2.imread('tests/fixtures/happy_face.jpg')
    result = analyze_emotion(frame)

    assert result['has_face'] == True
    assert 'happy' in result['emotions']
    assert result['dominant'] == 'happy'
    assert result['priority_score'] > 0.5

def test_emotion_detection_no_face():
    # Blank frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = analyze_emotion(frame)

    assert result['has_face'] == False
    assert result['priority_score'] == 0.0

def test_filter_clips_by_emotion(sample_clip):
    clips = [sample_clip]
    filtered = filter_clips_by_emotion(clips, min_priority=0.7)

    assert len(filtered) == 1  # Should pass with 0.8 score

    filtered = filter_clips_by_emotion(clips, min_priority=0.9)
    assert len(filtered) == 0  # Should fail with 0.8 score
```

### 4. Prediction Tests
Create `tests/test_prediction.py`:
```python
from services.gateway_api.src.prediction import CTRPredictor

def test_feature_extraction(sample_clip):
    predictor = CTRPredictor()
    features = predictor.extract_features(sample_clip)

    assert len(features) == 6  # All feature dimensions
    assert features[3] == 0.8  # Emotion priority score

def test_default_prediction(sample_clip):
    predictor = CTRPredictor()
    result = predictor._default_prediction(sample_clip)

    assert 'predicted_ctr' in result
    assert 'predicted_band' in result
    assert 0 <= result['predicted_ctr'] <= 1.0

def test_training_insufficient_data(db_session):
    predictor = CTRPredictor()
    success = predictor.train(db_session)

    assert success == False  # Not enough data
```

### 5. Rendering Tests
Create `tests/test_rendering.py`:
```python
from services.video_agent.src.render.engine import VideoRenderer

def test_renderer_initialization():
    renderer = VideoRenderer('/tmp/test_outputs')
    assert renderer.output_dir == '/tmp/test_outputs'

def test_storyboard_validation():
    storyboard = {
        'clips': [{'clip_id': 'test', 'start': 0, 'end': 5}],
        'resolution': '1920x1080'
    }
    # Validate structure
    assert 'clips' in storyboard
    assert len(storyboard['clips']) > 0

@pytest.mark.integration
def test_video_concatenation(sample_clip):
    # Requires actual video files
    pytest.skip("Integration test - requires video files")
```

### 6. Meta Integration Tests
Create `tests/test_meta.py`:
```python
from unittest.mock import Mock, patch

@patch('facebook_business_sdk.FacebookAdsApi.init')
def test_meta_client_init(mock_init):
    from services.meta_publisher.src.facebook.client import MetaAdsClient

    client = MetaAdsClient('test_token', 'act_123')
    assert client.accountId == 'act_123'
    mock_init.assert_called_once()

@patch('services.meta_publisher.src.facebook.client.MetaAdsClient.createCampaign')
async def test_create_campaign(mock_create):
    mock_create.return_value = 'campaign_123'

    from services.meta_publisher.src.facebook.client import MetaAdsClient
    client = MetaAdsClient('test_token', 'act_123')

    campaign_id = await client.createCampaign('Test')
    assert campaign_id == 'campaign_123'
```

### 7. Integration Tests
Create `tests/test_integration_full.py`:
```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_full_pipeline(db_session):
    """Test complete flow: ingest -> process -> score -> render -> publish"""

    # 1. Ingest
    from services.drive_intel.src.main import app as drive_app
    drive_client = TestClient(drive_app)
    response = drive_client.post("/ingest/local/folder", json={"path": "/test/video.mp4"})
    assert response.status_code == 200
    asset_id = response.json()['asset_id']

    # 2. Wait for processing (in real test, would mock)
    # ...

    # 3. Get ranked clips
    response = drive_client.get(f"/assets/{asset_id}/clips?ranked=true")
    assert response.status_code == 200
    clips = response.json()['clips']
    assert len(clips) > 0

    # 4. Predict CTR
    from services.gateway_api.src.index import app as gateway_app
    gateway_client = TestClient(gateway_app)
    clip_id = clips[0]['clip_id']
    response = gateway_client.post("/predict/ctr", json={"clip_id": clip_id})
    assert response.status_code == 200
    assert 'predicted_ctr' in response.json()

    # 5. Render video
    from services.video_agent.src.index import app as video_app
    video_client = TestClient(video_app)
    storyboard = {
        'clips': [{'clip_id': clip_id}],
        'resolution': '1920x1080'
    }
    response = video_client.post("/render/remix", json=storyboard)
    assert response.status_code == 200
    job_id = response.json()['job_id']

    # 6. Check render status
    response = video_client.get(f"/render/status/{job_id}")
    assert response.status_code == 200
```

### 8. Performance Tests
Create `tests/test_performance.py`:
```python
import time

def test_scoring_performance(sample_clip):
    """Ensure scoring is fast enough"""
    from services.gateway_api.src.scoring import calculateScoreBundle

    start = time.time()
    for _ in range(100):
        calculateScoreBundle(sample_clip.features or {})
    duration = time.time() - start

    assert duration < 1.0  # 100 scores in < 1 second

def test_emotion_detection_performance():
    """Ensure emotion detection is acceptable"""
    import cv2
    from services.drive_intel.src.features.emotion import analyze_emotion

    frame = cv2.imread('tests/fixtures/happy_face.jpg')

    start = time.time()
    for _ in range(10):
        analyze_emotion(frame)
    duration = time.time() - start

    assert duration < 5.0  # 10 detections in < 5 seconds
```

### 9. Test Runner Script
Create `tests/run_tests.sh`:
```bash
#!/bin/bash

echo "Running unit tests..."
pytest tests/ -v -m "not integration"

echo "Running integration tests..."
pytest tests/ -v -m integration

echo "Generating coverage report..."
pytest tests/ --cov=services --cov-report=html

echo "Tests complete! Coverage report in htmlcov/index.html"
```

## Deliverables
- [ ] Test fixtures and conftest
- [ ] Database tests
- [ ] Emotion recognition tests
- [ ] Prediction model tests
- [ ] Rendering tests
- [ ] Meta integration tests (mocked)
- [ ] Full integration test
- [ ] Performance tests
- [ ] 80%+ code coverage

## Branch
`agent-9-comprehensive-testing`

## Blockers
- **All agents** (tests their code)

## Who Depends On You
- Agent 10 (needs passing tests for CI/CD)
