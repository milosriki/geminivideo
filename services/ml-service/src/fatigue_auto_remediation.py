from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FatigueResult:
    ad_id: str
    fatigue_level: str # 'none', 'warning', 'critical'
    ctr_drop: float
    cpa_increase: float

class FatigueAutoRemediation:
    """
    Automatically takes action when ad fatigue is detected.
    """
    
    async def handle_fatigue(self, ad_id: str, fatigue_result: FatigueResult, current_budget: float) -> Dict[str, Any]:
        """
        Decides on an action based on fatigue level.
        """
        if fatigue_result.fatigue_level == "critical":
            print(f"🚨 CRITICAL FATIGUE detected for {ad_id}. Queueing PAUSE.")
            # In production: Queue to SafeExecutor/DB
            return {
                "action": "pause",
                "reason": "critical_fatigue",
                "target_budget": 0
            }
            
        elif fatigue_result.fatigue_level == "warning":
            print(f"⚠️ WARNING FATIGUE for {ad_id}. Reducing budget.")
            return {
                "action": "reduce_budget",
                "reason": "warning_fatigue",
                "target_budget": current_budget * 0.8
            }
            
        return {"action": "none"}
