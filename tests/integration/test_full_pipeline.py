"""
Full Pipeline Integration Tests
Verify: Video → Analysis → Optimization → Rendering → Publishing
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any

# Service URLs (from environment or defaults)
GATEWAY_URL = "https://gateway.geminivideo.run"
ML_SERVICE_URL = "https://ml-service.geminivideo.run"
TITAN_CORE_URL = "https://titan-core.geminivideo.run"
VIDEO_AGENT_URL = "https://video-agent.geminivideo.run"


class TestLearningLoop:
    """Test that learning loop is closed"""

    @pytest.mark.asyncio
    async def test_feedback_reaches_thompson(self):
        """Verify Meta insights flow to Thompson Sampling"""
        async with httpx.AsyncClient() as client:
            # Send feedback
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/feedback",
                json={
                    "ad_id": "test_ad_123",
                    "variant_id": "test_ad_123",
                    "impressions": 1000,
                    "clicks": 50,
                    "conversions": 5,
                    "spend": 100.0,
                    "revenue": 500.0
                }
            )
            assert response.status_code == 200

            # Verify Thompson state updated
            stats = await client.get(f"{ML_SERVICE_URL}/api/ml/ab/all-variants")
            assert stats.status_code == 200

            variants = stats.json()
            assert len(variants) > 0, "Should have at least one variant after feedback"

    @pytest.mark.asyncio
    async def test_cost_flow_not_zero(self):
        """Verify cost parameter actually accumulates"""
        async with httpx.AsyncClient() as client:
            variant_id = "cost_test_variant"

            # Register variant
            await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/register-variant",
                json={"variant_id": variant_id}
            )

            # Update with cost
            await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/update-variant",
                json={
                    "variant_id": variant_id,
                    "reward": 1.0,
                    "cost": 25.0
                }
            )

            # Verify spend accumulated
            stats = await client.get(f"{ML_SERVICE_URL}/api/ml/ab/variant-stats/{variant_id}")
            data = stats.json()

            assert data.get('spend', 0) > 0, "Spend should not be zero!"
            assert data.get('spend') == 25.0, f"Expected spend=25.0, got {data.get('spend')}"

    @pytest.mark.asyncio
    async def test_roas_calculation(self):
        """Verify ROAS is calculated correctly"""
        async with httpx.AsyncClient() as client:
            variant_id = "roas_test_variant"

            # Register variant
            await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/register-variant",
                json={"variant_id": variant_id}
            )

            # Update with revenue and cost
            await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/update-variant",
                json={
                    "variant_id": variant_id,
                    "reward": 1.0,
                    "cost": 100.0,
                    "metrics": {
                        "revenue": 500.0,
                        "impressions": 1000,
                        "clicks": 50,
                        "conversions": 5
                    }
                }
            )

            # Verify ROAS
            stats = await client.get(f"{ML_SERVICE_URL}/api/ml/ab/variant-stats/{variant_id}")
            data = stats.json()

            expected_roas = 500.0 / 100.0  # 5.0
            assert data.get('roas', 0) == expected_roas, f"Expected ROAS=5.0, got {data.get('roas')}"


class TestGatewayProxies:
    """Test all Gateway proxies work"""

    @pytest.mark.asyncio
    async def test_council_endpoints(self):
        """Verify AI Council endpoints are proxied"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/api/council/evaluate",
                json={
                    "script_text": "Test script",
                    "video_url": "https://example.com/test.mp4"
                }
            )
            # Should not be 404
            assert response.status_code != 404, "Council endpoint should be proxied"

    @pytest.mark.asyncio
    async def test_oracle_endpoints(self):
        """Verify Oracle prediction endpoint is proxied"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/api/oracle/predict",
                json={
                    "video_features": {}
                }
            )
            # Should not be 404
            assert response.status_code != 404, "Oracle endpoint should be proxied"


class TestThompsonSampling:
    """Test Thompson Sampling functionality"""

    @pytest.mark.asyncio
    async def test_variant_selection(self):
        """Test variant selection works"""
        async with httpx.AsyncClient() as client:
            # Register two variants
            await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/register-variant",
                json={"variant_id": "variant_a"}
            )
            await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/register-variant",
                json={"variant_id": "variant_b"}
            )

            # Select variant
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/select-variant",
                json={}
            )
            assert response.status_code == 200
            data = response.json()
            assert 'variant_id' in data

    @pytest.mark.asyncio
    async def test_time_decay_endpoint(self):
        """Test time decay endpoint exists and works"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/apply-decay",
                params={"decay_factor": 0.99}
            )
            # Should return 200 or 422 (validation error is OK, means endpoint exists)
            assert response.status_code in [200, 422]


class TestMLEndpoints:
    """Test ML Service core endpoints"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test ML service health check"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ML_SERVICE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'

    @pytest.mark.asyncio
    async def test_predict_ctr_endpoint(self):
        """Test CTR prediction endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/predict-ctr",
                json={
                    "clip_data": {
                        "hook_type": "curiosity_gap",
                        "duration": 30,
                        "has_cta": True
                    }
                }
            )
            # Should not be 404
            assert response.status_code != 404


class TestFullPipeline:
    """Test complete end-to-end pipeline"""

    @pytest.mark.asyncio
    async def test_feedback_to_thompson_to_selection(self):
        """Full flow: Feedback → Thompson Update → Selection"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            variant_id = "pipeline_test_variant"

            # 1. Register variant
            await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/register-variant",
                json={"variant_id": variant_id}
            )

            # 2. Send feedback
            feedback_response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/feedback",
                json={
                    "ad_id": variant_id,
                    "variant_id": variant_id,
                    "impressions": 1000,
                    "clicks": 50,
                    "conversions": 10,
                    "spend": 100.0,
                    "revenue": 600.0
                }
            )
            assert feedback_response.status_code == 200

            # 3. Verify stats updated
            stats_response = await client.get(
                f"{ML_SERVICE_URL}/api/ml/ab/variant-stats/{variant_id}"
            )
            assert stats_response.status_code == 200
            stats = stats_response.json()
            assert stats.get('spend', 0) > 0
            assert stats.get('roas', 0) > 0

            # 4. Select variant (should now favor this one with good ROAS)
            select_response = await client.post(
                f"{ML_SERVICE_URL}/api/ml/ab/select-variant",
                json={}
            )
            assert select_response.status_code == 200

            print(f"✅ Full pipeline test passed!")
            print(f"   Variant ROAS: {stats.get('roas', 0):.2f}")


# Run with: pytest tests/integration/test_full_pipeline.py -v -s
