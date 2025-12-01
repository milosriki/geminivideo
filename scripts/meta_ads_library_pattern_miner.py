#!/usr/bin/env python3
"""
Meta Ads Library Pattern Miner
Analyzes successful ads from Meta Ads Library to identify patterns
Extracts hooks, visual patterns, and engagement signals
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'services' / 'titan-core'))

# Import real Meta Ads Library implementation
try:
    from meta_ads_library import RealMetaAdsLibrary, meta_ads_library
    REAL_API_AVAILABLE = meta_ads_library.enabled
except ImportError:
    REAL_API_AVAILABLE = False
    print("Warning: Could not import RealMetaAdsLibrary, using mock data only")


class AdPatternMiner:
    """Mines patterns from Meta Ads Library data"""

    def __init__(self, config_path: Path, use_real_api: bool = True):
        self.config_path = config_path
        self.hooks_path = config_path / 'hooks' / 'hook_templates.json'
        self.use_real_api = use_real_api and REAL_API_AVAILABLE
        self.meta_api = meta_ads_library if REAL_API_AVAILABLE else None
        self.patterns = {
            'successful_hooks': [],
            'common_durations': [],
            'effective_visuals': [],
            'trending_topics': []
        }

        if self.use_real_api:
            print("✅ Using real Meta Ads Library API")
        else:
            print("⚠️  Using mock data (API not available)")
    
    def analyze_ad_library_export(
        self,
        export_path: Path = None,
        niche_keywords: str = "e-commerce product",
        min_impressions: int = 10000,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Analyze Meta Ads Library export or real API data

        Args:
            export_path: Path to exported data (deprecated, kept for compatibility)
            niche_keywords: Keywords to search for in Meta Ads Library
            min_impressions: Minimum impressions threshold for top performers
            limit: Number of ads to analyze

        Returns:
            Dictionary with analyzed patterns
        """
        print("Analyzing Meta Ads Library patterns...")

        if self.use_real_api:
            # Use real API data
            print(f"Fetching real ads for niche: {niche_keywords}")
            real_analysis = self.meta_api.analyze_top_performers(
                niche_keywords=niche_keywords,
                min_impressions=min_impressions,
                limit=limit
            )

            # Extract patterns from real data
            patterns = {
                'hook_patterns': self._analyze_hook_patterns_from_real_data(real_analysis),
                'duration_patterns': self._analyze_duration_patterns(),  # Keep mock for now
                'visual_patterns': self._analyze_visual_patterns(),  # Keep mock for now
                'cta_patterns': self._analyze_cta_patterns(),  # Keep mock for now
                'real_data_stats': {
                    'total_ads': real_analysis.get('total_ads_analyzed', 0),
                    'date_range': real_analysis.get('date_range', {}),
                    'spend_analysis': real_analysis.get('spend_analysis', {})
                }
            }
        else:
            # Fall back to mock analysis
            print("Using mock data for analysis...")
            patterns = {
                'hook_patterns': self._analyze_hook_patterns(),
                'duration_patterns': self._analyze_duration_patterns(),
                'visual_patterns': self._analyze_visual_patterns(),
                'cta_patterns': self._analyze_cta_patterns()
            }

        return patterns
    
    def _analyze_hook_patterns_from_real_data(self, real_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze hook patterns from real API data

        Args:
            real_analysis: Analysis results from Meta API

        Returns:
            Hook patterns dictionary
        """
        copy_patterns = real_analysis.get('copy_patterns', {})

        if not copy_patterns:
            # Fall back to mock if no real data
            return self._analyze_hook_patterns()

        # Map copy patterns to hook types
        hook_mapping = {
            'question': 'curiosity_gap',
            'urgency': 'urgency_scarcity',
            'social_proof': 'social_proof',
            'negative_hooks': 'pattern_interrupt',
            'transformation': 'emotional_story'
        }

        # Build Counter from real data
        hook_types = Counter()
        success_rates = {}

        for pattern_key, hook_type in hook_mapping.items():
            if pattern_key in copy_patterns:
                count = copy_patterns[pattern_key].get('count', 0)
                percentage = copy_patterns[pattern_key].get('percentage', 0)
                hook_types[hook_type] = count
                # Estimate success rate from usage percentage
                success_rates[hook_type] = round(percentage / 100 * 0.7 + 0.3, 2)  # Scale to 0.3-1.0

        # Add number hook pattern
        if 'number' in copy_patterns:
            hook_types['number_hook'] = copy_patterns['number']['count']
            success_rates['number_hook'] = round(copy_patterns['number']['percentage'] / 100 * 0.7 + 0.3, 2)

        return {
            'most_common': hook_types.most_common(3),
            'success_rate_by_type': success_rates,
            'data_source': 'meta_ads_api'
        }

    def _analyze_hook_patterns(self) -> Dict[str, Any]:
        """Analyze effective hook patterns (mock data fallback)"""
        # Mock data - would be extracted from actual ads
        hook_types = Counter({
            'curiosity_gap': 345,
            'urgency_scarcity': 289,
            'social_proof': 267,
            'pattern_interrupt': 198,
            'emotional_story': 234
        })

        return {
            'most_common': hook_types.most_common(3),
            'success_rate_by_type': {
                'curiosity_gap': 0.72,
                'urgency_scarcity': 0.68,
                'social_proof': 0.65,
                'pattern_interrupt': 0.61,
                'emotional_story': 0.70
            },
            'data_source': 'mock'
        }
    
    def _analyze_duration_patterns(self) -> Dict[str, Any]:
        """Analyze optimal video durations"""
        # Mock data
        duration_performance = {
            '6-10s': {'avg_ctr': 0.078, 'sample_size': 450},
            '11-15s': {'avg_ctr': 0.065, 'sample_size': 520},
            '16-20s': {'avg_ctr': 0.052, 'sample_size': 380},
            '21-30s': {'avg_ctr': 0.045, 'sample_size': 290}
        }
        
        return duration_performance
    
    def _analyze_visual_patterns(self) -> Dict[str, Any]:
        """Analyze effective visual elements"""
        return {
            'face_in_first_3s': 0.83,  # 83% of top ads show face early
            'text_overlay': 0.71,       # 71% use text overlays
            'product_showcase': 0.68,   # 68% show product
            'bright_colors': 0.75,      # 75% use bright colors
            'motion_intensity': 'high'  # High motion performs best
        }
    
    def _analyze_cta_patterns(self) -> Dict[str, Any]:
        """Analyze call-to-action patterns"""
        return {
            'top_ctas': [
                {'text': 'Learn More', 'frequency': 0.34},
                {'text': 'Shop Now', 'frequency': 0.28},
                {'text': 'Get Started', 'frequency': 0.22},
                {'text': 'Sign Up', 'frequency': 0.16}
            ],
            'cta_placement': 'lower_third',
            'cta_timing': 'last_3_seconds'
        }
    
    def update_config_with_patterns(self, patterns: Dict[str, Any]):
        """Update configuration files with discovered patterns"""
        print("\nUpdating configuration with discovered patterns...")
        
        # Load current hooks config
        with open(self.hooks_path, 'r') as f:
            hooks_config = json.load(f)
        
        # Update weights based on success rates
        hook_success = patterns['hook_patterns']['success_rate_by_type']
        for hook in hooks_config['hooks']:
            hook_id = hook['id']
            if hook_id in hook_success:
                # Update weight based on observed success rate
                hook['weight'] = round(hook_success[hook_id], 2)
                hook['last_updated'] = datetime.utcnow().isoformat()
                hook['data_source'] = 'meta_ads_library'
        
        # Save updated config
        with open(self.hooks_path, 'w') as f:
            json.dump(hooks_config, f, indent=2)
        
        print(f"Updated hooks config: {self.hooks_path}")
        
        # Generate insights report
        report_path = self.config_path.parent.parent / 'logs' / 'pattern_mining_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'patterns': patterns,
            'recommendations': self._generate_recommendations(patterns)
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Generated insights report: {report_path}")
    
    def _generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations from patterns"""
        recommendations = []
        
        # Duration recommendations
        best_duration = max(
            patterns['duration_patterns'].items(),
            key=lambda x: x[1]['avg_ctr']
        )
        recommendations.append(
            f"Optimize video duration to {best_duration[0]} for maximum CTR ({best_duration[1]['avg_ctr']:.2%})"
        )
        
        # Visual recommendations
        visuals = patterns['visual_patterns']
        if visuals['face_in_first_3s'] > 0.7:
            recommendations.append(
                "Include human faces in first 3 seconds (83% of top ads)"
            )
        
        if visuals['text_overlay'] > 0.6:
            recommendations.append(
                "Add text overlays for key messages (71% of top ads)"
            )
        
        # Hook recommendations
        top_hooks = patterns['hook_patterns']['most_common'][:2]
        recommendations.append(
            f"Prioritize {top_hooks[0][0]} and {top_hooks[1][0]} hook types"
        )
        
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
    print("Meta Ads Library Pattern Miner")
    print("=" * 60)

    base_path = Path(__file__).parent.parent
    config_path = base_path / 'shared' / 'config'

    # Initialize miner
    use_real_api = not args.use_mock
    miner = AdPatternMiner(config_path, use_real_api=use_real_api)

    # Analyze patterns
    if miner.use_real_api:
        print(f"\nSearching for: {args.niche}")
        print(f"Min impressions: {args.min_impressions:,}")
        print(f"Ads to analyze: {args.limit}")

    patterns = miner.analyze_ad_library_export(
        niche_keywords=args.niche,
        min_impressions=args.min_impressions,
        limit=args.limit
    )

    print("\nDiscovered Patterns:")
    print(f"  Hook patterns: {len(patterns['hook_patterns'])} analyzed")
    print(f"  Duration patterns: {len(patterns['duration_patterns'])} segments")
    print(f"  Visual patterns: {len(patterns['visual_patterns'])} elements")
    print(f"  CTA patterns: {len(patterns['cta_patterns']['top_ctas'])} CTAs")

    # Show real data stats if available
    if 'real_data_stats' in patterns:
        stats = patterns['real_data_stats']
        print(f"\nReal API Data:")
        print(f"  Total ads analyzed: {stats['total_ads']}")
        if stats['date_range']:
            print(f"  Date range: {stats['date_range'].get('earliest', 'N/A')} to {stats['date_range'].get('latest', 'N/A')}")
        if stats['spend_analysis']:
            spend = stats['spend_analysis']
            print(f"  Avg spend: ${spend.get('avg', 0):,.2f}")
            print(f"  Total spend: ${spend.get('total', 0):,.2f}")

    miner.update_config_with_patterns(patterns)

    print("\n" + "=" * 60)
    print("Pattern mining complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
