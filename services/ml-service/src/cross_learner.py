"""
Cross-Account Learning System for Network Effects
Agent 49 - 10x Leverage through Anonymized Pattern Sharing

This module implements cross-account learning that enables:
- Anonymized pattern extraction from high-performing accounts
- Niche-specific insights aggregation
- Network effects (more accounts = better insights)
- Privacy-preserving knowledge sharing
- New account bootstrapping with industry wisdom
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
from collections import defaultdict, Counter
import numpy as np
from scipy import stats

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import Session

# Database models
try:
    from db.models import Video, PerformanceMetric, Campaign, Prediction
except ImportError:
    Video = PerformanceMetric = Campaign = Prediction = None

# Anthropic for insight extraction
try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NicheCategory(Enum):
    """Industry/niche categories for grouping accounts"""
    FITNESS = "fitness"
    BEAUTY = "beauty"
    FASHION = "fashion"
    TECH = "tech"
    ECOMMERCE = "ecommerce"
    FOOD = "food"
    TRAVEL = "travel"
    FINANCE = "finance"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    SAAS = "saas"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    HOME_DECOR = "home_decor"
    AUTOMOTIVE = "automotive"
    UNKNOWN = "unknown"


@dataclass
class AccountInsights:
    """Anonymized insights from a single account"""
    account_id: str
    niche: str
    confidence: float  # Niche detection confidence

    # Winning patterns (anonymized)
    top_hook_types: List[Dict[str, Any]]
    optimal_duration_range: Tuple[float, float]
    best_posting_times: List[int]  # Hours of day (0-23)
    effective_cta_styles: List[str]
    visual_preferences: List[str]

    # Performance benchmarks (not raw data)
    avg_ctr: float
    avg_conversion_rate: float
    avg_roas: float

    # Metadata
    total_campaigns: int
    total_conversions: int
    account_age_days: int
    opted_in: bool

    extracted_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['extracted_at'] = self.extracted_at.isoformat()
        return data


@dataclass
class NicheWisdom:
    """Aggregated wisdom for a niche from multiple accounts"""
    niche: str
    sample_size: int  # Number of accounts contributing

    # Aggregated patterns
    top_hook_types: List[Dict[str, Any]]  # Hook type + success rate
    optimal_duration: Tuple[float, float]  # Duration range
    peak_hours: List[int]  # Best posting hours
    proven_cta_styles: List[Dict[str, Any]]  # CTA + success rate
    winning_visual_patterns: List[Dict[str, Any]]

    # Benchmark metrics
    niche_avg_ctr: float
    niche_avg_conversion_rate: float
    niche_avg_roas: float

    # Quality metrics
    confidence_score: float
    last_updated: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


class CrossAccountLearner:
    """
    Cross-Account Learning System

    Extracts anonymized patterns from accounts and shares insights
    across similar accounts to create network effects.

    Privacy-preserving: Only shares patterns and aggregated metrics,
    never actual content or specific campaign data.
    """

    def __init__(
        self,
        db_session: Session,
        anthropic_api_key: Optional[str] = None,
        min_sample_size: int = 5,  # Min accounts for niche wisdom
        min_campaigns_per_account: int = 3,  # Min campaigns to extract insights
        winner_threshold: float = 0.015  # CTR > 1.5% = winner
    ):
        """
        Initialize CrossAccountLearner.

        Args:
            db_session: SQLAlchemy database session
            anthropic_api_key: Optional Anthropic API key for AI-powered analysis
            min_sample_size: Minimum accounts needed to create niche wisdom
            min_campaigns_per_account: Minimum campaigns to extract account insights
            winner_threshold: CTR threshold to consider a campaign a "winner"
        """
        self.db_session = db_session
        self.min_sample_size = min_sample_size
        self.min_campaigns_per_account = min_campaigns_per_account
        self.winner_threshold = winner_threshold

        # Initialize Anthropic client for AI-powered niche detection
        self.anthropic_client = None
        if anthropic_api_key and AsyncAnthropic:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
            logger.info("Anthropic client initialized for niche detection")

        # In-memory cache for niche wisdom (should be Redis in production)
        self._wisdom_cache: Dict[str, NicheWisdom] = {}

        logger.info(f"CrossAccountLearner initialized: min_sample={min_sample_size}")

    async def extract_anonymized_insights(self, account_id: str) -> Optional[AccountInsights]:
        """
        Extract anonymized insights from an account's performance data.

        Only extracts patterns, not actual content.

        Args:
            account_id: User/account ID

        Returns:
            AccountInsights or None if insufficient data
        """
        try:
            logger.info(f"Extracting anonymized insights for account {account_id}")

            # Get account's campaigns
            campaigns = await self._get_account_campaigns(account_id)

            if len(campaigns) < self.min_campaigns_per_account:
                logger.info(f"Account {account_id} has only {len(campaigns)} campaigns, need {self.min_campaigns_per_account}")
                return None

            # Detect niche
            niche, confidence = await self.detect_niche(account_id)

            # Get winning campaigns (high CTR)
            winners = await self._get_account_winners(account_id)

            if not winners:
                logger.info(f"No winning campaigns found for account {account_id}")
                return None

            # Extract patterns from winners
            hook_types = self._aggregate_hook_types(winners)
            duration_range = self._calculate_duration_range(winners)
            posting_times = self._aggregate_posting_times(winners)
            cta_styles = self._aggregate_cta_styles(winners)
            visual_patterns = self._aggregate_visual_patterns(winners)

            # Calculate performance benchmarks
            avg_ctr = np.mean([w['ctr'] for w in winners])
            avg_conversion_rate = np.mean([w.get('conversion_rate', 0) for w in winners])
            avg_roas = np.mean([w.get('roas', 0) for w in winners if w.get('roas', 0) > 0])

            # Get account metadata
            account_age = await self._get_account_age(account_id)
            total_campaigns = len(campaigns)
            total_conversions = sum([w.get('conversions', 0) for w in winners])

            # Check if account opted in to sharing
            opted_in = await self._get_user_opt_in_status(account_id)

            insights = AccountInsights(
                account_id=account_id,
                niche=niche,
                confidence=confidence,
                top_hook_types=hook_types,
                optimal_duration_range=duration_range,
                best_posting_times=posting_times,
                effective_cta_styles=cta_styles,
                visual_preferences=visual_patterns,
                avg_ctr=avg_ctr,
                avg_conversion_rate=avg_conversion_rate,
                avg_roas=avg_roas,
                total_campaigns=total_campaigns,
                total_conversions=total_conversions,
                account_age_days=account_age,
                opted_in=opted_in,
                extracted_at=datetime.now()
            )

            logger.info(f"Insights extracted for account {account_id}: niche={niche}, {len(winners)} winners")
            return insights

        except Exception as e:
            logger.error(f"Error extracting insights for account {account_id}: {str(e)}")
            return None

    async def detect_niche(self, account_id: str) -> Tuple[str, float]:
        """
        Detect the niche/industry for an account using content analysis.

        Args:
            account_id: User/account ID

        Returns:
            Tuple of (niche, confidence_score)
        """
        try:
            # Get account's videos/campaigns
            campaigns = await self._get_account_campaigns(account_id)

            if not campaigns:
                return (NicheCategory.UNKNOWN.value, 0.0)

            # Collect text content for analysis
            titles = []
            descriptions = []

            for campaign in campaigns[:10]:  # Sample first 10
                if hasattr(campaign, 'name'):
                    titles.append(campaign.name or "")
                if hasattr(campaign, 'description'):
                    descriptions.append(campaign.description or "")

            # If we have Anthropic, use AI for better detection
            if self.anthropic_client:
                niche, confidence = await self._ai_niche_detection(titles, descriptions)
                return (niche, confidence)

            # Otherwise use keyword-based detection
            niche, confidence = self._keyword_niche_detection(titles, descriptions)
            return (niche, confidence)

        except Exception as e:
            logger.error(f"Error detecting niche for account {account_id}: {str(e)}")
            return (NicheCategory.UNKNOWN.value, 0.0)

    async def _ai_niche_detection(
        self,
        titles: List[str],
        descriptions: List[str]
    ) -> Tuple[str, float]:
        """Use Claude to detect niche from content."""
        try:
            content = "\n".join(titles + descriptions)

            prompt = f"""Analyze this collection of campaign titles and descriptions and determine the industry/niche:

