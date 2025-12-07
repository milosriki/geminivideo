"""
Shared Fixtures and Test Configuration for Integration Tests
Provides common test utilities, database setup, mock services, and test data.
"""

import pytest
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import json

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "services" / "titan-core"))
sys.path.insert(0, str(PROJECT_ROOT / "services" / "gateway-api"))

# MOCK XGBOOST (Bypass libomp missing on macOS/CI)
# This must happen before any imports that use xgboost
try:
    import xgboost
except Exception as e:
    # Create a mock module
    mock_xgb = Mock()
    mock_xgb.XGBClassifier = Mock
    mock_xgb.XGBRegressor = Mock
    mock_xgb.DMatrix = Mock
    sys.modules['xgboost'] = mock_xgb
    print(f"WARNING: XGBoost mocked due to error: {e}")


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring API access"
    )
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database"
    )


# ============================================================================
# EVENT LOOP CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_db_url():
    """Test database URL"""
    return os.getenv("TEST_DATABASE_URL", "postgresql://localhost/geminivideo_test")


@pytest.fixture
async def db_session(test_db_url):
    """Create test database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create test engine
    engine = create_engine(test_db_url, echo=False)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()


@pytest.fixture
async def clean_db(db_session):
    """Clean database before and after tests"""
    # Clean before
    await _clean_test_tables(db_session)

    yield

    # Clean after
    await _clean_test_tables(db_session)


async def _clean_test_tables(session):
    """Clean test database tables"""
    try:
        # Clear test data (preserving schema)
        tables_to_clean = [
            "performance_metrics",
            "scenes",
            "videos",
            "campaigns",
            "audit_logs"
        ]

        for table in tables_to_clean:
            try:
                session.execute(f"DELETE FROM {table} WHERE 1=1")
            except Exception:
                pass  # Table might not exist

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Warning: Could not clean test database: {e}")


# ============================================================================
# MOCK SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def mock_gemini_api():
    """Mock Gemini API client"""
    mock = Mock()
    mock.generate_content = AsyncMock(return_value=Mock(
        text="85.5",
        candidates=[Mock(content=Mock(parts=[Mock(text="85.5")]))]
    ))
    return mock


@pytest.fixture
def mock_openai_api():
    """Mock OpenAI API client"""
    mock = AsyncMock()
    mock.chat = Mock()
    mock.chat.completions = Mock()
    mock.chat.completions.create = AsyncMock(return_value=Mock(
        choices=[Mock(message=Mock(content='{"score": 82.0, "confidence": 0.85, "reasoning": "Good hook"}'))],
        usage=Mock(prompt_tokens=100, completion_tokens=50)
    ))
    return mock


@pytest.fixture
def mock_anthropic_api():
    """Mock Anthropic Claude API client"""
    mock = AsyncMock()
    mock.messages = Mock()
    mock.messages.create = AsyncMock(return_value=Mock(
        content=[Mock(text="78.5")],
        usage=Mock(input_tokens=100, output_tokens=10)
    ))
    return mock


@pytest.fixture
def mock_meta_api():
    """Mock Meta Marketing API client"""
    from tests.integration.test_publishing import mock_meta_client
    return mock_meta_client


@pytest.fixture
def mock_google_ads_api():
    """Mock Google Ads API client"""
    from tests.integration.test_publishing import mock_google_ads_client
    return mock_google_ads_client


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================

class TestDataFactory:
    """Factory for generating test data"""

    @staticmethod
    def create_campaign(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test campaign data"""
        data = {
            "id": "campaign_test_001",
            "name": "Test Campaign",
            "status": "draft",
            "budget_daily": 100.00,
            "target_audience": {
                "countries": ["US"],
                "age_min": 25,
                "age_max": 45
            },
            "created_at": datetime.utcnow().isoformat()
        }
        if overrides:
            data.update(overrides)
        return data

    @staticmethod
    def create_video(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test video data"""
        data = {
            "id": "video_test_001",
            "campaign_id": "campaign_test_001",
            "title": "Test Video",
            "description": "Test video description",
            "video_url": "https://storage.example.com/video_001.mp4",
            "duration_seconds": 30.0,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat()
        }
        if overrides:
            data.update(overrides)
        return data

    @staticmethod
    def create_blueprint(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test ad blueprint"""
        data = {
            "id": "bp_test_001",
            "hook_text": "Stop scrolling! This will change everything.",
            "scenes": [
                {
                    "timestamp": "0-5s",
                    "description": "Hook scene",
                    "visual": "Pattern interrupt",
                    "text_overlay": "WAIT!"
                },
                {
                    "timestamp": "5-25s",
                    "description": "Problem and solution",
                    "visual": "Transformation",
                    "text_overlay": "Here's how"
                },
                {
                    "timestamp": "25-30s",
                    "description": "CTA",
                    "visual": "Call to action",
                    "text_overlay": "Book now"
                }
            ],
            "cta_text": "Book your free call now",
            "platform": "instagram",
            "target_emotion": "urgency"
        }
        if overrides:
            data.update(overrides)
        return data

    @staticmethod
    def create_performance_metrics(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test performance metrics"""
        data = {
            "video_id": "video_test_001",
            "platform": "meta",
            "date": datetime.utcnow().date().isoformat(),
            "impressions": 10000,
            "clicks": 500,
            "spend": 100.00,
            "ctr": 0.05,
            "conversions": 25,
            "roas": 5.0
        }
        if overrides:
            data.update(overrides)
        return data

    @staticmethod
    def create_video_features(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create test video features for predictions"""
        data = {
            "hook_effectiveness": 8.5,
            "has_transformation": True,
            "cta_strength": 7.0,
            "num_emotional_triggers": 3,
            "has_human_face": True,
            "duration_seconds": 30,
            "scene_count": 4,
            "word_count": 75,
            "hook_type": "pattern_interrupt",
            "fast_paced": True
        }
        if overrides:
            data.update(overrides)
        return data


@pytest.fixture
def test_factory():
    """Test data factory fixture"""
    return TestDataFactory()


# ============================================================================
# FILE SYSTEM FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_video_file(temp_dir):
    """Create temporary test video file"""
    video_path = temp_dir / "test_video.mp4"

    # Create minimal valid MP4 header
    with open(video_path, "wb") as f:
        f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00')

    yield str(video_path)

    # Cleanup handled by temp_dir


@pytest.fixture
def test_image_file(temp_dir):
    """Create temporary test image file"""
    image_path = temp_dir / "test_image.jpg"

    # Create minimal valid JPEG header
    with open(image_path, "wb") as f:
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')

    yield str(image_path)


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def api_base_url():
    """API base URL"""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture
async def api_client(api_base_url):
    """HTTP client for API testing"""
    import httpx

    async with httpx.AsyncClient(base_url=api_base_url, timeout=30.0) as client:
        yield client


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture
def test_env_vars():
    """Set test environment variables"""
    original_env = os.environ.copy()

    # Set test environment
    os.environ.update({
        "ENVIRONMENT": "test",
        "DEBUG": "true",
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "test-key"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "test-key"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "test-key"),
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# ASSERTION HELPERS
# ============================================================================

class AssertionHelpers:
    """Helper methods for common assertions"""

    @staticmethod
    def assert_valid_uuid(value: str):
        """Assert value is a valid UUID"""
        import uuid
        try:
            uuid.UUID(value)
        except (ValueError, TypeError):
            pytest.fail(f"'{value}' is not a valid UUID")

    @staticmethod
    def assert_valid_score(score: float):
        """Assert score is in valid range 0-100"""
        assert 0 <= score <= 100, f"Score {score} not in range 0-100"

    @staticmethod
    def assert_valid_timestamp(timestamp: str):
        """Assert timestamp is valid ISO format"""
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            pytest.fail(f"'{timestamp}' is not a valid ISO timestamp")

    @staticmethod
    def assert_response_structure(data: dict, required_fields: list):
        """Assert response has required fields"""
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


@pytest.fixture
def assert_helpers():
    """Assertion helpers fixture"""
    return AssertionHelpers()


# ============================================================================
# TIMING UTILITIES
# ============================================================================

@pytest.fixture
def timer():
    """Simple timer for performance testing"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# ============================================================================
# LOGGING FIXTURES
# ============================================================================

@pytest.fixture
def capture_logs():
    """Capture log output for testing"""
    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)

    yield log_stream

    logger.removeHandler(handler)


# ============================================================================
# RETRY UTILITIES
# ============================================================================

async def retry_async(func, max_attempts=3, delay=1.0):
    """Retry async function with exponential backoff"""
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(delay * (2 ** attempt))


@pytest.fixture
def retry_helper():
    """Retry helper fixture"""
    return retry_async


# ============================================================================
# CLEANUP UTILITIES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Auto cleanup test artifacts after each test"""
    yield

    # Cleanup temp files
    temp_patterns = [
        "/tmp/test_*.mp4",
        "/tmp/render_*.mp4",
        "/tmp/titan-core/test_*"
    ]

    import glob
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.unlink(file_path)
            except Exception:
                pass


# ============================================================================
# SKIP CONDITIONS
# ============================================================================

skip_if_no_api_key = pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="API key not available"
)

skip_if_no_db = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Test database not configured"
)

requires_external_api = pytest.mark.skipif(
    os.getenv("SKIP_EXTERNAL_TESTS", "false").lower() == "true",
    reason="External API tests disabled"
)
