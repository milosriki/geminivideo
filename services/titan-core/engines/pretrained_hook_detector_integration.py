#!/usr/bin/env python3
"""
Integration Example: PretrainedHookDetector with Titan-Core Components
Shows how to integrate hook detection with other video intelligence engines
"""

from pretrained_hook_detector import PretrainedHookDetector, HookType
from typing import List, Dict, Any
import json


class VideoAdAnalyzer:
    """
    Integrates PretrainedHookDetector with video ad analysis pipeline.
    """

    def __init__(self):
        self.hook_detector = PretrainedHookDetector()
        self.hook_detector.warmup()

    def analyze_video_script(self, script: str) -> Dict[str, Any]:
        """
        Analyze a complete video script for hooks.

        Args:
            script: Full video script text

        Returns:
            Dict with hook analysis
        """
        # Split script into sentences
        sentences = [s.strip() for s in script.split('.') if s.strip()]

        # Detect hooks in each sentence
        results = self.hook_detector.detect_hooks_batch(sentences)

        # Find the strongest hook (likely the opening)
        strongest_idx = max(
            range(len(results)),
            key=lambda i: results[i].hook_strength
        )

        return {
            'script': script,
            'total_sentences': len(sentences),
            'opening_hook': {
                'text': results[0].text,
                'type': results[0].primary_hook_type.value,
                'strength': results[0].hook_strength,
                'suggestions': results[0].improvement_suggestions
            },
            'strongest_hook': {
                'text': results[strongest_idx].text,
                'type': results[strongest_idx].primary_hook_type.value,
                'strength': results[strongest_idx].hook_strength,
                'position': strongest_idx + 1
            },
            'overall_analysis': self.hook_detector.analyze_hooks(sentences).__dict__,
            'all_hooks': [
                {
                    'text': r.text,
                    'type': r.primary_hook_type.value,
                    'strength': r.hook_strength
                }
                for r in results
            ]
        }

    def optimize_opening_hook(
        self,
        current_hook: str,
        target_type: HookType = None
    ) -> Dict[str, Any]:
        """
        Optimize the opening hook of a video ad.

        Args:
            current_hook: Current opening hook
            target_type: Desired hook type (optional)

        Returns:
            Optimization recommendations
        """
        result = self.hook_detector.detect_hook(current_hook)

        # Generate variants
        variants = self.hook_detector.generate_hook_variants(current_hook, num_variants=5)

        # Score each variant
        variant_scores = []
        for variant in variants:
            v_result = self.hook_detector.detect_hook(variant)
            variant_scores.append({
                'text': variant,
                'strength': v_result.hook_strength,
                'type': v_result.primary_hook_type.value
            })

        # Rank variants
        variant_scores.sort(key=lambda x: x['strength'], reverse=True)

        return {
            'current': {
                'text': current_hook,
                'strength': result.hook_strength,
                'type': result.primary_hook_type.value,
                'sentiment': result.sentiment,
                'attention_score': result.attention_score
            },
            'suggestions': result.improvement_suggestions,
            'variants': variant_scores,
            'best_variant': variant_scores[0] if variant_scores else None,
            'improvement_potential': (
                variant_scores[0]['strength'] - result.hook_strength
                if variant_scores else 0
            )
        }

    def ab_test_hooks(
        self,
        hook_variants: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze multiple hook variants for A/B testing.

        Args:
            hook_variants: List of hook variations to test

        Returns:
            A/B test recommendations
        """
        comparison = self.hook_detector.compare_hooks(hook_variants)

        # Rank by strength
        ranked = self.hook_detector.rank_hooks(hook_variants, metric="strength")

        # Categorize by hook type
        results = self.hook_detector.detect_hooks_batch(hook_variants)
        by_type = {}
        for result in results:
            hook_type = result.primary_hook_type.value
            if hook_type not in by_type:
                by_type[hook_type] = []
            by_type[hook_type].append({
                'text': result.text,
                'strength': result.hook_strength
            })

        return {
            'total_variants': len(hook_variants),
            'comparison': comparison,
            'ranked_by_strength': [
                {'text': text, 'score': score}
                for text, score in ranked
            ],
            'by_hook_type': by_type,
            'recommendation': {
                'test_first': ranked[0][0],
                'test_second': ranked[1][0] if len(ranked) > 1 else None,
                'diversity_score': len(by_type)  # More types = more diverse
            }
        }

    def extract_campaign_patterns(
        self,
        successful_campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract patterns from successful video ad campaigns.

        Args:
            successful_campaigns: List of dicts with 'hook' and 'performance' keys

        Returns:
            Pattern analysis
        """
        # Extract hooks
        hooks = [c['hook'] for c in successful_campaigns]

        # Extract patterns
        patterns = self.hook_detector.extract_hook_patterns(hooks)

        # Analyze top performers
        top_performers = sorted(
            successful_campaigns,
            key=lambda x: x.get('performance', 0),
            reverse=True
        )[:5]

        top_hooks = [c['hook'] for c in top_performers]
        top_results = self.hook_detector.detect_hooks_batch(top_hooks)

        return {
            'total_campaigns': len(successful_campaigns),
            'patterns': patterns,
            'top_performer_analysis': {
                'hooks': [
                    {
                        'text': r.text,
                        'type': r.primary_hook_type.value,
                        'strength': r.hook_strength,
                        'performance': top_performers[i].get('performance', 0)
                    }
                    for i, r in enumerate(top_results)
                ],
                'common_type': max(
                    patterns['common_hook_types'].items(),
                    key=lambda x: x[1]
                )[0] if patterns.get('common_hook_types') else None
            },
            'recommendations': self._generate_recommendations(patterns)
        }

    def _generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on patterns."""
        recommendations = []

        if patterns.get('avg_length'):
            recommendations.append(
                f"Optimal hook length: {patterns['avg_length']} words"
            )

        if patterns.get('common_hook_types'):
            top_type = max(
                patterns['common_hook_types'].items(),
                key=lambda x: x[1]
            )[0]
            recommendations.append(
                f"Most successful hook type: {top_type}"
            )

        if patterns.get('common_words'):
            top_words = ', '.join(patterns['common_words'][:3])
            recommendations.append(
                f"Power words to use: {top_words}"
            )

        if patterns.get('common_patterns'):
            recommendations.append(
                f"Successful patterns: {', '.join(patterns['common_patterns'])}"
            )

        return recommendations


def example_video_script_analysis():
    """Example: Analyze a complete video script."""
    print("=" * 80)
    print("EXAMPLE 1: Video Script Analysis")
    print("=" * 80)

    analyzer = VideoAdAnalyzer()

    script = """
    What if you could 10X your sales in just 30 days?
    Most businesses struggle with lead generation.
    But here's the secret they don't want you to know.
    Our proven system has helped 10,000+ entrepreneurs.
    Limited time offer: Get 50% off today only.
    Don't wait - transform your business now!
    """

    analysis = analyzer.analyze_video_script(script)

    print(f"\nScript Analysis:")
    print(f"Total Sentences: {analysis['total_sentences']}")
    print(f"\nOpening Hook:")
    print(f"  Text: {analysis['opening_hook']['text']}")
    print(f"  Type: {analysis['opening_hook']['type']}")
    print(f"  Strength: {analysis['opening_hook']['strength']:.2%}")

    print(f"\nStrongest Hook (Position {analysis['strongest_hook']['position']}):")
    print(f"  Text: {analysis['strongest_hook']['text']}")
    print(f"  Strength: {analysis['strongest_hook']['strength']:.2%}")


def example_hook_optimization():
    """Example: Optimize opening hook."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Hook Optimization")
    print("=" * 80)

    analyzer = VideoAdAnalyzer()

    current_hook = "Learn how to make money online"

    optimization = analyzer.optimize_opening_hook(current_hook)

    print(f"\nCurrent Hook: {optimization['current']['text']}")
    print(f"Strength: {optimization['current']['strength']:.2%}")
    print(f"Type: {optimization['current']['type']}")

    print(f"\nTop 3 Improved Variants:")
    for i, variant in enumerate(optimization['variants'][:3], 1):
        print(f"{i}. [{variant['strength']:.2%}] {variant['text']}")

    print(f"\nImprovement Potential: +{optimization['improvement_potential']:.2%}")


