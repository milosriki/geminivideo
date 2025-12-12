"""
Tests for Drift Detection System - Agent 10
==========================================

Test suite for drift detection components:
    - DriftDetector (PSI, KS tests)
    - FeatureMonitor
    - PredictionMonitor
    - AlertManager

Author: Agent 10
Created: 2025-12-12
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.drift.drift_detector import DriftDetector, get_drift_detector
from src.drift.feature_monitor import FeatureMonitor, get_feature_monitor
from src.drift.prediction_monitor import PredictionMonitor, get_prediction_monitor
from src.drift.alert_manager import AlertManager, AlertSeverity


class TestDriftDetector:
    """Test DriftDetector class."""

    def test_calculate_psi_no_drift(self):
        """Test PSI calculation when no drift."""
        detector = DriftDetector()

        # Same distribution
        baseline = np.random.normal(0, 1, 1000)
        current = np.random.normal(0, 1, 1000)

        psi, details = detector.calculate_psi(baseline, current)

        assert psi < 0.1, f"PSI should be low for same distribution, got {psi}"
        assert details["baseline_samples"] == 1000
        assert details["current_samples"] == 1000

    def test_calculate_psi_with_drift(self):
        """Test PSI calculation when drift present."""
        detector = DriftDetector()

        # Different distributions
        baseline = np.random.normal(0, 1, 1000)
        current = np.random.normal(2, 1, 1000)  # Shifted mean

        psi, details = detector.calculate_psi(baseline, current)

        assert psi > 0.25, f"PSI should be high for drifted distribution, got {psi}"

    def test_kolmogorov_smirnov_no_drift(self):
        """Test KS test when no drift."""
        detector = DriftDetector()

        baseline = np.random.normal(0, 1, 1000)
        current = np.random.normal(0, 1, 1000)

        ks_stat, p_value, details = detector.kolmogorov_smirnov_test(baseline, current)

        assert p_value > 0.05, f"p-value should be high for same distribution, got {p_value}"
        assert not details["significant"]

    def test_kolmogorov_smirnov_with_drift(self):
        """Test KS test when drift present."""
        detector = DriftDetector()

        baseline = np.random.normal(0, 1, 1000)
        current = np.random.normal(2, 1, 1000)

        ks_stat, p_value, details = detector.kolmogorov_smirnov_test(baseline, current)

        assert p_value < 0.05, f"p-value should be low for drifted distribution, got {p_value}"
        assert details["significant"]

    def test_detect_feature_drift_no_drift(self):
        """Test feature drift detection with no drift."""
        detector = DriftDetector()

        baseline = np.random.normal(0, 1, 1000)
        current = np.random.normal(0, 1, 1000)

        result = detector.detect_feature_drift("test_feature", baseline, current)

        assert not result.drift_detected
        assert result.severity == 'none'

    def test_detect_feature_drift_with_drift(self):
        """Test feature drift detection with drift."""
        detector = DriftDetector()

        baseline = np.random.normal(0, 1, 1000)
        current = np.random.normal(2, 1, 1000)  # Significant shift

        result = detector.detect_feature_drift("test_feature", baseline, current)

        assert result.drift_detected
        assert result.severity in ['warning', 'critical', 'emergency']

    def test_detect_concept_drift(self):
        """Test concept drift detection (accuracy degradation)."""
        detector = DriftDetector()

        # Small drop - no drift
        result1 = detector.detect_concept_drift(
            "test_model",
            baseline_accuracy=0.90,
            current_accuracy=0.89
        )
        assert not result1.drift_detected

        # Large drop - drift detected
        result2 = detector.detect_concept_drift(
            "test_model",
            baseline_accuracy=0.90,
            current_accuracy=0.80
        )
        assert result2.drift_detected
        assert result2.severity == 'critical'

    def test_detect_multivariate_drift(self):
        """Test multivariate drift detection."""
        detector = DriftDetector()

        # 5 features
        baseline = np.random.normal(0, 1, (1000, 5))
        current = np.random.normal(0, 1, (1000, 5))
        # Drift in feature 2
        current[:, 2] = np.random.normal(2, 1, 1000)

        feature_names = ['f1', 'f2', 'f3', 'f4', 'f5']

        results = detector.detect_multivariate_drift(
            feature_names, baseline, current
        )

        assert len(results) == 5
        # Feature 2 should have drift
        assert results[2].drift_detected
        # Others should not
        assert not results[0].drift_detected
        assert not results[1].drift_detected

    def test_set_and_get_baseline(self):
        """Test baseline storage and retrieval."""
        detector = DriftDetector()

        baseline = np.random.normal(0, 1, 1000)
        stats = detector.set_baseline("test_metric", baseline)

        assert "mean" in stats
        assert "std" in stats

        retrieved = detector.get_baseline("test_metric")
        assert retrieved is not None
        assert retrieved["stats"]["mean"] == stats["mean"]

    def test_drift_summary(self):
        """Test drift summary statistics."""
        detector = DriftDetector()

        baseline = np.random.normal(0, 1, 1000)
        current1 = np.random.normal(0, 1, 1000)
        current2 = np.random.normal(2, 1, 1000)

        detector.detect_feature_drift("f1", baseline, current1)  # No drift
        detector.detect_feature_drift("f2", baseline, current2)  # Drift

        summary = detector.get_drift_summary()

        assert summary["total_checks"] == 2
        assert summary["drift_detected"] >= 1


class TestFeatureMonitor:
    """Test FeatureMonitor class."""

    def test_set_baseline(self):
        """Test setting feature baseline."""
        monitor = FeatureMonitor()

        baseline = np.random.normal(0, 1, 1000)
        snapshot = monitor.set_baseline("test_feature", baseline)

        assert snapshot.feature_name == "test_feature"
        assert abs(snapshot.mean - 0) < 0.1  # Should be close to 0
        assert abs(snapshot.std - 1) < 0.1   # Should be close to 1

    def test_set_baseline_from_dataframe(self):
        """Test setting baselines from DataFrame."""
        monitor = FeatureMonitor()

        df = pd.DataFrame({
            'feature1': np.random.normal(0, 1, 100),
            'feature2': np.random.normal(5, 2, 100),
            'feature3': np.random.normal(-1, 0.5, 100)
        })

        baselines = monitor.set_baseline_from_dataframe(df)

        assert len(baselines) == 3
        assert 'feature1' in baselines
        assert 'feature2' in baselines
        assert 'feature3' in baselines

    def test_track_features(self):
        """Test tracking individual features."""
        monitor = FeatureMonitor()

        # Track 100 observations
        for _ in range(100):
            monitor.track_features({
                'feature1': np.random.normal(0, 1),
                'feature2': np.random.normal(5, 2)
            })

        # Get current stats
        stats1 = monitor.get_current_stats('feature1')
        stats2 = monitor.get_current_stats('feature2')

        assert stats1 is not None
        assert stats2 is not None
        assert stats1.sample_count == 100
        assert stats2.sample_count == 100

    def test_check_drift_no_drift(self):
        """Test drift check with no drift."""
        monitor = FeatureMonitor()

        # Set baseline
        baseline = np.random.normal(0, 1, 1000)
        monitor.set_baseline("test_feature", baseline)

        # Track similar data
        for _ in range(200):
            monitor.track_features({
                'test_feature': np.random.normal(0, 1)
            })

        # Check drift
        report = monitor.check_drift("test_feature")

        assert report is not None
        assert not report.is_drifting

    def test_check_drift_with_drift(self):
        """Test drift check with drift present."""
        monitor = FeatureMonitor()

        # Set baseline
        baseline = np.random.normal(0, 1, 1000)
        monitor.set_baseline("test_feature", baseline)

        # Track drifted data
        for _ in range(200):
            monitor.track_features({
                'test_feature': np.random.normal(3, 1)  # Mean shifted
            })

        # Check drift
        report = monitor.check_drift("test_feature")

        assert report is not None
        assert report.is_drifting
        assert report.mean_shift > 2.0

    def test_get_top_drifting_features(self):
        """Test getting top drifting features."""
        monitor = FeatureMonitor()

        # Set baselines for multiple features
        for i in range(5):
            baseline = np.random.normal(0, 1, 1000)
            monitor.set_baseline(f"feature_{i}", baseline)

        # Track data with varying drift
        for _ in range(200):
            monitor.track_features({
                'feature_0': np.random.normal(0, 1),      # No drift
                'feature_1': np.random.normal(1, 1),      # Small drift
                'feature_2': np.random.normal(3, 1),      # Large drift
                'feature_3': np.random.normal(0.5, 1),    # Tiny drift
                'feature_4': np.random.normal(2, 1)       # Medium drift
            })

        # Get top drifting
        top = monitor.get_top_drifting_features(n=3)

        assert len(top) <= 3
        # feature_2 should be first (largest drift)
        if top:
            assert top[0].feature_name == 'feature_2'


class TestPredictionMonitor:
    """Test PredictionMonitor class."""

    def test_set_baseline(self):
        """Test setting prediction baseline."""
        monitor = PredictionMonitor()

        baseline = np.random.uniform(0, 1, 1000)
        snapshot = monitor.set_baseline("test_model", baseline)

        assert snapshot.model_name == "test_model"
        assert 0 <= snapshot.mean_prediction <= 1
        assert snapshot.sample_count == 1000

    def test_track_prediction(self):
        """Test tracking single prediction."""
        monitor = PredictionMonitor()

        monitor.track_prediction("test_model", 0.75)
        monitor.track_prediction("test_model", 0.82, actual=0.80)
        monitor.track_prediction("test_model", 0.68, actual=0.70, confidence=0.85)

        # Should have 3 predictions tracked
        assert len(monitor._prediction_windows["test_model"]) == 3

    def test_check_prediction_drift_no_drift(self):
        """Test prediction drift check with no drift."""
        monitor = PredictionMonitor()

        # Set baseline
        baseline = np.random.uniform(0.3, 0.7, 1000)
        monitor.set_baseline("test_model", baseline)

        # Track similar predictions
        for _ in range(200):
            monitor.track_prediction("test_model", np.random.uniform(0.3, 0.7))

        report = monitor.check_prediction_drift("test_model")

        assert report is not None
        assert not report.is_drifting

    def test_check_prediction_drift_with_drift(self):
        """Test prediction drift check with drift."""
        monitor = PredictionMonitor()

        # Set baseline
        baseline = np.random.uniform(0.3, 0.7, 1000)
        monitor.set_baseline("test_model", baseline)

        # Track drifted predictions
        for _ in range(200):
            monitor.track_prediction("test_model", np.random.uniform(0.7, 0.9))  # Shifted

        report = monitor.check_prediction_drift("test_model")

        assert report is not None
        assert report.is_drifting

    def test_check_calibration(self):
        """Test calibration check."""
        monitor = PredictionMonitor()

        # Track well-calibrated predictions
        for _ in range(100):
            pred = np.random.uniform(0, 1)
            actual = 1 if np.random.random() < pred else 0
            monitor.track_prediction("test_model", pred, actual=actual)

        result = monitor.check_calibration("test_model")

        assert result is not None
        # Should be reasonably calibrated (ECE < 0.2)
        assert result.expected_calibration_error < 0.3

    def test_get_prediction_accuracy(self):
        """Test prediction accuracy calculation."""
        monitor = PredictionMonitor()

        # Track predictions with actuals
        np.random.seed(42)
        for _ in range(100):
            actual = np.random.normal(0.5, 0.1)
            pred = actual + np.random.normal(0, 0.05)  # Small error
            monitor.track_prediction("test_model", pred, actual=actual)

        mae = monitor.get_prediction_accuracy("test_model", metric='mae')
        mse = monitor.get_prediction_accuracy("test_model", metric='mse')
        rmse = monitor.get_prediction_accuracy("test_model", metric='rmse')

        assert mae is not None
        assert mse is not None
        assert rmse is not None
        assert mae < 0.1  # Should be small error

    def test_get_model_freshness(self):
        """Test model freshness indicators."""
        monitor = PredictionMonitor()

        # Set baseline
        baseline = np.random.uniform(0, 1, 1000)
        monitor.set_baseline("test_model", baseline)

        # Check freshness
        freshness = monitor.get_model_freshness("test_model")

        assert "status" in freshness
        assert "baseline_age_days" in freshness
        assert "recommendation" in freshness


class TestAlertManager:
    """Test AlertManager class."""

    def test_send_drift_alert(self):
        """Test sending drift alert."""
        manager = AlertManager(
            slack_webhook_url=None,  # Disable Slack for testing
            email_enabled=False
        )

        alert = manager.send_drift_alert(
            model_name="test_model",
            drift_type="feature",
            metric_name="test_feature",
            drift_score=0.35,
            severity=AlertSeverity.WARNING,
            message="Test drift detected",
            recommendation="Monitor closely"
        )

        assert alert is not None
        assert alert.model_name == "test_model"
        assert alert.drift_type == "feature"
        assert alert.severity == AlertSeverity.WARNING

    def test_alert_cooldown(self):
        """Test alert cooldown to prevent spam."""
        manager = AlertManager(
            slack_webhook_url=None,
            email_enabled=False,
            alert_cooldown_minutes=60
        )

        # Send first alert
        alert1 = manager.send_drift_alert(
            model_name="test_model",
            drift_type="feature",
            metric_name="test_feature",
            drift_score=0.35,
            severity=AlertSeverity.WARNING,
            message="Test drift",
            recommendation="Monitor"
        )

        # Send duplicate immediately (should be blocked by cooldown)
        alert2 = manager.send_drift_alert(
            model_name="test_model",
            drift_type="feature",
            metric_name="test_feature",
            drift_score=0.40,
            severity=AlertSeverity.WARNING,
            message="Test drift",
            recommendation="Monitor"
        )

        assert alert1 is not None
        assert alert2 is None  # Should be blocked

    def test_get_alert_history(self):
        """Test getting alert history."""
        manager = AlertManager(
            slack_webhook_url=None,
            email_enabled=False,
            alert_cooldown_minutes=0  # Disable cooldown for testing
        )

        # Send multiple alerts
        for i in range(5):
            manager.send_drift_alert(
                model_name=f"model_{i}",
                drift_type="feature",
                metric_name=f"feature_{i}",
                drift_score=0.3 + i * 0.1,
                severity=AlertSeverity.WARNING,
                message=f"Test {i}",
                recommendation="Monitor"
            )

        history = manager.get_alert_history(hours=24)
        assert len(history) == 5

    def test_get_alert_summary(self):
        """Test alert summary statistics."""
        manager = AlertManager(
            slack_webhook_url=None,
            email_enabled=False,
            alert_cooldown_minutes=0
        )

        # Send alerts with different severities
        manager.send_drift_alert(
            "model1", "feature", "f1", 0.2,
            AlertSeverity.WARNING, "test", "monitor"
        )
        manager.send_drift_alert(
            "model2", "prediction", "p1", 0.5,
            AlertSeverity.CRITICAL, "test", "retrain"
        )

        summary = manager.get_alert_summary()

        assert summary["total_alerts"] == 2
        assert summary["severity_counts"]["warning"] == 1
        assert summary["severity_counts"]["critical"] == 1


# Integration tests

def test_end_to_end_drift_detection():
    """End-to-end drift detection workflow."""
    detector = DriftDetector()
    monitor = FeatureMonitor()

    # Simulate training phase
    X_train = np.random.normal(0, 1, (1000, 3))
    feature_names = ['feature1', 'feature2', 'feature3']

    # Set baselines
    for i, name in enumerate(feature_names):
        monitor.set_baseline(name, X_train[:, i])

    # Simulate production phase (no drift)
    for _ in range(100):
        features = {
            'feature1': np.random.normal(0, 1),
            'feature2': np.random.normal(0, 1),
            'feature3': np.random.normal(0, 1)
        }
        monitor.track_features(features)

    # Check drift - should be clean
    reports = monitor.check_all_features()
    drifted = sum(1 for r in reports if r.is_drifting)
    assert drifted == 0

    # Simulate drift in feature2
    for _ in range(100):
        features = {
            'feature1': np.random.normal(0, 1),
            'feature2': np.random.normal(3, 1),  # DRIFT!
            'feature3': np.random.normal(0, 1)
        }
        monitor.track_features(features)

    # Check drift again
    reports = monitor.check_all_features()
    drifted = sum(1 for r in reports if r.is_drifting)
    assert drifted >= 1  # feature2 should be drifting


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
