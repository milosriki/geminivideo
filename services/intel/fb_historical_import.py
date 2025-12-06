"""
Facebook Historical Data Importer

Imports historical campaign data from Facebook Ads
to bootstrap the learning system with real performance data.

Connection: Meta Marketing API
Required: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID

What we import:
- Campaign performance (spend, ROAS, CTR, CPM)
- Ad creative details (video, copy, thumbnails)
- Audience insights
- Winning/losing patterns
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class CampaignObjective(Enum):
    CONVERSIONS = "OUTCOME_SALES"
    LEADS = "OUTCOME_LEADS"
    TRAFFIC = "OUTCOME_TRAFFIC"
    AWARENESS = "OUTCOME_AWARENESS"
    ENGAGEMENT = "OUTCOME_ENGAGEMENT"


class PerformanceTier(Enum):
    WINNER = "winner"      # ROAS >= 3.0
    GOOD = "good"          # ROAS 2.0 - 3.0
    AVERAGE = "average"    # ROAS 1.0 - 2.0
    LOSER = "loser"        # ROAS < 1.0


@dataclass
class HistoricalCampaign:
    """Historical campaign data from FB"""
    id: str
    name: str
    objective: CampaignObjective
    status: str

    # Spend
    spend: float
    budget: float

    # Performance
    impressions: int
    clicks: int
    conversions: int
    revenue: float

    # Calculated
    ctr: float
    cpc: float
    cpm: float
    cpa: float
    roas: float
    tier: PerformanceTier

    # Time
    start_date: datetime
    end_date: Optional[datetime]
    days_running: int

    # Audience
    targeting: Dict[str, Any]


@dataclass
class HistoricalAd:
    """Historical ad creative from FB"""
    id: str
    campaign_id: str
    adset_id: str
    name: str

    # Creative
    creative_type: str  # video, image, carousel
    headline: str
    primary_text: str
    cta_text: str
    video_url: Optional[str]
    image_url: Optional[str]
    thumbnail_url: Optional[str]

    # Performance
    spend: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    ctr: float
    roas: float
    tier: PerformanceTier

    # Analysis
    hook_text: str  # First line of primary text
    patterns: Dict[str, Any]


@dataclass
class ImportResult:
    """Result of historical import"""
    campaigns_imported: int
    ads_imported: int
    total_spend: float
    total_revenue: float
    date_range: Tuple[datetime, datetime]
    winners_found: int
    patterns_extracted: int


class FBHistoricalImporter:
    """
    Facebook Ads Historical Data Importer

    Imports past campaign data to:
    1. Bootstrap learning with proven winners
    2. Identify losing patterns to avoid
    3. Calculate industry benchmarks
    4. Extract winning creative elements
    """

    GRAPH_API_VERSION = "v19.0"
    BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    def __init__(
        self,
        access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None
    ):
        """
        Initialize FB importer.

        Args:
            access_token: Meta access token
            ad_account_id: Ad account ID (act_xxx format)
        """
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = ad_account_id or os.getenv("META_AD_ACCOUNT_ID")
        self.session = None

        if not self.access_token:
            logger.warning("No META_ACCESS_TOKEN - import will fail")
        if not self.ad_account_id:
            logger.warning("No META_AD_ACCOUNT_ID - import will fail")

    async def connect(self) -> bool:
        """Test connection to Meta API"""
        if not self.access_token or not self.ad_account_id:
            logger.error("Missing credentials")
            return False

        try:
            self.session = aiohttp.ClientSession()

            # Test connection
            url = f"{self.BASE_URL}/{self.ad_account_id}"
            params = {
                "access_token": self.access_token,
                "fields": "name,account_status"
            }

            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"Connected to Meta Ads: {data.get('name', 'Unknown')}")
                    return True
                else:
                    error = await resp.json()
                    logger.error(f"Connection failed: {error}")
                    return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()
            self.session = None

    # =========================================================================
    # Import Methods
    # =========================================================================

    async def import_campaigns(
        self,
        days_back: int = 90,
        min_spend: float = 100,
        objective: CampaignObjective = None
    ) -> List[HistoricalCampaign]:
        """
        Import historical campaigns.

        Args:
            days_back: How far back to look
            min_spend: Minimum spend to include
            objective: Filter by objective

        Returns:
            List of historical campaigns
        """
        if not self.session:
            await self.connect()

        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Build query
            url = f"{self.BASE_URL}/{self.ad_account_id}/campaigns"
            params = {
                "access_token": self.access_token,
                "fields": ",".join([
                    "id", "name", "objective", "status",
                    "daily_budget", "lifetime_budget",
                    "start_time", "stop_time",
                    "insights{spend,impressions,clicks,actions,action_values}"
                ]),
                "time_range": f'{{"since":"{start_date.strftime("%Y-%m-%d")}","until":"{end_date.strftime("%Y-%m-%d")}"}}',
                "limit": 500
            }

            if objective:
                params["filtering"] = f'[{{"field":"objective","operator":"EQUAL","value":"{objective.value}"}}]'

            campaigns = []
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    for c in data.get("data", []):
                        campaign = self._parse_campaign(c)
                        if campaign and campaign.spend >= min_spend:
                            campaigns.append(campaign)

                    logger.info(f"Imported {len(campaigns)} campaigns from FB")
                else:
                    error = await resp.json()
                    logger.error(f"Failed to get campaigns: {error}")

            return campaigns

        except Exception as e:
            logger.error(f"Error importing campaigns: {e}")
            return []

    async def import_ads(
        self,
        days_back: int = 90,
        min_spend: float = 50,
        only_winners: bool = False
    ) -> List[HistoricalAd]:
        """
        Import historical ads with creative details.

        Args:
            days_back: How far back to look
            min_spend: Minimum spend to include
            only_winners: Only import winning ads (ROAS >= 2.0)

        Returns:
            List of historical ads
        """
        if not self.session:
            await self.connect()

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            url = f"{self.BASE_URL}/{self.ad_account_id}/ads"
            params = {
                "access_token": self.access_token,
                "fields": ",".join([
                    "id", "name", "campaign_id", "adset_id", "status",
                    "creative{title,body,call_to_action_type,object_story_spec,thumbnail_url,video_id,image_url}",
                    "insights{spend,impressions,clicks,actions,action_values,ctr,cpc}"
                ]),
                "time_range": f'{{"since":"{start_date.strftime("%Y-%m-%d")}","until":"{end_date.strftime("%Y-%m-%d")}"}}',
                "limit": 500
            }

            ads = []
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    for a in data.get("data", []):
                        ad = self._parse_ad(a)
                        if ad and ad.spend >= min_spend:
                            if only_winners and ad.roas < 2.0:
                                continue
                            ads.append(ad)

                    logger.info(f"Imported {len(ads)} ads from FB")
                else:
                    error = await resp.json()
                    logger.error(f"Failed to get ads: {error}")

            return ads

        except Exception as e:
            logger.error(f"Error importing ads: {e}")
            return []

    async def import_all(
        self,
        days_back: int = 90
    ) -> ImportResult:
        """
        Import all historical data.

        Args:
            days_back: Days of history to import

        Returns:
            ImportResult with summary
        """
        logger.info(f"Starting full import of last {days_back} days...")

        # Import campaigns
        campaigns = await self.import_campaigns(days_back=days_back)

        # Import ads
        ads = await self.import_ads(days_back=days_back)

        # Calculate stats
        total_spend = sum(c.spend for c in campaigns)
        total_revenue = sum(c.revenue for c in campaigns)
        winners = [c for c in campaigns if c.tier == PerformanceTier.WINNER]

        # Extract patterns
        patterns = self.extract_winning_patterns(ads)

        result = ImportResult(
            campaigns_imported=len(campaigns),
            ads_imported=len(ads),
            total_spend=total_spend,
            total_revenue=total_revenue,
            date_range=(
                datetime.now() - timedelta(days=days_back),
                datetime.now()
            ),
            winners_found=len(winners),
            patterns_extracted=len(patterns.get("hooks", []))
        )

        logger.info(f"Import complete: {result.campaigns_imported} campaigns, {result.ads_imported} ads")
        logger.info(f"Found {result.winners_found} winning campaigns")

        return result

    # =========================================================================
    # Pattern Extraction
    # =========================================================================

    def extract_winning_patterns(
        self,
        ads: List[HistoricalAd]
    ) -> Dict[str, Any]:
        """
        Extract patterns from winning ads.

        This is the key function - learns what made ads win.
        """
        winners = [ad for ad in ads if ad.tier in [PerformanceTier.WINNER, PerformanceTier.GOOD]]
        losers = [ad for ad in ads if ad.tier == PerformanceTier.LOSER]

        patterns = {
            "hooks": [],
            "ctas": [],
            "headlines": [],
            "winning_elements": {},
            "losing_elements": {},
            "benchmarks": {},
            "total_analyzed": len(ads),
            "winners_analyzed": len(winners),
            "losers_analyzed": len(losers)
        }

        # Extract winning hooks
        for ad in winners:
            if ad.hook_text:
                patterns["hooks"].append({
                    "text": ad.hook_text,
                    "roas": ad.roas,
                    "ctr": ad.ctr,
                    "source": "fb_historical"
                })

            if ad.cta_text:
                patterns["ctas"].append({
                    "text": ad.cta_text,
                    "roas": ad.roas
                })

            if ad.headline:
                patterns["headlines"].append({
                    "text": ad.headline,
                    "roas": ad.roas
                })

        # Analyze winning elements
        patterns["winning_elements"] = self._analyze_common_elements(winners)
        patterns["losing_elements"] = self._analyze_common_elements(losers)

        # Calculate benchmarks
        if ads:
            patterns["benchmarks"] = {
                "avg_ctr": sum(a.ctr for a in ads) / len(ads),
                "avg_roas": sum(a.roas for a in ads if a.roas > 0) / len([a for a in ads if a.roas > 0]) if any(a.roas > 0 for a in ads) else 0,
                "winner_ctr": sum(a.ctr for a in winners) / len(winners) if winners else 0,
                "winner_roas": sum(a.roas for a in winners) / len(winners) if winners else 0
            }

        # Sort by performance
        patterns["hooks"] = sorted(patterns["hooks"], key=lambda x: x["roas"], reverse=True)[:50]
        patterns["ctas"] = sorted(patterns["ctas"], key=lambda x: x["roas"], reverse=True)[:20]

        logger.info(f"Extracted {len(patterns['hooks'])} winning hooks, {len(patterns['ctas'])} CTAs")
        return patterns

    def _analyze_common_elements(self, ads: List[HistoricalAd]) -> Dict[str, Any]:
        """Analyze common elements in a group of ads"""
        elements = {
            "creative_types": {},
            "cta_types": {},
            "text_lengths": [],
            "has_emoji": 0,
            "has_numbers": 0,
            "has_questions": 0
        }

        for ad in ads:
            # Creative type
            ct = ad.creative_type
            elements["creative_types"][ct] = elements["creative_types"].get(ct, 0) + 1

            # CTA type
            if ad.cta_text:
                elements["cta_types"][ad.cta_text] = elements["cta_types"].get(ad.cta_text, 0) + 1

            # Text analysis
            if ad.primary_text:
                elements["text_lengths"].append(len(ad.primary_text))

                if any(ord(c) > 127 for c in ad.primary_text):
                    elements["has_emoji"] += 1

                if any(c.isdigit() for c in ad.primary_text[:50]):
                    elements["has_numbers"] += 1

                if "?" in ad.primary_text[:100]:
                    elements["has_questions"] += 1

        # Calculate percentages
        total = len(ads) if ads else 1
        elements["emoji_pct"] = elements["has_emoji"] / total
        elements["numbers_pct"] = elements["has_numbers"] / total
        elements["questions_pct"] = elements["has_questions"] / total
        elements["avg_text_length"] = sum(elements["text_lengths"]) / len(elements["text_lengths"]) if elements["text_lengths"] else 0

        return elements

    # =========================================================================
    # Sync to Learning System
    # =========================================================================

    async def sync_to_cross_learning(
        self,
        campaigns: List[HistoricalCampaign],
        cross_learner
    ) -> int:
        """
        Sync historical data to cross-campaign learning.

        Args:
            campaigns: Historical campaigns
            cross_learner: CrossCampaignLearner instance

        Returns:
            Number of campaigns synced
        """
        synced = 0

        for campaign in campaigns:
            await cross_learner.ingest_campaign_result(
                campaign_id=campaign.id,
                industry="imported",
                spend=campaign.spend,
                revenue=campaign.revenue,
                roas=campaign.roas,
                ctr=campaign.ctr,
                conversions=campaign.conversions,
                source="fb_historical"
            )
            synced += 1

        logger.info(f"Synced {synced} campaigns to cross-learning")
        return synced

    async def sync_to_patterns_db(
        self,
        ads: List[HistoricalAd],
        patterns_db
    ) -> int:
        """
        Sync winning patterns to patterns database.

        Args:
            ads: Historical ads
            patterns_db: WinningPatternsDB instance

        Returns:
            Number of patterns synced
        """
        patterns = self.extract_winning_patterns(ads)
        synced = 0

        # Sync hooks
        for hook in patterns["hooks"]:
            await patterns_db.add_hook_pattern(
                text=hook["text"],
                hook_type="historical",
                industry="imported",
                source="fb_historical",
                performance_score=hook["roas"]
            )
            synced += 1

        # Sync CTAs
        for cta in patterns["ctas"]:
            await patterns_db.add_cta_pattern(
                text=cta["text"],
                industry="imported",
                source="fb_historical",
                performance_score=cta["roas"]
            )
            synced += 1

        logger.info(f"Synced {synced} patterns to database")
        return synced

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_campaign(self, data: Dict) -> Optional[HistoricalCampaign]:
        """Parse API response to HistoricalCampaign"""
        try:
            insights = data.get("insights", {}).get("data", [{}])[0]

            spend = float(insights.get("spend", 0))
            impressions = int(insights.get("impressions", 0))
            clicks = int(insights.get("clicks", 0))

            # Parse actions and values
            conversions = 0
            revenue = 0

            for action in insights.get("actions", []):
                if action.get("action_type") in ["purchase", "omni_purchase", "lead"]:
                    conversions += int(action.get("value", 0))

            for value in insights.get("action_values", []):
                if value.get("action_type") in ["purchase", "omni_purchase"]:
                    revenue += float(value.get("value", 0))

            # Calculate metrics
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cpc = spend / clicks if clicks > 0 else 0
            cpm = (spend / impressions * 1000) if impressions > 0 else 0
            cpa = spend / conversions if conversions > 0 else 0
            roas = revenue / spend if spend > 0 else 0

            # Determine tier
            if roas >= 3.0:
                tier = PerformanceTier.WINNER
            elif roas >= 2.0:
                tier = PerformanceTier.GOOD
            elif roas >= 1.0:
                tier = PerformanceTier.AVERAGE
            else:
                tier = PerformanceTier.LOSER

            # Parse dates
            start_date = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()).replace("Z", "+00:00"))
            end_date = None
            if data.get("stop_time"):
                end_date = datetime.fromisoformat(data["stop_time"].replace("Z", "+00:00"))

            days_running = (end_date - start_date).days if end_date else (datetime.now() - start_date.replace(tzinfo=None)).days

            return HistoricalCampaign(
                id=data["id"],
                name=data.get("name", ""),
                objective=CampaignObjective(data.get("objective", "OUTCOME_SALES")),
                status=data.get("status", "UNKNOWN"),
                spend=spend,
                budget=float(data.get("daily_budget", data.get("lifetime_budget", 0)) or 0) / 100,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                revenue=revenue,
                ctr=ctr,
                cpc=cpc,
                cpm=cpm,
                cpa=cpa,
                roas=roas,
                tier=tier,
                start_date=start_date,
                end_date=end_date,
                days_running=days_running,
                targeting={}
            )

        except Exception as e:
            logger.warning(f"Failed to parse campaign: {e}")
            return None

    def _parse_ad(self, data: Dict) -> Optional[HistoricalAd]:
        """Parse API response to HistoricalAd"""
        try:
            insights = data.get("insights", {}).get("data", [{}])[0]
            creative = data.get("creative", {})

            spend = float(insights.get("spend", 0))
            impressions = int(insights.get("impressions", 0))
            clicks = int(insights.get("clicks", 0))

            # Parse conversions and revenue
            conversions = 0
            revenue = 0

            for action in insights.get("actions", []):
                if action.get("action_type") in ["purchase", "omni_purchase", "lead"]:
                    conversions += int(action.get("value", 0))

            for value in insights.get("action_values", []):
                if value.get("action_type") in ["purchase", "omni_purchase"]:
                    revenue += float(value.get("value", 0))

            ctr = float(insights.get("ctr", 0))
            roas = revenue / spend if spend > 0 else 0

            # Determine tier
            if roas >= 3.0:
                tier = PerformanceTier.WINNER
            elif roas >= 2.0:
                tier = PerformanceTier.GOOD
            elif roas >= 1.0:
                tier = PerformanceTier.AVERAGE
            else:
                tier = PerformanceTier.LOSER

            # Extract creative details
            story_spec = creative.get("object_story_spec", {})
            link_data = story_spec.get("link_data", {})
            video_data = story_spec.get("video_data", {})

            primary_text = link_data.get("message", video_data.get("message", ""))
            headline = link_data.get("name", video_data.get("title", creative.get("title", "")))
            cta_text = link_data.get("call_to_action", {}).get("type", "")

            # Determine creative type
            if creative.get("video_id") or video_data:
                creative_type = "video"
            elif link_data.get("child_attachments"):
                creative_type = "carousel"
            else:
                creative_type = "image"

            # Extract hook
            hook_text = ""
            if primary_text:
                lines = primary_text.split('\n')
                hook_text = lines[0].strip() if lines else ""

            return HistoricalAd(
                id=data["id"],
                campaign_id=data.get("campaign_id", ""),
                adset_id=data.get("adset_id", ""),
                name=data.get("name", ""),
                creative_type=creative_type,
                headline=headline,
                primary_text=primary_text,
                cta_text=cta_text,
                video_url=None,  # Would need separate API call
                image_url=creative.get("image_url"),
                thumbnail_url=creative.get("thumbnail_url"),
                spend=spend,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                revenue=revenue,
                ctr=ctr,
                roas=roas,
                tier=tier,
                hook_text=hook_text,
                patterns=self._extract_ad_patterns(primary_text, headline)
            )

        except Exception as e:
            logger.warning(f"Failed to parse ad: {e}")
            return None

    def _extract_ad_patterns(self, text: str, headline: str) -> Dict[str, Any]:
        """Extract patterns from ad copy"""
        return {
            "has_emoji": any(ord(c) > 127 for c in text),
            "has_numbers": any(c.isdigit() for c in (text[:50] if text else "")),
            "has_question": "?" in (text[:100] if text else ""),
            "text_length": len(text) if text else 0,
            "headline_length": len(headline) if headline else 0,
            "has_urgency": any(w in text.lower() for w in ["now", "today", "limited", "hurry"]) if text else False
        }
