"""
Test suite for Creative Attribution Analysis - Agent 12
Demonstrates real statistical analysis with synthetic data
"""
import pytest
import numpy as np
from typing import Dict, List, Any
from creative_attribution import (
    CreativeAttribution,
    HookMetrics,
    VisualMetrics,
    CopyMetrics,
    FeatureCorrelation,
    Recommendation
)


class MockDatabaseService:
    """Mock database service for testing"""

    def __init__(self):
        self.campaign_data = self._generate_test_data()
        self.insights_store = []

    def _generate_test_data(self) -> List[Dict[str, Any]]:
        """Generate realistic test campaign data"""
        np.random.seed(42)

        data = []
        hook_types = ['curiosity_gap', 'transformation', 'social_proof', 'question', 'statistic_hook']
        visual_patterns = ['face_closeup', 'product_focus', 'testimonial', 'tutorial_demo', 'ugc_style']
        cta_types = ['shop_now', 'learn_more', 'sign_up', 'get_started', 'claim_offer']

        for i in range(100):
            hook_type = np.random.choice(hook_types)
            visual_pattern = np.random.choice(visual_patterns)
            cta_type = np.random.choice(cta_types)

            # Simulate correlation: certain patterns perform better
            base_ctr = 0.035
            base_roas = 2.5

            # Hook influence
            if hook_type == 'transformation':
                base_ctr *= 1.3
                base_roas *= 1.4
            elif hook_type == 'social_proof':
                base_ctr *= 1.2
                base_roas *= 1.3

            # Visual influence
            if visual_pattern == 'testimonial':
                base_ctr *= 1.15
                base_roas *= 1.25

            # Add noise
            ctr = max(0.01, base_ctr + np.random.normal(0, 0.01))
            roas = max(0.5, base_roas + np.random.normal(0, 0.5))
            conversion_rate = max(0.005, ctr * 0.6 + np.random.normal(0, 0.005))

            data.append({
                'creative_id': f'creative_{i}',
                'campaign_id': f'campaign_{i % 10}',
                'hook_text': f"This is a {hook_type} hook example {i}",
                'visual_pattern': visual_pattern,
                'cta_type': cta_type,
                'ad_copy': f"Example ad copy for {cta_type} with some words here",
                'ctr': ctr,
                'roas': roas,
                'conversion_rate': conversion_rate,
                'sentiment_score': np.random.uniform(-1, 1),
                # Features for correlation analysis
                'hook_strength': np.random.uniform(0.3, 0.9),
                'visual_energy': np.random.uniform(0.4, 0.95),
                'motion_score': np.random.uniform(0.2, 0.8),
                'text_density': np.random.uniform(0.1, 0.7),
                'emotion_score': np.random.uniform(0.3, 0.9),
                'technical_quality': np.random.uniform(0.5, 1.0),
                'face_time_ratio': np.random.uniform(0.0, 0.8),
                'color_vibrancy': np.random.uniform(0.3, 0.95),
                'scene_transitions': int(np.random.uniform(3, 15)),
                'color_palette': [f'#COLOR{j}' for j in range(3)]
            })

        return data

    def query_campaign_performance(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query campaign performance data"""
        if filters is None:
            return self.campaign_data

        filtered = self.campaign_data

        if 'campaign_id' in filters:
            filtered = [d for d in filtered if d['campaign_id'] == filters['campaign_id']]

        return filtered

    def store_insight(self, insight: Dict[str, Any]):
        """Store insight in mock database"""
        self.insights_store.append(insight)

    def query_insights(self, category: str = None, limit: int = 10, order_by: str = None) -> List[Dict[str, Any]]:
        """Query insights"""
        insights = self.insights_store

        if category:
            insights = [i for i in insights if i.get('category') == category]

        return insights[:limit]


class MockHookClassifier:
    """Mock hook classifier for testing"""

    class Classification:
        def __init__(self, hook_type):
            self.primary_hook = hook_type
            self.confidence = 0.85
            self.hook_strength = 0.75

    def classify(self, text: str):
        """Mock classification based on text content"""
        if 'transformation' in text.lower():
            return self.Classification('transformation')
        elif 'social_proof' in text.lower():
            return self.Classification('social_proof')
        elif 'question' in text.lower():
            return self.Classification('question')
        elif 'statistic' in text.lower():
            return self.Classification('statistic_hook')
        else:
            return self.Classification('curiosity_gap')


class MockVisualAnalyzer:
    """Mock visual analyzer for testing"""
    pass


class TestCreativeAttribution:
    """Test suite for CreativeAttribution"""

    @pytest.fixture
    def setup(self):
        """Setup test fixtures"""
        db = MockDatabaseService()
        hook_classifier = MockHookClassifier()
        visual_analyzer = MockVisualAnalyzer()

        attribution = CreativeAttribution(db, hook_classifier, visual_analyzer)

        return {
            'attribution': attribution,
            'db': db,
            'hook_classifier': hook_classifier,
            'visual_analyzer': visual_analyzer
        }

    def test_initialization(self, setup):
        """Test proper initialization"""
        attribution = setup['attribution']
        assert attribution is not None
        assert attribution.db is not None
        assert attribution.hook_classifier is not None
        assert attribution.visual_analyzer is not None

    def test_analyze_hook_performance(self, setup):
        """Test hook performance analysis"""
        attribution = setup['attribution']

        hook_metrics = attribution.analyze_hook_performance()

        assert isinstance(hook_metrics, list)
        assert len(hook_metrics) > 0

        # Check first metric
        metric = hook_metrics[0]
        assert isinstance(metric, HookMetrics)
        assert metric.count > 0
        assert 0 <= metric.avg_ctr <= 1
        assert metric.avg_roas >= 0
        assert 0 <= metric.statistical_significance <= 1

        print(f"\n✅ Hook Analysis:")
        for i, m in enumerate(hook_metrics[:3], 1):
            print(f"  {i}. {m.hook_type}: ROAS={m.avg_roas:.2f}, CTR={m.avg_ctr:.3f}, "
                  f"Significance={m.statistical_significance:.2f}, N={m.count}")

    def test_get_best_hooks(self, setup):
        """Test getting best performing hooks"""
        attribution = setup['attribution']

        # Test ROAS optimization
        best_roas = attribution.get_best_hooks(objective='roas', limit=3)
        assert isinstance(best_roas, list)
        assert len(best_roas) <= 3

        # Test CTR optimization
        best_ctr = attribution.get_best_hooks(objective='ctr', limit=3)
        assert isinstance(best_ctr, list)

        # Verify sorting
        if len(best_roas) >= 2:
            assert best_roas[0].avg_roas >= best_roas[1].avg_roas

        print(f"\n✅ Best Hooks (ROAS):")
        for i, hook in enumerate(best_roas, 1):
            print(f"  {i}. {hook.hook_type}: {hook.avg_roas:.2f}x ROAS")

    def test_analyze_visual_elements(self, setup):
        """Test visual element analysis"""
        attribution = setup['attribution']

        visual_metrics = attribution.analyze_visual_elements()

        assert isinstance(visual_metrics, list)
        assert len(visual_metrics) > 0

        metric = visual_metrics[0]
        assert isinstance(metric, VisualMetrics)
        assert metric.count > 0
        assert metric.avg_roas >= 0

        print(f"\n✅ Visual Analysis:")
        for i, m in enumerate(visual_metrics[:3], 1):
            print(f"  {i}. {m.pattern_type}: ROAS={m.avg_roas:.2f}, Motion={m.motion_score:.2f}")

    def test_get_optimal_visual_patterns(self, setup):
        """Test optimal visual pattern identification"""
        attribution = setup['attribution']

        optimal = attribution.get_optimal_visual_patterns(objective='roas')

        assert isinstance(optimal, dict)
        assert 'optimal_pattern' in optimal
        assert 'avg_roas' in optimal
        assert optimal['avg_roas'] > 0

        print(f"\n✅ Optimal Visual Pattern: {optimal['optimal_pattern']}")
        print(f"   ROAS: {optimal['avg_roas']:.2f}x")
        print(f"   CTR: {optimal['avg_ctr']:.3f}")

    def test_analyze_copy_patterns(self, setup):
        """Test copy pattern analysis"""
        attribution = setup['attribution']

        copy_metrics = attribution.analyze_copy_patterns()

        assert isinstance(copy_metrics, list)
        assert len(copy_metrics) > 0

        metric = copy_metrics[0]
        assert isinstance(metric, CopyMetrics)
        assert metric.count > 0

        print(f"\n✅ Copy Analysis:")
        for i, m in enumerate(copy_metrics[:3], 1):
            print(f"  {i}. {m.cta_type}: Conv={m.avg_conversion_rate:.3f}, "
                  f"Words={m.avg_word_count:.0f}")

    def test_correlate_features_to_roas(self, setup):
        """Test ROAS correlation analysis"""
        attribution = setup['attribution']

        correlations = attribution.correlate_features_to_roas()

        assert isinstance(correlations, list)
        assert len(correlations) > 0

        corr = correlations[0]
        assert isinstance(corr, FeatureCorrelation)
        assert -1 <= corr.correlation_with_roas <= 1
        assert 0 <= corr.p_value <= 1
        assert isinstance(corr.is_significant, bool)

        print(f"\n✅ Feature Correlations:")
        for i, c in enumerate(correlations[:5], 1):
            sig_marker = "***" if c.is_significant else ""
            print(f"  {i}. {c.feature_name}: r={c.correlation_with_roas:.3f}, "
                  f"p={c.p_value:.4f} {sig_marker}")

    def test_run_multivariate_analysis(self, setup):
        """Test multivariate regression analysis"""
        attribution = setup['attribution']

        result = attribution.run_multivariate_analysis(target_metric='roas')

        assert isinstance(result, dict)

        if 'error' not in result:
            assert 'r2_score' in result
            assert 'feature_importance' in result
            assert 'sample_size' in result
            assert result['sample_size'] > 0

            print(f"\n✅ Multivariate Analysis:")
            print(f"   R² Score: {result['r2_score']:.3f}")
            print(f"   Sample Size: {result['sample_size']}")
            print(f"   Top Features:")
            for i, (feat, imp) in enumerate(list(result['feature_importance'].items())[:3], 1):
                print(f"     {i}. {feat}: {imp:.3f}")

    def test_generate_recommendations(self, setup):
        """Test recommendation generation"""
        attribution = setup['attribution']

        recommendations = attribution.generate_recommendations('campaign_1')

        assert isinstance(recommendations, list)

        if len(recommendations) > 0:
            rec = recommendations[0]
            assert isinstance(rec, Recommendation)
            assert rec.category in ['hook', 'visual', 'copy', 'targeting', 'creative_element']
            assert 0 <= rec.confidence <= 1
            assert isinstance(rec.supporting_data, dict)

            print(f"\n✅ Recommendations:")
            for i, r in enumerate(recommendations, 1):
                print(f"  {i}. [{r.category.upper()}] {r.recommendation}")
                print(f"     Impact: {r.expected_impact} (Confidence: {r.confidence:.2f})")

    def test_get_improvement_opportunities(self, setup):
        """Test improvement opportunity identification"""
        attribution = setup['attribution']

        opportunities = attribution.get_improvement_opportunities(
            'campaign_1',
            min_confidence=0.5
        )

        assert isinstance(opportunities, list)

        # All should have confidence >= 0.5
        for opp in opportunities:
            assert opp.confidence >= 0.5

        print(f"\n✅ Found {len(opportunities)} high-confidence opportunities")

    def test_benchmark_against_account(self, setup):
        """Test account benchmarking"""
        attribution = setup['attribution']

        benchmark = attribution.benchmark_against_account('creative_0')

        assert isinstance(benchmark, dict)

        if 'error' not in benchmark:
            assert 'creative_metrics' in benchmark
            assert 'account_averages' in benchmark
            assert 'vs_account' in benchmark
            assert 'percentiles' in benchmark

            print(f"\n✅ Account Benchmark:")
            print(f"   Creative CTR: {benchmark['creative_metrics']['ctr']:.3f}")
            print(f"   Account Avg CTR: {benchmark['account_averages']['ctr']:.3f}")
            print(f"   Difference: {benchmark['vs_account']['ctr_diff']:.1f}%")
            print(f"   Percentile: {benchmark['percentiles']['ctr']:.0f}th")

    def test_benchmark_against_industry(self, setup):
        """Test industry benchmarking"""
        attribution = setup['attribution']

        benchmark = attribution.benchmark_against_industry('creative_0', 'ecommerce')

        assert isinstance(benchmark, dict)

        if 'error' not in benchmark:
            assert 'creative_metrics' in benchmark
            assert 'industry_benchmarks' in benchmark
            assert 'vs_industry' in benchmark

            print(f"\n✅ Industry Benchmark (E-commerce):")
            print(f"   Creative ROAS: {benchmark['creative_metrics']['roas']:.2f}")
            print(f"   Industry Avg: {benchmark['industry_benchmarks']['roas']:.2f}")
            print(f"   Difference: {benchmark['vs_industry']['roas_diff']:.1f}%")

    def test_update_knowledge_base(self, setup):
        """Test knowledge base updates"""
        attribution = setup['attribution']

        insights = [
            {
                'category': 'hook',
                'finding': 'Transformation hooks perform 40% better',
                'confidence': 0.85,
                'data': {'avg_roas': 3.5}
            }
        ]

        result = attribution.update_knowledge_base(insights)
        assert result is True

        # Verify stored
        assert len(setup['db'].insights_store) > 0

        print(f"\n✅ Knowledge Base Updated: {len(insights)} insights stored")

    def test_get_historical_insights(self, setup):
        """Test historical insight retrieval"""
        attribution = setup['attribution']

        # First store some insights
        insights = [
            {
                'category': 'hook',
                'finding': 'Test finding',
                'confidence': 0.9,
                'data': {}
            }
        ]
        attribution.update_knowledge_base(insights)

        # Retrieve
        historical = attribution.get_historical_insights('hook', limit=5)

        assert isinstance(historical, list)

        print(f"\n✅ Retrieved {len(historical)} historical insights")


def run_integration_test():
    """Run full integration test"""
    print("\n" + "="*70)
    print("CREATIVE ATTRIBUTION ANALYSIS - INTEGRATION TEST")
    print("="*70)

    # Setup
    db = MockDatabaseService()
    hook_classifier = MockHookClassifier()
    visual_analyzer = MockVisualAnalyzer()
    attribution = CreativeAttribution(db, hook_classifier, visual_analyzer)

    print(f"\n📊 Analyzing {len(db.campaign_data)} campaign records...")

    # 1. Hook Analysis
    print("\n1️⃣  HOOK PERFORMANCE ANALYSIS")
    print("-" * 70)
    hook_metrics = attribution.analyze_hook_performance()
    for i, metric in enumerate(hook_metrics[:3], 1):
        print(f"   {i}. {metric.hook_type:20s} | ROAS: {metric.avg_roas:5.2f}x | "
              f"CTR: {metric.avg_ctr:.3f} | Sig: {metric.statistical_significance:.2f}")

    # 2. Visual Analysis
    print("\n2️⃣  VISUAL PATTERN ANALYSIS")
    print("-" * 70)
    visual_metrics = attribution.analyze_visual_elements()
    for i, metric in enumerate(visual_metrics[:3], 1):
        print(f"   {i}. {metric.pattern_type:20s} | ROAS: {metric.avg_roas:5.2f}x | "
              f"Motion: {metric.motion_score:.2f}")

    # 3. Feature Correlations
    print("\n3️⃣  FEATURE CORRELATION ANALYSIS")
    print("-" * 70)
    correlations = attribution.correlate_features_to_roas()
    for i, corr in enumerate(correlations[:5], 1):
        sig = "***" if corr.is_significant else "   "
        print(f"   {i}. {corr.feature_name:20s} | r={corr.correlation_with_roas:+.3f} | "
              f"p={corr.p_value:.4f} {sig}")

    # 4. Multivariate Analysis
    print("\n4️⃣  MULTIVARIATE REGRESSION ANALYSIS")
    print("-" * 70)
    mv_result = attribution.run_multivariate_analysis('roas')
    if 'error' not in mv_result:
        print(f"   R² Score: {mv_result['r2_score']:.3f}")
        print(f"   Sample Size: {mv_result['sample_size']}")
        print(f"   Top 3 Features:")
        for i, (feat, imp) in enumerate(mv_result['top_3_features'], 1):
            print(f"      {i}. {feat[0]:20s} | Importance: {feat[1]:.3f}")

    # 5. Recommendations
    print("\n5️⃣  DATA-DRIVEN RECOMMENDATIONS")
    print("-" * 70)
    recommendations = attribution.generate_recommendations('campaign_1')
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. [{rec.category.upper():15s}] {rec.recommendation}")
        print(f"      Impact: {rec.expected_impact} | Confidence: {rec.confidence:.0%}")

    # 6. Benchmarking
    print("\n6️⃣  BENCHMARKING")
    print("-" * 70)
    benchmark = attribution.benchmark_against_account('creative_0')
    if 'error' not in benchmark:
        print(f"   Creative Performance vs Account Average:")
        print(f"      CTR:   {benchmark['vs_account']['ctr_diff']:+6.1f}%")
        print(f"      ROAS:  {benchmark['vs_account']['roas_diff']:+6.1f}%")
        print(f"      Percentile: {benchmark['percentiles']['roas']:.0f}th")

    print("\n" + "="*70)
    print("✅ INTEGRATION TEST COMPLETE - ALL REAL STATISTICAL ANALYSIS")
    print("="*70)


if __name__ == '__main__':
    # Run integration test
    run_integration_test()

    # Run pytest
    print("\n\nRunning pytest suite...")
    pytest.main([__file__, '-v'])
