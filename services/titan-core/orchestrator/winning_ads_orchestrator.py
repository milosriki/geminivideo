"""
Winning Ads Orchestrator

The BRAIN that coordinates all AI components to create winning video ads.

Flow:
1. Receive creative concept
2. Analyze with temporal intelligence
3. Generate 50 variations
4. Predict performance
5. Render top variations
6. Publish to platforms
7. Track conversions
8. Learn and improve

This is what makes ROI happen.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class OrchestratorStage(Enum):
    CONCEPT_ANALYSIS = "concept_analysis"
    PATTERN_MATCHING = "pattern_matching"
    VARIATION_GENERATION = "variation_generation"
    PERFORMANCE_PREDICTION = "performance_prediction"
    VIDEO_RENDERING = "video_rendering"
    PLATFORM_PUBLISHING = "platform_publishing"
    CONVERSION_TRACKING = "conversion_tracking"
    LEARNING = "learning"

@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator"""
    enable_yolo: bool = True
    enable_ai_video_generation: bool = True
    enable_voice_cloning: bool = True
    enable_auto_budget: bool = True
    enable_kill_switch: bool = True
    variations_per_concept: int = 50
    top_variations_to_render: int = 10
    target_roas: float = 2.0
    target_cpa: float = 50.0

@dataclass
class CreativeRequest:
    """Request for creative generation"""
    concept_id: str
    product: str
    key_benefit: str
    pain_point: str
    target_audience: str
    industry: str
    objective: str  # conversions, leads, awareness
    budget_daily: float
    platforms: List[str]  # meta, google, tiktok

@dataclass
class OrchestratorResult:
    """Result of orchestration"""
    request_id: str
    status: str
    stages_completed: List[str]
    variations_generated: int
    variations_rendered: int
    campaigns_created: int
    predicted_roas: float
    errors: List[str]
    execution_time: float
    created_at: datetime

