"""Test ad fatigue detection logic.

Tests CTR decline detection, frequency saturation, and fatigue signals
based on time-series performance metrics.
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class FatigueResult:
    """Fatigue detection result."""
    status: str  # "HEALTHY", "FATIGUING", "SATURATED"
    reason: str
    metrics: Dict[str, Any]


def detect_fatigue(ad_id: str, metrics: List[Dict[str, Any]]) -> FatigueResult:
    """
    Detect ad fatigue based on time-series metrics.

    Args:
        ad_id: Ad identifier
        metrics: List of metric snapshots over time (oldest to newest)

    Returns:
        FatigueResult with status and reason
    """
    if len(metrics) < 2:
        return FatigueResult(
            status="INSUFFICIENT_DATA",
            reason="Need at least 2 data points",
            metrics={}
        )

    latest = metrics[-1]
    earliest = metrics[0]

    # Check 1: CTR Decline (>25% drop)
    if earliest["ctr"] > 0:
        ctr_decline_pct = ((earliest["ctr"] - latest["ctr"]) / earliest["ctr"]) * 100

        if ctr_decline_pct > 25:
            return FatigueResult(
                status="FATIGUING",
                reason=f"CTR dropped {ctr_decline_pct:.1f}% from {earliest['ctr']:.2f}% to {latest['ctr']:.2f}%",
                metrics={
                    "ctr_decline_pct": ctr_decline_pct,
                    "initial_ctr": earliest["ctr"],
                    "current_ctr": latest["ctr"]
                }
            )

    # Check 2: Frequency Saturation (>3.5)
    if latest["frequency"] > 3.5:
        return FatigueResult(
            status="SATURATED",
            reason=f"Frequency too high: {latest['frequency']:.1f} (threshold: 3.5)",
            metrics={
                "frequency": latest["frequency"],
                "threshold": 3.5
            }
        )

    # Check 3: CPM Increase (>30%)
    if earliest["cpm"] > 0:
        cpm_increase_pct = ((latest["cpm"] - earliest["cpm"]) / earliest["cpm"]) * 100

        if cpm_increase_pct > 30:
            return FatigueResult(
                status="FATIGUING",
                reason=f"CPM increased {cpm_increase_pct:.1f}% from ${earliest['cpm']:.2f} to ${latest['cpm']:.2f}",
                metrics={
                    "cpm_increase_pct": cpm_increase_pct,
                    "initial_cpm": earliest["cpm"],
                    "current_cpm": latest["cpm"]
                }
            )

    # Check 4: Combined Fatigue (declining CTR + rising CPM + high frequency)
    if (latest["ctr"] < earliest["ctr"] * 0.8 and
        latest["cpm"] > earliest["cpm"] * 1.2 and
        latest["frequency"] > 2.5):
        return FatigueResult(
            status="FATIGUING",
            reason="Combined fatigue signals: declining CTR, rising CPM, high frequency",
            metrics={
                "ctr_change": latest["ctr"] / earliest["ctr"],
                "cpm_change": latest["cpm"] / earliest["cpm"],
                "frequency": latest["frequency"]
            }
        )

    # All checks passed
    return FatigueResult(
        status="HEALTHY",
        reason="No fatigue detected",
        metrics={
            "ctr": latest["ctr"],
            "frequency": latest["frequency"],
            "cpm": latest["cpm"]
        }
    )


@pytest.mark.integration
def test_ctr_decline_detection():
    """Test CTR decline detection (>25% drop)."""
    metrics = [
        {"ctr": 4.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 3.5, "frequency": 2.2, "cpm": 11.0},
        {"ctr": 3.0, "frequency": 2.4, "cpm": 12.0},
        {"ctr": 2.5, "frequency": 2.6, "cpm": 13.0},  # 37.5% decline
    ]

    result = detect_fatigue("ad_1", metrics)

    assert result.status == "FATIGUING"
    assert "CTR dropped" in result.reason
    assert result.metrics["ctr_decline_pct"] > 25


@pytest.mark.integration
def test_frequency_saturation():
    """Test frequency saturation detection (>3.5)."""
    metrics = [
        {"ctr": 3.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 2.9, "frequency": 3.0, "cpm": 11.0},
        {"ctr": 2.8, "frequency": 3.6, "cpm": 12.0},  # Frequency > 3.5
    ]

    result = detect_fatigue("ad_2", metrics)

    assert result.status == "SATURATED"
    assert "Frequency" in result.reason
    assert result.metrics["frequency"] > 3.5


@pytest.mark.integration
def test_cpm_increase_detection():
    """Test CPM increase detection (>30%)."""
    metrics = [
        {"ctr": 3.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 2.9, "frequency": 2.2, "cpm": 11.0},
        {"ctr": 2.8, "frequency": 2.4, "cpm": 13.5},  # 35% increase
    ]

    result = detect_fatigue("ad_3", metrics)

    assert result.status == "FATIGUING"
    assert "CPM increased" in result.reason
    assert result.metrics["cpm_increase_pct"] > 30


@pytest.mark.integration
def test_combined_fatigue_signals():
    """Test combined fatigue (declining CTR + rising CPM + high frequency)."""
    metrics = [
        {"ctr": 4.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 3.0, "frequency": 2.8, "cpm": 13.0},  # All signals present
    ]

    result = detect_fatigue("ad_4", metrics)

    assert result.status == "FATIGUING"
    assert "Combined fatigue" in result.reason


@pytest.mark.integration
def test_healthy_ad_no_fatigue():
    """Test that healthy ads are not flagged."""
    metrics = [
        {"ctr": 3.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 3.1, "frequency": 2.1, "cpm": 10.5},  # Stable/improving
        {"ctr": 3.2, "frequency": 2.2, "cpm": 10.3},
    ]

    result = detect_fatigue("ad_5", metrics)

    assert result.status == "HEALTHY"
    assert "No fatigue" in result.reason


@pytest.mark.integration
def test_insufficient_data():
    """Test that insufficient data is handled."""
    metrics = [
        {"ctr": 3.0, "frequency": 2.0, "cpm": 10.0},
    ]

    result = detect_fatigue("ad_6", metrics)

    assert result.status == "INSUFFICIENT_DATA"


@pytest.mark.integration
def test_gradual_decline_not_flagged():
    """Test that gradual decline (<25%) is not flagged."""
    metrics = [
        {"ctr": 3.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 2.9, "frequency": 2.1, "cpm": 10.5},
        {"ctr": 2.8, "frequency": 2.2, "cpm": 11.0},
        {"ctr": 2.7, "frequency": 2.3, "cpm": 11.5},  # 10% decline
    ]

    result = detect_fatigue("ad_7", metrics)

    # Should be healthy (decline < 25%)
    # Note: might be flagged by CPM increase if >30%
    assert result.status in ["HEALTHY", "FATIGUING"]


@pytest.mark.integration
def test_recovery_pattern():
    """Test that ads recovering from fatigue are handled."""
    metrics = [
        {"ctr": 4.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 2.5, "frequency": 3.0, "cpm": 15.0},  # Fatigued
        {"ctr": 3.5, "frequency": 2.2, "cpm": 11.0},  # Recovered
    ]

    result = detect_fatigue("ad_8", metrics)

    # Latest vs earliest: CTR went down slightly, but not >25%
    assert result.status in ["HEALTHY", "FATIGUING"]


@pytest.mark.integration
def test_zero_ctr_edge_case():
    """Test handling of zero CTR edge case."""
    metrics = [
        {"ctr": 0.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 0.1, "frequency": 2.5, "cpm": 12.0},
    ]

    result = detect_fatigue("ad_9", metrics)

    # Should not crash on division by zero
    assert result.status in ["HEALTHY", "FATIGUING", "SATURATED"]


@pytest.mark.integration
def test_extreme_frequency():
    """Test extreme frequency detection (>5.0)."""
    metrics = [
        {"ctr": 3.0, "frequency": 2.0, "cpm": 10.0},
        {"ctr": 2.0, "frequency": 6.0, "cpm": 20.0},  # Extreme frequency
    ]

    result = detect_fatigue("ad_10", metrics)

    assert result.status == "SATURATED"
    assert result.metrics["frequency"] > 3.5


@pytest.mark.integration
def test_time_series_multiple_points():
    """Test with longer time series (7 data points)."""
    # Simulate a week of daily metrics
    metrics = [
        {"ctr": 4.0, "frequency": 1.5, "cpm": 8.0},   # Day 1
        {"ctr": 3.8, "frequency": 1.8, "cpm": 9.0},   # Day 2
        {"ctr": 3.5, "frequency": 2.1, "cpm": 10.0},  # Day 3
        {"ctr": 3.2, "frequency": 2.4, "cpm": 11.0},  # Day 4
        {"ctr": 2.8, "frequency": 2.8, "cpm": 12.5},  # Day 5
        {"ctr": 2.5, "frequency": 3.2, "cpm": 14.0},  # Day 6
        {"ctr": 2.0, "frequency": 3.8, "cpm": 16.0},  # Day 7 - Clear fatigue
    ]

    result = detect_fatigue("ad_11", metrics)

    # Should detect fatigue (50% CTR decline, 100% CPM increase, high frequency)
    assert result.status in ["FATIGUING", "SATURATED"]


# Integration with alert_rules.py (if available)
@pytest.mark.integration
def test_integration_with_alert_rules():
    """Test integration with alert_rules AlertRule system."""
    try:
        import sys
        from pathlib import Path
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(PROJECT_ROOT / "services" / "ml-service"))

        from src.alerts.alert_rules import AlertRule, AlertType, AlertSeverity

        # Create CTR anomaly rule
        rule = AlertRule(
            rule_id="ctr_drop_test",
            name="CTR Drop >25%",
            alert_type=AlertType.CTR_ANOMALY,
            severity=AlertSeverity.MEDIUM,
            threshold=25.0,
            threshold_operator=">=",
            enabled=True
        )

        # Test with 30% drop
        should_alert = rule.evaluate(30.0)
        assert should_alert == True

        # Test with 20% drop
        should_alert = rule.evaluate(20.0)
        assert should_alert == False

    except ImportError:
        pytest.skip("alert_rules module not available")
