"""
Test suite for Prediction Logger - €5M Investment Validation

This test suite demonstrates and validates the prediction logging system
for tracking ML model accuracy and ROI validation.

Run with:
    pytest test_prediction_logger.py -v

Or run directly:
    python test_prediction_logger.py
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from src.prediction_logger import PredictionLogger, log_prediction, update_prediction_with_actuals, get_model_accuracy


class TestPredictionLogger:
    """Test suite for PredictionLogger class."""

    @pytest.fixture
    async def logger(self):
        """Create a PredictionLogger instance."""
        return PredictionLogger()

    @pytest.mark.asyncio
    async def test_log_prediction_success(self, logger):
        """Test successfully logging a prediction."""
        prediction_id = await logger.log_prediction(
            video_id="video_test_001",
            ad_id="fb_ad_test_001",
            predicted_ctr=0.045,
            predicted_roas=3.2,
            predicted_conversion=0.012,
            council_score=0.87,
            hook_type="problem_solution",
            template_type="ugc_style",
            platform="meta",
            metadata={"model_version": "v2.1", "feature_set": "full"}
        )

        assert prediction_id is not None
        assert len(prediction_id) > 0
        print(f"✓ Successfully logged prediction: {prediction_id}")

    @pytest.mark.asyncio
    async def test_log_prediction_validation(self, logger):
        """Test prediction input validation."""
        # Test invalid CTR (> 1.0)
        with pytest.raises(ValueError, match="predicted_ctr must be between 0 and 1"):
            await logger.log_prediction(
                video_id="video_test_002",
                ad_id="fb_ad_test_002",
                predicted_ctr=1.5,  # Invalid
                predicted_roas=3.0,
                predicted_conversion=0.01,
                council_score=0.8,
                hook_type="testimonial",
                template_type="branded",
                platform="meta"
            )

        # Test invalid ROAS (negative)
        with pytest.raises(ValueError, match="predicted_roas must be non-negative"):
            await logger.log_prediction(
                video_id="video_test_003",
                ad_id="fb_ad_test_003",
                predicted_ctr=0.04,
                predicted_roas=-1.0,  # Invalid
                predicted_conversion=0.01,
                council_score=0.8,
                hook_type="testimonial",
                template_type="branded",
                platform="meta"
            )

        # Test invalid platform
        with pytest.raises(ValueError, match="platform must be one of"):
            await logger.log_prediction(
                video_id="video_test_004",
                ad_id="fb_ad_test_004",
                predicted_ctr=0.04,
                predicted_roas=3.0,
                predicted_conversion=0.01,
                council_score=0.8,
                hook_type="testimonial",
                template_type="branded",
                platform="invalid_platform"  # Invalid
            )

        print("✓ Input validation working correctly")

    @pytest.mark.asyncio
    async def test_update_with_actuals(self, logger):
        """Test updating prediction with actual performance."""
        # First, log a prediction
        prediction_id = await logger.log_prediction(
            video_id="video_test_005",
            ad_id="fb_ad_test_005",
            predicted_ctr=0.045,
            predicted_roas=3.2,
            predicted_conversion=0.012,
            council_score=0.87,
            hook_type="problem_solution",
            template_type="ugc_style",
            platform="meta"
        )

        # Update with actuals
        result = await logger.update_with_actuals(
            prediction_id=prediction_id,
            actual_ctr=0.048,  # Slightly higher than predicted
            actual_roas=3.5,   # Better than predicted
            actual_conversion=0.013,
            impressions=10000,
            clicks=480,
            spend=150.00
        )

        # Validate result
        assert result is not None
        assert result['prediction_id'] == prediction_id
        assert result['actual']['ctr'] == 0.048
        assert result['actual']['roas'] == 3.5
        assert result['errors']['ctr_error'] == pytest.approx(0.003, abs=0.001)
        assert result['accuracy']['overall_accuracy'] > 90.0  # Should be high accuracy

        print(f"✓ Updated prediction with actuals")
        print(f"  Overall Accuracy: {result['accuracy']['overall_accuracy']:.2f}%")
        print(f"  CTR Error: {result['errors']['ctr_error']:.4f}")
        print(f"  ROAS Error: {result['errors']['roas_error']:.2f}")

    @pytest.mark.asyncio
    async def test_get_pending_predictions(self, logger):
        """Test retrieving pending predictions."""
        # Log a prediction that should be pending
        await logger.log_prediction(
            video_id="video_test_006",
            ad_id="fb_ad_test_006",
            predicted_ctr=0.05,
            predicted_roas=2.8,
            predicted_conversion=0.015,
            council_score=0.75,
            hook_type="testimonial",
            template_type="branded",
            platform="meta"
        )

        # Get pending predictions (note: days_old=0 to include just-created)
        pending = await logger.get_pending_predictions(days_old=0)

        assert pending is not None
        assert len(pending) > 0
        assert all(p['actual'] is None for p in pending)

        print(f"✓ Found {len(pending)} pending predictions")

    @pytest.mark.asyncio
    async def test_get_model_performance_stats(self, logger):
        """Test getting model performance statistics."""
        # Create a prediction with actuals for stats
        prediction_id = await logger.log_prediction(
            video_id="video_test_007",
            ad_id="fb_ad_test_007",
            predicted_ctr=0.042,
            predicted_roas=3.0,
            predicted_conversion=0.011,
            council_score=0.82,
            hook_type="problem_solution",
            template_type="ugc_style",
            platform="meta"
        )

        await logger.update_with_actuals(
            prediction_id=prediction_id,
            actual_ctr=0.044,
            actual_roas=3.1,
            actual_conversion=0.012,
            impressions=15000,
            clicks=660,
            spend=200.00
        )

        # Get performance stats
        stats = await logger.get_model_performance_stats(days=30, platform="meta")

        assert stats is not None
        assert stats['total_predictions'] > 0
        print(f"✓ Performance stats retrieved")
        print(f"  Total Predictions: {stats['total_predictions']}")
        print(f"  With Actuals: {stats['predictions_with_actuals']}")
        if stats['avg_overall_accuracy']:
            print(f"  Avg Accuracy: {stats['avg_overall_accuracy']:.2f}%")

    @pytest.mark.asyncio
    async def test_get_prediction_by_id(self, logger):
        """Test retrieving a specific prediction by ID."""
        prediction_id = await logger.log_prediction(
            video_id="video_test_008",
            ad_id="fb_ad_test_008",
            predicted_ctr=0.038,
            predicted_roas=2.9,
            predicted_conversion=0.010,
            council_score=0.79,
            hook_type="testimonial",
            template_type="branded",
            platform="tiktok"
        )

        # Retrieve by ID
        prediction = await logger.get_prediction_by_id(prediction_id)

        assert prediction is not None
        assert prediction['id'] == prediction_id
        assert prediction['video_id'] == "video_test_008"
        assert prediction['platform'] == "tiktok"

        print(f"✓ Retrieved prediction by ID: {prediction_id}")

    @pytest.mark.asyncio
    async def test_get_predictions_by_video(self, logger):
        """Test retrieving all predictions for a video."""
        video_id = "video_test_009"

        # Log multiple predictions for same video
        pred1 = await logger.log_prediction(
            video_id=video_id,
            ad_id="fb_ad_test_009a",
            predicted_ctr=0.040,
            predicted_roas=3.0,
            predicted_conversion=0.011,
            council_score=0.80,
            hook_type="problem_solution",
            template_type="ugc_style",
            platform="meta"
        )

        pred2 = await logger.log_prediction(
            video_id=video_id,
            ad_id="tiktok_ad_test_009b",
            predicted_ctr=0.055,
            predicted_roas=2.5,
            predicted_conversion=0.013,
            council_score=0.78,
            hook_type="problem_solution",
            template_type="ugc_style",
            platform="tiktok"
        )

        # Retrieve all predictions for video
        predictions = await logger.get_predictions_by_video(video_id)

        assert len(predictions) == 2
        assert predictions[0]['video_id'] == video_id
        assert predictions[1]['video_id'] == video_id

        print(f"✓ Retrieved {len(predictions)} predictions for video {video_id}")

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions."""
        # Test log_prediction convenience function
        prediction_id = await log_prediction(
            video_id="video_test_010",
            ad_id="fb_ad_test_010",
            predicted_ctr=0.046,
            predicted_roas=3.3,
            predicted_conversion=0.012,
            council_score=0.85,
            hook_type="problem_solution",
            template_type="ugc_style",
            platform="meta"
        )

        assert prediction_id is not None

        # Test update convenience function
        result = await update_prediction_with_actuals(
            prediction_id=prediction_id,
            actual_ctr=0.047,
            actual_roas=3.4,
            actual_conversion=0.012,
            impressions=12000,
            clicks=564,
            spend=175.00
        )

        assert result is not None
        assert result['accuracy']['overall_accuracy'] > 95.0

        print(f"✓ Convenience functions working correctly")