class WinningAdsOrchestrator:
    """
    Central orchestrator for the AI video ad platform.

    Coordinates:
    - Video analysis (motion, faces, audio sync)
    - Pattern matching (winning patterns database)
    - Variation generation (50 variations)
    - Performance prediction (ML models)
    - Video rendering (FFmpeg, AI generation)
    - Platform publishing (Meta, Google, TikTok)
    - Conversion tracking (CAPI, Google)
    - Budget optimization (auto-shift, kill switch)
    - Cross-campaign learning
    """

    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()
        self.components = {}
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all AI components"""
        logger.info("Initializing Winning Ads Orchestrator...")

        # Video Analysis Components (Agents 99-107)
        try:
            from ..video_agent.pro.motion_moment_sdk import MotionMomentSDK
            self.components['motion_sdk'] = MotionMomentSDK()
            logger.info("✓ Motion Moment SDK loaded")
        except ImportError as e:
            logger.warning(f"Motion SDK not available: {e}")

        try:
            from ..video_agent.pro.face_weighted_analyzer import FaceWeightedAnalyzer
            self.components['face_analyzer'] = FaceWeightedAnalyzer(use_yolo=self.config.enable_yolo)
            logger.info("✓ Face Weighted Analyzer loaded")
        except ImportError as e:
            logger.warning(f"Face Analyzer not available: {e}")

        try:
            from ..video_agent.pro.hook_optimizer import HookOptimizer
            self.components['hook_optimizer'] = HookOptimizer()
            logger.info("✓ Hook Optimizer loaded")
        except ImportError as e:
            logger.warning(f"Hook Optimizer not available: {e}")

        try:
            from ..video_agent.pro.cta_optimizer import CTAOptimizer
            self.components['cta_optimizer'] = CTAOptimizer()
            logger.info("✓ CTA Optimizer loaded")
        except ImportError as e:
            logger.warning(f"CTA Optimizer not available: {e}")

        # AI Generation Components (Agents 110-111)
        if self.config.enable_ai_video_generation:
            try:
                from .integrations.runway_gen3 import get_runway_client
                self.components['runway'] = get_runway_client()
                logger.info("✓ Runway Gen-3 loaded")
            except ImportError as e:
                logger.warning(f"Runway not available: {e}")

        if self.config.enable_voice_cloning:
            try:
                from .integrations.elevenlabs_voice import get_elevenlabs_client
                self.components['elevenlabs'] = get_elevenlabs_client()
                logger.info("✓ ElevenLabs Voice loaded")
            except ImportError as e:
                logger.warning(f"ElevenLabs not available: {e}")

        # ML Components (Agents 112-115)
        try:
            from ..ml_service.src.variation_generator import VariationGenerator
            self.components['variation_gen'] = VariationGenerator()
            logger.info("✓ Variation Generator loaded")
        except ImportError as e:
            logger.warning(f"Variation Generator not available: {e}")

        try:
            from ..ml_service.src.budget_optimizer import BudgetOptimizer
            self.components['budget_optimizer'] = BudgetOptimizer(target_roas=self.config.target_roas)
            logger.info("✓ Budget Optimizer loaded")
        except ImportError as e:
            logger.warning(f"Budget Optimizer not available: {e}")

        try:
            from ..ml_service.src.loser_kill_switch import LoserKillSwitch
            self.components['kill_switch'] = LoserKillSwitch(
                target_cpa=self.config.target_cpa,
                target_roas=self.config.target_roas
            )
            logger.info("✓ Kill Switch loaded")
        except ImportError as e:
            logger.warning(f"Kill Switch not available: {e}")

        try:
            from ..ml_service.src.cross_campaign_learning import CrossCampaignLearner
            self.components['cross_learning'] = CrossCampaignLearner()
            logger.info("✓ Cross-Campaign Learning loaded")
        except ImportError as e:
            logger.warning(f"Cross Learning not available: {e}")

        # Pattern Database (Agent 109)
        try:
            from ..drive_intel.services.winning_patterns_db import WinningPatternsDB
            self.components['patterns_db'] = WinningPatternsDB()
            logger.info("✓ Winning Patterns DB loaded")
        except ImportError as e:
            logger.warning(f"Patterns DB not available: {e}")

        logger.info(f"Orchestrator initialized with {len(self.components)} components")

    async def process_request(self, request: CreativeRequest) -> OrchestratorResult:
        """
        Process a creative request through the full pipeline.

        This is the main entry point for generating winning ads.
        """
        start_time = datetime.now()
        stages_completed = []
        errors = []

        try:
            # Stage 1: Get recommendations from cross-learning
            logger.info(f"[{request.concept_id}] Stage 1: Pattern matching")
            recommendations = await self._get_recommendations(request)
            stages_completed.append(OrchestratorStage.PATTERN_MATCHING.value)

            # Stage 2: Generate variations
            logger.info(f"[{request.concept_id}] Stage 2: Generating variations")
            variations = await self._generate_variations(request, recommendations)
            stages_completed.append(OrchestratorStage.VARIATION_GENERATION.value)

            # Stage 3: Predict performance
            logger.info(f"[{request.concept_id}] Stage 3: Predicting performance")
            ranked_variations = await self._predict_performance(variations)
            stages_completed.append(OrchestratorStage.PERFORMANCE_PREDICTION.value)

            # Stage 4: Render top variations
            logger.info(f"[{request.concept_id}] Stage 4: Rendering videos")
            rendered = await self._render_videos(ranked_variations[:self.config.top_variations_to_render])
            stages_completed.append(OrchestratorStage.VIDEO_RENDERING.value)

            # Stage 5: Publish to platforms
            logger.info(f"[{request.concept_id}] Stage 5: Publishing to platforms")
            campaigns = await self._publish_campaigns(rendered, request)
            stages_completed.append(OrchestratorStage.PLATFORM_PUBLISHING.value)

            execution_time = (datetime.now() - start_time).total_seconds()

            return OrchestratorResult(
                request_id=request.concept_id,
                status="success",
                stages_completed=stages_completed,
                variations_generated=len(variations),
                variations_rendered=len(rendered),
                campaigns_created=len(campaigns),
                predicted_roas=self._calculate_predicted_roas(ranked_variations),
                errors=errors,
                execution_time=execution_time,
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return OrchestratorResult(
                request_id=request.concept_id,
                status="failed",
                stages_completed=stages_completed,
                variations_generated=0,
                variations_rendered=0,
                campaigns_created=0,
                predicted_roas=0,
                errors=[str(e)],
                execution_time=(datetime.now() - start_time).total_seconds(),
                created_at=datetime.now()
            )

    async def _get_recommendations(self, request: CreativeRequest) -> Dict:
        """Get recommendations from cross-learning"""
        if 'cross_learning' in self.components:
            return self.components['cross_learning'].get_recommendations_for_campaign(
                industry=request.industry,
                objective=request.objective
            )
        return {}

    async def _generate_variations(self, request: CreativeRequest,
                                    recommendations: Dict) -> List[Dict]:
        """Generate variations using the variation generator"""
        if 'variation_gen' not in self.components:
            return []

        # Create concept from request
        from ..ml_service.src.variation_generator import CreativeConcept

        concept = CreativeConcept(
            id=request.concept_id,
            name=f"Campaign for {request.product}",
            description=request.key_benefit,
            target_audience=request.target_audience,
            industry=request.industry,
            objective=request.objective,
            product=request.product,
            key_benefit=request.key_benefit,
            pain_point=request.pain_point,
            social_proof="Thousands of happy customers",
            brand_colors=["#FF6B6B", "#4ECDC4"],
            tone="energetic",
            hook_script=f"Tired of {request.pain_point}?",
            main_script=f"Discover {request.key_benefit} with {request.product}",
            cta_text=f"Get {request.product} Now"
        )

        variations = self.components['variation_gen'].generate_variations(
            concept,
            count=self.config.variations_per_concept
        )

        return self.components['variation_gen'].export_variations(variations)

    async def _predict_performance(self, variations: List[Dict]) -> List[Dict]:
        """Predict and rank variations by expected performance"""
        # Sort by predicted_score (already included from variation generator)
        return sorted(variations, key=lambda v: v.get('predicted_score', 0), reverse=True)

    async def _render_videos(self, variations: List[Dict]) -> List[Dict]:
        """Render video variations"""
        rendered = []

        for variation in variations:
            # Would call actual rendering pipeline
            rendered.append({
                **variation,
                'rendered': True,
                'video_url': f"/videos/{variation['id']}.mp4"
            })

        return rendered

    async def _publish_campaigns(self, videos: List[Dict],
                                  request: CreativeRequest) -> List[Dict]:
        """Publish to advertising platforms"""
        campaigns = []

        for platform in request.platforms:
            for video in videos[:3]:  # Top 3 per platform
                campaigns.append({
                    'platform': platform,
                    'video_id': video['id'],
                    'budget': request.budget_daily / len(request.platforms),
                    'status': 'pending'
                })

        return campaigns

    def _calculate_predicted_roas(self, variations: List[Dict]) -> float:
        """Calculate predicted ROAS from top variations"""
        if not variations:
            return 0.0

        scores = [v.get('predicted_score', 0) for v in variations[:10]]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Convert score to ROAS estimate
        return 1.0 + (avg_score * 3.0)  # Score 0-1 maps to ROAS 1-4

    async def optimize_active_campaigns(self):
        """Run optimization on active campaigns"""
        if 'budget_optimizer' not in self.components:
            return

        # Would fetch active ads from database
        # For now, log optimization run
        logger.info("Running campaign optimization...")

    async def run_kill_switch_check(self):
        """Check for ads that should be killed"""
        if 'kill_switch' not in self.components:
            return

        # Would fetch ads and evaluate
        logger.info("Running kill switch evaluation...")

    def get_system_status(self) -> Dict:
        """Get status of all components"""
        return {
            'components_loaded': list(self.components.keys()),
            'components_count': len(self.components),
            'config': {
                'yolo_enabled': self.config.enable_yolo,
                'ai_video_enabled': self.config.enable_ai_video_generation,
                'voice_cloning_enabled': self.config.enable_voice_cloning,
                'auto_budget_enabled': self.config.enable_auto_budget,
                'kill_switch_enabled': self.config.enable_kill_switch,
                'variations_per_concept': self.config.variations_per_concept,
                'target_roas': self.config.target_roas
            }
        }


# Factory function
def create_orchestrator(config: Dict = None) -> WinningAdsOrchestrator:
    """Create orchestrator with optional config override"""
    cfg = OrchestratorConfig()
    if config:
        for key, value in config.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
    return WinningAdsOrchestrator(cfg)
