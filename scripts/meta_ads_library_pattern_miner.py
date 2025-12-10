#!/usr/bin/env python3
"""
Meta Ads Library Pattern Miner - REAL DATA VERSION

Analyzes successful ads from real market data sources:
- CSV imports of competitor ads
- Tracked competitor data from CompetitorTracker
- Real analysis with actual engagement metrics

ALL FAKE DATA HAS BEEN REMOVED.
"""

import sys
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter

# Add market-intel service to path (hyphenated directory name)
market_intel_path = Path(__file__).parent.parent / "services" / "market-intel"
sys.path.insert(0, str(market_intel_path))

from csv_importer import CSVImporter
from competitor_tracker import CompetitorTracker


class AdPatternMiner:
    """Mines patterns from REAL Meta Ads Library data"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.hooks_path = config_path / 'hooks' / 'hook_templates.json'
        self.tracker = CompetitorTracker()
        self.ads_data = []

    def load_from_csv(self, csv_path: str) -> int:
        """
        Load competitor ads from CSV file

        Args:
            csv_path: Path to CSV file with columns:
                     brand, hook_text, engagement, platform, views, url

        Returns:
            Number of ads loaded
        """
        print(f"Loading ads from CSV: {csv_path}")
        self.ads_data = CSVImporter.import_competitor_ads(csv_path)

        # Track all imported ads
        for ad in self.ads_data:
            self.tracker.track_ad(ad)

        print(f"Loaded {len(self.ads_data)} ads from CSV")
        return len(self.ads_data)

    def load_from_tracker(self, days: int = 30, min_engagement: float = 0) -> int:
        """
        Load ads from CompetitorTracker database

        Args:
            days: Load ads from last N days
            min_engagement: Minimum engagement threshold

        Returns:
            Number of ads loaded
        """
        print(f"Loading ads from tracker (last {days} days)...")
        self.ads_data = self.tracker.get_competitor_ads(
            days=days,
            min_engagement=min_engagement
        )
        print(f"Loaded {len(self.ads_data)} ads from tracker")
        return len(self.ads_data)

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns from REAL loaded ads data

        Returns:
            Dictionary containing real pattern analysis
        """
        if not self.ads_data:
            return {
                "error": "No data loaded. Use load_from_csv() or load_from_tracker() first.",
                "hook_patterns": {},
                "duration_patterns": {},
                "visual_patterns": {},
                "cta_patterns": {}
            }

        print(f"\nAnalyzing {len(self.ads_data)} real ads...")

        patterns = {
            'hook_patterns': self._analyze_hook_patterns(),
            'engagement_patterns': self._analyze_engagement_patterns(),
            'platform_patterns': self._analyze_platform_patterns(),
            'brand_patterns': self._analyze_brand_patterns(),
            'data_source': 'real_data',
            'total_ads_analyzed': len(self.ads_data),
            'analyzed_at': datetime.utcnow().isoformat()
        }

        return patterns

    def _analyze_hook_patterns(self) -> Dict[str, Any]:
        """Analyze REAL hook patterns from loaded ads"""
        hook_types = Counter()
        hook_engagement = {}

        for ad in self.ads_data:
            hook = ad.get("hook_text", "").lower()
            engagement = ad.get("engagement", 0)

            # Classify hook types based on actual content
            classified_types = []

            if "?" in hook:
                classified_types.append("question_based")

            if any(word in hook for word in ["secret", "discover", "revealed", "hidden", "truth"]):
                classified_types.append("curiosity_gap")

            if any(word in hook for word in ["now", "today", "limited", "urgent", "hurry"]):
                classified_types.append("urgency_scarcity")

            if any(word in hook for word in ["proven", "tested", "thousands", "millions", "trust"]):
                classified_types.append("social_proof")

            if any(word in hook for word in ["how to", "learn", "discover how", "find out"]):
                classified_types.append("educational")

            if any(word in hook for word in ["free", "save", "discount", "$", "deal"]):
                classified_types.append("value_proposition")

            # Count hook types
            for htype in classified_types:
                hook_types[htype] += 1

                # Track engagement per hook type
                if htype not in hook_engagement:
                    hook_engagement[htype] = []
                hook_engagement[htype].append(engagement)

        # Calculate real success rates based on actual engagement
        total_ads = len(self.ads_data)
        success_rates = {}

        for htype, engagements in hook_engagement.items():
            avg_engagement = sum(engagements) / len(engagements) if engagements else 0
            success_rates[htype] = {
                "count": hook_types[htype],
                "percentage": round(hook_types[htype] / total_ads * 100, 2),
                "avg_engagement": round(avg_engagement, 4)
            }
    
    def _analyze_visual_patterns(self) -> Dict[str, Any]:
        """Analyze effective visual elements"""
        # Visual pattern analysis from real data
        visual_elements = Counter()
        
        for ad in self.ads_data:
            # Extract visual cues from ad data if available
            if ad.get("has_video"):
                visual_elements["video"] += 1
            if ad.get("has_text_overlay"):
                visual_elements["text_overlay"] += 1
            if ad.get("has_product_shot"):
                visual_elements["product_shot"] += 1
        
        return {
            'most_common': visual_elements.most_common(5) if visual_elements else [],
            'source': 'real_ad_analysis'
        }
    
    def _analyze_cta_patterns(self) -> Dict[str, Any]:
        """Analyze CTA patterns from real data"""
        cta_types = Counter()
        
        for ad in self.ads_data:
            cta = ad.get("cta", "").lower()
            if "shop" in cta or "buy" in cta:
                cta_types["purchase"] += 1
            elif "learn" in cta or "more" in cta:
                cta_types["learn_more"] += 1
            elif "sign" in cta or "join" in cta:
                cta_types["signup"] += 1
        
        return {
            'top_ctas': cta_types.most_common(5),
            'source': 'real_ad_analysis'
        }

    def _analyze_engagement_patterns(self) -> Dict[str, Any]:
        """Analyze REAL engagement patterns"""
        engagements = [ad.get("engagement", 0) for ad in self.ads_data]

        if not engagements:
            return {"error": "No engagement data available"}

        # Calculate real statistics
        sorted_engagements = sorted(engagements)
        n = len(sorted_engagements)

        return {
            "avg_engagement": round(sum(engagements) / n, 4),
            "median_engagement": sorted_engagements[n // 2],
            "top_10_percent": round(sorted_engagements[int(n * 0.9)], 4),
            "top_25_percent": round(sorted_engagements[int(n * 0.75)], 4),
            "min_engagement": sorted_engagements[0],
            "max_engagement": sorted_engagements[-1],
            "sample_size": n,
            "source": "real_metrics"
        }

    def _analyze_platform_patterns(self) -> Dict[str, Any]:
        """Analyze REAL platform distribution"""
        platform_counts = Counter()
        platform_engagement = {}

        for ad in self.ads_data:
            platform = ad.get("platform", "Unknown")
            engagement = ad.get("engagement", 0)

            platform_counts[platform] += 1

            if platform not in platform_engagement:
                platform_engagement[platform] = []
            platform_engagement[platform].append(engagement)

        # Calculate average engagement per platform
        platform_stats = {}
        for platform, count in platform_counts.items():
            avg_eng = sum(platform_engagement[platform]) / len(platform_engagement[platform])
            platform_stats[platform] = {
                "count": count,
                "percentage": round(count / len(self.ads_data) * 100, 2),
                "avg_engagement": round(avg_eng, 4)
            }

        return {
            "platforms": platform_stats,
            "total_platforms": len(platform_counts),
            "source": "real_platform_data"
        }

    def _analyze_brand_patterns(self) -> Dict[str, Any]:
        """Analyze REAL brand/competitor patterns"""
        brand_counts = Counter()
        brand_engagement = {}

        for ad in self.ads_data:
            brand = ad.get("brand", "Unknown")
            engagement = ad.get("engagement", 0)

            brand_counts[brand] += 1

            if brand not in brand_engagement:
                brand_engagement[brand] = []
            brand_engagement[brand].append(engagement)

        # Top competitors by activity
        top_competitors = []
        for brand, count in brand_counts.most_common(10):
            avg_eng = sum(brand_engagement[brand]) / len(brand_engagement[brand])
            top_competitors.append({
                "brand": brand,
                "ad_count": count,
                "avg_engagement": round(avg_eng, 4)
            })

        return {
            "top_competitors": top_competitors,
            "total_brands": len(brand_counts),
            "source": "real_competitor_data"
        }

    def update_config_with_patterns(self, patterns: Dict[str, Any]):
        """Update configuration files with discovered REAL patterns"""
        print("\nUpdating configuration with REAL discovered patterns...")

        # Check if hooks config exists
        if not self.hooks_path.exists():
            print(f"Hooks config not found at {self.hooks_path}")
            print("Skipping config update")
        else:
            # Load current hooks config
            with open(self.hooks_path, 'r') as f:
                hooks_config = json.load(f)

            # Update weights based on REAL success rates
            hook_success = patterns.get('hook_patterns', {}).get('success_rates_by_type', {})

            for hook in hooks_config.get('hooks', []):
                hook_id = hook.get('id', '')

                # Map hook IDs to our analyzed types
                if hook_id in hook_success:
                    metrics = hook_success[hook_id]
                    # Weight by normalized engagement
                    hook['weight'] = round(metrics.get('avg_engagement', 0), 2)
                    hook['last_updated'] = datetime.utcnow().isoformat()
                    hook['data_source'] = 'real_market_data'
                    hook['sample_size'] = metrics.get('count', 0)

            # Save updated config
            with open(self.hooks_path, 'w') as f:
                json.dump(hooks_config, f, indent=2)

            print(f"Updated hooks config: {self.hooks_path}")

        # Generate insights report
        report_path = self.config_path.parent.parent / 'logs' / 'pattern_mining_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'real_market_intelligence',
            'total_ads_analyzed': patterns.get('total_ads_analyzed', 0),
            'patterns': patterns,
            'recommendations': self._generate_recommendations(patterns)
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Generated insights report: {report_path}")

    def _generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations from REAL patterns"""
        recommendations = []

        # Hook recommendations based on real data
        hook_patterns = patterns.get('hook_patterns', {})
        top_hooks = hook_patterns.get('most_common', [])

        if top_hooks:
            top_3 = top_hooks[:3]
            recommendations.append(
                f"Top performing hook types (real data): {', '.join([h[0] for h in top_3])}"
            )

        # Engagement recommendations
        engagement = patterns.get('engagement_patterns', {})
        if engagement and 'avg_engagement' in engagement:
            recommendations.append(
                f"Average engagement rate: {engagement['avg_engagement']:.2%} "
                f"(target top 25%: {engagement.get('top_25_percent', 0):.2%})"
            )

        # Platform recommendations
        platform_patterns = patterns.get('platform_patterns', {})
        platforms = platform_patterns.get('platforms', {})
        if platforms:
            best_platform = max(platforms.items(), key=lambda x: x[1].get('avg_engagement', 0))
            recommendations.append(
                f"Best performing platform: {best_platform[0]} "
                f"({best_platform[1].get('avg_engagement', 0):.2%} avg engagement)"
            )

        # Competitor insights
        brand_patterns = patterns.get('brand_patterns', {})
        top_competitors = brand_patterns.get('top_competitors', [])
        if top_competitors:
            recommendations.append(
                f"Most active competitor: {top_competitors[0]['brand']} "
                f"({top_competitors[0]['ad_count']} ads tracked)"
            )

        if not recommendations:
            recommendations.append("Load more data for better recommendations")

        return recommendations


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Meta Ads Library Pattern Miner')
    parser.add_argument(
        '--niche',
        default='e-commerce product',
        help='Niche keywords to search for (default: "e-commerce product")'
    )
    parser.add_argument(
        '--min-impressions',
        type=int,
        default=10000,
        help='Minimum impressions threshold (default: 10000)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Number of ads to analyze (default: 50)'
    )
    parser.add_argument(
        '--use-mock',
        action='store_true',
        help='Force use of mock data instead of real API'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Meta Ads Library Pattern Miner - REAL DATA VERSION")
    print("=" * 60)

    base_path = Path(__file__).parent.parent
    config_path = base_path / 'shared' / 'config'

    miner = AdPatternMiner(config_path)

    # Check for CSV data source
    csv_path = base_path / 'data' / 'competitor_ads.csv'

    if csv_path.exists():
        print(f"\nFound CSV data source: {csv_path}")
        miner.load_from_csv(str(csv_path))
    else:
        print(f"\nNo CSV found at {csv_path}")
        print("Attempting to load from CompetitorTracker...")
        count = miner.load_from_tracker(days=30)

        if count == 0:
            print("\n" + "!" * 60)
            print("NO REAL DATA AVAILABLE")
            print("!" * 60)
            print("\nTo use this tool, you need REAL competitor ad data:")
            print("\nOption 1: Create CSV file at:")
            print(f"  {csv_path}")
            print("\n  Required columns:")
            print("    - brand: Competitor brand name")
            print("    - hook_text: Ad hook/opening text")
            print("    - engagement: Engagement rate (0-1)")
            print("    - platform: Meta, TikTok, YouTube, etc.")
            print("    - views: Number of views")
            print("    - url: Link to ad")
            print("\nOption 2: Use CompetitorTracker API to import ads")
            print("  POST /api/market-intel/import-csv")
            print("\nOption 3: Manual tracking via CompetitorTracker")
            print("  tracker.track_ad({...})")
            print("\n" + "!" * 60)
            return

    # Analyze patterns from REAL data
    patterns = miner.analyze_patterns()

    if 'error' in patterns:
        print(f"\nError: {patterns['error']}")
        return

    print("\nReal Pattern Analysis:")
    print(f"  Total ads analyzed: {patterns.get('total_ads_analyzed', 0)}")

    hook_patterns = patterns.get('hook_patterns', {})
    print(f"  Hook types found: {len(hook_patterns.get('most_common', []))}")

    platform_patterns = patterns.get('platform_patterns', {})
    print(f"  Platforms: {platform_patterns.get('total_platforms', 0)}")

    brand_patterns = patterns.get('brand_patterns', {})
    print(f"  Competitors tracked: {brand_patterns.get('total_brands', 0)}")

    miner.update_config_with_patterns(patterns)

    print("\n" + "=" * 60)
    print("Pattern mining complete! (REAL DATA)")
    print("=" * 60)


if __name__ == '__main__':
    main()