class TestAccuracyCalculations:
    """Test accuracy calculation logic."""

    def test_calculate_accuracy_exact_match(self):
        """Test accuracy calculation with exact match."""
        logger = PredictionLogger()
        accuracy = logger._calculate_accuracy(0.045, 0.045)
        assert accuracy == 100.0
        print("✓ Exact match: 100% accuracy")

    def test_calculate_accuracy_close_match(self):
        """Test accuracy calculation with close match."""
        logger = PredictionLogger()
        accuracy = logger._calculate_accuracy(0.045, 0.048)
        # Error is 0.003, which is 0.003/0.048 = 6.25% error
        # Accuracy should be 93.75%
        assert 93.0 < accuracy < 94.0
        print(f"✓ Close match: {accuracy:.2f}% accuracy")

    def test_calculate_accuracy_poor_match(self):
        """Test accuracy calculation with poor match."""
        logger = PredictionLogger()
        accuracy = logger._calculate_accuracy(0.045, 0.090)
        # Error is 0.045, which is 0.045/0.090 = 50% error
        # Accuracy should be 50%
        assert 49.0 < accuracy < 51.0
        print(f"✓ Poor match: {accuracy:.2f}% accuracy")

    def test_calculate_accuracy_zero_actual(self):
        """Test accuracy calculation with zero actual value."""
        logger = PredictionLogger()

        # Both zero = perfect
        accuracy = logger._calculate_accuracy(0.0, 0.0)
        assert accuracy == 100.0

        # Predicted non-zero, actual zero = 0% accuracy
        accuracy = logger._calculate_accuracy(0.045, 0.0)
        assert accuracy == 0.0

        print("✓ Zero actual value handling correct")


