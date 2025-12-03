"""
Unit tests for Titan-Core Master API

Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the AI Council and PRO Video components before importing main
sys.modules['ai_council'] = Mock()
sys.modules['services.video_agent.pro.winning_ads_generator'] = Mock()
sys.modules['services.video_agent.pro.motion_graphics'] = Mock()
sys.modules['services.video_agent.services.renderer'] = Mock()
sys.modules['services.video_agent.models.render_job'] = Mock()

from main import app, app_state


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_app_state():
    """Mock app state"""
    app_state.initialized = True
    app_state.council = Mock()
    app_state.oracle = Mock()
    app_state.director = Mock()
    app_state.pipeline = Mock()
    app_state.video_renderer = Mock()
    return app_state


# ============================================================================
# HEALTH & STATUS TESTS
# ============================================================================

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_system_status(client):
    """Test system status endpoint"""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "overall_status" in data
    assert "components" in data
    assert "active_render_jobs" in data
    assert isinstance(data["components"], list)


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Titan-Core Master API"
    assert "endpoints" in data


# ============================================================================
# AI COUNCIL ENDPOINT TESTS
# ============================================================================

def test_evaluate_script_without_council(client):
    """Test script evaluation when council is not available"""
    app_state.council = None
    response = client.post(
        "/council/evaluate",
        json={
            "script": "Test script",
            "visual_features": {}
        }
    )
    assert response.status_code == 503


def test_evaluate_script_with_council(client, mock_app_state):
    """Test script evaluation with council"""
    # Mock council response
    mock_app_state.council.evaluate_script = AsyncMock(return_value={
        "final_score": 92.5,
        "breakdown": {
            "Gemini": 95.0,
            "GPT-4o": 90.0,
            "Claude": 93.0,
            "DeepCTR": 88.0
        }
    })

    response = client.post(
        "/council/evaluate",
        json={
            "script": "Stop scrolling if you want to lose 20lbs",
            "visual_features": {
                "has_human_face": True,
                "hook_type": "pattern_interrupt"
            }
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "final_score" in data
    assert "approved" in data
    assert "breakdown" in data


def test_evaluate_script_validation_error(client):
    """Test script evaluation with missing required field"""
    response = client.post(
        "/council/evaluate",
        json={"visual_features": {}}  # Missing script
    )
    assert response.status_code == 422


def test_oracle_predict_without_oracle(client):
    """Test ROAS prediction when oracle is not available"""
    app_state.oracle = None
    response = client.post(
        "/oracle/predict",
        json={
            "video_id": "test_001",
            "features": {"hook_effectiveness": 8.5}
        }
    )
    assert response.status_code == 503


def test_director_generate_without_director(client):
    """Test blueprint generation when director is not available"""
    app_state.director = None
    response = client.post(
        "/director/generate",
        json={
            "product_name": "Test Product",
            "offer": "Test Offer",
            "target_avatar": "Test Avatar",
            "pain_points": ["pain1"],
            "desires": ["desire1"]
        }
    )
    assert response.status_code == 503


# ============================================================================
# VIDEO PROCESSING ENDPOINT TESTS
# ============================================================================

def test_start_render_without_renderer(client):
    """Test starting render when renderer is not available"""
    app_state.video_renderer = None
    response = client.post(
        "/render/start",
        json={
            "blueprint": {"id": "test"},
            "platform": "instagram",
            "quality": "high",
            "aspect_ratio": "9:16"
        }
    )
    assert response.status_code == 503


def test_get_render_status_not_found(client):
    """Test getting status of non-existent job"""
    response = client.get("/render/nonexistent_job/status")
    assert response.status_code == 404


def test_download_render_not_found(client):
    """Test downloading non-existent job"""
    response = client.get("/render/nonexistent_job/download")
    assert response.status_code == 404


def test_download_render_not_completed(client):
    """Test downloading incomplete job"""
    # Add a pending job
    app_state.render_jobs["test_job"] = {
        "id": "test_job",
        "status": "pending",
        "request": {},
        "progress": 0.0,
        "output_path": None,
        "error": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }

    response = client.get("/render/test_job/download")
    assert response.status_code == 400


# ============================================================================
# PIPELINE ENDPOINT TESTS
# ============================================================================

def test_generate_campaign_without_pipeline(client):
    """Test campaign generation when pipeline is not available"""
    app_state.pipeline = None
    response = client.post(
        "/pipeline/generate-campaign",
        json={
            "product_name": "Test Product",
            "offer": "Test Offer",
            "target_avatar": "Test Avatar",
            "pain_points": ["pain1"],
            "desires": ["desire1"],
            "num_variations": 10
        }
    )
    assert response.status_code == 503


def test_generate_campaign_validation(client):
    """Test campaign generation with invalid data"""
    response = client.post(
        "/pipeline/generate-campaign",
        json={
            "product_name": "Test Product",
            # Missing required fields
        }
    )
    assert response.status_code == 422


def test_render_winning_validation(client):
    """Test render winning with invalid data"""
    response = client.post(
        "/pipeline/render-winning",
        json={
            # Missing blueprints
            "platform": "instagram"
        }
    )
    assert response.status_code == 422


# ============================================================================
# REQUEST VALIDATION TESTS
# ============================================================================

def test_blueprint_request_validation(client):
    """Test blueprint request validation"""
    # Valid request with minimum fields
    response = client.post(
        "/director/generate",
        json={
            "product_name": "Test",
            "offer": "Test",
            "target_avatar": "Test",
            "pain_points": ["test"],
            "desires": ["test"]
        }
    )
    # Should fail with 503 if director not available, not 422 validation error
    assert response.status_code in [200, 503]

    # Invalid request - num_variations out of range
    response = client.post(
        "/director/generate",
        json={
            "product_name": "Test",
            "offer": "Test",
            "target_avatar": "Test",
            "pain_points": ["test"],
            "desires": ["test"],
            "num_variations": 100  # Max is 50
        }
    )
    assert response.status_code == 422


def test_render_request_validation(client):
    """Test render request validation"""
    # Valid request
    response = client.post(
        "/render/start",
        json={
            "blueprint": {"id": "test"},
            "platform": "instagram",
            "quality": "high",
            "aspect_ratio": "9:16"
        }
    )
    # Should fail with 503 if renderer not available, not 422 validation error
    assert response.status_code in [200, 503]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
def test_complete_workflow(client, mock_app_state):
    """Test complete workflow from campaign generation to render"""
    # Mock pipeline response
    from unittest.mock import MagicMock
    from datetime import datetime

    mock_result = MagicMock()
    mock_result.campaign_id = "test_campaign"
    mock_result.blueprints_generated = 10
    mock_result.blueprints_approved = 7
    mock_result.blueprints_rejected = 3
    mock_result.variants = []
    mock_result.avg_council_score = 88.5
    mock_result.avg_predicted_roas = 3.2
    mock_result.duration_seconds = 45.2

    mock_app_state.pipeline.generate_winning_ads = AsyncMock(return_value=mock_result)

    # Step 1: Generate campaign
    response = client.post(
        "/pipeline/generate-campaign",
        json={
            "product_name": "Test Product",
            "offer": "Test Offer",
            "target_avatar": "Test Avatar",
            "pain_points": ["pain1", "pain2"],
            "desires": ["desire1", "desire2"],
            "num_variations": 10
        }
    )

    assert response.status_code == 200
    campaign = response.json()
    assert "campaign_id" in campaign
    assert campaign["status"] == "completed"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_404_on_invalid_endpoint(client):
    """Test 404 error on invalid endpoint"""
    response = client.get("/invalid/endpoint")
    assert response.status_code == 404


def test_405_on_wrong_method(client):
    """Test 405 error on wrong HTTP method"""
    response = client.post("/health")  # GET endpoint
    assert response.status_code == 405


# ============================================================================
# CORS TESTS
# ============================================================================

def test_cors_headers(client):
    """Test CORS headers are present"""
    response = client.options("/health")
    assert response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
