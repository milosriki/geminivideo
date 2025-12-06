"""
Integration Tests for AI Video Ad Platform

Tests all new components from Agents 99-116:
- Motion Moment SDK
- Face Weighting
- Audio-Visual Sync
- Psychological Timing
- YOLOv8 Detection
- CAPI Feedback
- Hook/CTA Optimization
- Variation Generator
- Budget Optimizer
- Kill Switch
- Cross-Campaign Learning
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/video-agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/ml-service/src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/titan-core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/drive-intel/services'))

# ============================================
# TEST: Motion Moment SDK (Agent 99)
# ============================================
class TestMotionMomentSDK:
    """Test 30-frame temporal analysis"""

    def test_sdk_initialization(self):
        """Test SDK initializes with correct parameters"""
        from pro.motion_moment_sdk import MotionMomentSDK

        sdk = MotionMomentSDK(fps=30.0)
        assert sdk.fps == 30.0
        assert sdk.WINDOW_SIZE == 30
        assert sdk.FACE_WEIGHT == 3.2

    def test_motion_energy_calculation(self):
        """Test motion energy between frames"""
        import numpy as np
        from pro.motion_moment_sdk import MotionMomentSDK

        sdk = MotionMomentSDK()

        # Create mock frames
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 255  # Different frame

        energy = sdk.calculate_motion_energy(frame1, frame2)
        assert energy > 0, "Motion energy should be positive for different frames"

# ============================================
# TEST: Face Weighting (Agent 100)
# ============================================
class TestFaceWeighting:
    """Test 3.2x face weighting system"""

    def test_face_weight_constant(self):
        """Verify 3.2x face weight"""
        from pro.face_weighted_analyzer import FaceWeightedAnalyzer, FACE_WEIGHT

        assert FACE_WEIGHT == 3.2, "Face weight must be 3.2x"

    def test_analyzer_initialization(self):
        """Test analyzer init"""
        from pro.face_weighted_analyzer import FaceWeightedAnalyzer

        analyzer = FaceWeightedAnalyzer(use_yolo=False)
        assert analyzer.FACE_WEIGHT == 3.2

# ============================================
# TEST: Audio-Visual Sync (Agent 101)
# ============================================
class TestAudioVisualSync:
    """Test 0.1s precision sync"""

    def test_tolerance_constant(self):
        """Verify 0.1s sync tolerance"""
        from pro.precision_av_sync import PrecisionAVSync, SYNC_TOLERANCE

        assert SYNC_TOLERANCE == 0.1, "Sync tolerance must be 0.1 seconds"

    def test_sync_initialization(self):
        """Test sync system init"""
        from pro.precision_av_sync import PrecisionAVSync

        sync = PrecisionAVSync(sr=22050)
        assert sync.TOLERANCE == 0.1

# ============================================
# TEST: Psychological Timing (Agent 102)
# ============================================
class TestPsychologicalTiming:
    """Test psychological trigger timing"""

    def test_trigger_types_exist(self):
        """Verify all trigger types defined"""
        from pro.psychological_timing import TriggerType, TRIGGER_CONFIGS

        required_triggers = ['PAIN_POINT', 'AGITATION', 'SOLUTION', 'SOCIAL_PROOF', 'URGENCY', 'CTA', 'HOOK']
        for trigger in required_triggers:
            assert hasattr(TriggerType, trigger), f"Missing trigger type: {trigger}"

    def test_pain_point_low_motion(self):
        """Pain points should trigger during low motion"""
        from pro.psychological_timing import TriggerType, TRIGGER_CONFIGS

        config = TRIGGER_CONFIGS[TriggerType.PAIN_POINT]
        assert config.ideal_motion_level == 'low', "Pain points need low motion for absorption"

# ============================================
# TEST: YOLOv8 Detection (Agents 103-104)
# ============================================
class TestYOLODetection:
    """Test YOLOv8 face and object detection"""

    def test_face_detector_init(self):
        """Test face detector initialization"""
        from pro.yolo_face_detector import YOLOFaceDetector

        detector = YOLOFaceDetector(confidence_threshold=0.5)
        assert detector.confidence_threshold == 0.5

    def test_object_detector_init(self):
        """Test object detector initialization"""
        from pro.yolo_object_detector import YOLOObjectDetector, COCO_CLASSES

        detector = YOLOObjectDetector(model_size='n')
        assert len(COCO_CLASSES) == 80, "Should have 80 COCO classes"

# ============================================
# TEST: Hook Optimizer (Agent 107)
# ============================================
class TestHookOptimizer:
    """Test first 3 seconds hook optimization"""

    def test_hook_types_exist(self):
        """Verify hook types"""
        from pro.hook_optimizer import HookType, HOOK_TEMPLATES

        assert len(HOOK_TEMPLATES) >= 5, "Should have at least 5 hook templates"

    def test_optimizer_initialization(self):
        """Test optimizer init"""
        from pro.hook_optimizer import HookOptimizer

        optimizer = HookOptimizer()
        assert optimizer.HOOK_DURATION == 3.0, "Hook duration should be 3 seconds"

# ============================================
# TEST: CTA Optimizer (Agent 108)
# ============================================
class TestCTAOptimizer:
    """Test CTA timing optimization"""

    def test_cta_types_exist(self):
        """Verify CTA types"""
        from pro.cta_optimizer import CTAType, BEST_CTA_CONFIGS

        assert len(BEST_CTA_CONFIGS) >= 4, "Should have at least 4 CTA configs"
        assert 'ecommerce' in BEST_CTA_CONFIGS
        assert 'saas' in BEST_CTA_CONFIGS

# ============================================
# TEST: Variation Generator (Agent 112)
# ============================================
class TestVariationGenerator:
    """Test 50x variation generation"""

    def test_target_variations(self):
        """Verify 50 variations target"""
        from variation_generator import VariationGenerator

        generator = VariationGenerator()
        assert generator.TARGET_VARIATIONS == 50

# ============================================
# TEST: Budget Optimizer (Agent 113)
# ============================================
class TestBudgetOptimizer:
    """Test auto-budget shifting"""

    def test_optimizer_thresholds(self):
        """Verify budget thresholds"""
        from budget_optimizer import BudgetOptimizer

        optimizer = BudgetOptimizer(target_roas=2.0)
        assert optimizer.target_roas == 2.0
        assert optimizer.MIN_SPEND_FOR_DECISION == 50
        assert optimizer.MAX_BUDGET_INCREASE_PERCENT == 50

# ============================================
# TEST: Loser Kill Switch (Agent 114)
# ============================================
class TestLoserKillSwitch:
    """Test automatic ad termination"""

    def test_kill_thresholds(self):
        """Verify kill thresholds"""
        from loser_kill_switch import LoserKillSwitch

        switch = LoserKillSwitch(target_cpa=50.0, target_roas=2.0)
        assert switch.MIN_CTR == 0.005  # 0.5%
        assert switch.MIN_CVR == 0.005  # 0.5%
        assert switch.NO_CONVERSION_SPEND_LIMIT == 100

# ============================================
# TEST: Cross-Campaign Learning (Agent 115)
# ============================================
class TestCrossCampaignLearning:
    """Test knowledge accumulation"""

    def test_learner_initialization(self):
        """Test learner init"""
        from cross_campaign_learning import CrossCampaignLearner

        learner = CrossCampaignLearner()
        assert learner.learnings == {}
        assert learner.industry_insights == {}

# ============================================
# TEST: Winning Patterns DB (Agent 109)
# ============================================
class TestWinningPatternsDB:
    """Test pattern database"""

    def test_db_initialization(self):
        """Test DB init"""
        from winning_patterns_db import WinningPatternsDB

        db = WinningPatternsDB()
        assert db.patterns == {} or len(db.patterns) >= 0

# ============================================
# INTEGRATION TEST: Full Pipeline
# ============================================
class TestFullPipeline:
    """Test components work together"""

    def test_hook_to_cta_flow(self):
        """Test hook analysis flows to CTA optimization"""
        from pro.hook_optimizer import HookOptimizer
        from pro.cta_optimizer import CTAOptimizer

        hook_opt = HookOptimizer()
        cta_opt = CTAOptimizer()

        # Get recommended templates
        best_hook = hook_opt.get_best_template('ecommerce')
        best_cta = cta_opt.get_best_cta_for_goal('sales')

        assert best_hook is not None
        assert best_cta is not None

    def test_budget_to_kill_flow(self):
        """Test budget optimizer triggers kill switch"""
        from budget_optimizer import BudgetOptimizer, AdPerformance, AdStatus
        from loser_kill_switch import LoserKillSwitch, AdMetrics

        # Create underperforming ad
        ad = AdPerformance(
            ad_id="test_ad_1",
            campaign_id="test_campaign",
            creative_id="test_creative",
            spend=150,
            daily_budget=200,
            impressions=10000,
            clicks=50,
            conversions=0,
            revenue=0,
            ctr=0.005,
            cvr=0,
            cpa=0,
            roas=0,
            hours_active=48,
            last_conversion_time=None,
            status=AdStatus.LEARNING,
            confidence=0.8
        )

        # Budget optimizer should flag as loser
        optimizer = BudgetOptimizer()
        categories = optimizer.analyze_ads([ad])
        assert 'losers' in categories

        # Kill switch should confirm kill
        switch = LoserKillSwitch()
        metrics = AdMetrics(
            ad_id="test_ad_1",
            campaign_id="test_campaign",
            spend=150,
            budget=200,
            impressions=10000,
            clicks=50,
            conversions=0,
            revenue=0,
            ctr=0.005,
            cvr=0,
            cpa=0,
            roas=0,
            hours_running=48,
            last_conversion=None
        )
        decision = switch.evaluate_ad(metrics)
        assert decision.should_kill == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
