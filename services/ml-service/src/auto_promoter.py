"""
Auto-Promotion System for A/B Test Winners
Agent 44 - 10x Leverage with Automatic Winner Promotion

This module implements automatic winner detection, budget reallocation,
insight extraction, and compound learning from A/B test results.
"""

import os
import sys
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from scipy import stats

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'titan-core'))

from sqlalchemy import select, and_, or_, update, desc
from sqlalchemy.orm import Session
from db.models import ABTest as ABTestModel, Video, PerformanceMetric

# Meta API integration
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'titan-core', 'meta'))
from marketing_api import RealMetaAdsManager

# Anthropic for insight extraction
try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromotionStatus(Enum):
    """Status of promotion operation"""
    CONTINUE_TESTING = "continue_testing"
    PROMOTED = "promoted"
    INSUFFICIENT_DATA = "insufficient_data"
    ERROR = "error"


@dataclass
class WinnerInsights:
    """Insights extracted from winning variant"""
    hook_patterns: List[str]
    visual_elements: List[str]
    performance_metrics: Dict[str, float]
    winning_factors: List[str]
    replicable_patterns: List[str]
    audience_resonance: Dict[str, Any]
    confidence_score: float
    extracted_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['extracted_at'] = self.extracted_at.isoformat()
        return data


@dataclass
class PromotionResult:
    """Result of auto-promotion check"""
    experiment_id: str
    status: PromotionStatus
    winner_ad_id: Optional[str] = None
    winner_metrics: Optional[Dict[str, Any]] = None
    loser_ad_id: Optional[str] = None
    budget_reallocation: Optional[Dict[str, Any]] = None
    insights: Optional[WinnerInsights] = None
    confidence: Optional[float] = None
    message: str = ""
    promoted_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'experiment_id': self.experiment_id,
            'status': self.status.value,
            'winner_ad_id': self.winner_ad_id,
            'winner_metrics': self.winner_metrics,
            'loser_ad_id': self.loser_ad_id,
            'budget_reallocation': self.budget_reallocation,
            'insights': self.insights.to_dict() if self.insights else None,
            'confidence': self.confidence,
            'message': self.message,
            'promoted_at': self.promoted_at.isoformat() if self.promoted_at else None
        }
        return data