async def demo_full_workflow():
    """
    Demonstrate complete prediction logging workflow.
    This simulates a real-world scenario.
    """
    print("\n" + "="*70)
    print("PREDICTION LOGGER DEMO - Full Workflow")
    print("="*70 + "\n")

    logger = PredictionLogger()

    # Step 1: Log predictions for multiple videos
    print("Step 1: Logging predictions for 3 videos...")
    predictions = []

    for i in range(1, 4):
        pred_id = await logger.log_prediction(
            video_id=f"demo_video_{i}",
            ad_id=f"fb_ad_demo_{i}",
            predicted_ctr=0.040 + (i * 0.005),
            predicted_roas=3.0 + (i * 0.2),
            predicted_conversion=0.010 + (i * 0.002),
            council_score=0.80 + (i * 0.03),
            hook_type="problem_solution" if i % 2 == 1 else "testimonial",
            template_type="ugc_style" if i % 2 == 1 else "branded",
            platform="meta",
            metadata={"campaign": "demo_campaign", "test_run": True}
        )
        predictions.append(pred_id)
        print(f"  ✓ Logged prediction {i}: {pred_id}")

    # Step 2: Simulate waiting for campaign results
    print("\nStep 2: Simulating campaign run (in production, wait 7+ days)...")
    print("  ... campaigns running ...")

    # Step 3: Update with actual results
    print("\nStep 3: Updating predictions with actual performance...")
    actual_results = [
        {"ctr": 0.042, "roas": 3.1, "conversion": 0.011, "impressions": 10000, "clicks": 420, "spend": 150},
        {"ctr": 0.051, "roas": 3.5, "conversion": 0.014, "impressions": 12000, "clicks": 612, "spend": 180},
        {"ctr": 0.048, "roas": 3.3, "conversion": 0.015, "impressions": 9000, "clicks": 432, "spend": 140}
    ]

    for i, pred_id in enumerate(predictions):
        actuals = actual_results[i]
        result = await logger.update_with_actuals(
            prediction_id=pred_id,
            actual_ctr=actuals["ctr"],
            actual_roas=actuals["roas"],
            actual_conversion=actuals["conversion"],
            impressions=actuals["impressions"],
            clicks=actuals["clicks"],
            spend=actuals["spend"]
        )
        print(f"  ✓ Video {i+1} Accuracy: {result['accuracy']['overall_accuracy']:.2f}%")
        print(f"    - CTR: predicted {result['predicted']['ctr']:.4f}, actual {result['actual']['ctr']:.4f}")
        print(f"    - ROAS: predicted {result['predicted']['roas']:.2f}, actual {result['actual']['roas']:.2f}")

    # Step 4: Get overall model performance
    print("\nStep 4: Analyzing overall model performance...")
    stats = await logger.get_model_performance_stats(days=30, platform="meta")
    print(f"  Total Predictions: {stats['total_predictions']}")
    print(f"  With Actuals: {stats['predictions_with_actuals']}")
    if stats['avg_overall_accuracy']:
        print(f"  Average Accuracy: {stats['avg_overall_accuracy']:.2f}%")
        print(f"  Avg CTR Error: {stats['avg_ctr_error']:.5f}")
        print(f"  Avg ROAS Error: {stats['avg_roas_error']:.2f}")

    # Step 5: Check pending predictions
    print("\nStep 5: Checking for predictions needing actuals...")
    pending = await logger.get_pending_predictions(days_old=0)
    print(f"  Found {len(pending)} predictions pending actuals")

    print("\n" + "="*70)
    print("DEMO COMPLETE - Prediction logging system validated!")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_full_workflow())

    print("\nTo run full test suite, use: pytest test_prediction_logger.py -v")
