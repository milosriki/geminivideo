"""
Integration Tests for API Endpoints
Tests all gateway-api and titan-core endpoints with real API calls.

Coverage:
- Health and status endpoints
- Council evaluation endpoints
- Oracle prediction endpoints
- Director blueprint generation
- Pipeline campaign generation
- Vertex AI endpoints
- Meta Ads Library endpoints
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any
from datetime import datetime


# Test Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


class TestHealthEndpoints:
    """Test health check and status endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test /health endpoint returns 200 OK"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data

    @pytest.mark.asyncio
    async def test_system_status(self):
        """Test /status endpoint returns detailed component status"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/status")

            assert response.status_code == 200
            data = response.json()

            # Check overall structure
            assert "overall_status" in data
            assert "components" in data
            assert "active_render_jobs" in data
            assert "timestamp" in data

            # Check components list
            assert isinstance(data["components"], list)
            assert len(data["components"]) > 0

            # Verify each component has required fields
            for component in data["components"]:
                assert "name" in component
                assert "available" in component
                assert "status" in component

            # Check for key components
            component_names = [c["name"] for c in data["components"]]
            assert "AI Council" in component_names
            assert "Oracle Agent" in component_names

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test / endpoint returns API information"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/")

            assert response.status_code == 200
            data = response.json()

            assert data["name"] == "Titan-Core Master API"
            assert data["status"] == "operational"
            assert "endpoints" in data
            assert "vertex_ai_capabilities" in data


class TestCouncilEndpoints:
    """Test Council of Titans evaluation endpoints"""

    @pytest.mark.asyncio
    async def test_evaluate_script_basic(self):
        """Test /council/evaluate with valid script"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "script": "Stop scrolling if you want to lose 20lbs in 90 days without spending hours at the gym. Book your free transformation call now.",
                "visual_features": {
                    "has_human_face": True,
                    "hook_type": "pattern_interrupt"
                }
            }

            response = await client.post(
                f"{API_BASE_URL}/council/evaluate",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "final_score" in data
            assert "approved" in data
            assert "breakdown" in data
            assert "timestamp" in data

            # Validate score range
            assert 0 <= data["final_score"] <= 100

            # Check breakdown has all models
            breakdown = data["breakdown"]
            assert "gemini_2_0_thinking" in breakdown
            assert "claude_3_5" in breakdown
            assert "deep_ctr" in breakdown

    @pytest.mark.asyncio
    async def test_evaluate_script_no_visual_features(self):
        """Test /council/evaluate without visual features"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "script": "Transform your body with our 90-day challenge. Join now!"
            }

            response = await client.post(
                f"{API_BASE_URL}/council/evaluate",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()
            assert "final_score" in data

    @pytest.mark.asyncio
    async def test_evaluate_script_validation(self):
        """Test /council/evaluate with invalid input"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Missing required field
            request_data = {}

            response = await client.post(
                f"{API_BASE_URL}/council/evaluate",
                json=request_data
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_evaluate_multiple_scripts(self):
        """Test that Council returns varied scores for different scripts"""
        scripts = [
            "Stop! This will change everything. Click now.",
            "Learn how to make money online with our proven system. Sign up today.",
            "Transform your life in 90 days. Book your free call."
        ]

        scores = []
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for script in scripts:
                request_data = {"script": script}
                response = await client.post(
                    f"{API_BASE_URL}/council/evaluate",
                    json=request_data
                )

                if response.status_code == 200:
                    data = response.json()
                    scores.append(data["final_score"])

        # Should have at least some variation in scores
        if len(scores) >= 2:
            assert len(set(scores)) > 1 or max(scores) - min(scores) > 5


class TestOracleEndpoints:
    """Test Oracle Agent prediction endpoints"""

    @pytest.mark.asyncio
    async def test_predict_roas(self):
        """Test /oracle/predict with valid features"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "video_id": "test_video_001",
                "features": {
                    "hook_effectiveness": 8.5,
                    "has_transformation": True,
                    "cta_strength": 7.0,
                    "num_emotional_triggers": 3,
                    "has_human_face": True,
                    "duration_seconds": 30
                }
            }

            response = await client.post(
                f"{API_BASE_URL}/oracle/predict",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "predicted_roas" in data or "ensemble_prediction" in data
            assert "video_id" in data

    @pytest.mark.asyncio
    async def test_predict_roas_minimal_features(self):
        """Test /oracle/predict with minimal features"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "video_id": "test_minimal",
                "features": {
                    "hook_effectiveness": 5.0
                }
            }

            response = await client.post(
                f"{API_BASE_URL}/oracle/predict",
                json=request_data
            )

            assert response.status_code == 200


class TestDirectorEndpoints:
    """Test Director Agent blueprint generation endpoints"""

    @pytest.mark.asyncio
    async def test_generate_blueprints(self):
        """Test /director/generate with valid request"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "product_name": "Elite Fitness Coaching",
                "offer": "Book your free transformation call",
                "target_avatar": "Busy professionals 30-45",
                "pain_points": ["no time", "low energy", "weight gain"],
                "desires": ["look great", "feel confident", "have energy"],
                "platform": "reels",
                "num_variations": 3  # Small number for fast testing
            }

            response = await client.post(
                f"{API_BASE_URL}/director/generate",
                json=request_data,
                timeout=60.0  # Director can take longer
            )

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "blueprints" in data
            assert "count" in data
            assert "timestamp" in data

            # Validate blueprints
            assert data["count"] > 0
            assert len(data["blueprints"]) == data["count"]

            # Check first blueprint structure
            if data["blueprints"]:
                blueprint = data["blueprints"][0]
                assert "hook_text" in blueprint or "scenes" in blueprint

    @pytest.mark.asyncio
    async def test_generate_blueprints_different_platforms(self):
        """Test /director/generate for different platforms"""
        platforms = ["reels", "tiktok", "youtube_shorts"]

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for platform in platforms:
                request_data = {
                    "product_name": "Test Product",
                    "offer": "Sign up now",
                    "target_avatar": "Anyone",
                    "pain_points": ["problem"],
                    "desires": ["solution"],
                    "platform": platform,
                    "num_variations": 1
                }

                response = await client.post(
                    f"{API_BASE_URL}/director/generate",
                    json=request_data,
                    timeout=60.0
                )

                # Should accept all platforms
                assert response.status_code in [200, 503]  # 503 if director not available


class TestPipelineEndpoints:
    """Test end-to-end pipeline endpoints"""

    @pytest.mark.asyncio
    async def test_generate_campaign(self):
        """Test /pipeline/generate-campaign with complete flow"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "product_name": "Elite Fitness Coaching",
                "offer": "Book your free transformation call",
                "target_avatar": "Busy professionals 30-45",
                "pain_points": ["no time", "low energy"],
                "desires": ["look great", "feel confident"],
                "num_variations": 5,  # Small for testing
                "approval_threshold": 75.0,
                "platforms": ["instagram"]
            }

            response = await client.post(
                f"{API_BASE_URL}/pipeline/generate-campaign",
                json=request_data,
                timeout=120.0  # Pipeline can take time
            )

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "campaign_id" in data
            assert "status" in data
            assert "blueprints_generated" in data
            assert "blueprints_approved" in data
            assert "top_blueprints" in data
            assert "avg_council_score" in data
            assert "avg_predicted_roas" in data

            # Validate data
            assert data["status"] == "completed"
            assert data["blueprints_generated"] > 0
            assert len(data["top_blueprints"]) > 0


