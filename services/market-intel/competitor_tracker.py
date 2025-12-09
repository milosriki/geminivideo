"""
Competitor Tracker

Tracks competitor ads over time to identify trends, patterns, and winning strategies.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path


class CompetitorTracker:
    """Track and analyze competitor ads over time"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize competitor tracker

        Args:
            db_path: Path to store tracking data (JSON for now, will migrate to DB)
        """
        self.db_path = db_path or "/home/user/geminivideo/data/competitor_tracking.json"
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Load existing tracking data"""
        path = Path(self.db_path)
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return {"ads": [], "competitors": {}, "trends": []}

    def _save_data(self):
        """Save tracking data to file"""
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def track_ad(self, ad_data: Dict[str, Any]):
        """
        Track a new competitor ad

        Args:
            ad_data: Dictionary containing ad information
                Required fields: brand, hook_text, platform
                Optional fields: engagement, views, url, creative_type
        """
        ad_record = {
            "id": f"{ad_data['brand']}_{datetime.utcnow().timestamp()}",
            "brand": ad_data["brand"],
            "hook_text": ad_data.get("hook_text", ""),
            "platform": ad_data.get("platform", "Meta"),
            "engagement": ad_data.get("engagement", 0),
            "views": ad_data.get("views", 0),
            "url": ad_data.get("url", ""),
            "creative_type": ad_data.get("creative_type", "video"),
            "tracked_at": datetime.utcnow().isoformat(),
            "first_seen": ad_data.get("first_seen", datetime.utcnow().isoformat())
        }

        self.data["ads"].append(ad_record)

        # Update competitor stats
        brand = ad_data["brand"]
        if brand not in self.data["competitors"]:
            self.data["competitors"][brand] = {
                "total_ads": 0,
                "avg_engagement": 0,
                "platforms": set(),
                "first_tracked": datetime.utcnow().isoformat()
            }

        comp = self.data["competitors"][brand]
        comp["total_ads"] += 1
        comp["platforms"] = list(set(comp.get("platforms", [])) | {ad_data.get("platform", "Meta")})

        self._save_data()

    def get_competitor_ads(
        self,
        brand: Optional[str] = None,
        days: int = 30,
        min_engagement: float = 0
    ) -> List[Dict[str, Any]]:
        """
        Get tracked ads with optional filters

        Args:
            brand: Filter by specific brand
            days: Only return ads from last N days
            min_engagement: Minimum engagement threshold

        Returns:
            List of ad records matching filters
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        filtered_ads = []
        for ad in self.data["ads"]:
            # Date filter
            tracked_at = datetime.fromisoformat(ad["tracked_at"])
            if tracked_at < cutoff_date:
                continue

            # Brand filter
            if brand and ad["brand"] != brand:
                continue

            # Engagement filter
            if ad.get("engagement", 0) < min_engagement:
                continue

            filtered_ads.append(ad)

        return filtered_ads

    def analyze_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze trends from tracked ads

        Args:
            days: Analyze trends from last N days

        Returns:
            Dictionary with trend analysis
        """
        ads = self.get_competitor_ads(days=days)

        if not ads:
            return {
                "error": "No ads to analyze",
                "period_days": days,
                "total_ads": 0
            }

        # Analyze hook patterns
        hook_patterns = defaultdict(int)
        platform_distribution = defaultdict(int)
        brand_activity = defaultdict(int)

        for ad in ads:
            # Hook analysis
            hook = ad.get("hook_text", "").lower()
            if "?" in hook:
                hook_patterns["question_based"] += 1
            if any(word in hook for word in ["secret", "discover", "revealed", "hidden"]):
                hook_patterns["curiosity_gap"] += 1
            if any(word in hook for word in ["now", "today", "limited", "urgent"]):
                hook_patterns["urgency"] += 1
            if any(word in hook for word in ["free", "save", "discount", "$"]):
                hook_patterns["value_proposition"] += 1

            # Platform distribution
            platform_distribution[ad.get("platform", "Unknown")] += 1

            # Brand activity
            brand_activity[ad["brand"]] += 1

        total_ads = len(ads)

        return {
            "period_days": days,
            "total_ads": total_ads,
            "hook_patterns": {
                k: {"count": v, "percentage": round(v/total_ads * 100, 2)}
                for k, v in hook_patterns.items()
            },
            "platform_distribution": dict(platform_distribution),
            "top_competitors": sorted(
                brand_activity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "avg_engagement": sum(ad.get("engagement", 0) for ad in ads) / total_ads,
            "data_source": "real_tracked_data",
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def get_winning_hooks(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing hooks based on engagement

        Args:
            top_n: Number of top hooks to return

        Returns:
            List of top performing hooks with metrics
        """
        ads = self.data["ads"]

        # Sort by engagement
        sorted_ads = sorted(
            [ad for ad in ads if ad.get("hook_text")],
            key=lambda x: x.get("engagement", 0),
            reverse=True
        )[:top_n]

        return [
            {
                "hook_text": ad["hook_text"],
                "brand": ad["brand"],
                "engagement": ad.get("engagement", 0),
                "views": ad.get("views", 0),
                "platform": ad.get("platform", "Unknown"),
                "tracked_at": ad["tracked_at"]
            }
            for ad in sorted_ads
        ]

    def export_to_csv(self, output_path: str, days: int = 30):
        """
        Export tracked ads to CSV for analysis

        Args:
            output_path: Path to save CSV file
            days: Export ads from last N days
        """
        import pandas as pd

        ads = self.get_competitor_ads(days=days)

        if not ads:
            print(f"No ads to export from last {days} days")
            return

        df = pd.DataFrame(ads)
        df.to_csv(output_path, index=False)
        print(f"Exported {len(ads)} ads to {output_path}")


# ============================================================================
# ENDPOINT STUB FOR GATEWAY-API
# ============================================================================
"""
# Add to services/gateway-api/routes/market_intel.py:

from flask import Blueprint, request, jsonify
from services.market_intel import CompetitorTracker, CSVImporter

market_intel_bp = Blueprint('market_intel', __name__, url_prefix='/api/market-intel')

@market_intel_bp.route('/trends', methods=['GET'])
def get_trends():
    '''Get current market trends from tracked competitor ads'''
    days = request.args.get('days', default=30, type=int)

    tracker = CompetitorTracker()
    trends = tracker.analyze_trends(days=days)

    return jsonify(trends)

@market_intel_bp.route('/competitors/<brand>/ads', methods=['GET'])
def get_competitor_ads(brand):
    '''Get ads for a specific competitor'''
    days = request.args.get('days', default=30, type=int)

    tracker = CompetitorTracker()
    ads = tracker.get_competitor_ads(brand=brand, days=days)

    return jsonify({
        'brand': brand,
        'total_ads': len(ads),
        'ads': ads
    })

@market_intel_bp.route('/winning-hooks', methods=['GET'])
def get_winning_hooks():
    '''Get top performing hooks from competitor analysis'''
    top_n = request.args.get('top_n', default=10, type=int)

    tracker = CompetitorTracker()
    hooks = tracker.get_winning_hooks(top_n=top_n)

    return jsonify({
        'top_hooks': hooks,
        'source': 'real_competitor_data'
    })

@market_intel_bp.route('/import-csv', methods=['POST'])
def import_csv():
    '''Import competitor ads from CSV file'''
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # SECURITY FIX: Sanitize filename to prevent path traversal
    import os
    from pathlib import Path
    
    # Get safe filename (remove path components)
    safe_filename = os.path.basename(file.filename)
    # Remove any dangerous characters
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
    
    # Validate extension
    allowed_extensions = {'.csv', '.json', '.txt', '.xlsx'}
    ext = Path(safe_filename).suffix.lower()
    if ext not in allowed_extensions:
        return jsonify({'error': f'Invalid file extension: {ext}'}), 400
    
    # Create safe path
    temp_dir = Path('/tmp/competitor_imports')
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / safe_filename
    
    # Resolve to absolute path and verify it's within temp_dir
    temp_path = temp_path.resolve()
    temp_dir_abs = temp_dir.resolve()
    
    if not str(temp_path).startswith(str(temp_dir_abs)):
        return jsonify({'error': 'Path traversal detected'}), 403
    
    # Save file with secure permissions
    file.save(str(temp_path))
    os.chmod(temp_path, 0o600)  # Owner read/write only

    # Import ads
    ads = CSVImporter.import_competitor_ads(temp_path)

    # Track all imported ads
    tracker = CompetitorTracker()
    for ad in ads:
        tracker.track_ad(ad)

    # Analyze patterns
    patterns = CSVImporter.analyze_patterns(ads)

    return jsonify({
        'imported': len(ads),
        'patterns': patterns,
        'status': 'success'
    })

# Register blueprint in main app:
# app.register_blueprint(market_intel_bp)
"""
