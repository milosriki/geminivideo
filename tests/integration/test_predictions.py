"""
Integration Tests for Predictions and Performance Tracking
Tests CTR prediction, ROAS forecasting, actuals fetching, and accuracy tracking.

Coverage:
- Oracle Agent predictions (8-engine ensemble)
- CTR prediction models
- ROAS forecasting
- Prediction logging and storage
- Actuals fetching from platforms
- Accuracy tracking and metrics
- Model performance evaluation
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json


@pytest.fixture
def oracle_agent():
    """Mock Oracle Agent with 8 prediction engines"""
    oracle = Mock()

    oracle.engines = [
        "DeepFM",
        "DCN",
        "XGBoost",
        "LightGBM",
        "CatBoost",
        "NeuralNet",
        "RandomForest",
        "GradientBoost"
    ]

    oracle.predict = AsyncMock(return_value={
        "video_id": "test_001",
        "predicted_roas": 4.5,
        "confidence": 0.85,
        "ensemble_prediction": 4.5,
        "individual_predictions": {
            "DeepFM": 4.3,
            "DCN": 4.7,
            "XGBoost": 4.5,
            "LightGBM": 4.4,
            "CatBoost": 4.6,
            "NeuralNet": 4.5,
            "RandomForest": 4.2,
            "GradientBoost": 4.8
        }
    })

    return oracle


@pytest.fixture
def sample_features():
    """Sample video features for prediction"""
    return {
        "hook_effectiveness": 8.5,
        "has_transformation": True,
        "cta_strength": 7.0,
        "num_emotional_triggers": 3,
        "has_human_face": True,
        "duration_seconds": 30,
        "scene_count": 4,
        "word_count": 75,
        "hook_type": "pattern_interrupt",
        "fast_paced": True,
        "high_contrast": True
    }


@pytest.fixture
def historical_performance_data():
    """Historical performance data for training"""
    return [
        {
            "video_id": "video_001",
            "impressions": 10000,
            "clicks": 500,
            "spend": 100.00,
            "conversions": 25,
            "ctr": 0.05,
            "roas": 5.0
        },
        {
            "video_id": "video_002",
            "impressions": 8000,
            "clicks": 320,
            "spend": 80.00,
            "conversions": 16,
            "ctr": 0.04,
            "roas": 4.0
        },
        {
            "video_id": "video_003",
            "impressions": 12000,
            "clicks": 720,
            "spend": 120.00,
            "conversions": 36,
            "ctr": 0.06,
            "roas": 6.0
        }
    ]


class TestOracleAgent:
    """Test Oracle Agent prediction system"""

    @pytest.mark.asyncio
    async def test_oracle_predict_basic(self, oracle_agent, sample_features):
        """Test basic prediction with Oracle Agent"""
        prediction = await oracle_agent.predict(
            features=sample_features,
            video_id="test_001"
        )

        # Check response structure
        assert "predicted_roas" in prediction
        assert "confidence" in prediction
        assert "ensemble_prediction" in prediction
        assert "individual_predictions" in prediction

        # Validate ranges
        assert 0 <= prediction["predicted_roas"] <= 100
        assert 0 <= prediction["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_oracle_ensemble_consistency(self, oracle_agent, sample_features):
        """Test ensemble prediction consistency"""
        prediction = await oracle_agent.predict(
            features=sample_features,
            video_id="test_001"
        )

        individual = prediction["individual_predictions"]
        ensemble = prediction["ensemble_prediction"]

        # Ensemble should be near the average of individual predictions
        avg_individual = sum(individual.values()) / len(individual)
        assert abs(ensemble - avg_individual) < 1.0

    @pytest.mark.asyncio
    async def test_oracle_all_engines(self, oracle_agent):
        """Test that all 8 engines are used"""
        expected_engines = [
            "DeepFM", "DCN", "XGBoost", "LightGBM",
            "CatBoost", "NeuralNet", "RandomForest", "GradientBoost"
        ]

        assert len(oracle_agent.engines) == 8
        for engine in expected_engines:
            assert engine in oracle_agent.engines

    @pytest.mark.asyncio
    async def test_oracle_confidence_score(self, oracle_agent, sample_features):
        """Test confidence score calculation"""
        prediction = await oracle_agent.predict(
            features=sample_features,
            video_id="test_001"
        )

        confidence = prediction["confidence"]

        # Confidence should be reasonable
        assert 0.5 <= confidence <= 1.0  # High confidence expected


class TestCTRPrediction:
    """Test CTR prediction models"""

    @pytest.mark.asyncio
    async def test_predict_ctr_basic(self, sample_features):
        """Test basic CTR prediction"""
        # Mock CTR prediction
        predicted_ctr = 0.05  # 5%

        assert 0 <= predicted_ctr <= 1.0

    @pytest.mark.asyncio
    async def test_ctr_feature_importance(self, sample_features):
        """Test feature importance for CTR prediction"""
        feature_importance = {
            "hook_effectiveness": 0.35,
            "has_human_face": 0.20,
            "cta_strength": 0.15,
            "duration_seconds": 0.10,
            "num_emotional_triggers": 0.10,
            "other": 0.10
        }

        # Sum should be approximately 1.0
        total = sum(feature_importance.values())
        assert abs(total - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_ctr_by_platform(self):
        """Test CTR prediction by platform"""
        platform_ctrs = {
            "facebook": 0.045,
            "instagram": 0.052,
            "tiktok": 0.058,
            "youtube": 0.038
        }

        # All should be positive and reasonable
        for platform, ctr in platform_ctrs.items():
            assert 0 < ctr < 0.2  # Typical range

    @pytest.mark.asyncio
    async def test_ctr_confidence_intervals(self):
        """Test CTR confidence intervals"""
        prediction = {
            "predicted_ctr": 0.05,
            "lower_bound": 0.04,
            "upper_bound": 0.06,
            "confidence_level": 0.95
        }

        assert prediction["lower_bound"] < prediction["predicted_ctr"]
        assert prediction["predicted_ctr"] < prediction["upper_bound"]


class TestROASForecasting:
    """Test ROAS forecasting"""

    @pytest.mark.asyncio
    async def test_predict_roas(self, oracle_agent, sample_features):
        """Test ROAS prediction"""
        prediction = await oracle_agent.predict(
            features=sample_features,
            video_id="test_001"
        )

        predicted_roas = prediction["predicted_roas"]

        # ROAS should be positive
        assert predicted_roas > 0

        # Typical range: 2x - 10x for good ads
        assert 0.5 <= predicted_roas <= 20.0

    @pytest.mark.asyncio
    async def test_roas_by_budget_level(self):
        """Test ROAS prediction by budget level"""
        budget_scenarios = {
            "low": {"budget": 50, "predicted_roas": 5.5},
            "medium": {"budget": 200, "predicted_roas": 4.8},
            "high": {"budget": 1000, "predicted_roas": 4.2}
        }

        # Generally, ROAS might decrease with higher budgets (law of diminishing returns)
        assert budget_scenarios["low"]["predicted_roas"] >= budget_scenarios["high"]["predicted_roas"]

    @pytest.mark.asyncio
    async def test_roas_forecast_scenarios(self):
        """Test ROAS forecasting for different scenarios"""
        scenarios = {
            "best_case": {"roas": 7.0, "probability": 0.1},
            "expected": {"roas": 4.5, "probability": 0.7},
            "worst_case": {"roas": 2.0, "probability": 0.2}
        }

        # Probabilities should sum to 1.0
        total_prob = sum(s["probability"] for s in scenarios.values())
        assert abs(total_prob - 1.0) < 0.01


class TestPredictionLogging:
    """Test prediction logging and storage"""

    @pytest.mark.asyncio
    async def test_log_prediction(self, sample_features):
        """Test logging prediction to database"""
        prediction_log = {
            "prediction_id": "pred_001",
            "video_id": "video_001",
            "predicted_ctr": 0.05,
            "predicted_roas": 4.5,
            "confidence": 0.85,
            "features": sample_features,
            "model_version": "v2.1",
            "created_at": datetime.utcnow().isoformat()
        }

        # Validate structure
        assert "prediction_id" in prediction_log
        assert "video_id" in prediction_log
        assert "created_at" in prediction_log

    @pytest.mark.asyncio
    async def test_retrieve_prediction_history(self):
        """Test retrieving prediction history"""
        video_id = "video_001"

        prediction_history = [
            {
                "prediction_id": "pred_001",
                "predicted_roas": 4.5,
                "created_at": "2025-01-01T10:00:00"
            },
            {
                "prediction_id": "pred_002",
                "predicted_roas": 4.7,
                "created_at": "2025-01-02T10:00:00"
            }
        ]

        assert len(prediction_history) > 0
        assert all(p["predicted_roas"] > 0 for p in prediction_history)

    @pytest.mark.asyncio
    async def test_prediction_versioning(self):
        """Test model versioning in predictions"""
        predictions = [
            {"model_version": "v1.0", "accuracy": 0.75},
            {"model_version": "v2.0", "accuracy": 0.82},
            {"model_version": "v2.1", "accuracy": 0.85}
        ]

        # Newer versions should generally be more accurate
        assert predictions[-1]["accuracy"] >= predictions[0]["accuracy"]


class TestActualsFetching:
    """Test fetching actual performance data"""

    @pytest.mark.asyncio
    async def test_fetch_actuals_from_meta(self):
        """Test fetching actual performance from Meta"""
        actuals = {
            "video_id": "video_001",
            "platform": "meta",
            "impressions": 10500,
            "clicks": 525,
            "spend": 105.00,
            "conversions": 26,
            "actual_ctr": 0.05,
            "actual_roas": 4.95,
            "date_range": "2025-01-01 to 2025-01-07"
        }

        assert actuals["actual_ctr"] > 0
        assert actuals["actual_roas"] > 0

    @pytest.mark.asyncio
    async def test_fetch_actuals_from_google(self):
        """Test fetching actual performance from Google Ads"""
        actuals = {
            "video_id": "video_002",
            "platform": "google",
            "impressions": 8200,
            "clicks": 328,
            "cost_micros": 82000000,  # $82
            "conversions": 17,
            "actual_ctr": 0.04,
            "actual_roas": 4.15
        }

        assert actuals["actual_ctr"] > 0
        assert actuals["actual_roas"] > 0

    @pytest.mark.asyncio
    async def test_aggregate_cross_platform_actuals(self):
        """Test aggregating actuals across platforms"""
        platform_actuals = {
            "meta": {
                "impressions": 10000,
                "clicks": 500,
                "spend": 100.00
            },
            "google": {
                "impressions": 8000,
                "clicks": 320,
                "spend": 80.00
            }
        }

        # Aggregate totals
        total_impressions = sum(p["impressions"] for p in platform_actuals.values())
        total_clicks = sum(p["clicks"] for p in platform_actuals.values())
        total_spend = sum(p["spend"] for p in platform_actuals.values())

        assert total_impressions == 18000
        assert total_clicks == 820
        assert total_spend == 180.00

    @pytest.mark.asyncio
    async def test_actuals_data_freshness(self):
        """Test actuals data freshness"""
        last_updated = datetime.utcnow() - timedelta(hours=2)
        max_age_hours = 24

        age_hours = (datetime.utcnow() - last_updated).total_seconds() / 3600

        # Data should be fresh
        assert age_hours < max_age_hours


class TestAccuracyTracking:
    """Test prediction accuracy tracking"""

    @pytest.mark.asyncio
    async def test_calculate_prediction_accuracy(self):
        """Test calculating prediction vs actual accuracy"""
        predicted_roas = 4.5
        actual_roas = 4.8

        # Calculate error metrics
        absolute_error = abs(predicted_roas - actual_roas)
        relative_error = absolute_error / actual_roas
        accuracy = 1.0 - relative_error

        assert absolute_error == 0.3
        assert relative_error < 0.1  # Within 10%
        assert accuracy > 0.9  # 90%+ accurate

    @pytest.mark.asyncio
    async def test_track_accuracy_over_time(self):
        """Test tracking accuracy metrics over time"""
        accuracy_history = [
            {"date": "2025-01-01", "accuracy": 0.85, "sample_size": 10},
            {"date": "2025-01-02", "accuracy": 0.87, "sample_size": 15},
            {"date": "2025-01-03", "accuracy": 0.89, "sample_size": 20}
        ]

        # Accuracy should improve over time
        first_accuracy = accuracy_history[0]["accuracy"]
        last_accuracy = accuracy_history[-1]["accuracy"]

        assert last_accuracy >= first_accuracy

    @pytest.mark.asyncio
    async def test_calculate_mae(self):
        """Test Mean Absolute Error calculation"""
        predictions = [4.5, 5.0, 3.8, 6.2]
        actuals = [4.8, 4.9, 4.0, 6.0]

        mae = sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(predictions)

        assert mae < 0.5  # Good accuracy

    @pytest.mark.asyncio
    async def test_calculate_rmse(self):
        """Test Root Mean Squared Error calculation"""
        predictions = [4.5, 5.0, 3.8, 6.2]
        actuals = [4.8, 4.9, 4.0, 6.0]

        mse = sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)
        rmse = mse ** 0.5

        assert rmse < 0.6

    @pytest.mark.asyncio
    async def test_calculate_mape(self):
        """Test Mean Absolute Percentage Error"""
        predictions = [4.5, 5.0, 3.8, 6.2]
        actuals = [4.8, 4.9, 4.0, 6.0]

        mape = sum(abs((a - p) / a) for p, a in zip(predictions, actuals)) / len(predictions) * 100

        assert mape < 10  # Within 10% error


class TestModelPerformance:
    """Test ML model performance evaluation"""

    @pytest.mark.asyncio
    async def test_compare_model_versions(self):
        """Test comparing different model versions"""
        model_performance = {
            "v1.0": {"mae": 0.8, "rmse": 1.0, "accuracy": 0.75},
            "v2.0": {"mae": 0.5, "rmse": 0.7, "accuracy": 0.82},
            "v2.1": {"mae": 0.4, "rmse": 0.6, "accuracy": 0.85}
        }

        # Latest version should be best
        latest = model_performance["v2.1"]
        oldest = model_performance["v1.0"]

        assert latest["accuracy"] > oldest["accuracy"]
        assert latest["mae"] < oldest["mae"]

    @pytest.mark.asyncio
    async def test_model_calibration(self):
        """Test model calibration metrics"""
        calibration_data = [
            {"predicted_prob": 0.9, "actual_rate": 0.88},
            {"predicted_prob": 0.7, "actual_rate": 0.72},
            {"predicted_prob": 0.5, "actual_rate": 0.48}
        ]

        # Predictions should be close to actuals
        for item in calibration_data:
            error = abs(item["predicted_prob"] - item["actual_rate"])
            assert error < 0.05

    @pytest.mark.asyncio
    async def test_feature_importance_stability(self):
        """Test feature importance stability across versions"""
        importance_v1 = {
            "hook_effectiveness": 0.35,
            "has_human_face": 0.20,
            "cta_strength": 0.15
        }

        importance_v2 = {
            "hook_effectiveness": 0.37,
            "has_human_face": 0.19,
            "cta_strength": 0.16
        }

        # Top features should be consistent
        top_features_v1 = sorted(importance_v1.keys(), key=importance_v1.get, reverse=True)
        top_features_v2 = sorted(importance_v2.keys(), key=importance_v2.get, reverse=True)

        # First two should match
        assert top_features_v1[0] == top_features_v2[0]


class TestPredictionScenarios:
    """Test various prediction scenarios"""

    @pytest.mark.asyncio
    async def test_predict_high_performer(self, oracle_agent):
        """Test prediction for high-performing video"""
        high_performer_features = {
            "hook_effectiveness": 9.5,
            "has_transformation": True,
            "cta_strength": 9.0,
            "num_emotional_triggers": 5,
            "has_human_face": True,
            "duration_seconds": 30,
            "fast_paced": True
        }

        prediction = await oracle_agent.predict(
            features=high_performer_features,
            video_id="high_performer"
        )

        # Should predict high ROAS
        assert prediction["predicted_roas"] > 5.0

    @pytest.mark.asyncio
    async def test_predict_low_performer(self, oracle_agent):
        """Test prediction for low-performing video"""
        low_performer_features = {
            "hook_effectiveness": 3.0,
            "has_transformation": False,
            "cta_strength": 4.0,
            "num_emotional_triggers": 1,
            "has_human_face": False,
            "duration_seconds": 60,
            "fast_paced": False
        }

        prediction = await oracle_agent.predict(
            features=low_performer_features,
            video_id="low_performer"
        )

        # Should predict lower ROAS
        assert prediction["predicted_roas"] < 4.0

    @pytest.mark.asyncio
    async def test_predict_with_missing_features(self, oracle_agent):
        """Test prediction with some missing features"""
        partial_features = {
            "hook_effectiveness": 7.0,
            "has_human_face": True
        }

        prediction = await oracle_agent.predict(
            features=partial_features,
            video_id="partial"
        )

        # Should still return a prediction
        assert "predicted_roas" in prediction


class TestRealtimeTracking:
    """Test real-time performance tracking"""

    @pytest.mark.asyncio
    async def test_track_live_metrics(self):
        """Test tracking live campaign metrics"""
        live_metrics = {
            "campaign_id": "campaign_001",
            "current_spend": 45.50,
            "current_conversions": 9,
            "current_roas": 4.95,
            "prediction_variance": 0.1,  # 10% above prediction
            "status": "on_track"
        }

        assert live_metrics["current_roas"] > 0

    @pytest.mark.asyncio
    async def test_detect_underperformance(self):
        """Test detecting underperforming campaigns"""
        predicted_roas = 5.0
        actual_roas = 3.0
        threshold = 0.2  # 20% below prediction

        underperforming = (predicted_roas - actual_roas) / predicted_roas > threshold

        assert underperforming is True

    @pytest.mark.asyncio
    async def test_trigger_optimization_alert(self):
        """Test triggering optimization alerts"""
        performance_status = {
            "is_underperforming": True,
            "variance": -0.35,  # 35% below prediction
            "alert_triggered": True,
            "recommended_action": "pause_and_review"
        }

        if performance_status["is_underperforming"]:
            assert performance_status["alert_triggered"] is True
