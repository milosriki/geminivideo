import pandas as pd
from typing import List, Dict, Any
from datetime import datetime


class CSVImporter:
    """Import competitor ad data from CSV files"""

    @staticmethod
    def import_competitor_ads(csv_path: str) -> List[Dict[str, Any]]:
        """
        Import competitor ads from CSV.
        Expected columns: brand, hook_text, engagement, platform, views, url
        """
        df = pd.read_csv(csv_path)

        ads = []
        for _, row in df.iterrows():
            ads.append({
                "brand": row.get("brand", "Unknown"),
                "hook_text": row.get("hook_text", ""),
                "engagement": float(row.get("engagement", 0)),
                "platform": row.get("platform", "Meta"),
                "views": int(row.get("views", 0)),
                "url": row.get("url", ""),
                "imported_at": datetime.utcnow().isoformat()
            })

        return ads

    @staticmethod
    def analyze_patterns(ads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze REAL patterns from imported ads"""
        if not ads:
            return {"error": "No ads to analyze"}

        # Real analysis from real data
        hook_types = {}
        for ad in ads:
            hook = ad.get("hook_text", "").lower()
            if "?" in hook:
                hook_types["question"] = hook_types.get("question", 0) + 1
            if any(w in hook for w in ["secret", "discover", "revealed"]):
                hook_types["curiosity"] = hook_types.get("curiosity", 0) + 1
            if any(w in hook for w in ["now", "today", "limited"]):
                hook_types["urgency"] = hook_types.get("urgency", 0) + 1

        # Calculate REAL success rates
        total = len(ads)
        patterns = {
            "hook_patterns": {k: {"count": v, "rate": v/total} for k, v in hook_types.items()},
            "avg_engagement": sum(a.get("engagement", 0) for a in ads) / total,
            "total_analyzed": total,
            "source": "real_data"
        }

        return patterns