def example_ab_testing():
    """Example: A/B test hook variants."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: A/B Test Hook Variants")
    print("=" * 80)

    analyzer = VideoAdAnalyzer()

    variants = [
        "Save money on your energy bills",
        "SHOCKING: Your energy company is ripping you off!",
        "What if you could cut energy costs by 50%?",
        "Join 50,000+ people saving on energy",
        "The secret to slashing your energy bill revealed"
    ]

    ab_test = analyzer.ab_test_hooks(variants)

    print(f"\nTesting {ab_test['total_variants']} variants")
    print(f"\nRanked by Strength:")
    for i, variant in enumerate(ab_test['ranked_by_strength'][:3], 1):
        print(f"{i}. [{variant['score']:.2%}] {variant['text']}")

    print(f"\nRecommendation:")
    print(f"  Test First: {ab_test['recommendation']['test_first']}")
    print(f"  Test Second: {ab_test['recommendation']['test_second']}")
    print(f"  Diversity Score: {ab_test['recommendation']['diversity_score']} types")


def example_campaign_patterns():
    """Example: Extract patterns from successful campaigns."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Campaign Pattern Analysis")
    print("=" * 80)

    analyzer = VideoAdAnalyzer()

    successful_campaigns = [
        {'hook': 'What if you could 10X your results?', 'performance': 95},
        {'hook': 'Limited time: Get 50% off today', 'performance': 88},
        {'hook': 'Discover the secret to viral content', 'performance': 92},
        {'hook': '10,000+ customers trust our system', 'performance': 85},
        {'hook': 'WARNING: Stop wasting money on ads', 'performance': 90}
    ]

    patterns = analyzer.extract_campaign_patterns(successful_campaigns)

    print(f"\nAnalyzed {patterns['total_campaigns']} successful campaigns")
    print(f"\nTop Performer Hook Type: {patterns['top_performer_analysis']['common_type']}")

    print(f"\nRecommendations:")
    for rec in patterns['recommendations']:
        print(f"  - {rec}")


def main():
    """Run all integration examples."""
    print("\n" + "=" * 80)
    print("PRETRAINED HOOK DETECTOR - INTEGRATION EXAMPLES")
    print("Integrating with Titan-Core Video Intelligence")
    print("=" * 80)

    example_video_script_analysis()
    example_hook_optimization()
    example_ab_testing()
    example_campaign_patterns()

    print("\n" + "=" * 80)
    print("INTEGRATION EXAMPLES COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
