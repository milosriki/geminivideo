"""Integration tests for ML feedback loop.

Tests verify that the ML service learns from user feedback and
improves predictions over time.
"""
import pytest
import httpx
import asyncio
from datetime import datetime


class TestFeedbackLoop:
    """Test that ML feedback loop is working and learning"""

    BASE_URL = "http://localhost:8000"
    ML_URL = "http://localhost:8003"

    @pytest.mark.asyncio
    async def test_feedback_endpoint_exists(self):
        """Verify feedback endpoint is available"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/api/feedback",
                json={
                    "video_id": "test_video_1",
                    "prediction": {"virality_score": 7.5},
                    "actual": {"impressions": 50000, "engagement_rate": 0.08},
                    "feedback_type": "performance"
                }
            )

            # Should not return 404
            assert resp.status_code != 404, "Feedback endpoint doesn't exist"
            # Should accept feedback (200) or indicate processing (202)
            assert resp.status_code in [200, 202, 201], f"Unexpected status: {resp.status_code}"

    @pytest.mark.asyncio
    async def test_feedback_stored(self):
        """Verify feedback is stored in database"""
        async with httpx.AsyncClient() as client:
            # Submit feedback
            video_id = f"test_video_{datetime.now().timestamp()}"
            feedback_data = {
                "video_id": video_id,
                "prediction": {"virality_score": 6.0},
                "actual": {"impressions": 30000, "engagement_rate": 0.05},
                "feedback_type": "performance"
            }

            resp = await client.post(
                f"{self.BASE_URL}/api/feedback",
                json=feedback_data
            )

            if resp.status_code in [200, 201, 202]:
                # Try to retrieve feedback history
                history_resp = await client.get(
                    f"{self.BASE_URL}/api/feedback/history",
                    params={"video_id": video_id}
                )

                if history_resp.status_code == 200:
                    history = history_resp.json()
                    assert len(history) > 0, "Feedback was not stored"

    @pytest.mark.asyncio
    async def test_ml_model_updates(self):
        """Verify ML model can be retrained with feedback"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Check if ML service has training endpoint
            resp = await client.post(
                f"{self.ML_URL}/train",
                json={"trigger": "test"}
            )

            # Should not return 404 (endpoint exists)
            assert resp.status_code != 404, "ML training endpoint doesn't exist"

    @pytest.mark.asyncio
    async def test_predictions_improve_with_feedback(self):
        """Verify predictions change after feedback (learning indicator)"""
        async with httpx.AsyncClient() as client:
            test_video = "test_learning_video.mp4"

            # Get initial prediction
            resp1 = await client.post(
                f"{self.BASE_URL}/api/analyze",
                json={"video_uri": test_video}
            )

            if resp1.status_code != 200:
                pytest.skip("Analyze endpoint not working")

            initial_prediction = resp1.json()

            # Submit feedback indicating prediction was wrong
            await client.post(
                f"{self.BASE_URL}/api/feedback",
                json={
                    "video_id": test_video,
                    "prediction": initial_prediction,
                    "actual": {
                        "impressions": 100000,  # Much higher than predicted
                        "engagement_rate": 0.15
                    },
                    "feedback_type": "correction"
                }
            )

            # Trigger model update
            await client.post(
                f"{self.ML_URL}/train",
                json={"trigger": "test"}
            )

            # Wait a bit for model to update
            await asyncio.sleep(2)

            # Get new prediction
            resp2 = await client.post(
                f"{self.BASE_URL}/api/analyze",
                json={"video_uri": test_video}
            )

            if resp2.status_code == 200:
                new_prediction = resp2.json()

                # Predictions should differ (model learned)
                # Note: This is a weak test - in production you'd want
                # to verify the prediction moved in the right direction
                assert initial_prediction != new_prediction, \
                    "Model didn't update after feedback"

    @pytest.mark.asyncio
    async def test_feedback_metrics_tracked(self):
        """Verify system tracks feedback accuracy metrics"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.ML_URL}/metrics")

            if resp.status_code == 200:
                metrics = resp.json()

                # Should track accuracy/error metrics
                metric_keys = str(metrics).lower()
                has_accuracy_metrics = any(
                    term in metric_keys for term in
                    ["accuracy", "error", "mse", "rmse", "mae", "loss"]
                )

                assert has_accuracy_metrics, "No accuracy metrics tracked"

    @pytest.mark.asyncio
    async def test_feedback_data_quality(self):
        """Verify feedback data is validated"""
        async with httpx.AsyncClient() as client:
            # Submit invalid feedback (missing required fields)
            resp = await client.post(
                f"{self.BASE_URL}/api/feedback",
                json={"invalid": "data"}
            )

            # Should reject invalid data (400 or 422)
            assert resp.status_code in [400, 422], \
                "System accepts invalid feedback data"

    @pytest.mark.asyncio
    async def test_user_feedback_integration(self):
        """Verify user thumbs up/down feedback is captured"""
        async with httpx.AsyncClient() as client:
            # Submit user feedback
            resp = await client.post(
                f"{self.BASE_URL}/api/feedback/user",
                json={
                    "video_id": "test_user_feedback",
                    "suggestion_id": "suggestion_123",
                    "rating": "positive",
                    "comment": "This suggestion was helpful"
                }
            )

            # Should accept user feedback
            assert resp.status_code in [200, 201, 202], \
                "User feedback endpoint not working"

    @pytest.mark.asyncio
    async def test_ab_test_tracking(self):
        """Verify A/B test results are tracked"""
        async with httpx.AsyncClient() as client:
            # Check if A/B test tracking exists
            resp = await client.post(
                f"{self.BASE_URL}/api/feedback/ab-test",
                json={
                    "experiment_id": "test_exp_1",
                    "variant": "A",
                    "video_id": "test_video",
                    "outcome": {"clicks": 100, "impressions": 1000}
                }
            )

            # Should not return 404
            assert resp.status_code != 404, "A/B test tracking not implemented"

    @pytest.mark.asyncio
    async def test_continuous_learning_pipeline(self):
        """Verify continuous learning pipeline exists"""
        async with httpx.AsyncClient() as client:
            # Check for scheduled training status
            resp = await client.get(f"{self.ML_URL}/training/status")

            if resp.status_code == 200:
                status = resp.json()

                # Should have info about training schedule/history
                has_training_info = any(
                    key in status for key in
                    ["last_trained", "next_training", "training_frequency", "status"]
                )

                assert has_training_info, "No continuous learning pipeline info"
