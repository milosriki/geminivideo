"""
Fatigue Detector - Predict ad fatigue BEFORE the crash.
Don't wait for CTR to drop 50%. Detect the TREND.
"""
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FatigueResult:
    status: str  # HEALTHY, FATIGUING, SATURATED, AUDIENCE_EXHAUSTED
    confidence: float
    reason: str
    days_until_critical: float

def detect_fatigue(ad_id: str, metrics_history: List[Dict]) -> FatigueResult:
    """
    Don't wait for crash. Detect the TREND.
    Called every 6 hours by scheduled task.

    Args:
        ad_id: Ad identifier
        metrics_history: List of daily metrics dicts with keys: ctr, frequency, cpm, impressions

    Returns:
        FatigueResult with status and recommendation
    """
    if len(metrics_history) < 3:
        return FatigueResult(
            status="INSUFFICIENT_DATA",
            confidence=0.0,
            reason="Need at least 3 days of data",
            days_until_critical=999
        )

    recent = metrics_history[-1]  # Last 24 hours
    older = metrics_history[-3]   # 3 days ago

    # Rule 1: CTR Decline (20% drop = fatiguing)
    if older.get('ctr', 0) > 0:
        ctr_decline = (older['ctr'] - recent.get('ctr', 0)) / older['ctr']
        if ctr_decline > 0.20:
            return FatigueResult(
                status="FATIGUING",
                confidence=min(ctr_decline, 1.0),
                reason=f"CTR dropped {ctr_decline*100:.1f}% in 3 days",
                days_until_critical=3.0
            )

    # Rule 2: Frequency Saturation (>3.5 = saturated)
    if recent.get('frequency', 0) > 3.5:
        return FatigueResult(
            status="SATURATED",
            confidence=min(recent['frequency'] / 5.0, 1.0),
            reason=f"Frequency at {recent['frequency']:.1f} (>3.5 threshold)",
            days_until_critical=2.0
        )

    # Rule 3: CPM Spike (50% increase = audience exhausted)
    if older.get('cpm', 0) > 0:
        cpm_increase = (recent.get('cpm', 0) - older['cpm']) / older['cpm']
        if cpm_increase > 0.50:
            return FatigueResult(
                status="AUDIENCE_EXHAUSTED",
                confidence=min(cpm_increase, 1.0),
                reason=f"CPM spiked {cpm_increase*100:.1f}% in 3 days",
                days_until_critical=1.0
            )

    # Rule 4: Impressions Saturation
    if len(metrics_history) >= 7:
        week_ago = metrics_history[-7]
        if week_ago.get('impressions', 0) > 0:
            impr_growth = (recent.get('impressions', 0) - week_ago['impressions']) / week_ago['impressions']
            if impr_growth < 0.10:  # Less than 10% growth in a week
                return FatigueResult(
                    status="FATIGUING",
                    confidence=0.6,
                    reason=f"Impression growth slowing ({impr_growth*100:.1f}% in 7 days)",
                    days_until_critical=5.0
                )

    return FatigueResult(
        status="HEALTHY",
        confidence=0.0,
        reason="No fatigue signals detected",
        days_until_critical=14.0
    )
