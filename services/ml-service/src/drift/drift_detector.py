"""
Drift Detector - Core drift detection algorithms
=================================================

Implements:
    - Population Stability Index (PSI) for feature drift
    - Kolmogorov-Smirnov test for distribution comparison
    - Concept drift detection (accuracy degradation)
    - Configurable alerting thresholds
    - Drift trend tracking over time

Author: Agent 10
Created: 2025-12-12
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from scipy import stats
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class DriftResult:
    """Result of drift detection analysis"""
    metric_name: str
    drift_detected: bool
    drift_score: float
    severity: str  # 'none', 'warning', 'critical', 'emergency'
    baseline_stats: Dict[str, float]
    current_stats: Dict[str, float]
    test_statistic: float
    p_value: Optional[float]
    recommendation: str
    detected_at: datetime


@dataclass
class ConceptDriftResult:
    """Result of concept drift (accuracy) detection"""
    model_name: str
    drift_detected: bool
    baseline_accuracy: float
    current_accuracy: float
    accuracy_drop: float
    severity: str
    recommendation: str
    detected_at: datetime


class DriftDetector:
    """
    Core drift detection system using PSI and KS tests.

    Detects when ML model inputs or outputs change distribution,
    indicating need for retraining or investigation.
    """

    def __init__(
        self,
        psi_warning_threshold: float = 0.1,
        psi_critical_threshold: float = 0.25,
        psi_emergency_threshold: float = 0.5,
        ks_warning_threshold: float = 0.1,
        ks_critical_threshold: float = 0.2,
        accuracy_warning_threshold: float = 0.05,  # 5% drop
        accuracy_critical_threshold: float = 0.10,  # 10% drop
        min_samples: int = 100,
        lookback_days: int = 7
    ):
        """
        Initialize Drift Detector.

        Args:
            psi_warning_threshold: PSI threshold for warning (0.1 = small shift)
            psi_critical_threshold: PSI threshold for critical (0.25 = medium shift)
            psi_emergency_threshold: PSI threshold for emergency (0.5 = large shift)
            ks_warning_threshold: KS test threshold for warning
            ks_critical_threshold: KS test threshold for critical
            accuracy_warning_threshold: Accuracy drop threshold for warning
            accuracy_critical_threshold: Accuracy drop threshold for critical
            min_samples: Minimum samples required for drift detection
            lookback_days: Days of history to compare against
        """
        self.psi_warning_threshold = psi_warning_threshold
        self.psi_critical_threshold = psi_critical_threshold
        self.psi_emergency_threshold = psi_emergency_threshold
        self.ks_warning_threshold = ks_warning_threshold
        self.ks_critical_threshold = ks_critical_threshold
        self.accuracy_warning_threshold = accuracy_warning_threshold
        self.accuracy_critical_threshold = accuracy_critical_threshold
        self.min_samples = min_samples
        self.lookback_days = lookback_days

        # Storage for baseline distributions (in production, use database)
        self._baseline_distributions: Dict[str, Dict] = {}
        self._drift_history: List[DriftResult] = []

        logger.info(
            f"DriftDetector initialized: "
            f"PSI thresholds=[{psi_warning_threshold}, {psi_critical_threshold}, {psi_emergency_threshold}], "
            f"KS thresholds=[{ks_warning_threshold}, {ks_critical_threshold}], "
            f"min_samples={min_samples}"
        )

    def calculate_psi(
        self,
        baseline: np.ndarray,
        current: np.ndarray,
        bins: int = 10
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Population Stability Index (PSI).

        PSI measures the change in distribution between two samples:
            - PSI < 0.1: No significant change
            - 0.1 <= PSI < 0.25: Small change (monitor)
            - PSI >= 0.25: Large change (investigate/retrain)

        Formula:
            PSI = Σ (actual_% - expected_%) * ln(actual_% / expected_%)

        Args:
            baseline: Baseline (training) distribution
            current: Current (production) distribution
            bins: Number of bins for discretization

        Returns:
            Tuple of (PSI score, details dict)
        """
        if len(baseline) < self.min_samples or len(current) < self.min_samples:
            logger.warning(
                f"Insufficient samples for PSI: baseline={len(baseline)}, current={len(current)}"
            )
            return 0.0, {"error": "insufficient_samples"}

        # Create bins using baseline distribution
        _, bin_edges = np.histogram(baseline, bins=bins)

        # Calculate distributions
        baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
        current_counts, _ = np.histogram(current, bins=bin_edges)

        # Convert to percentages (avoid division by zero)
        baseline_pct = (baseline_counts + 1e-10) / (len(baseline) + bins * 1e-10)
        current_pct = (current_counts + 1e-10) / (len(current) + bins * 1e-10)

        # Calculate PSI
        psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))

        details = {
            "psi": float(psi),
            "bins": bins,
            "baseline_samples": len(baseline),
            "current_samples": len(current),
            "bin_contributions": [
                {
                    "bin": i,
                    "baseline_pct": float(baseline_pct[i]),
                    "current_pct": float(current_pct[i]),
                    "contribution": float((current_pct[i] - baseline_pct[i]) * np.log(current_pct[i] / baseline_pct[i]))
                }
                for i in range(len(bin_edges) - 1)
            ]
        }

        return float(psi), details

    def kolmogorov_smirnov_test(
        self,
        baseline: np.ndarray,
        current: np.ndarray
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Perform Kolmogorov-Smirnov test for distribution comparison.

        The KS test measures the maximum distance between two cumulative
        distribution functions (CDFs).

        Args:
            baseline: Baseline distribution
            current: Current distribution

        Returns:
            Tuple of (KS statistic, p-value, details dict)
        """
        if len(baseline) < self.min_samples or len(current) < self.min_samples:
            logger.warning(
                f"Insufficient samples for KS test: baseline={len(baseline)}, current={len(current)}"
            )
            return 0.0, 1.0, {"error": "insufficient_samples"}

        # Perform KS test
        ks_statistic, p_value = stats.ks_2samp(baseline, current)

        details = {
            "ks_statistic": float(ks_statistic),
            "p_value": float(p_value),
            "baseline_samples": len(baseline),
            "current_samples": len(current),
            "significant": p_value < 0.05,  # 95% confidence
            "interpretation": self._interpret_ks_result(ks_statistic, p_value)
        }

        return float(ks_statistic), float(p_value), details

    def detect_feature_drift(
        self,
        feature_name: str,
        baseline: np.ndarray,
        current: np.ndarray,
        use_psi: bool = True,
        use_ks: bool = True
    ) -> DriftResult:
        """
        Detect drift in a single feature using PSI and/or KS test.

        Args:
            feature_name: Name of feature being monitored
            baseline: Baseline (training) values
            current: Current (production) values
            use_psi: Whether to use PSI test
            use_ks: Whether to use KS test

        Returns:
            DriftResult with detection outcome
        """
        logger.info(f"Detecting drift for feature: {feature_name}")

        # Calculate baseline statistics
        baseline_stats = self._calculate_stats(baseline)
        current_stats = self._calculate_stats(current)

        drift_detected = False
        severity = 'none'
        test_statistic = 0.0
        p_value = None
        recommendation = "No drift detected. Model inputs are stable."

        # Run PSI test
        if use_psi:
            psi_score, psi_details = self.calculate_psi(baseline, current)
            test_statistic = psi_score

            if psi_score >= self.psi_emergency_threshold:
                drift_detected = True
                severity = 'emergency'
                recommendation = (
                    f"CRITICAL DRIFT DETECTED (PSI={psi_score:.3f})! "
                    f"Feature distribution has changed drastically. "
                    f"IMMEDIATE ACTION REQUIRED: Stop model, investigate root cause, retrain."
                )
            elif psi_score >= self.psi_critical_threshold:
                drift_detected = True
                severity = 'critical'
                recommendation = (
                    f"Significant drift detected (PSI={psi_score:.3f}). "
                    f"Schedule immediate retraining. Monitor predictions closely."
                )
            elif psi_score >= self.psi_warning_threshold:
                drift_detected = True
                severity = 'warning'
                recommendation = (
                    f"Minor drift detected (PSI={psi_score:.3f}). "
                    f"Monitor closely. Consider retraining if trend continues."
                )

        # Run KS test (if requested and no emergency from PSI)
        if use_ks and severity != 'emergency':
            ks_stat, ks_p, ks_details = self.kolmogorov_smirnov_test(baseline, current)

            # If KS test shows higher severity, use it
            if ks_stat >= self.ks_critical_threshold and severity != 'critical':
                drift_detected = True
                severity = 'critical'
                test_statistic = ks_stat
                p_value = ks_p
                recommendation = (
                    f"Distribution shift detected (KS={ks_stat:.3f}, p={ks_p:.4f}). "
                    f"Significant change in feature distribution. Schedule retraining."
                )
            elif ks_stat >= self.ks_warning_threshold and severity == 'none':
                drift_detected = True
                severity = 'warning'
                test_statistic = ks_stat
                p_value = ks_p
                recommendation = (
                    f"Possible distribution shift (KS={ks_stat:.3f}, p={ks_p:.4f}). "
                    f"Monitor feature closely."
                )

        result = DriftResult(
            metric_name=feature_name,
            drift_detected=drift_detected,
            drift_score=test_statistic,
            severity=severity,
            baseline_stats=baseline_stats,
            current_stats=current_stats,
            test_statistic=test_statistic,
            p_value=p_value,
            recommendation=recommendation,
            detected_at=datetime.utcnow()
        )

        # Store in history
        self._drift_history.append(result)

        logger.info(
            f"Drift detection complete for {feature_name}: "
            f"drift={drift_detected}, severity={severity}, score={test_statistic:.3f}"
        )

        return result

    def detect_concept_drift(
        self,
        model_name: str,
        baseline_accuracy: float,
        current_accuracy: float
    ) -> ConceptDriftResult:
        """
        Detect concept drift (model accuracy degradation).

        Concept drift occurs when the relationship between features and
        target changes, causing model accuracy to degrade.

        Args:
            model_name: Name of model being monitored
            baseline_accuracy: Baseline (training/validation) accuracy
            current_accuracy: Current (production) accuracy

        Returns:
            ConceptDriftResult with detection outcome
        """
        logger.info(
            f"Detecting concept drift for {model_name}: "
            f"baseline={baseline_accuracy:.3f}, current={current_accuracy:.3f}"
        )

        accuracy_drop = baseline_accuracy - current_accuracy
        drift_detected = False
        severity = 'none'
        recommendation = "No concept drift detected. Model accuracy is stable."

        if accuracy_drop >= self.accuracy_critical_threshold:
            drift_detected = True
            severity = 'critical'
            recommendation = (
                f"CRITICAL ACCURACY DROP ({accuracy_drop:.1%})! "
                f"Model performance has degraded significantly. "
                f"IMMEDIATE ACTION: Stop model, investigate, retrain with recent data."
            )
        elif accuracy_drop >= self.accuracy_warning_threshold:
            drift_detected = True
            severity = 'warning'
            recommendation = (
                f"Accuracy drop detected ({accuracy_drop:.1%}). "
                f"Model performance declining. Schedule retraining soon."
            )
        elif accuracy_drop < 0:
            # Accuracy improved (unusual but possible)
            recommendation = (
                f"Model accuracy improved by {abs(accuracy_drop):.1%}. "
                f"This is unexpected - verify metrics are correct."
            )

        result = ConceptDriftResult(
            model_name=model_name,
            drift_detected=drift_detected,
            baseline_accuracy=baseline_accuracy,
            current_accuracy=current_accuracy,
            accuracy_drop=accuracy_drop,
            severity=severity,
            recommendation=recommendation,
            detected_at=datetime.utcnow()
        )

        logger.info(
            f"Concept drift detection complete for {model_name}: "
            f"drift={drift_detected}, severity={severity}, drop={accuracy_drop:.1%}"
        )

        return result

    def detect_multivariate_drift(
        self,
        feature_names: List[str],
        baseline_features: np.ndarray,
        current_features: np.ndarray
    ) -> List[DriftResult]:
        """
        Detect drift across multiple features simultaneously.

        Args:
            feature_names: List of feature names
            baseline_features: Baseline feature matrix (n_samples, n_features)
            current_features: Current feature matrix (n_samples, n_features)

        Returns:
            List of DriftResult, one per feature
        """
        logger.info(f"Detecting multivariate drift across {len(feature_names)} features")

        if baseline_features.shape[1] != len(feature_names):
            raise ValueError(
                f"Feature count mismatch: {baseline_features.shape[1]} vs {len(feature_names)}"
            )

        results = []
        for i, feature_name in enumerate(feature_names):
            baseline_col = baseline_features[:, i]
            current_col = current_features[:, i]

            result = self.detect_feature_drift(
                feature_name=feature_name,
                baseline=baseline_col,
                current=current_col
            )
            results.append(result)

        # Log summary
        drift_count = sum(1 for r in results if r.drift_detected)
        critical_count = sum(1 for r in results if r.severity in ['critical', 'emergency'])

        logger.info(
            f"Multivariate drift detection complete: "
            f"{drift_count}/{len(feature_names)} features drifted, "
            f"{critical_count} critical"
        )

        return results

    def set_baseline(
        self,
        metric_name: str,
        baseline_data: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Set baseline distribution for a metric.

        Args:
            metric_name: Name of metric (feature, prediction, etc.)
            baseline_data: Baseline distribution values
            metadata: Optional metadata (model version, date, etc.)

        Returns:
            Baseline statistics
        """
        stats = self._calculate_stats(baseline_data)

        self._baseline_distributions[metric_name] = {
            "data": baseline_data.tolist() if len(baseline_data) < 10000 else None,  # Don't store huge arrays
            "stats": stats,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "sample_count": len(baseline_data)
        }

        logger.info(f"Baseline set for {metric_name}: {len(baseline_data)} samples")
        return stats

    def get_baseline(self, metric_name: str) -> Optional[Dict]:
        """Get stored baseline for a metric."""
        return self._baseline_distributions.get(metric_name)

    def get_drift_trend(
        self,
        metric_name: str,
        days: int = 7
    ) -> List[DriftResult]:
        """
        Get drift trend for a metric over time.

        Args:
            metric_name: Name of metric to analyze
            days: Number of days to look back

        Returns:
            List of historical drift results
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        trend = [
            result for result in self._drift_history
            if result.metric_name == metric_name and result.detected_at >= cutoff
        ]

        return sorted(trend, key=lambda x: x.detected_at)

    def get_drift_summary(self) -> Dict[str, Any]:
        """
        Get summary of all drift detections.

        Returns:
            Summary statistics
        """
        total_checks = len(self._drift_history)
        drift_detected = sum(1 for r in self._drift_history if r.drift_detected)

        severity_counts = {
            'warning': sum(1 for r in self._drift_history if r.severity == 'warning'),
            'critical': sum(1 for r in self._drift_history if r.severity == 'critical'),
            'emergency': sum(1 for r in self._drift_history if r.severity == 'emergency')
        }

        return {
            "total_checks": total_checks,
            "drift_detected": drift_detected,
            "drift_rate": drift_detected / max(total_checks, 1),
            "severity_counts": severity_counts,
            "baselines_stored": len(self._baseline_distributions),
            "last_check": self._drift_history[-1].detected_at.isoformat() if self._drift_history else None
        }

    # Helper methods

    def _calculate_stats(self, data: np.ndarray) -> Dict[str, float]:
        """Calculate statistical moments of data."""
        return {
            "mean": float(np.mean(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "median": float(np.median(data)),
            "q25": float(np.percentile(data, 25)),
            "q75": float(np.percentile(data, 75)),
            "skew": float(stats.skew(data)),
            "kurtosis": float(stats.kurtosis(data)),
            "sample_count": len(data)
        }

    def _interpret_ks_result(self, ks_statistic: float, p_value: float) -> str:
        """Interpret KS test result."""
        if p_value < 0.001:
            return "Very strong evidence of distribution difference"
        elif p_value < 0.01:
            return "Strong evidence of distribution difference"
        elif p_value < 0.05:
            return "Moderate evidence of distribution difference"
        elif p_value < 0.1:
            return "Weak evidence of distribution difference"
        else:
            return "No significant distribution difference"


# Singleton instance
_drift_detector_instance = None


def get_drift_detector() -> DriftDetector:
    """Get or create DriftDetector singleton."""
    global _drift_detector_instance
    if _drift_detector_instance is None:
        _drift_detector_instance = DriftDetector()
    return _drift_detector_instance