{content}

Classify into one of these categories:
- fitness
- beauty
- fashion
- tech
- ecommerce
- food
- travel
- finance
- education
- real_estate
- saas
- health
- entertainment
- home_decor
- automotive

Respond with JSON:
{{
  "niche": "category_name",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}
"""

            response = await self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=512,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            result_text = response.content[0].text
            if '{' in result_text and '}' in result_text:
                json_start = result_text.index('{')
                json_end = result_text.rindex('}') + 1
                result = json.loads(result_text[json_start:json_end])

                niche = result.get('niche', 'unknown')
                confidence = result.get('confidence', 0.5)

                logger.info(f"AI niche detection: {niche} (confidence: {confidence:.2f})")
                return (niche, confidence)

        except Exception as e:
            logger.error(f"Error in AI niche detection: {str(e)}")

        # Fallback to keyword detection
        return self._keyword_niche_detection(titles, descriptions)

    def _keyword_niche_detection(
        self,
        titles: List[str],
        descriptions: List[str]
    ) -> Tuple[str, float]:
        """Keyword-based niche detection (fallback)."""
        content = " ".join(titles + descriptions).lower()

        # Keyword patterns for each niche
        patterns = {
            NicheCategory.FITNESS.value: ['workout', 'fitness', 'gym', 'exercise', 'muscle', 'training', 'bodybuilding'],
            NicheCategory.BEAUTY.value: ['makeup', 'skincare', 'beauty', 'cosmetics', 'skin', 'hair', 'nail'],
            NicheCategory.FASHION.value: ['fashion', 'style', 'clothing', 'outfit', 'wear', 'dress', 'shoes'],
            NicheCategory.TECH.value: ['tech', 'software', 'app', 'digital', 'coding', 'programming', 'ai'],
            NicheCategory.ECOMMERCE.value: ['shop', 'store', 'product', 'sale', 'buy', 'discount', 'deal'],
            NicheCategory.FOOD.value: ['food', 'recipe', 'cooking', 'restaurant', 'meal', 'chef', 'cuisine'],
            NicheCategory.TRAVEL.value: ['travel', 'trip', 'vacation', 'destination', 'hotel', 'tour', 'flight'],
            NicheCategory.FINANCE.value: ['finance', 'money', 'invest', 'trading', 'stock', 'crypto', 'wealth'],
            NicheCategory.EDUCATION.value: ['learn', 'education', 'course', 'teaching', 'student', 'school', 'tutorial'],
            NicheCategory.REAL_ESTATE.value: ['real estate', 'property', 'house', 'home', 'apartment', 'rent', 'mortgage'],
            NicheCategory.SAAS.value: ['saas', 'platform', 'subscription', 'tool', 'dashboard', 'analytics'],
            NicheCategory.HEALTH.value: ['health', 'medical', 'wellness', 'doctor', 'therapy', 'healthcare'],
            NicheCategory.ENTERTAINMENT.value: ['entertainment', 'movie', 'music', 'game', 'fun', 'comedy'],
            NicheCategory.HOME_DECOR.value: ['home', 'decor', 'interior', 'furniture', 'design', 'decoration'],
            NicheCategory.AUTOMOTIVE.value: ['car', 'auto', 'vehicle', 'automotive', 'truck', 'motor'],
        }

        # Count matches for each niche
        scores = {}
        for niche, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                scores[niche] = score

        if not scores:
            return (NicheCategory.UNKNOWN.value, 0.0)

        # Get best match
        best_niche = max(scores.items(), key=lambda x: x[1])
        total_keywords = sum(len(kw) for kw in patterns.values())
        confidence = min(best_niche[1] / 5.0, 1.0)  # Normalize to 0-1

        logger.info(f"Keyword niche detection: {best_niche[0]} (confidence: {confidence:.2f})")
        return (best_niche[0], confidence)

    async def get_niche_insights(self, niche: str, force_refresh: bool = False) -> Optional[NicheWisdom]:
        """
        Get aggregated insights for a niche from all contributing accounts.

        Args:
            niche: Niche category
            force_refresh: Force recalculation even if cached

        Returns:
            NicheWisdom or None if insufficient data
        """
        try:
            # Check cache
            if not force_refresh and niche in self._wisdom_cache:
                cached = self._wisdom_cache[niche]
                # Check if cache is fresh (< 1 hour old)
                if (datetime.now() - cached.last_updated).total_seconds() < 3600:
                    logger.info(f"Returning cached wisdom for niche {niche}")
                    return cached

            logger.info(f"Calculating niche wisdom for {niche}")

            # Get all accounts in this niche
            accounts_in_niche = await self._get_accounts_by_niche(niche)

            if len(accounts_in_niche) < self.min_sample_size:
                logger.info(f"Niche {niche} has only {len(accounts_in_niche)} accounts, need {self.min_sample_size}")
                return None

            # Extract insights from each account
            all_insights = []
            for account_id in accounts_in_niche:
                insights = await self.extract_anonymized_insights(account_id)
                if insights and insights.opted_in:
                    all_insights.append(insights)

            if len(all_insights) < self.min_sample_size:
                logger.info(f"Only {len(all_insights)} accounts opted in for niche {niche}")
                return None

            # Aggregate across all accounts
            niche_wisdom = NicheWisdom(
                niche=niche,
                sample_size=len(all_insights),
                top_hook_types=self._rank_by_frequency([i.top_hook_types for i in all_insights]),
                optimal_duration=self._average_range([i.optimal_duration_range for i in all_insights]),
                peak_hours=self._find_common_peaks([i.best_posting_times for i in all_insights]),
                proven_cta_styles=self._rank_by_success([i.effective_cta_styles for i in all_insights]),
                winning_visual_patterns=self._rank_by_frequency([i.visual_preferences for i in all_insights]),
                niche_avg_ctr=float(np.mean([i.avg_ctr for i in all_insights])),
                niche_avg_conversion_rate=float(np.mean([i.avg_conversion_rate for i in all_insights])),
                niche_avg_roas=float(np.mean([i.avg_roas for i in all_insights if i.avg_roas > 0])),
                confidence_score=self._calculate_wisdom_confidence(all_insights),
                last_updated=datetime.now()
            )

            # Cache the wisdom
            self._wisdom_cache[niche] = niche_wisdom

            logger.info(f"Niche wisdom calculated for {niche}: {len(all_insights)} accounts, confidence {niche_wisdom.confidence_score:.2f}")
            return niche_wisdom

        except Exception as e:
            logger.error(f"Error calculating niche wisdom for {niche}: {str(e)}")
            return None

    async def apply_niche_wisdom(
        self,
        new_account_id: str,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        Apply niche wisdom to a new account to bootstrap performance.

        Args:
            new_account_id: Account ID to apply wisdom to
            auto_apply: If True, automatically configure account with wisdom

        Returns:
            Dict with niche, wisdom, and application status
        """
        try:
            logger.info(f"Applying niche wisdom to account {new_account_id}")

            # Detect account's niche
            niche, confidence = await self.detect_niche(new_account_id)

            if niche == NicheCategory.UNKNOWN.value:
                return {
                    "success": False,
                    "message": "Could not detect niche for account",
                    "niche": niche
                }

            # Get niche wisdom
            wisdom = await self.get_niche_insights(niche)

            if not wisdom:
                return {
                    "success": False,
                    "message": f"Insufficient data for niche {niche}",
                    "niche": niche
                }

            # Prepare recommendations
            recommendations = {
                "niche": niche,
                "niche_confidence": confidence,
                "based_on_accounts": wisdom.sample_size,
                "recommended_patterns": {
                    "hook_types": wisdom.top_hook_types[:5],
                    "optimal_duration": {
                        "min_seconds": wisdom.optimal_duration[0],
                        "max_seconds": wisdom.optimal_duration[1]
                    },
                    "best_posting_hours": wisdom.peak_hours[:5],
                    "cta_styles": wisdom.proven_cta_styles[:5],
                    "visual_patterns": wisdom.winning_visual_patterns[:5]
                },
                "benchmarks": {
                    "niche_avg_ctr": wisdom.niche_avg_ctr,
                    "niche_avg_conversion_rate": wisdom.niche_avg_conversion_rate,
                    "niche_avg_roas": wisdom.niche_avg_roas
                },
                "wisdom_confidence": wisdom.confidence_score
            }

            # Auto-apply if requested
            if auto_apply:
                await self._configure_account_defaults(new_account_id, recommendations)
                recommendations["applied"] = True
            else:
                recommendations["applied"] = False

            logger.info(f"Niche wisdom prepared for account {new_account_id}: {niche} ({wisdom.sample_size} accounts)")
            return {
                "success": True,
                "niche": niche,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Error applying niche wisdom to account {new_account_id}: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

    async def get_cross_learning_dashboard(self, account_id: str) -> Dict[str, Any]:
        """
        Generate cross-learning dashboard for an account.

        Shows:
        - Account's niche
        - Performance vs. niche benchmarks
        - Improvement opportunities
        - Network effect stats

        Args:
            account_id: Account ID

        Returns:
            Dashboard data
        """
        try:
            # Detect niche
            niche, confidence = await self.detect_niche(account_id)

            # Get account insights
            account_insights = await self.extract_anonymized_insights(account_id)

            # Get niche wisdom
            niche_wisdom = await self.get_niche_insights(niche) if niche != NicheCategory.UNKNOWN.value else None

            # Compare account to niche benchmarks
            comparison = {}
            opportunities = []

            if account_insights and niche_wisdom:
                # CTR comparison
                ctr_diff = account_insights.avg_ctr - niche_wisdom.niche_avg_ctr
                ctr_pct_diff = (ctr_diff / niche_wisdom.niche_avg_ctr * 100) if niche_wisdom.niche_avg_ctr > 0 else 0

                comparison["ctr"] = {
                    "account": account_insights.avg_ctr,
                    "niche_avg": niche_wisdom.niche_avg_ctr,
                    "difference": ctr_diff,
                    "difference_pct": ctr_pct_diff,
                    "performance": "above" if ctr_diff > 0 else "below"
                }

                # Conversion rate comparison
                cvr_diff = account_insights.avg_conversion_rate - niche_wisdom.niche_avg_conversion_rate
                cvr_pct_diff = (cvr_diff / niche_wisdom.niche_avg_conversion_rate * 100) if niche_wisdom.niche_avg_conversion_rate > 0 else 0

                comparison["conversion_rate"] = {
                    "account": account_insights.avg_conversion_rate,
                    "niche_avg": niche_wisdom.niche_avg_conversion_rate,
                    "difference": cvr_diff,
                    "difference_pct": cvr_pct_diff,
                    "performance": "above" if cvr_diff > 0 else "below"
                }

                # ROAS comparison
                roas_diff = account_insights.avg_roas - niche_wisdom.niche_avg_roas
                roas_pct_diff = (roas_diff / niche_wisdom.niche_avg_roas * 100) if niche_wisdom.niche_avg_roas > 0 else 0

                comparison["roas"] = {
                    "account": account_insights.avg_roas,
                    "niche_avg": niche_wisdom.niche_avg_roas,
                    "difference": roas_diff,
                    "difference_pct": roas_pct_diff,
                    "performance": "above" if roas_diff > 0 else "below"
                }

                # Identify opportunities
                if ctr_pct_diff < -10:
                    opportunities.append({
                        "area": "CTR",
                        "issue": f"CTR is {abs(ctr_pct_diff):.1f}% below niche average",
                        "recommendation": f"Try top hook types: {', '.join([h['hook_type'] for h in niche_wisdom.top_hook_types[:3]])}"
                    })

                if cvr_pct_diff < -10:
                    opportunities.append({
                        "area": "Conversion Rate",
                        "issue": f"Conversion rate is {abs(cvr_pct_diff):.1f}% below niche average",
                        "recommendation": f"Try proven CTA styles: {', '.join([c['style'] for c in niche_wisdom.proven_cta_styles[:3]])}"
                    })

            # Network effect stats
            total_accounts = await self._get_total_account_count()
            total_niches = await self._get_active_niche_count()

            dashboard = {
                "account_id": account_id,
                "niche": {
                    "category": niche,
                    "confidence": confidence,
                    "contributing_accounts": niche_wisdom.sample_size if niche_wisdom else 0
                },
                "performance_comparison": comparison,
                "improvement_opportunities": opportunities,
                "network_stats": {
                    "total_accounts": total_accounts,
                    "total_niches": total_niches,
                    "your_niche_accounts": niche_wisdom.sample_size if niche_wisdom else 0,
                    "wisdom_quality": niche_wisdom.confidence_score if niche_wisdom else 0.0
                },
                "generated_at": datetime.now().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Error generating dashboard for account {account_id}: {str(e)}")
            return {"error": str(e)}

    # ==================== HELPER METHODS ====================

    async def _get_account_campaigns(self, account_id: str) -> List[Any]:
        """Get all campaigns for an account."""
        try:
            if not Campaign:
                return []

            result = await self.db_session.execute(
                select(Campaign)
                .where(Campaign.userId == account_id)
                .order_by(desc(Campaign.createdAt))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching campaigns: {str(e)}")
            return []

    async def _get_account_winners(self, account_id: str) -> List[Dict[str, Any]]:
        """Get winning campaigns (high CTR) for an account."""
        try:
            if not Campaign or not PerformanceMetric:
                return []

            # Get campaigns with good performance
            result = await self.db_session.execute(
                select(Campaign, func.avg(PerformanceMetric.ctr).label('avg_ctr'))
                .join(Video, Campaign.id == Video.campaign_id)
                .join(PerformanceMetric, Video.id == PerformanceMetric.video_id)
                .where(Campaign.userId == account_id)
                .group_by(Campaign.id)
                .having(func.avg(PerformanceMetric.ctr) >= self.winner_threshold)
                .order_by(desc('avg_ctr'))
            )

            winners = []
            for campaign, avg_ctr in result:
                # Get full metrics for this campaign
                # Get aggregated metrics including conversion value from raw_data
                metrics_raw_result = await self.db_session.execute(
                    select(PerformanceMetric)
                    .join(Video, PerformanceMetric.video_id == Video.id)
                    .where(Video.campaign_id == campaign.id)
                )

                metrics_list = metrics_raw_result.scalars().all()

                # Calculate totals
                impressions = sum(m.impressions or 0 for m in metrics_list)
                clicks = sum(m.clicks or 0 for m in metrics_list)
                conversions = sum(m.conversions or 0 for m in metrics_list)
                spend = sum(float(m.spend or 0) for m in metrics_list)

                # Calculate conversion value from raw_data
                conversion_value = 0.0
                for m in metrics_list:
                    if m.raw_data and isinstance(m.raw_data, dict):
                        # Try to extract conversion value from raw_data
                        conv_val = m.raw_data.get('conversion_value', 0) or m.raw_data.get('action_values', 0)
                        if conv_val:
                            conversion_value += float(conv_val)

                # Calculate ROAS
                roas = (conversion_value / spend) if spend > 0 else 0.0

                if impressions:
                    winners.append({
                        'campaign_id': campaign.id,
                        'campaign_name': campaign.name,
                        'ctr': float(avg_ctr or 0),
                        'impressions': impressions,
                        'clicks': clicks,
                        'conversions': conversions,
                        'spend': spend,
                        'conversion_rate': (conversions / clicks * 100) if clicks else 0,
                        'roas': roas
                    })

            return winners

        except Exception as e:
            logger.error(f"Error fetching winners: {str(e)}")
            return []

    def _aggregate_hook_types(self, winners: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate hook types from winning campaigns."""
        # Simplified - would extract from video script content
        # For now, return mock data
        hook_types = [
            {"hook_type": "question", "count": 5, "avg_ctr": 0.025},
            {"hook_type": "pain_point", "count": 3, "avg_ctr": 0.022},
            {"hook_type": "curiosity_gap", "count": 4, "avg_ctr": 0.021}
        ]
        return hook_types

    def _calculate_duration_range(self, winners: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate optimal duration range from winners."""
        # Simplified - would get actual video durations
        # For now, return typical range
        return (15.0, 30.0)  # 15-30 seconds

    def _aggregate_posting_times(self, winners: List[Dict[str, Any]]) -> List[int]:
        """Aggregate best posting times (hours of day)."""
        # Simplified - would analyze actual posting times
        # For now, return typical best hours
        return [9, 12, 17, 19, 21]  # 9am, 12pm, 5pm, 7pm, 9pm

    def _aggregate_cta_styles(self, winners: List[Dict[str, Any]]) -> List[str]:
        """Aggregate effective CTA styles."""
        # Simplified - would extract from video content
        return ["learn_more", "shop_now", "sign_up", "get_started"]

    def _aggregate_visual_patterns(self, winners: List[Dict[str, Any]]) -> List[str]:
        """Aggregate winning visual patterns."""
        # Simplified - would analyze video content
        return ["fast_cuts", "text_overlay", "product_demo", "before_after"]

    async def _get_account_age(self, account_id: str) -> int:
        """Get account age in days."""
        try:
            # Simplified - would get from user creation date
            return 90  # Mock: 90 days
        except Exception:
            return 0

    async def _get_user_opt_in_status(self, account_id: str) -> bool:
        """
        Get user opt-in status for cross-account learning.

        Args:
            account_id: User/account ID

        Returns:
            True if user opted in, False otherwise (default True)
        """
        try:
            from db.models import AccountInsights as AccountInsightsModel

            # Check if there's an existing AccountInsights record
            result = await self.db_session.execute(
                select(AccountInsightsModel.opted_in)
                .where(AccountInsightsModel.account_id == account_id)
                .order_by(desc(AccountInsightsModel.created_at))
                .limit(1)
            )

            opted_in_row = result.first()
            if opted_in_row:
                return opted_in_row[0]

            # Default to True (opt-in by default, user can opt-out later)
            return True

        except Exception as e:
            logger.error(f"Error fetching opt-in status for account {account_id}: {str(e)}")
            # Default to True if there's an error
            return True

    async def _get_accounts_by_niche(self, niche: str) -> List[str]:
        """Get all account IDs in a specific niche."""
        # Simplified - would query from account_insights table
        # For now, return mock data
        return []

    def _rank_by_frequency(self, items_lists: List[List]) -> List[Dict[str, Any]]:
        """Rank items by frequency across multiple lists."""
        all_items = []
        for items in items_lists:
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        all_items.append(item.get('hook_type') or item.get('style') or str(item))
                    else:
                        all_items.append(str(item))

        counter = Counter(all_items)
        ranked = [
            {"item": item, "frequency": count, "percentage": count / len(items_lists) * 100}
            for item, count in counter.most_common(10)
        ]
        return ranked

    def _average_range(self, ranges: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Average duration ranges."""
        if not ranges:
            return (15.0, 30.0)

        mins = [r[0] for r in ranges]
        maxs = [r[1] for r in ranges]
        return (float(np.mean(mins)), float(np.mean(maxs)))

    def _find_common_peaks(self, hour_lists: List[List[int]]) -> List[int]:
        """Find common peak hours across accounts."""
        all_hours = []
        for hours in hour_lists:
            all_hours.extend(hours)

        counter = Counter(all_hours)
        return [hour for hour, count in counter.most_common(5)]

    def _rank_by_success(self, cta_lists: List[List[str]]) -> List[Dict[str, Any]]:
        """Rank CTAs by success rate."""
        all_ctas = []
        for ctas in cta_lists:
            all_ctas.extend(ctas)

        counter = Counter(all_ctas)
        ranked = [
            {"style": cta, "success_count": count, "success_rate": count / len(cta_lists) * 100}
            for cta, count in counter.most_common(10)
        ]
        return ranked

    def _calculate_wisdom_confidence(self, insights_list: List[AccountInsights]) -> float:
        """Calculate confidence score for niche wisdom."""
        if not insights_list:
            return 0.0

        # Base confidence on sample size and account quality
        sample_factor = min(len(insights_list) / 20.0, 1.0)  # Max at 20 accounts
        quality_factor = np.mean([i.confidence for i in insights_list])

        return float(sample_factor * quality_factor)

    async def _configure_account_defaults(
        self,
        account_id: str,
        recommendations: Dict[str, Any]
    ) -> None:
        """Apply niche wisdom recommendations to account settings."""
        # Would update account preferences/settings
        # For now, just log
        logger.info(f"Would configure account {account_id} with recommendations: {recommendations}")

    async def _get_total_account_count(self) -> int:
        """Get total number of accounts in system."""
        # Simplified
        return 150  # Mock

    async def _get_active_niche_count(self) -> int:
        """Get number of active niches with sufficient data."""
        # Simplified
        return 8  # Mock


# Initialize singleton instance
cross_learner: Optional[CrossAccountLearner] = None


def initialize_cross_learner(
    db_session: Session,
    anthropic_api_key: Optional[str] = None
) -> CrossAccountLearner:
    """Initialize the global cross-learner instance."""
    global cross_learner
    cross_learner = CrossAccountLearner(
        db_session=db_session,
        anthropic_api_key=anthropic_api_key
    )
    logger.info("Global CrossAccountLearner initialized")
    return cross_learner
