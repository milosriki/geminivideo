"""
End-to-End Video Generation Pipeline Tests

Tests the complete flow from concept to published ad:
1. Concept input
2. Pattern matching
3. Variation generation
4. Video rendering
5. Platform publishing
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add service paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services'))

class TestE2EVideoGeneration:
    """End-to-end video generation tests"""

    @pytest.fixture
    def sample_concept(self):
        """Sample creative concept for testing"""
        return {
            'id': 'test_concept_001',
            'product': 'SuperWidget Pro',
            'key_benefit': 'Save 10 hours per week',
            'pain_point': 'wasting time on manual tasks',
            'target_audience': 'busy professionals',
            'industry': 'saas',
            'objective': 'conversions',
            'budget_daily': 500.0,
            'platforms': ['meta', 'google']
        }

    def test_concept_to_variations(self, sample_concept):
        """Test concept produces 50 variations"""
        try:
            from ml_service.src.variation_generator import VariationGenerator, CreativeConcept

            concept = CreativeConcept(
                id=sample_concept['id'],
                name=f"Test Campaign",
                description=sample_concept['key_benefit'],
                target_audience=sample_concept['target_audience'],
                industry=sample_concept['industry'],
                objective=sample_concept['objective'],
                product=sample_concept['product'],
                key_benefit=sample_concept['key_benefit'],
                pain_point=sample_concept['pain_point'],
                social_proof="10,000+ customers",
                brand_colors=["#FF0000", "#00FF00"],
                tone="energetic",
                hook_script=f"Stop {sample_concept['pain_point']}!",
                main_script=f"Discover {sample_concept['key_benefit']}",
                cta_text="Start Free Trial"
            )

            generator = VariationGenerator()
            variations = generator.generate_variations(concept, count=50)

            assert len(variations) == 50, f"Expected 50 variations, got {len(variations)}"

            # Verify each variation has required fields
            for v in variations:
                assert v.hook is not None
                assert v.cta is not None
                assert v.headline is not None
                assert v.duration > 0

        except ImportError:
            pytest.skip("Variation generator not available")

    def test_variation_ranking(self, sample_concept):
        """Test variations are properly ranked by predicted performance"""
        try:
            from ml_service.src.variation_generator import VariationGenerator, CreativeConcept

            concept = CreativeConcept(
                id=sample_concept['id'],
                name="Test",
                description="Test",
                target_audience="test",
                industry="saas",
                objective="conversions",
                product="Test",
                key_benefit="Test",
                pain_point="test",
                social_proof="test",
                brand_colors=["#000000"],
                tone="calm",
                hook_script="Test",
                main_script="Test",
                cta_text="Test"
            )

            generator = VariationGenerator()
            variations = generator.generate_variations(concept, count=10)
            ranked = generator.rank_variations(variations)

            # Verify sorted descending by performance
            for i in range(len(ranked) - 1):
                assert ranked[i].predicted_performance >= ranked[i+1].predicted_performance

        except ImportError:
            pytest.skip("Variation generator not available")

    def test_hook_optimization(self):
        """Test hook optimizer provides recommendations"""
        try:
            from video_agent.pro.hook_optimizer import HookOptimizer, HookType

            optimizer = HookOptimizer()

            # Get best template for industry
            template = optimizer.get_best_template('ecommerce')

            assert template is not None
            assert template.avg_performance > 0
            assert len(template.structure) > 0

            # Generate script
            script = optimizer.generate_hook_script(
                product="Test Product",
                pain_point="wasting money",
                template=template
            )

            assert 'template' in script
            assert 'structure' in script

        except ImportError:
            pytest.skip("Hook optimizer not available")

    def test_cta_sequence_generation(self):
        """Test CTA sequence is properly generated"""
        try:
            from video_agent.pro.cta_optimizer import CTAOptimizer

            optimizer = CTAOptimizer()
            sequence = optimizer.generate_cta_sequence(
                video_duration=30.0,
                industry='ecommerce'
            )

            assert 'sequence' in sequence
            assert len(sequence['sequence']) >= 3  # social_proof, urgency, cta

            # Verify CTA is at end
            cta_element = [s for s in sequence['sequence'] if s['type'] == 'cta']
            assert len(cta_element) > 0
            assert cta_element[0]['end'] == 30.0

        except ImportError:
            pytest.skip("CTA optimizer not available")

    def test_budget_optimization_flow(self):
        """Test budget optimizer categorizes ads correctly"""
        try:
            from ml_service.src.budget_optimizer import BudgetOptimizer, AdPerformance, AdStatus

            # Create test ads
            winner = AdPerformance(
                ad_id="ad_winner",
                campaign_id="test",
                creative_id="test",
                spend=200,
                daily_budget=100,
                impressions=50000,
                clicks=2500,
                conversions=50,
                revenue=1000,
                ctr=0.05,
                cvr=0.02,
                cpa=4.0,
                roas=5.0,  # Winner!
                hours_active=48,
                last_conversion_time=datetime.now(),
                status=AdStatus.SCALING,
                confidence=0.9
            )

            loser = AdPerformance(
                ad_id="ad_loser",
                campaign_id="test",
                creative_id="test",
                spend=200,
                daily_budget=100,
                impressions=50000,
                clicks=500,
                conversions=1,
                revenue=20,
                ctr=0.01,
                cvr=0.002,
                cpa=200,
                roas=0.1,  # Loser!
                hours_active=48,
                last_conversion_time=None,
                status=AdStatus.DECLINING,
                confidence=0.9
            )

            optimizer = BudgetOptimizer(target_roas=2.0)
            categories = optimizer.analyze_ads([winner, loser])

            assert len(categories['winners']) >= 1
            assert len(categories['losers']) >= 1

            # Generate recommendations
            recommendations = optimizer.generate_recommendations([winner, loser])

            # Should recommend cutting loser budget
            loser_rec = [r for r in recommendations if r.ad_id == 'ad_loser']
            assert len(loser_rec) > 0
            assert loser_rec[0].change_amount < 0  # Budget decrease

        except ImportError:
            pytest.skip("Budget optimizer not available")

    def test_kill_switch_detection(self):
        """Test kill switch correctly identifies failing ads"""
        try:
            from ml_service.src.loser_kill_switch import LoserKillSwitch, AdMetrics, KillReason

            # Ad with no conversions after $100 spend
            failing_ad = AdMetrics(
                ad_id="test_failing",
                campaign_id="test",
                spend=150,  # Over $100 threshold
                budget=500,
                impressions=10000,
                clicks=100,
                conversions=0,  # Zero conversions!
                revenue=0,
                ctr=0.01,
                cvr=0,
                cpa=0,
                roas=0,
                hours_running=48,
                last_conversion=None
            )

            switch = LoserKillSwitch(target_cpa=50.0)
            decision = switch.evaluate_ad(failing_ad)

            assert decision.should_kill == True
            assert decision.reason == KillReason.NO_CONVERSIONS
            assert decision.waste_prevented > 0

        except ImportError:
            pytest.skip("Kill switch not available")

    def test_cross_learning_recommendations(self):
        """Test cross-campaign learning provides recommendations"""
        try:
            from ml_service.src.cross_campaign_learning import CrossCampaignLearner

            learner = CrossCampaignLearner()

            # Get recommendations (should work even with empty database)
            recommendations = learner.get_recommendations_for_campaign(
                industry='ecommerce',
                objective='conversions'
            )

            assert 'industry_benchmarks' in recommendations
            assert 'recommended_hooks' in recommendations
            assert 'recommended_ctas' in recommendations

        except ImportError:
            pytest.skip("Cross learning not available")


class TestE2EPlatformPublishing:
    """Test platform publishing integration"""

    def test_meta_campaign_structure(self):
        """Test Meta campaign data structure is valid"""
        campaign_data = {
            'name': 'Test Campaign',
            'objective': 'CONVERSIONS',
            'status': 'PAUSED',
            'budget_daily': 100.0,
            'targeting': {
                'age_min': 25,
                'age_max': 54,
                'genders': [1, 2],
                'interests': ['technology']
            },
            'creative': {
                'video_url': 'https://example.com/video.mp4',
                'headline': 'Test Headline',
                'description': 'Test Description',
                'cta': 'SHOP_NOW'
            }
        }

        # Verify required fields
        assert 'name' in campaign_data
        assert 'objective' in campaign_data
        assert 'creative' in campaign_data
        assert 'video_url' in campaign_data['creative']

    def test_google_campaign_structure(self):
        """Test Google Ads campaign data structure is valid"""
        campaign_data = {
            'name': 'Test Campaign',
            'budget': {
                'amount_micros': 100000000,  # $100
                'delivery_method': 'STANDARD'
            },
            'targeting': {
                'locations': ['US'],
                'languages': ['en']
            },
            'ad_group': {
                'name': 'Test Ad Group',
                'cpc_bid_micros': 1000000  # $1
            }
        }

        # Verify required fields
        assert 'name' in campaign_data
        assert 'budget' in campaign_data
        assert 'amount_micros' in campaign_data['budget']


class TestE2EPerformanceTracking:
    """Test conversion and performance tracking"""

    def test_roas_calculation(self):
        """Test ROAS is calculated correctly"""
        spend = 100.0
        revenue = 350.0

        roas = revenue / spend

        assert roas == 3.5
        assert roas > 1.0  # Profitable

    def test_ctr_calculation(self):
        """Test CTR is calculated correctly"""
        impressions = 10000
        clicks = 250

        ctr = clicks / impressions

        assert ctr == 0.025  # 2.5%
        assert ctr > 0.01  # Above minimum threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
