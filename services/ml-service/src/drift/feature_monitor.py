"""
Feature Monitor - Track feature distributions over time
=======================================================

Monitors statistical moments of input features and compares
against training distribution to identify drift sources.

Features:
    - Real-time feature statistics tracking
    - Distribution comparison vs training data
    - Feature-level drift identification
    - Histogram visualization data
    - Trend analysis over time

Author: Agent 10
Created: 2025-12-12
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class FeatureSnapshot:
    """Snapshot of feature statistics at a point in time"""
    feature_name: str
    mean: float
    std: float
    min: float
    max: float
    median: float
    q25: float
    q75: float
    skew: float
    kurtosis: float
    sample_count: int
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class FeatureDriftReport:
    """Drift report for a single feature"""
    feature_name: str
    is_drifting: bool
    drift_magnitude: float  # How much it's drifted (normalized)
    baseline_mean: float
    current_mean: float
    baseline_std: float
    current_std: float
    mean_shift: float  # Change in mean (standard deviations)
    std_shift: float   # Change in std
    recommendation: str
    histogram_data: Optional[Dict] = None


class FeatureMonitor:
    """
    Monitor feature distributions and detect drift.

    Tracks statistical moments of features over time and compares
    against baseline (training) distribution.
    """

    def __init__(
        self,
        window_size: int = 1000,  # Rolling window for current stats
        max_history: int = 100,   # Max snapshots to keep in memory
        mean_shift_threshold: float = 2.0,  # Mean shift in std devs
        std_shift_threshold: float = 0.5,   # Std change ratio
    ):
        """
        Initialize Feature Monitor.

        Args:
            window_size: Size of rolling window for current statistics
            max_history: Maximum number of historical snapshots to keep
            mean_shift_threshold: Threshold for mean shift (in std devs)
            std_shift_threshold: Threshold for std change ratio
        """
        self.window_size = window_size
        self.max_history = max_history
        self.mean_shift_threshold = mean_shift_threshold
        self.std_shift_threshold = std_shift_threshold

        # Storage for baseline (training) statistics
        self._baseline_stats: Dict[str, FeatureSnapshot] = {}

        # Rolling windows for current features
        self._feature_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )

        # Historical snapshots
        self._feature_history: Dict[str, List[FeatureSnapshot]] = defaultdict(list)

        logger.info(
            f"FeatureMonitor initialized: "
            f"window_size={window_size}, max_history={max_history}"
        )

    def set_baseline(
        self,
        feature_name: str,
        baseline_values: np.ndarray
    ) -> FeatureSnapshot:
        """
        Set baseline (training) statistics for a feature.

        Args:
            feature_name: Name of feature
            baseline_values: Training data for this feature

        Returns:
            FeatureSnapshot of baseline
        """
        snapshot = self._create_snapshot(feature_name, baseline_values)
        self._baseline_stats[feature_name] = snapshot

        logger.info(
            f"Baseline set for {feature_name}: "
            f"mean={snapshot.mean:.4f}, std={snapshot.std:.4f}, "
            f"samples={snapshot.sample_count}"
        )

        return snapshot

    def set_baseline_from_dataframe(
        self,
        df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None
    ) -> Dict[str, FeatureSnapshot]:
        """
        Set baseline for all features from DataFrame.

        Args:
            df: DataFrame with training data
            feature_columns: List of feature columns (None = all numeric)

        Returns:
            Dict mapping feature name to baseline snapshot
        """
        if feature_columns is None:
            feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        baselines = {}
        for col in feature_columns:
            if col in df.columns:
                snapshot = self.set_baseline(col, df[col].values)
                baselines[col] = snapshot

        logger.info(f"Baseline set for {len(baselines)} features from DataFrame")
        return baselines

    def track_features(
        self,
        feature_values: Dict[str, float]
    ):
        """
        Track a single observation of features.

        Args:
            feature_values: Dict mapping feature name to value
        """
        for feature_name, value in feature_values.items():
            self._feature_windows[feature_name].append(value)

    def track_batch(
        self,
        df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None
    ):
        """
        Track a batch of feature observations.

        Args:
            df: DataFrame with feature values
            feature_columns: List of feature columns to track
        """
        if feature_columns is None:
            feature_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in feature_columns:
            if col in df.columns:
                for value in df[col].values:
                    self._feature_windows[col].append(value)

        logger.debug(f"Tracked batch of {len(df)} samples across {len(feature_columns)} features")

    def get_current_stats(
        self,
        feature_name: str
    ) -> Optional[FeatureSnapshot]:
        """
        Get current statistics for a feature.

        Args:
            feature_name: Name of feature

        Returns:
            Current FeatureSnapshot or None if insufficient data
        """
        if feature_name not in self._feature_windows:
            return None

        window = self._feature_windows[feature_name]
        if len(window) < 10:  # Need minimum samples
            return None

        values = np.array(list(window))
        return self._create_snapshot(feature_name, values)

    def check_drift(
        self,
        feature_name: str,
        create_histogram: bool = True
    ) -> Optional[FeatureDriftReport]:
        """
        Check if a feature has drifted from baseline.

        Args:
            feature_name: Name of feature to check
            create_histogram: Whether to create histogram data

        Returns:
            FeatureDriftReport or None if cannot check
        """
        # Need baseline and current stats
        if feature_name not in self._baseline_stats:
            logger.warning(f"No baseline for feature {feature_name}")
            return None

        current = self.get_current_stats(feature_name)
        if current is None:
            logger.warning(f"Insufficient current data for {feature_name}")
            return None

        baseline = self._baseline_stats[feature_name]

        # Calculate shifts
        mean_shift = abs(current.mean - baseline.mean) / max(baseline.std, 1e-10)
        std_shift = abs(current.std - baseline.std) / max(baseline.std, 1e-10)

        # Determine if drifting
        is_drifting = (
            mean_shift > self.mean_shift_threshold or
            std_shift > self.std_shift_threshold
        )

        # Calculate overall drift magnitude (0-1 scale)
        drift_magnitude = min(
            (mean_shift / self.mean_shift_threshold + std_shift / self.std_shift_threshold) / 2,
            1.0
        )

        # Generate recommendation
        recommendation = self._generate_drift_recommendation(
            feature_name, is_drifting, mean_shift, std_shift
        )

        # Create histogram data if requested
        histogram_data = None
        if create_histogram:
            histogram_data = self._create_histogram_comparison(
                feature_name,
                baseline,
                current
            )

        report = FeatureDriftReport(
            feature_name=feature_name,
            is_drifting=is_drifting,
            drift_magnitude=drift_magnitude,
            baseline_mean=baseline.mean,
            current_mean=current.mean,
            baseline_std=baseline.std,
            current_std=current.std,
            mean_shift=mean_shift,
            std_shift=std_shift,
            recommendation=recommendation,
            histogram_data=histogram_data
        )

        logger.info(
            f"Drift check for {feature_name}: "
            f"drifting={is_drifting}, magnitude={drift_magnitude:.3f}, "
            f"mean_shift={mean_shift:.2f}σ, std_shift={std_shift:.2f}"
        )

        return report

    def check_all_features(
        self,
        create_histograms: bool = False
    ) -> List[FeatureDriftReport]:
        """
        Check drift for all features with baselines.

        Args:
            create_histograms: Whether to create histogram data

        Returns:
            List of drift reports
        """
        reports = []

        for feature_name in self._baseline_stats.keys():
            report = self.check_drift(feature_name, create_histogram=create_histograms)
            if report:
                reports.append(report)

        # Log summary
        drifting_count = sum(1 for r in reports if r.is_drifting)
        logger.info(
            f"Checked {len(reports)} features: "
            f"{drifting_count} drifting ({drifting_count/max(len(reports), 1):.1%})"
        )

        return reports

    def get_top_drifting_features(
        self,
        n: int = 10
    ) -> List[FeatureDriftReport]:
        """
        Get top N features with highest drift magnitude.

        Args:
            n: Number of features to return

        Returns:
            List of drift reports sorted by magnitude
        """
        reports = self.check_all_features(create_histograms=True)

        # Sort by drift magnitude
        reports.sort(key=lambda r: r.drift_magnitude, reverse=True)

        return reports[:n]

    def snapshot_all_features(self) -> Dict[str, FeatureSnapshot]:
        """
        Create snapshot of all current feature statistics.

        Returns:
            Dict mapping feature name to snapshot
        """
        snapshots = {}

        for feature_name in self._feature_windows.keys():
            snapshot = self.get_current_stats(feature_name)
            if snapshot:
                snapshots[feature_name] = snapshot

                # Add to history
                self._feature_history[feature_name].append(snapshot)

                # Limit history size
                if len(self._feature_history[feature_name]) > self.max_history:
                    self._feature_history[feature_name].pop(0)

        logger.info(f"Created snapshots for {len(snapshots)} features")
        return snapshots

    def get_feature_trend(
        self,
        feature_name: str,
        hours: int = 24
    ) -> List[FeatureSnapshot]:
        """
        Get historical trend for a feature.

        Args:
            feature_name: Name of feature
            hours: Hours of history to return

        Returns:
            List of historical snapshots
        """
        if feature_name not in self._feature_history:
            return []

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        trend = [
            snapshot for snapshot in self._feature_history[feature_name]
            if snapshot.timestamp >= cutoff
        ]

        return sorted(trend, key=lambda s: s.timestamp)

    def export_statistics(self) -> Dict[str, Any]:
        """
        Export all statistics for persistence.

        Returns:
            Dict with baseline stats and current windows
        """
        return {
            "baselines": {
                name: snapshot.to_dict()
                for name, snapshot in self._baseline_stats.items()
            },
            "window_sizes": {
                name: len(window)
                for name, window in self._feature_windows.items()
            },
            "exported_at": datetime.utcnow().isoformat()
        }

    # Helper methods

    def _create_snapshot(
        self,
        feature_name: str,
        values: np.ndarray
    ) -> FeatureSnapshot:
        """Create feature snapshot from values."""
        from scipy import stats as scipy_stats

        return FeatureSnapshot(
            feature_name=feature_name,
            mean=float(np.mean(values)),
            std=float(np.std(values)),
            min=float(np.min(values)),
            max=float(np.max(values)),
            median=float(np.median(values)),
            q25=float(np.percentile(values, 25)),
            q75=float(np.percentile(values, 75)),
            skew=float(scipy_stats.skew(values)),
            kurtosis=float(scipy_stats.kurtosis(values)),
            sample_count=len(values),
            timestamp=datetime.utcnow()
        )

    def _generate_drift_recommendation(
        self,
        feature_name: str,
        is_drifting: bool,
        mean_shift: float,
        std_shift: float
    ) -> str:
        """Generate recommendation based on drift."""
        if not is_drifting:
            return f"{feature_name} is stable. No action needed."

        if mean_shift > 3.0:
            return (
                f"{feature_name} has significant mean shift ({mean_shift:.1f}σ). "
                f"CRITICAL: Investigate data pipeline. Likely indicates upstream changes. "
                f"Model retraining required."
            )
        elif std_shift > 1.0:
            return (
                f"{feature_name} has significant variance change (±{std_shift:.1%}). "
                f"Data volatility has changed. Monitor closely. Consider retraining."
            )
        else:
            return (
                f"{feature_name} showing drift (mean: {mean_shift:.1f}σ, std: ±{std_shift:.1%}). "
                f"Monitor trend. Retrain if drift persists."
            )

    def _create_histogram_comparison(
        self,
        feature_name: str,
        baseline: FeatureSnapshot,
        current: FeatureSnapshot,
        bins: int = 20
    ) -> Dict[str, Any]:
        """Create histogram data for visualization."""
        # Get baseline and current windows
        baseline_window = self._baseline_stats.get(feature_name)
        current_window = list(self._feature_windows.get(feature_name, []))

        if not current_window:
            return {}

        # Create shared bins
        all_values = current_window
        min_val = min(all_values)
        max_val = max(all_values)
        bin_edges = np.linspace(min_val, max_val, bins + 1)

        # Create current histogram
        current_hist, _ = np.histogram(current_window, bins=bin_edges)
        current_hist = current_hist / len(current_window)  # Normalize

        return {
            "feature_name": feature_name,
            "bin_edges": bin_edges.tolist(),
            "current_distribution": current_hist.tolist(),
            "baseline_mean": baseline.mean,
            "baseline_std": baseline.std,
            "current_mean": current.mean,
            "current_std": current.std,
            "bins": bins
        }


# Singleton instance
_feature_monitor_instance = None


def get_feature_monitor() -> FeatureMonitor:
    """Get or create FeatureMonitor singleton."""
    global _feature_monitor_instance
    if _feature_monitor_instance is None:
        _feature_monitor_instance = FeatureMonitor()
    return _feature_monitor_instance
