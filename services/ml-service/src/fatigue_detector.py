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
    """
    if len(metrics_history) < 3:
        return FatigueResult("INSUFFICIENT_DATA", 0.0, "Need 3+ days of data", 999)
    
    recent = metrics_history[-1]  # Last 24h
    older = metrics_history[-3]   # 3 days ago
    
    # Rule 1: CTR Decline (20% drop = fatiguing)
    if older.get('ctr', 0) > 0:
        ctr_decline = (older['ctr'] - recent.get('ctr', 0)) / older['ctr']
        if ctr_decline > 0.20:
            return FatigueResult(
                "FATIGUING", 
                min(ctr_decline, 1.0),
                f"CTR dropped {ctr_decline*100:.1f}% in 3 days",
                3.0
            )
    
    # Rule 2: Frequency Saturation (>3.5 = saturated)
    if recent.get('frequency', 0) > 3.5:
        return FatigueResult(
            "SATURATED",
            min(recent['frequency'] / 5.0, 1.0),
            f"Frequency at {recent['frequency']:.1f} (>3.5 threshold)",
            2.0
        )
    
    # Rule 3: CPM Spike (50% increase = audience exhausted)
    if older.get('cpm', 0) > 0:
        cpm_increase = (recent.get('cpm', 0) - older['cpm']) / older['cpm']
        if cpm_increase > 0.50:
            return FatigueResult(
                "AUDIENCE_EXHAUSTED",
                min(cpm_increase, 1.0),
                f"CPM spiked {cpm_increase*100:.1f}% in 3 days",
                1.0
            )
    
    return FatigueResult("HEALTHY", 0.0, "No fatigue signals detected", 14.0)