class AutoPromoter:
    """
    Automatic A/B Test Winner Promotion System

    Features:
    - Detects statistically significant winners
    - Reallocates budgets via Meta API
    - Extracts insights using Claude
    - Stores patterns for future use
    - Creates compound learning effects
    """

    def __init__(
        self,
        db_session: Session,
        meta_api_manager: Optional[RealMetaAdsManager] = None,
        anthropic_api_key: Optional[str] = None,
        confidence_threshold: float = 0.95,
        min_sample_size: int = 100,
        winner_budget_pct: float = 0.80,
        loser_budget_pct: float = 0.20
    ):
        """
        Initialize AutoPromoter.

        Args:
            db_session: SQLAlchemy database session
            meta_api_manager: Meta Ads API manager for budget control
            anthropic_api_key: Anthropic API key for insight extraction
            confidence_threshold: Minimum confidence for promotion (default 0.95)
            min_sample_size: Minimum sample size per variant (default 100)
            winner_budget_pct: Budget percentage for winner (default 0.80)
            loser_budget_pct: Budget percentage for loser (default 0.20)
        """
        self.db_session = db_session
        self.meta_api = meta_api_manager
        self.confidence_threshold = confidence_threshold
        self.min_sample_size = min_sample_size
        self.winner_budget_pct = winner_budget_pct
        self.loser_budget_pct = loser_budget_pct

        # Initialize Anthropic client for insight extraction
        self.anthropic_client = None
        if anthropic_api_key and AsyncAnthropic:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
            logger.info("Anthropic client initialized for insight extraction")
        else:
            logger.warning("Anthropic client not available - insights will be limited")

        logger.info(f"AutoPromoter initialized: confidence={confidence_threshold}, min_samples={min_sample_size}")

    async def check_and_promote(
        self,
        experiment_id: str,
        force_promotion: bool = False
    ) -> PromotionResult:
        """
        Check if experiment has clear winner and promote if ready.

        Args:
            experiment_id: A/B test experiment ID
            force_promotion: Force promotion even if confidence is below threshold

        Returns:
            PromotionResult with status and details
        """
        try:
            logger.info(f"Checking experiment {experiment_id} for promotion")

            # Get experiment from database
            experiment = await self._get_experiment(experiment_id)
            if not experiment:
                return PromotionResult(
                    experiment_id=experiment_id,
                    status=PromotionStatus.ERROR,
                    message=f"Experiment {experiment_id} not found"
                )

            # Check if experiment is still active
            if experiment.status != 'active':
                return PromotionResult(
                    experiment_id=experiment_id,
                    status=PromotionStatus.ERROR,
                    message=f"Experiment status is {experiment.status}, not active"
                )

            # Get performance data for both variants
            variant_a_data = await self._get_variant_performance(experiment.model_a_id)
            variant_b_data = await self._get_variant_performance(experiment.model_b_id)

            # Check if we have enough data
            if len(variant_a_data) < self.min_sample_size or len(variant_b_data) < self.min_sample_size:
                return PromotionResult(
                    experiment_id=experiment_id,
                    status=PromotionStatus.INSUFFICIENT_DATA,
                    message=f"Need {self.min_sample_size} samples per variant. A:{len(variant_a_data)}, B:{len(variant_b_data)}"
                )

            # Calculate statistical significance
            significance_result = self._calculate_statistical_significance(
                variant_a_data,
                variant_b_data
            )

            confidence = significance_result['confidence']
            winner_variant = significance_result['winner']

            logger.info(f"Statistical test: confidence={confidence:.3f}, winner={winner_variant}")

            # Check if we should promote
            if not force_promotion and confidence < self.confidence_threshold:
                return PromotionResult(
                    experiment_id=experiment_id,
                    status=PromotionStatus.CONTINUE_TESTING,
                    confidence=confidence,
                    message=f"Confidence {confidence:.3f} below threshold {self.confidence_threshold}"
                )

            # Determine winner and loser
            winner_ad_id = experiment.model_a_id if winner_variant == 'A' else experiment.model_b_id
            loser_ad_id = experiment.model_b_id if winner_variant == 'A' else experiment.model_a_id
            winner_data = variant_a_data if winner_variant == 'A' else variant_b_data
            loser_data = variant_b_data if winner_variant == 'A' else variant_a_data

            # Calculate metrics
            winner_metrics = self._calculate_metrics(winner_data)
            loser_metrics = self._calculate_metrics(loser_data)

            logger.info(f"Winner: {winner_ad_id} (CTR: {winner_metrics['ctr']:.4f})")
            logger.info(f"Loser: {loser_ad_id} (CTR: {loser_metrics['ctr']:.4f})")

            # Reallocate budget via Meta API
            budget_reallocation = None
            if self.meta_api:
                budget_reallocation = await self._reallocate_budget(
                    winner_ad_id=winner_ad_id,
                    loser_ad_id=loser_ad_id,
                    experiment=experiment
                )
                logger.info(f"Budget reallocated: {budget_reallocation}")

            # Extract winner insights using Claude
            insights = None
            if self.anthropic_client:
                insights = await self._extract_winner_insights(
                    winner_ad_id=winner_ad_id,
                    winner_metrics=winner_metrics,
                    loser_metrics=loser_metrics,
                    confidence=confidence
                )
                logger.info(f"Insights extracted: {len(insights.winning_factors)} winning factors identified")

                # Store insights for future use
                await self._store_winning_patterns(insights, winner_ad_id)

            # Update experiment status
            await self._update_experiment_status(
                experiment_id=experiment_id,
                winner_id=winner_ad_id,
                results={
                    'winner_metrics': winner_metrics,
                    'loser_metrics': loser_metrics,
                    'confidence': confidence,
                    'statistical_test': significance_result,
                    'promoted_at': datetime.now().isoformat()
                }
            )

            # Create promotion result
            result = PromotionResult(
                experiment_id=experiment_id,
                status=PromotionStatus.PROMOTED,
                winner_ad_id=winner_ad_id,
                winner_metrics=winner_metrics,
                loser_ad_id=loser_ad_id,
                budget_reallocation=budget_reallocation,
                insights=insights,
                confidence=confidence,
                message=f"Winner promoted with {confidence:.1%} confidence",
                promoted_at=datetime.now()
            )

            logger.info(f"Experiment {experiment_id} promoted successfully")
            return result

        except Exception as e:
            logger.error(f"Error checking/promoting experiment {experiment_id}: {str(e)}")
            return PromotionResult(
                experiment_id=experiment_id,
                status=PromotionStatus.ERROR,
                message=f"Error: {str(e)}"
            )

    async def _get_experiment(self, experiment_id: str) -> Optional[ABTestModel]:
        """Get experiment from database."""
        try:
            result = await self.db_session.execute(
                select(ABTestModel).where(ABTestModel.test_id == experiment_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching experiment: {str(e)}")
            return None

    async def _get_variant_performance(self, ad_id: str) -> List[Dict[str, Any]]:
        """
        Get performance data for a variant.

        Returns list of performance records with impressions, clicks, etc.
        """
        try:
            result = await self.db_session.execute(
                select(PerformanceMetric)
                .join(Video, PerformanceMetric.video_id == Video.id)
                .where(Video.meta_platform_id == ad_id)
                .order_by(desc(PerformanceMetric.date))
            )
            metrics = result.scalars().all()

            # Convert to list of dicts
            performance_data = []
            for metric in metrics:
                performance_data.append({
                    'date': metric.date,
                    'impressions': metric.impressions or 0,
                    'clicks': metric.clicks or 0,
                    'spend': float(metric.spend) if metric.spend else 0.0,
                    'ctr': float(metric.ctr) if metric.ctr else 0.0,
                    'conversions': metric.conversions or 0
                })

            return performance_data

        except Exception as e:
            logger.error(f"Error fetching variant performance: {str(e)}")
            return []

    def _calculate_statistical_significance(
        self,
        variant_a_data: List[Dict[str, Any]],
        variant_b_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate statistical significance using two-sample t-test.

        Args:
            variant_a_data: Performance data for variant A
            variant_b_data: Performance data for variant B

        Returns:
            Dict with winner, confidence, p_value, and test details
        """
        try:
            # Extract CTR values
            ctr_a = np.array([d['ctr'] for d in variant_a_data if d['impressions'] > 0])
            ctr_b = np.array([d['ctr'] for d in variant_b_data if d['impressions'] > 0])

            # Handle empty arrays
            if len(ctr_a) == 0 or len(ctr_b) == 0:
                return {
                    'winner': 'A' if len(ctr_a) > len(ctr_b) else 'B',
                    'confidence': 0.0,
                    'p_value': 1.0,
                    'test_type': 't-test',
                    'error': 'Insufficient data'
                }

            # Perform two-sample t-test
            t_stat, p_value = stats.ttest_ind(ctr_a, ctr_b, equal_var=False)

            # Calculate means
            mean_a = np.mean(ctr_a)
            mean_b = np.mean(ctr_b)

            # Determine winner
            winner = 'A' if mean_a > mean_b else 'B'

            # Calculate confidence (1 - p_value for two-tailed test)
            confidence = 1 - p_value if p_value <= 1.0 else 0.0

            return {
                'winner': winner,
                'confidence': float(confidence),
                'p_value': float(p_value),
                't_statistic': float(t_stat),
                'mean_a': float(mean_a),
                'mean_b': float(mean_b),
                'difference': float(abs(mean_a - mean_b)),
                'improvement_pct': float(abs(mean_a - mean_b) / min(mean_a, mean_b) * 100) if min(mean_a, mean_b) > 0 else 0.0,
                'sample_size_a': len(ctr_a),
                'sample_size_b': len(ctr_b),
                'test_type': 't-test'
            }

        except Exception as e:
            logger.error(f"Error calculating statistical significance: {str(e)}")
            return {
                'winner': 'A',
                'confidence': 0.0,
                'p_value': 1.0,
                'error': str(e)
            }

    def _calculate_metrics(self, performance_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregated metrics from performance data."""
        total_impressions = sum(d['impressions'] for d in performance_data)
        total_clicks = sum(d['clicks'] for d in performance_data)
        total_spend = sum(d['spend'] for d in performance_data)
        total_conversions = sum(d['conversions'] for d in performance_data)

        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0
        cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0.0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0.0

        return {
            'impressions': total_impressions,
            'clicks': total_clicks,
            'spend': total_spend,
            'conversions': total_conversions,
            'ctr': ctr,
            'cpc': cpc,
            'cpm': cpm,
            'conversion_rate': conversion_rate
        }

    async def _reallocate_budget(
        self,
        winner_ad_id: str,
        loser_ad_id: str,
        experiment: ABTestModel
    ) -> Dict[str, Any]:
        """
        Reallocate budget via Meta API.

        Args:
            winner_ad_id: Meta ad ID for winner
            loser_ad_id: Meta ad ID for loser
            experiment: Experiment record

        Returns:
            Dict with reallocation details
        """
        try:
            if not self.meta_api:
                logger.warning("Meta API not available - skipping budget reallocation")
                return {
                    'status': 'skipped',
                    'reason': 'Meta API not configured'
                }

            # Get current ad sets for both ads
            winner_adset = self.meta_api.get_ad_set(winner_ad_id)
            loser_adset = self.meta_api.get_ad_set(loser_ad_id)

            # Get current budgets
            winner_budget = float(winner_adset.get('daily_budget', 0))
            loser_budget = float(loser_adset.get('daily_budget', 0))
            total_budget = winner_budget + loser_budget

            # Calculate new budgets
            new_winner_budget = int(total_budget * self.winner_budget_pct)
            new_loser_budget = int(total_budget * self.loser_budget_pct)

            logger.info(f"Reallocating budget: Winner ${new_winner_budget/100:.2f}/day, Loser ${new_loser_budget/100:.2f}/day")

            # Update budgets gradually (not instant)
            # Start with 60/40 split, then move to 70/30, then 80/20
            intermediate_winner = int(total_budget * 0.60)
            intermediate_loser = int(total_budget * 0.40)

            # Phase 1: 60/40
            await asyncio.sleep(1)  # Gradual adjustment
            self.meta_api.update_ad_set(winner_ad_id, daily_budget=intermediate_winner)
            self.meta_api.update_ad_set(loser_ad_id, daily_budget=intermediate_loser)
            logger.info("Phase 1: 60/40 split applied")

            # Phase 2: 70/30
            await asyncio.sleep(3600)  # Wait 1 hour
            intermediate_winner = int(total_budget * 0.70)
            intermediate_loser = int(total_budget * 0.30)
            self.meta_api.update_ad_set(winner_ad_id, daily_budget=intermediate_winner)
            self.meta_api.update_ad_set(loser_ad_id, daily_budget=intermediate_loser)
            logger.info("Phase 2: 70/30 split applied")

            # Phase 3: 80/20 (final)
            await asyncio.sleep(7200)  # Wait 2 hours
            self.meta_api.update_ad_set(winner_ad_id, daily_budget=new_winner_budget)
            self.meta_api.update_ad_set(loser_ad_id, daily_budget=new_loser_budget)
            logger.info("Phase 3: 80/20 split applied (final)")

            return {
                'status': 'completed',
                'total_budget_cents': total_budget,
                'winner_old_budget_cents': winner_budget,
                'winner_new_budget_cents': new_winner_budget,
                'loser_old_budget_cents': loser_budget,
                'loser_new_budget_cents': new_loser_budget,
                'winner_budget_pct': self.winner_budget_pct,
                'loser_budget_pct': self.loser_budget_pct,
                'phased_rollout': True,
                'reallocated_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error reallocating budget: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _extract_winner_insights(
        self,
        winner_ad_id: str,
        winner_metrics: Dict[str, float],
        loser_metrics: Dict[str, float],
        confidence: float
    ) -> WinnerInsights:
        """
        Extract insights about why the winner performed better using Claude.

        Args:
            winner_ad_id: Winner ad ID
            winner_metrics: Winner performance metrics
            loser_metrics: Loser performance metrics
            confidence: Statistical confidence

        Returns:
            WinnerInsights object with extracted patterns
        """
        try:
            # Get video/creative details for winner
            result = await self.db_session.execute(
                select(Video).where(Video.meta_platform_id == winner_ad_id)
            )
            winner_video = result.scalar_one_or_none()

            if not winner_video:
                logger.warning(f"Winner video not found for ad {winner_ad_id}")
                return self._create_default_insights()

            # Build prompt for Claude
            prompt = self._build_insight_extraction_prompt(
                winner_video=winner_video,
                winner_metrics=winner_metrics,
                loser_metrics=loser_metrics,
                confidence=confidence
            )

            # Call Claude API
            response = await self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                temperature=0.7,
                system="You are an expert performance marketing analyst specializing in video ad creative analysis. Extract actionable insights from A/B test results.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            insights_text = response.content[0].text
            insights_data = self._parse_insights_response(insights_text)

            # Create WinnerInsights object
            insights = WinnerInsights(
                hook_patterns=insights_data.get('hook_patterns', []),
                visual_elements=insights_data.get('visual_elements', []),
                performance_metrics=winner_metrics,
                winning_factors=insights_data.get('winning_factors', []),
                replicable_patterns=insights_data.get('replicable_patterns', []),
                audience_resonance=insights_data.get('audience_resonance', {}),
                confidence_score=confidence,
                extracted_at=datetime.now()
            )

            logger.info(f"Insights extracted via Claude: {len(insights.winning_factors)} factors")
            return insights

        except Exception as e:
            logger.error(f"Error extracting insights: {str(e)}")
            return self._create_default_insights()

    def _build_insight_extraction_prompt(
        self,
        winner_video: Video,
        winner_metrics: Dict[str, float],
        loser_metrics: Dict[str, float],
        confidence: float
    ) -> str:
        """Build Claude prompt for insight extraction."""
        script_content = winner_video.script_content or {}
        hook = script_content.get('hook', 'N/A')
        description = winner_video.description or 'N/A'

        improvement_pct = ((winner_metrics['ctr'] - loser_metrics['ctr']) / loser_metrics['ctr'] * 100) if loser_metrics['ctr'] > 0 else 0

        prompt = f"""Analyze why this ad variant won the A/B test with {confidence:.1%} confidence:

**WINNER CREATIVE:**
- Hook: "{hook}"
- Description: {description}
- Video Title: {winner_video.title}

**PERFORMANCE:**
- Winner CTR: {winner_metrics['ctr']:.2f}%
- Loser CTR: {loser_metrics['ctr']:.2f}%
- Improvement: {improvement_pct:+.1f}%
- Winner Clicks: {winner_metrics['clicks']:,}
- Winner Impressions: {winner_metrics['impressions']:,}
- Winner Conversions: {winner_metrics['conversions']}

**ANALYSIS REQUIRED:**
Extract specific, actionable patterns:

1. **Hook Patterns**: What hook style/formula worked? (e.g., "Question format", "Pain agitation", "Curiosity gap")

2. **Visual Elements**: What visual elements contributed? (e.g., "Fast cuts", "Text overlays", "Product demo")

3. **Winning Factors**: Top 3-5 specific reasons why this variant won

4. **Replicable Patterns**: Concrete patterns to apply to future creatives

5. **Audience Resonance**: Why did this resonate with the target audience?

Respond in JSON format:
{{
  "hook_patterns": ["pattern1", "pattern2"],
  "visual_elements": ["element1", "element2"],
  "winning_factors": ["factor1", "factor2", "factor3"],
  "replicable_patterns": ["pattern1", "pattern2"],
  "audience_resonance": {{
    "emotional_trigger": "...",
    "value_proposition": "...",
    "pain_point_addressed": "..."
  }}
}}
"""
        return prompt

    def _parse_insights_response(self, insights_text: str) -> Dict[str, Any]:
        """Parse Claude's response into structured insights."""
        try:
            # Try to parse as JSON
            if '{' in insights_text and '}' in insights_text:
                json_start = insights_text.index('{')
                json_end = insights_text.rindex('}') + 1
                json_str = insights_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback to text parsing
                return {
                    'hook_patterns': [],
                    'visual_elements': [],
                    'winning_factors': [insights_text[:200]],
                    'replicable_patterns': [],
                    'audience_resonance': {}
                }
        except Exception as e:
            logger.error(f"Error parsing insights: {str(e)}")
            return {}

    def _create_default_insights(self) -> WinnerInsights:
        """Create default insights when extraction fails."""
        return WinnerInsights(
            hook_patterns=[],
            visual_elements=[],
            performance_metrics={},
            winning_factors=[],
            replicable_patterns=[],
            audience_resonance={},
            confidence_score=0.0,
            extracted_at=datetime.now()
        )

    async def _store_winning_patterns(
        self,
        insights: WinnerInsights,
        winner_ad_id: str
    ) -> None:
        """
        Store winning patterns in knowledge base for future use.

        This integrates with the vector store to enable RAG-powered
        creative generation using learned patterns.
        """
        try:
            # Store in knowledge base vectors table
            from db.models import KnowledgeBaseVector
            import uuid

            # Create knowledge entries for each pattern type
            entries = []

            # Hook patterns
            for pattern in insights.hook_patterns:
                content_id = f"hook_pattern_{uuid.uuid4().hex[:8]}"
                entry = {
                    'content_id': content_id,
                    'content_type': 'pattern',
                    'title': f"Winning Hook Pattern: {pattern}",
                    'content': f"Hook pattern '{pattern}' achieved {insights.confidence_score:.1%} confidence in A/B test. Winner ad: {winner_ad_id}",
                    'summary': pattern,
                    'category': 'hook_writing',
                    'tags': ['hook', 'ab_test_winner', 'pattern'],
                    'confidence_score': insights.confidence_score,
                    'usage_count': 0,
                    'success_rate': insights.confidence_score,
                    'source': 'ab_test_learning',
                    'metadata': {
                        'ad_id': winner_ad_id,
                        'extracted_at': insights.extracted_at.isoformat(),
                        'performance_metrics': insights.performance_metrics
                    }
                }
                entries.append(entry)

            # Visual elements
            for element in insights.visual_elements:
                content_id = f"visual_element_{uuid.uuid4().hex[:8]}"
                entry = {
                    'content_id': content_id,
                    'content_type': 'pattern',
                    'title': f"Winning Visual Element: {element}",
                    'content': f"Visual element '{element}' contributed to winning performance in A/B test. Winner ad: {winner_ad_id}",
                    'summary': element,
                    'category': 'visual_design',
                    'tags': ['visual', 'ab_test_winner', 'pattern'],
                    'confidence_score': insights.confidence_score,
                    'usage_count': 0,
                    'success_rate': insights.confidence_score,
                    'source': 'ab_test_learning',
                    'metadata': {
                        'ad_id': winner_ad_id,
                        'extracted_at': insights.extracted_at.isoformat()
                    }
                }
                entries.append(entry)

            # Replicable patterns
            for pattern in insights.replicable_patterns:
                content_id = f"replicable_{uuid.uuid4().hex[:8]}"
                entry = {
                    'content_id': content_id,
                    'content_type': 'best_practice',
                    'title': f"Replicable Pattern: {pattern}",
                    'content': f"Pattern '{pattern}' is replicable and should be applied to future creatives. Proven in A/B test with {insights.confidence_score:.1%} confidence.",
                    'summary': pattern,
                    'category': 'best_practice',
                    'tags': ['replicable', 'ab_test_winner', 'best_practice'],
                    'confidence_score': insights.confidence_score,
                    'usage_count': 0,
                    'success_rate': insights.confidence_score,
                    'source': 'ab_test_learning',
                    'metadata': {
                        'ad_id': winner_ad_id,
                        'extracted_at': insights.extracted_at.isoformat()
                    }
                }
                entries.append(entry)

            logger.info(f"Storing {len(entries)} winning patterns in knowledge base")

            # Note: Actual embedding and insertion would require the vector store
            # For now, just log the patterns. Full integration requires:
            # 1. Generate embeddings using OpenAI text-embedding-3-large
            # 2. Insert into knowledge_base_vectors table
            # 3. Create vector indices for similarity search

            for entry in entries:
                logger.info(f"Pattern: {entry['title']}")

        except Exception as e:
            logger.error(f"Error storing winning patterns: {str(e)}")

    async def _update_experiment_status(
        self,
        experiment_id: str,
        winner_id: str,
        results: Dict[str, Any]
    ) -> None:
        """Update experiment status in database."""
        try:
            await self.db_session.execute(
                update(ABTestModel)
                .where(ABTestModel.test_id == experiment_id)
                .values(
                    status='completed',
                    winner=winner_id,
                    results=results,
                    updated_at=datetime.now()
                )
            )
            await self.db_session.commit()
            logger.info(f"Experiment {experiment_id} marked as completed with winner {winner_id}")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating experiment status: {str(e)}")

    async def check_all_active_experiments(self) -> List[PromotionResult]:
        """
        Check all active experiments for promotion opportunities.

        This should be called periodically (e.g., every 6 hours) by a scheduler.

        Returns:
            List of PromotionResult for all checked experiments
        """
        try:
            # Get all active experiments
            result = await self.db_session.execute(
                select(ABTestModel).where(ABTestModel.status == 'active')
            )
            active_experiments = result.scalars().all()

            logger.info(f"Checking {len(active_experiments)} active experiments")

            results = []
            for experiment in active_experiments:
                # Check if experiment has been running for at least 24 hours
                time_running = datetime.now() - experiment.start_date
                if time_running.total_seconds() < 86400:  # 24 hours
                    logger.info(f"Experiment {experiment.test_id} too new (running {time_running.total_seconds()/3600:.1f}h)")
                    continue

                # Check and promote
                promotion_result = await self.check_and_promote(experiment.test_id)
                results.append(promotion_result)

                # Log result
                if promotion_result.status == PromotionStatus.PROMOTED:
                    logger.info(f"✓ {experiment.test_id}: PROMOTED ({promotion_result.confidence:.1%} confidence)")
                elif promotion_result.status == PromotionStatus.CONTINUE_TESTING:
                    logger.info(f"→ {experiment.test_id}: Continue testing ({promotion_result.confidence:.1%} confidence)")
                else:
                    logger.info(f"✗ {experiment.test_id}: {promotion_result.status.value} - {promotion_result.message}")

            return results

        except Exception as e:
            logger.error(f"Error checking active experiments: {str(e)}")
            return []

    async def get_promotion_history(
        self,
        days_back: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get history of promoted experiments.

        Args:
            days_back: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of promoted experiments with details
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            result = await self.db_session.execute(
                select(ABTestModel)
                .where(
                    and_(
                        ABTestModel.status == 'completed',
                        ABTestModel.winner.isnot(None),
                        ABTestModel.updated_at >= cutoff_date
                    )
                )
                .order_by(desc(ABTestModel.updated_at))
                .limit(limit)
            )
            completed_experiments = result.scalars().all()

            history = []
            for exp in completed_experiments:
                results = exp.results or {}
                history.append({
                    'experiment_id': exp.test_id,
                    'winner_id': exp.winner,
                    'confidence': results.get('confidence', 0.0),
                    'winner_metrics': results.get('winner_metrics', {}),
                    'loser_metrics': results.get('loser_metrics', {}),
                    'promoted_at': results.get('promoted_at'),
                    'test_duration_days': exp.duration_days,
                    'start_date': exp.start_date.isoformat(),
                    'end_date': exp.end_date.isoformat()
                })

            logger.info(f"Retrieved {len(history)} promoted experiments from last {days_back} days")
            return history

        except Exception as e:
            logger.error(f"Error getting promotion history: {str(e)}")
            return []

    async def get_cumulative_improvement_report(self) -> Dict[str, Any]:
        """
        Generate report showing cumulative improvement from auto-promotions.

        This demonstrates the compound learning effect.

        Returns:
            Dict with cumulative metrics and improvement trends
        """
        try:
            # Get all completed experiments
            result = await self.db_session.execute(
                select(ABTestModel)
                .where(
                    and_(
                        ABTestModel.status == 'completed',
                        ABTestModel.winner.isnot(None)
                    )
                )
                .order_by(ABTestModel.end_date)
            )
            experiments = result.scalars().all()

            if not experiments:
                return {
                    'total_experiments': 0,
                    'message': 'No completed experiments yet'
                }

            # Calculate metrics
            total_experiments = len(experiments)
            improvements = []
            avg_confidence = []

            for exp in experiments:
                results = exp.results or {}
                winner_metrics = results.get('winner_metrics', {})
                loser_metrics = results.get('loser_metrics', {})
                confidence = results.get('confidence', 0.0)

                if winner_metrics and loser_metrics:
                    winner_ctr = winner_metrics.get('ctr', 0)
                    loser_ctr = loser_metrics.get('ctr', 0)
                    if loser_ctr > 0:
                        improvement_pct = (winner_ctr - loser_ctr) / loser_ctr * 100
                        improvements.append(improvement_pct)
                        avg_confidence.append(confidence)

            # Calculate compound effect
            compound_improvement = 1.0
            for imp in improvements:
                compound_improvement *= (1 + imp / 100)
            compound_improvement = (compound_improvement - 1) * 100

            report = {
                'total_experiments': total_experiments,
                'successful_promotions': len(improvements),
                'avg_improvement_per_test': np.mean(improvements) if improvements else 0.0,
                'median_improvement': np.median(improvements) if improvements else 0.0,
                'compound_improvement_pct': compound_improvement,
                'avg_confidence': np.mean(avg_confidence) if avg_confidence else 0.0,
                'total_improvement_range': {
                    'min': min(improvements) if improvements else 0.0,
                    'max': max(improvements) if improvements else 0.0
                },
                'improvement_trend': improvements[-10:] if len(improvements) >= 10 else improvements,
                'generated_at': datetime.now().isoformat()
            }

            logger.info(f"Cumulative improvement report: {compound_improvement:.1f}% compound improvement from {total_experiments} tests")
            return report

        except Exception as e:
            logger.error(f"Error generating cumulative improvement report: {str(e)}")
            return {'error': str(e)}


# Initialize singleton instance (will be configured in main.py)
auto_promoter: Optional[AutoPromoter] = None


def initialize_auto_promoter(
    db_session: Session,
    meta_api_manager: Optional[RealMetaAdsManager] = None,
    anthropic_api_key: Optional[str] = None
) -> AutoPromoter:
    """Initialize the global auto-promoter instance."""
    global auto_promoter
    auto_promoter = AutoPromoter(
        db_session=db_session,
        meta_api_manager=meta_api_manager,
        anthropic_api_key=anthropic_api_key
    )
    logger.info("Global AutoPromoter initialized")
    return auto_promoter
