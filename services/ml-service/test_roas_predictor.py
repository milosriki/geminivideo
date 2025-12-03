"""
Test suite for ROAS Predictor - Agent 16
Demonstrates real ML functionality with XGBoost + LightGBM ensemble.
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest decorators if not available
    class pytest:
        class fixture:
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, func):
                return func

import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from roas_predictor import ROASPredictor, FeatureSet, ROASPrediction


class TestROASPredictor:
    """Test suite for ROAS Predictor."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample training data."""
        np.random.seed(42)
        n_samples = 500

        # Generate realistic campaign data
        data = {
            # Creative features
            'hook_type': np.random.choice(['problem_solution', 'testimonial', 'demo', 'ugc'], n_samples),
            'hook_strength': np.random.uniform(5, 10, n_samples),
            'visual_complexity': np.random.uniform(3, 9, n_samples),
            'text_density': np.random.uniform(0.05, 0.3, n_samples),
            'face_presence': np.random.choice([True, False], n_samples),
            'motion_score': np.random.uniform(5, 10, n_samples),
            'video_duration': np.random.uniform(6, 60, n_samples),
            'aspect_ratio': np.random.choice([0.5625, 1.0, 1.7778], n_samples),  # 9:16, 1:1, 16:9
            'color_vibrancy': np.random.uniform(4, 10, n_samples),
            'scene_count': np.random.randint(1, 8, n_samples),

            # Targeting features
            'audience_size': np.random.randint(500000, 5000000, n_samples),
            'audience_overlap': np.random.uniform(0.05, 0.4, n_samples),
            'cpm_estimate': np.random.uniform(8, 25, n_samples),
            'age_min': np.random.choice([18, 25, 35, 45], n_samples),
            'age_max': np.random.choice([34, 44, 54, 65], n_samples),
            'gender_targeting': np.random.choice(['all', 'male', 'female'], n_samples),
            'interest_count': np.random.randint(3, 15, n_samples),
            'custom_audience': np.random.choice([True, False], n_samples),

            # Historical features
            'account_avg_roas': np.random.uniform(1.5, 5.0, n_samples),
            'account_avg_ctr': np.random.uniform(0.8, 3.0, n_samples),
            'vertical_avg_roas': np.random.uniform(1.8, 4.5, n_samples),
            'similar_creative_roas': np.random.uniform(1.5, 5.5, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples),
            'hour_of_day': np.random.randint(0, 24, n_samples),
            'days_since_last_winner': np.random.randint(1, 60, n_samples),
            'account_spend_30d': np.random.uniform(10000, 200000, n_samples),
            'account_conversions_30d': np.random.randint(50, 1000, n_samples),
            'creative_fatigue_score': np.random.uniform(0, 0.8, n_samples),

            # Copy features
            'cta_type': np.random.choice(['shop_now', 'learn_more', 'sign_up', 'get_offer'], n_samples),
            'urgency_score': np.random.uniform(3, 10, n_samples),
            'benefit_count': np.random.randint(1, 6, n_samples),
            'pain_point_addressed': np.random.choice([True, False], n_samples),
            'social_proof_present': np.random.choice([True, False], n_samples),
            'word_count': np.random.randint(20, 100, n_samples),
            'emoji_count': np.random.randint(0, 8, n_samples),
            'question_present': np.random.choice([True, False], n_samples),
        }

        df = pd.DataFrame(data)

        # Generate synthetic ROAS based on key features
        roas = (
            df['hook_strength'] * 0.3 +
            df['motion_score'] * 0.25 +
            df['account_avg_roas'] * 0.5 +
            df['similar_creative_roas'] * 0.4 +
            (df['face_presence'].astype(int) * 0.5) +
            (df['social_proof_present'].astype(int) * 0.3) +
            df['urgency_score'] * 0.2 +
            np.random.normal(0, 0.5, n_samples)  # Add noise
        )

        # Normalize to realistic ROAS range (0.5 to 8.0)
        roas = (roas - roas.min()) / (roas.max() - roas.min()) * 7.5 + 0.5
        df['actual_roas'] = roas

        return df

    @pytest.fixture
    def trained_predictor(self, sample_data):
        """Create and train a predictor."""
        predictor = ROASPredictor()
        predictor.train(sample_data)
        return predictor

    def test_initialization(self):
        """Test predictor initialization."""
        predictor = ROASPredictor()
        assert predictor.xgb_model is None
        assert predictor.lgb_model is None
        assert predictor.ensemble is None
        assert predictor.scaler is not None

    def test_training(self, sample_data):
        """Test model training."""
        predictor = ROASPredictor()
        metrics = predictor.train(sample_data)

        # Check metrics exist
        assert 'r2_score' in metrics
        assert 'mae' in metrics
        assert 'rmse' in metrics

        # Check reasonable performance
        assert metrics['r2_score'] > 0.5  # Should explain variance
        assert metrics['mae'] < 2.0  # Reasonable error

        # Check models trained
        assert predictor.xgb_model is not None
        assert predictor.lgb_model is not None
        assert predictor.ensemble is not None

    def test_prediction(self, trained_predictor):
        """Test single prediction."""
        features = FeatureSet(
            hook_strength=8.5,
            motion_score=9.0,
            face_presence=True,
            account_avg_roas=4.0,
            similar_creative_roas=4.5,
            social_proof_present=True,
            urgency_score=8.0
        )

        prediction = trained_predictor.predict_roas(features)

        # Check prediction structure
        assert isinstance(prediction, ROASPrediction)
        assert prediction.predicted_roas > 0
        assert prediction.confidence_low < prediction.predicted_roas
        assert prediction.confidence_high > prediction.predicted_roas
        assert 0 <= prediction.confidence_score <= 1
        assert len(prediction.feature_contributions) > 0

    def test_batch_prediction(self, trained_predictor):
        """Test batch prediction."""
        features_list = [
            FeatureSet(hook_strength=8.0, motion_score=8.5),
            FeatureSet(hook_strength=6.0, motion_score=5.5),
            FeatureSet(hook_strength=9.0, motion_score=9.5)
        ]

        predictions = trained_predictor.predict_batch(features_list)

        assert len(predictions) == 3
        assert all(isinstance(p, ROASPrediction) for p in predictions)
        assert all(p.predicted_roas > 0 for p in predictions)

    def test_feature_importance(self, trained_predictor):
        """Test feature importance calculation."""
        importance = trained_predictor.get_feature_importance()

        assert len(importance) == len(ROASPredictor.FEATURE_COLUMNS)
        assert all(v >= 0 for v in importance.values())
        assert sum(importance.values()) > 0

    def test_top_features(self, trained_predictor):
        """Test top features extraction."""
        top_features = trained_predictor.get_top_features(n=5)

        assert len(top_features) == 5
        assert all(isinstance(f[0], str) for f in top_features)
        assert all(isinstance(f[1], float) for f in top_features)

        # Check sorted by importance
        importances = [f[1] for f in top_features]
        assert importances == sorted(importances, reverse=True)

    def test_confidence_interval(self, trained_predictor):
        """Test confidence interval calculation."""
        features = FeatureSet()

        conf_low, conf_high = trained_predictor.confidence_interval(features)

        assert conf_low >= 0  # ROAS can't be negative
        assert conf_high > conf_low
        assert conf_high - conf_low > 0  # Non-zero interval

    def test_prediction_uncertainty(self, trained_predictor):
        """Test uncertainty score calculation."""
        features = FeatureSet()

        uncertainty = trained_predictor.get_prediction_uncertainty(features)

        assert 0 <= uncertainty <= 1

    def test_explain_prediction(self, trained_predictor):
        """Test SHAP explanation."""
        features = FeatureSet()

        explanation = trained_predictor.explain_prediction(features)

        assert 'base_value' in explanation
        assert 'predicted_value' in explanation
        assert 'shap_values' in explanation
        assert 'top_positive_features' in explanation
        assert 'top_negative_features' in explanation

        # Check SHAP values sum approximately to prediction
        shap_sum = sum(explanation['shap_values'].values())
        expected = explanation['predicted_value'] - explanation['base_value']
        assert abs(shap_sum - expected) < 0.01

    def test_model_persistence(self, trained_predictor):
        """Test model save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model"

            # Save model
            trained_predictor.save_model(str(model_path))

            # Check files exist
            assert (model_path / 'xgb_model.pkl').exists()
            assert (model_path / 'lgb_model.pkl').exists()
            assert (model_path / 'scaler.pkl').exists()
            assert (model_path / 'metadata.json').exists()

            # Load model
            new_predictor = ROASPredictor()
            new_predictor.load_model(str(model_path))

            # Check models loaded
            assert new_predictor.xgb_model is not None
            assert new_predictor.lgb_model is not None
            assert new_predictor.ensemble is not None

            # Check predictions match
            features = FeatureSet()
            pred1 = trained_predictor.predict_roas(features, return_explanation=False)
            pred2 = new_predictor.predict_roas(features, return_explanation=False)

            assert abs(pred1.predicted_roas - pred2.predicted_roas) < 0.01

    def test_model_drift_detection(self, trained_predictor, sample_data):
        """Test model drift detection."""
        # Use a subset of training data
        recent_data = sample_data.sample(n=100, random_state=42)

        drift_metrics = trained_predictor.evaluate_model_drift(recent_data)

        assert 'current_r2' in drift_metrics
        assert 'current_mae' in drift_metrics
        assert 'drift_detected' in drift_metrics
        assert 'recommendation' in drift_metrics

    def test_retraining_recommendation(self, trained_predictor):
        """Test retraining recommendation."""
        recommendation = trained_predictor.get_retraining_recommendation()

        assert 'should_retrain' in recommendation
        assert 'reason' in recommendation
        assert 'days_since_training' in recommendation

    def test_feature_engineering(self, trained_predictor):
        """Test feature engineering from raw data."""
        raw_data = {
            'hook_type': 'problem_solution',
            'hook_strength': 8.5,
            'motion_score': 9.0,
            'account_avg_roas': 4.0
        }

        features = trained_predictor.engineer_features(raw_data)

        assert isinstance(features, FeatureSet)
        assert features.hook_type == 'problem_solution'
        assert features.hook_strength == 8.5
        assert features.motion_score == 9.0
        assert features.account_avg_roas == 4.0

        # Check defaults filled in
        assert features.video_duration > 0
        assert features.audience_size > 0

    def test_categorical_encoding(self, trained_predictor):
        """Test categorical feature encoding."""
        # Test known category
        encoded = trained_predictor._encode_categorical('hook_type', 'problem_solution')
        assert isinstance(encoded, (int, np.integer))

        # Test unknown category (should return 0 with warning)
        encoded = trained_predictor._encode_categorical('hook_type', 'unknown_hook')
        assert encoded == 0

    def test_high_performing_creative(self, trained_predictor):
        """Test prediction for high-performing creative."""
        features = FeatureSet(
            hook_type='problem_solution',
            hook_strength=9.5,
            visual_complexity=7.5,
            face_presence=True,
            motion_score=9.0,
            video_duration=15.0,
            account_avg_roas=4.5,
            similar_creative_roas=5.0,
            social_proof_present=True,
            urgency_score=9.0,
            benefit_count=4
        )

        prediction = trained_predictor.predict_roas(features)

        # Should predict high ROAS
        assert prediction.predicted_roas > 2.0  # Above average
        assert prediction.confidence_score > 0.5

    def test_low_performing_creative(self, trained_predictor):
        """Test prediction for low-performing creative."""
        features = FeatureSet(
            hook_strength=3.0,
            motion_score=4.0,
            face_presence=False,
            account_avg_roas=1.5,
            similar_creative_roas=1.0,
            social_proof_present=False,
            urgency_score=3.0
        )

        prediction = trained_predictor.predict_roas(features)

        # Should predict lower ROAS
        assert prediction.predicted_roas < 5.0

    def test_feature_contributions(self, trained_predictor):
        """Test that feature contributions are meaningful."""
        features = FeatureSet(
            hook_strength=9.5,  # Very high
            motion_score=9.0,   # Very high
            account_avg_roas=5.0  # Very high
        )

        prediction = trained_predictor.predict_roas(features)

        # Check that important features have non-zero contributions
        contributions = prediction.feature_contributions

        # Should have contributions from key features
        assert 'hook_strength' in contributions
        assert 'motion_score' in contributions
        assert 'account_avg_roas' in contributions


def test_end_to_end_workflow():
    """Test complete workflow from training to prediction."""
    # Generate data
    np.random.seed(42)
    n_samples = 300

    data = {
        'hook_type': np.random.choice(['problem_solution', 'testimonial'], n_samples),
        'hook_strength': np.random.uniform(5, 10, n_samples),
        'visual_complexity': np.random.uniform(3, 9, n_samples),
        'text_density': np.random.uniform(0.05, 0.3, n_samples),
        'face_presence': np.random.choice([True, False], n_samples),
        'motion_score': np.random.uniform(5, 10, n_samples),
        'video_duration': np.random.uniform(10, 30, n_samples),
        'aspect_ratio': np.random.choice([0.5625, 1.0], n_samples),
        'color_vibrancy': np.random.uniform(5, 10, n_samples),
        'scene_count': np.random.randint(2, 6, n_samples),
        'audience_size': np.random.randint(1000000, 3000000, n_samples),
        'audience_overlap': np.random.uniform(0.1, 0.3, n_samples),
        'cpm_estimate': np.random.uniform(10, 20, n_samples),
        'age_min': np.random.choice([25, 35], n_samples),
        'age_max': np.random.choice([44, 54], n_samples),
        'gender_targeting': np.random.choice(['all', 'female'], n_samples),
        'interest_count': np.random.randint(3, 10, n_samples),
        'custom_audience': np.random.choice([True, False], n_samples),
        'account_avg_roas': np.random.uniform(2.5, 4.5, n_samples),
        'account_avg_ctr': np.random.uniform(1.0, 2.5, n_samples),
        'vertical_avg_roas': np.random.uniform(2.0, 4.0, n_samples),
        'similar_creative_roas': np.random.uniform(2.0, 5.0, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'hour_of_day': np.random.randint(8, 20, n_samples),
        'days_since_last_winner': np.random.randint(3, 30, n_samples),
        'account_spend_30d': np.random.uniform(30000, 100000, n_samples),
        'account_conversions_30d': np.random.randint(200, 800, n_samples),
        'creative_fatigue_score': np.random.uniform(0, 0.5, n_samples),
        'cta_type': np.random.choice(['shop_now', 'learn_more'], n_samples),
        'urgency_score': np.random.uniform(5, 10, n_samples),
        'benefit_count': np.random.randint(2, 5, n_samples),
        'pain_point_addressed': np.random.choice([True, False], n_samples),
        'social_proof_present': np.random.choice([True, False], n_samples),
        'word_count': np.random.randint(30, 80, n_samples),
        'emoji_count': np.random.randint(1, 5, n_samples),
        'question_present': np.random.choice([True, False], n_samples),
    }

    df = pd.DataFrame(data)

    # Synthetic ROAS
    df['actual_roas'] = (
        df['hook_strength'] * 0.4 +
        df['account_avg_roas'] * 0.6 +
        np.random.normal(0, 0.3, n_samples)
    )
    df['actual_roas'] = df['actual_roas'].clip(0.5, 8.0)

    # Train
    predictor = ROASPredictor()
    metrics = predictor.train(df)

    assert metrics['r2_score'] > 0.3

    # Predict
    features = FeatureSet(
        hook_strength=8.5,
        motion_score=8.0,
        account_avg_roas=3.5
    )

    prediction = predictor.predict_roas(features)
    assert prediction.predicted_roas > 0

    # Save and reload
    with tempfile.TemporaryDirectory() as tmpdir:
        predictor.save_model(tmpdir)

        new_predictor = ROASPredictor(tmpdir)
        new_prediction = new_predictor.predict_roas(features, return_explanation=False)

        assert abs(prediction.predicted_roas - new_prediction.predicted_roas) < 0.01

    print(f"\n✅ End-to-end test passed!")
    print(f"   R² Score: {metrics['r2_score']:.4f}")
    print(f"   MAE: {metrics['mae']:.4f}")
    print(f"   Predicted ROAS: {prediction.predicted_roas:.2f}")
    print(f"   Confidence: [{prediction.confidence_low:.2f}, {prediction.confidence_high:.2f}]")


if __name__ == '__main__':
    # Run end-to-end test
    test_end_to_end_workflow()

    print("\n🚀 Run full test suite with: pytest test_roas_predictor.py -v")