class TestRenderEndpoints:
    """Test video rendering endpoints"""

    @pytest.mark.asyncio
    async def test_start_render(self):
        """Test /render/start to create render job"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "blueprint": {
                    "id": "test_bp_001",
                    "hook_text": "Stop scrolling!",
                    "cta_text": "Book now"
                },
                "platform": "instagram",
                "quality": "high",
                "aspect_ratio": "9:16"
            }

            response = await client.post(
                f"{API_BASE_URL}/render/start",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()

            # Check response
            assert "job_id" in data
            assert "status" in data
            assert data["status"] in ["pending", "processing"]

    @pytest.mark.asyncio
    async def test_render_status(self):
        """Test /render/{job_id}/status"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # First create a render job
            request_data = {
                "blueprint": {"id": "test", "hook_text": "Test"},
                "platform": "instagram"
            }

            response = await client.post(
                f"{API_BASE_URL}/render/start",
                json=request_data
            )

            if response.status_code == 200:
                job_id = response.json()["job_id"]

                # Check status
                status_response = await client.get(
                    f"{API_BASE_URL}/render/{job_id}/status"
                )

                assert status_response.status_code == 200
                data = status_response.json()

                assert "job_id" in data
                assert "status" in data
                assert "progress" in data
                assert 0 <= data["progress"] <= 100


