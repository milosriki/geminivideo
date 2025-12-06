"""
Cross-Campaign Learning

Learn from ALL campaigns across ALL accounts.
This is how AI compounds knowledge.

Human approach: Each campaign starts from scratch
AI approach: Every new campaign benefits from all previous learnings
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class CampaignLearning:
    """Learning extracted from a campaign"""
    campaign_id: str
    account_id: str
    industry: str
    objective: str

    # What worked
    winning_patterns: List[Dict]
    winning_hooks: List[str]
    winning_ctas: List[str]
    best_audiences: List[Dict]
    best_times: List[Dict]

    # What didn't work
    failed_patterns: List[Dict]
    failed_hooks: List[str]
    failed_audiences: List[Dict]

    # Performance data
    best_roas: float
    best_ctr: float
    best_cpa: float
    total_spend: float
    total_conversions: int

    # Confidence
    confidence_score: float
    data_points: int

    # Metadata
    extracted_at: datetime
    campaign_duration_days: int

@dataclass
class IndustryInsight:
    """Aggregated insights for an industry"""
    industry: str
    sample_size: int

    # Performance benchmarks
    avg_roas: float
    avg_ctr: float
    avg_cpa: float

    # Winning patterns
    top_hook_types: List[Tuple[str, float]]  # (hook_type, avg_performance)
    top_cta_types: List[Tuple[str, float]]
    best_video_duration: Tuple[int, int]  # (min, max)
    best_posting_times: List[Dict]

    # Audience insights
    best_age_ranges: List[str]
    best_interests: List[str]

    # Confidence
    confidence: float
    last_updated: datetime

class CrossCampaignLearner:
    """
    Learn from all campaigns to improve predictions.

    Key insights:
    1. Industry-specific patterns
    2. Audience behavior patterns
    3. Creative element effectiveness
    4. Timing patterns
    5. Budget optimization patterns
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/tmp/cross_learning"
        self.learnings: Dict[str, CampaignLearning] = {}
        self.industry_insights: Dict[str, IndustryInsight] = {}
        self.pattern_database: Dict[str, List[Dict]] = defaultdict(list)

    def add_campaign_learning(self, learning: CampaignLearning):
        """Add learning from a campaign"""
        self.learnings[learning.campaign_id] = learning

        # Update industry insights
        self._update_industry_insights(learning)

        # Add patterns to database
        self._add_patterns(learning)

        logger.info(f"Added learning from campaign {learning.campaign_id}")

    def _update_industry_insights(self, learning: CampaignLearning):
        """Update industry-level insights"""
        industry = learning.industry

        if industry not in self.industry_insights:
            self.industry_insights[industry] = IndustryInsight(
                industry=industry,
                sample_size=0,
                avg_roas=0,
                avg_ctr=0,
                avg_cpa=0,
                top_hook_types=[],
                top_cta_types=[],
                best_video_duration=(15, 30),
                best_posting_times=[],
                best_age_ranges=[],
                best_interests=[],
                confidence=0,
                last_updated=datetime.now()
            )

        insight = self.industry_insights[industry]

        # Update averages (running average)
        n = insight.sample_size
        insight.avg_roas = (insight.avg_roas * n + learning.best_roas) / (n + 1)
        insight.avg_ctr = (insight.avg_ctr * n + learning.best_ctr) / (n + 1)
        insight.avg_cpa = (insight.avg_cpa * n + learning.best_cpa) / (n + 1)
        insight.sample_size += 1

        # Update confidence
        insight.confidence = min(1.0, insight.sample_size / 100)
        insight.last_updated = datetime.now()

    def _add_patterns(self, learning: CampaignLearning):
        """Add patterns to searchable database"""
        for pattern in learning.winning_patterns:
            pattern['source_campaign'] = learning.campaign_id
            pattern['industry'] = learning.industry
            pattern['performance'] = learning.best_roas
            self.pattern_database['winning'].append(pattern)

        for pattern in learning.failed_patterns:
            pattern['source_campaign'] = learning.campaign_id
            pattern['industry'] = learning.industry
            self.pattern_database['failed'].append(pattern)

    def get_recommendations_for_campaign(self, industry: str, objective: str,
                                          target_audience: Dict = None) -> Dict:
        """
        Get recommendations for a new campaign based on cross-learning.

        Args:
            industry: Target industry
            objective: Campaign objective
            target_audience: Optional audience targeting info

        Returns:
            Recommendations based on all learnings
        """
        # Get industry insights
        insight = self.industry_insights.get(industry)

        if not insight:
            # No data for this industry, use general learnings
            insight = self._get_general_insights()

        # Find similar campaigns
        similar_campaigns = self._find_similar_campaigns(industry, objective)

        # Extract winning patterns
        winning_hooks = self._aggregate_winning_hooks(similar_campaigns)
        winning_ctas = self._aggregate_winning_ctas(similar_campaigns)

        return {
            'industry_benchmarks': {
                'expected_roas': insight.avg_roas if insight else 2.0,
                'expected_ctr': insight.avg_ctr if insight else 0.02,
                'expected_cpa': insight.avg_cpa if insight else 50.0,
                'confidence': insight.confidence if insight else 0.1
            },
            'recommended_hooks': winning_hooks[:5],
            'recommended_ctas': winning_ctas[:5],
            'recommended_duration': insight.best_video_duration if insight else (15, 30),
            'recommended_posting_times': insight.best_posting_times if insight else [],
            'patterns_to_avoid': self._get_failed_patterns(industry)[:5],
            'similar_campaigns_analyzed': len(similar_campaigns),
            'total_learnings_used': len(self.learnings)
        }

    def _find_similar_campaigns(self, industry: str, objective: str) -> List[CampaignLearning]:
        """Find campaigns with similar characteristics"""
        similar = []

        for learning in self.learnings.values():
            score = 0
            if learning.industry == industry:
                score += 2
            if learning.objective == objective:
                score += 1
            if score > 0:
                similar.append((score, learning))

        # Sort by similarity score
        similar.sort(key=lambda x: x[0], reverse=True)

        return [l for _, l in similar[:50]]  # Top 50 most similar

    def _aggregate_winning_hooks(self, campaigns: List[CampaignLearning]) -> List[Dict]:
        """Aggregate winning hooks across campaigns"""
        hooks = defaultdict(lambda: {'count': 0, 'total_roas': 0})

        for campaign in campaigns:
            for hook in campaign.winning_hooks:
                hooks[hook]['count'] += 1
                hooks[hook]['total_roas'] += campaign.best_roas

        # Calculate average ROAS per hook
        result = []
        for hook, data in hooks.items():
            avg_roas = data['total_roas'] / data['count']
            result.append({
                'hook': hook,
                'avg_roas': avg_roas,
                'usage_count': data['count']
            })

        return sorted(result, key=lambda x: x['avg_roas'], reverse=True)

    def _aggregate_winning_ctas(self, campaigns: List[CampaignLearning]) -> List[Dict]:
        """Aggregate winning CTAs across campaigns"""
        ctas = defaultdict(lambda: {'count': 0, 'total_roas': 0})

        for campaign in campaigns:
            for cta in campaign.winning_ctas:
                ctas[cta]['count'] += 1
                ctas[cta]['total_roas'] += campaign.best_roas

        result = []
        for cta, data in ctas.items():
            avg_roas = data['total_roas'] / data['count']
            result.append({
                'cta': cta,
                'avg_roas': avg_roas,
                'usage_count': data['count']
            })

        return sorted(result, key=lambda x: x['avg_roas'], reverse=True)

    def _get_failed_patterns(self, industry: str) -> List[Dict]:
        """Get patterns that consistently fail"""
        failed = [p for p in self.pattern_database['failed'] if p.get('industry') == industry]
        return failed[:10]

    def _get_general_insights(self) -> IndustryInsight:
        """Get general insights across all industries"""
        if not self.learnings:
            return None

        all_roas = [l.best_roas for l in self.learnings.values()]
        all_ctr = [l.best_ctr for l in self.learnings.values()]
        all_cpa = [l.best_cpa for l in self.learnings.values()]

        return IndustryInsight(
            industry='general',
            sample_size=len(self.learnings),
            avg_roas=np.mean(all_roas),
            avg_ctr=np.mean(all_ctr),
            avg_cpa=np.mean(all_cpa),
            top_hook_types=[],
            top_cta_types=[],
            best_video_duration=(15, 30),
            best_posting_times=[],
            best_age_ranges=[],
            best_interests=[],
            confidence=min(1.0, len(self.learnings) / 100),
            last_updated=datetime.now()
        )

    def get_learning_stats(self) -> Dict:
        """Get statistics about accumulated learning"""
        total_campaigns = len(self.learnings)
        total_spend = sum(l.total_spend for l in self.learnings.values())
        total_conversions = sum(l.total_conversions for l in self.learnings.values())
        industries = set(l.industry for l in self.learnings.values())

        return {
            'total_campaigns_learned': total_campaigns,
            'total_spend_analyzed': total_spend,
            'total_conversions_analyzed': total_conversions,
            'industries_covered': list(industries),
            'winning_patterns_count': len(self.pattern_database['winning']),
            'failed_patterns_count': len(self.pattern_database['failed']),
            'industry_insights': {k: v.sample_size for k, v in self.industry_insights.items()}
        }

    def export_knowledge_base(self) -> Dict:
        """Export accumulated knowledge for backup/transfer"""
        return {
            'learnings': {k: self._learning_to_dict(v) for k, v in self.learnings.items()},
            'industry_insights': {k: self._insight_to_dict(v) for k, v in self.industry_insights.items()},
            'patterns': dict(self.pattern_database),
            'exported_at': datetime.now().isoformat()
        }

    def _learning_to_dict(self, learning: CampaignLearning) -> Dict:
        """Convert learning to dictionary"""
        return {
            'campaign_id': learning.campaign_id,
            'industry': learning.industry,
            'objective': learning.objective,
            'winning_patterns': learning.winning_patterns,
            'winning_hooks': learning.winning_hooks,
            'winning_ctas': learning.winning_ctas,
            'best_roas': learning.best_roas,
            'confidence_score': learning.confidence_score
        }

    def _insight_to_dict(self, insight: IndustryInsight) -> Dict:
        """Convert insight to dictionary"""
        return {
            'industry': insight.industry,
            'sample_size': insight.sample_size,
            'avg_roas': insight.avg_roas,
            'avg_ctr': insight.avg_ctr,
            'avg_cpa': insight.avg_cpa,
            'confidence': insight.confidence
        }
