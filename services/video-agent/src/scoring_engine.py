import random
from typing import Dict, Any

class OracleScorer:
    """
    The 'Oracle' Predictive Engine.
    Predicts ad performance (CTR, ROAS, Viral Score) based on video attributes.
    In a real production system, this would load a trained XGBoost or Transformer model.
    For this '2026' demo, we use advanced heuristics and simulated probabilistic models.
    """

    def __init__(self):
        self.base_ctr = 0.015  # 1.5% baseline
        self.base_roas = 2.5   # 2.5x baseline

    def predict(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict performance metrics for a given video metadata.
        """
        # Extract features (simulated)
        has_hook = metadata.get('has_hook', True)
        duration = metadata.get('duration', 30)
        pacing = metadata.get('pacing', 'fast') # fast, medium, slow
        visual_style = metadata.get('visual_style', 'ugc') # ugc, cinematic, corporate

        # Calculate scores
        ctr_score = self._calculate_ctr(has_hook, pacing, visual_style)
        roas_score = self._calculate_roas(ctr_score, duration)
        viral_score = self._calculate_viral_score(ctr_score, pacing)

        return {
            "predicted_ctr": round(ctr_score, 4),
            "predicted_roas": round(roas_score, 2),
            "viral_potential": round(viral_score, 1),
            "confidence": 0.85, # Simulated model confidence
            "insights": self._generate_insights(ctr_score, roas_score, viral_score)
        }

    def _calculate_ctr(self, has_hook: bool, pacing: str, visual_style: str) -> float:
        score = self.base_ctr

        # Hook is critical
        if has_hook:
            score *= 1.5
        
        # Fast pacing usually wins on social
        if pacing == 'fast':
            score *= 1.3
        elif pacing == 'slow':
            score *= 0.8

        # UGC tends to have higher CTR than corporate
        if visual_style == 'ugc':
            score *= 1.2
        elif visual_style == 'corporate':
            score *= 0.7

        # Add some randomness to simulate real world variance
        score *= random.uniform(0.9, 1.1)

        return min(score, 0.08) # Cap at 8% CTR

    def _calculate_roas(self, ctr: float, duration: int) -> float:
        # Higher CTR often correlates with better ROAS, but not always
        score = self.base_roas * (ctr / self.base_ctr)

        # Duration penalty/boost
        if 15 <= duration <= 45:
            score *= 1.1 # Sweet spot
        else:
            score *= 0.9

        return min(score, 12.0) # Cap at 12x ROAS

    def _calculate_viral_score(self, ctr: float, pacing: str) -> float:
        # Viral score 0-100
        base = ctr * 1000 # Convert CTR to rough score
        
        if pacing == 'fast':
            base += 20
        
        return min(base, 99.9)

    def _generate_insights(self, ctr: float, roas: float, viral: float) -> list:
        insights = []
        if ctr > 0.03:
            insights.append("🔥 High stopping power detected.")
        else:
            insights.append("⚠️ Hook might be too weak. Consider adding a pattern interrupt.")

        if roas > 4.0:
            insights.append("💰 Excellent ROAS potential.")
        
        if viral > 70:
            insights.append("🚀 Viral potential is high!")

        return insights