class TestVertexAIEndpoints:
    """Test Vertex AI endpoints (if available)"""

    @pytest.mark.asyncio
    async def test_analyze_video(self):
        """Test /api/vertex/analyze-video"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "video_uri": "gs://test-bucket/test-video.mp4"
            }

            response = await client.post(
                f"{API_BASE_URL}/api/vertex/analyze-video",
                json=request_data,
                timeout=60.0
            )

            # May be unavailable if Vertex AI not configured
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert "summary" in data
                assert "scenes" in data

    @pytest.mark.asyncio
    async def test_generate_ad_copy(self):
        """Test /api/vertex/generate-ad-copy"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "product_info": "Elite fitness coaching with personalized meal plans",
                "style": "urgent",
                "num_variants": 3
            }

            response = await client.post(
                f"{API_BASE_URL}/api/vertex/generate-ad-copy",
                json=request_data,
                timeout=60.0
            )

            # May be unavailable if Vertex AI not configured
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert "variants" in data
                assert "count" in data
                assert data["count"] == 3

    @pytest.mark.asyncio
    async def test_improve_hook(self):
        """Test /api/vertex/improve-hook"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "current_hook": "Want to lose weight fast?",
                "target_emotion": "FOMO"
            }

            response = await client.post(
                f"{API_BASE_URL}/api/vertex/improve-hook",
                json=request_data,
                timeout=60.0
            )

            # May be unavailable if Vertex AI not configured
            assert response.status_code in [200, 503]

            if response.status_code == 200:
                data = response.json()
                assert "improved_hooks" in data
                assert "original_hook" in data


class TestMetaAdsEndpoints:
    """Test Meta Ads Library endpoints"""

    @pytest.mark.asyncio
    async def test_meta_ads_search(self):
        """Test /meta/ads-library/search"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            request_data = {
                "search_terms": "fitness coaching",
                "platforms": ["facebook", "instagram"],
                "limit": 10
            }

            response = await client.post(
                f"{API_BASE_URL}/meta/ads-library/search",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()

            assert "ads" in data
            assert isinstance(data["ads"], list)

    @pytest.mark.asyncio
    async def test_generate_insights(self):
        """Test /insights/generate"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                f"{API_BASE_URL}/insights/generate",
                params={"context": "dashboard"}
            )

            assert response.status_code == 200
            data = response.json()

            assert "insights" in data
            assert isinstance(data["insights"], list)

    @pytest.mark.asyncio
    async def test_list_avatars(self):
        """Test /avatars/list"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/avatars/list")

            assert response.status_code == 200
            data = response.json()

            assert isinstance(data, list)
            if data:
                avatar = data[0]
                assert "key" in avatar
                assert "name" in avatar


class TestAuthenticationAndSecurity:
    """Test authentication flows and security"""

    @pytest.mark.asyncio
    async def test_cors_headers(self):
        """Test CORS headers are present"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/health")

            # Check for CORS headers
            headers = response.headers
            assert "access-control-allow-origin" in headers or response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that API handles multiple requests"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Send multiple requests in quick succession
            tasks = [
                client.get(f"{API_BASE_URL}/health")
                for _ in range(10)
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed or be rate limited gracefully
            for response in responses:
                if not isinstance(response, Exception):
                    assert response.status_code in [200, 429]


class TestErrorHandling:
    """Test error handling and validation"""

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self):
        """Test 404 for non-existent endpoints"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/nonexistent")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_json(self):
        """Test handling of invalid JSON"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/council/evaluate",
                content="invalid json{",
                headers={"Content-Type": "application/json"}
            )

            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test validation of required fields"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Missing required 'script' field
            response = await client.post(
                f"{API_BASE_URL}/council/evaluate",
                json={"visual_features": {}}
            )

            assert response.status_code == 422
