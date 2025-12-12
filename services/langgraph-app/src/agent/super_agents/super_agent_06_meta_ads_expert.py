"""Super Agent 6: Meta Ads Expert - Learns from Meta, Scrapes Data, Recalculates Ads."""

from typing import Any, Dict, List, Optional
import os
import logging
import requests
from datetime import datetime, timedelta

from agent.super_agents.base_super_agent import SuperAgent
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class MetaAdsExpertAgent(SuperAgent):
    """Expert in Meta Ads - learns from real campaigns, scrapes data, recalculates ads."""

    def __init__(self, **kwargs):
        super().__init__(
            name="MetaAdsExpertAgent",
            description=(
                "Meta Ads expert. Learns from real Meta campaigns, scrapes ad data "
                "from accounts immediately, recalculates ads, finds patterns, copies "
                "winning videos. Focuses on Meta ads optimization, performance, and "
                "winning ad patterns."
            ),
            domains=[
                "Meta Ads API",
                "Ad Scraping",
                "Campaign Analysis",
                "Ad Recalculation",
                "Video Pattern Copying",
                "Performance Optimization",
                "Winning Ad Patterns",
            ],
            thinking_steps=5,
            **kwargs,
        )
        self.meta_access_token = os.getenv("META_ACCESS_TOKEN")
        self.meta_ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        self.base_url = "https://graph.facebook.com/v19.0"
        self.client = supabase_client.client

    async def _execute_with_reasoning(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        thinking: Dict[str, Any],
    ) -> Any:
        """Execute Meta Ads expert operations."""
        operation = input_data.get("operation", "learn_from_meta")

        if operation == "learn_from_meta":
            return await self._learn_from_meta(input_data, thinking)
        elif operation == "scrape_account_ads":
            return await self._scrape_account_ads(input_data, thinking)
        elif operation == "recalculate_ads":
            return await self._recalculate_ads(input_data, thinking)
        elif operation == "copy_video_patterns":
            return await self._copy_video_patterns(input_data, thinking)
        elif operation == "find_winning_patterns":
            return await self._find_winning_patterns(input_data, thinking)
        elif operation == "analyze_meta_performance":
            return await self._analyze_meta_performance(input_data, thinking)
        else:
            return {
                "operation": operation,
                "thinking": thinking.get("final_reasoning"),
                "status": "processed",
            }

    async def _learn_from_meta(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Learn from Meta Ads API - fetch real campaign data."""
        if not self.meta_access_token or not self.meta_ad_account_id:
            return {
                "error": "Meta credentials not configured",
                "message": "Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID",
            }

        try:
            days_back = input_data.get("days_back", 30)
            min_spend = input_data.get("min_spend", 10.0)

            # Fetch campaign insights
            params = {
                "access_token": self.meta_access_token,
                "fields": ",".join([
                    "campaign_name",
                    "campaign_id",
                    "adset_name",
                    "ad_name",
                    "spend",
                    "impressions",
                    "clicks",
                    "cpm",
                    "ctr",
                    "cpc",
                    "actions",
                    "action_values",
                    "purchase_roas",
                    "cost_per_action_type",
                    "video_30_sec_watched_actions",
                    "video_avg_time_watched_actions",
                ]),
                "level": "ad",
                "time_range": {
                    "since": (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
                    "until": datetime.now().strftime("%Y-%m-%d"),
                },
                "limit": 100,
            }

            url = f"{self.base_url}/{self.meta_ad_account_id}/insights"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            ads = data.get("data", [])

            # Extract patterns
            patterns = self._extract_patterns(ads)

            # Save to agent memory
            if self.client:
                self.client.table("agent_memory").insert({
                    "key": f"meta_learning_{datetime.now().isoformat()}",
                    "value": {
                        "ads_count": len(ads),
                        "patterns": patterns,
                        "date_range": f"{days_back} days",
                    },
                    "type": "meta_learning",
                    "metadata": {
                        "source": "meta_ads_api",
                        "account_id": self.meta_ad_account_id,
                    },
                }).execute()

            logger.info(f"✅ Learned from {len(ads)} Meta ads")

            return {
                "ads_analyzed": len(ads),
                "patterns_found": len(patterns),
                "patterns": patterns,
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Meta learning error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _scrape_account_ads(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scrape ads from Meta account immediately."""
        if not self.meta_access_token:
            return {"error": "META_ACCESS_TOKEN not configured"}

        try:
            page_id = input_data.get("page_id")
            limit = input_data.get("limit", 100)

            # Use Ads Library API
            url = f"{self.base_url}/ads_archive"
            params = {
                "access_token": self.meta_access_token,
                "search_page_ids": page_id if page_id else None,
                "ad_active_status": "ALL",
                "fields": ",".join([
                    "id",
                    "ad_creative_bodies",
                    "ad_creative_link_captions",
                    "ad_creative_link_titles",
                    "page_name",
                    "publisher_platforms",
                    "estimated_audience_size",
                    "ad_snapshot_url",
                ]),
                "limit": limit,
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            ads = data.get("data", [])

            # Save scraped ads
            if self.client:
                for ad in ads:
                    self.client.table("agent_memory").insert({
                        "key": f"scraped_ad_{ad.get('id')}",
                        "value": ad,
                        "type": "scraped_ad",
                        "metadata": {
                            "source": "meta_ads_library",
                            "page_id": page_id,
                            "scraped_at": datetime.now().isoformat(),
                        },
                    }).execute()

            logger.info(f"✅ Scraped {len(ads)} ads from account")

            return {
                "ads_scraped": len(ads),
                "ads": ads[:10],  # Return first 10
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Ad scraping error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _recalculate_ads(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recalculate ad performance and optimize."""
        try:
            campaign_id = input_data.get("campaign_id")
            ad_ids = input_data.get("ad_ids", [])

            # Fetch latest performance data
            if self.meta_access_token and self.meta_ad_account_id:
                url = f"{self.base_url}/{self.meta_ad_account_id}/insights"
                params = {
                    "access_token": self.meta_access_token,
                    "fields": "spend,impressions,clicks,ctr,cpc,actions,action_values",
                    "level": "ad",
                    "time_range": {
                        "since": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                        "until": datetime.now().strftime("%Y-%m-%d"),
                    },
                }

                if ad_ids:
                    params["filtering"] = [{"field": "ad.id", "operator": "IN", "value": ad_ids}]

                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                ads = data.get("data", [])

                # Recalculate metrics
                recalculated = []
                for ad in ads:
                    spend = float(ad.get("spend", 0))
                    clicks = int(ad.get("clicks", 0))
                    impressions = int(ad.get("impressions", 0))

                    new_cpc = spend / clicks if clicks > 0 else 0
                    new_ctr = (clicks / impressions * 100) if impressions > 0 else 0

                    recalculated.append({
                        "ad_id": ad.get("ad_id"),
                        "ad_name": ad.get("ad_name"),
                        "spend": spend,
                        "clicks": clicks,
                        "impressions": impressions,
                        "recalculated_cpc": new_cpc,
                        "recalculated_ctr": new_ctr,
                        "recommendation": "pause" if new_cpc > 5.0 else "continue",
                    })

                return {
                    "ads_recalculated": len(recalculated),
                    "recalculated_ads": recalculated,
                    "thinking": thinking.get("final_reasoning"),
                }

            return {"error": "Meta credentials not configured"}

        except Exception as e:
            logger.error(f"Recalculation error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _copy_video_patterns(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Copy winning video patterns from Meta ads."""
        try:
            # Get winning ads from memory
            if self.client:
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .eq("type", "scraped_ad")
                    .order("created_at", desc=True)
                    .limit(50)
                    .execute()
                )

                ads = result.data or []

                # Extract video patterns
                video_patterns = []
                for ad in ads:
                    ad_data = ad.get("value", {})
                    if "video" in str(ad_data).lower() or "reels" in str(ad_data).lower():
                        pattern = {
                            "ad_id": ad.get("key", "").replace("scraped_ad_", ""),
                            "creative_body": ad_data.get("ad_creative_bodies", [""])[0] if ad_data.get("ad_creative_bodies") else "",
                            "platform": ad_data.get("publisher_platforms", []),
                            "pattern_type": "video",
                        }
                        video_patterns.append(pattern)

                # Save patterns
                if video_patterns:
                    self.client.table("agent_memory").insert({
                        "key": f"video_patterns_{datetime.now().isoformat()}",
                        "value": {"patterns": video_patterns},
                        "type": "video_patterns",
                    }).execute()

                return {
                    "patterns_copied": len(video_patterns),
                    "video_patterns": video_patterns[:10],
                    "thinking": thinking.get("final_reasoning"),
                }

            return {"error": "Supabase client not available"}

        except Exception as e:
            logger.error(f"Video pattern copying error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _find_winning_patterns(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find every winning pattern from Meta ads."""
        try:
            # Get all Meta learning data
            if self.client:
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .in_("type", ["meta_learning", "scraped_ad", "video_patterns"])
                    .order("created_at", desc=True)
                    .limit(200)
                    .execute()
                )

                all_data = result.data or []

                # Analyze patterns
                patterns = {
                    "high_ctr_patterns": [],
                    "high_roas_patterns": [],
                    "video_patterns": [],
                    "copy_patterns": [],
                    "creative_patterns": [],
                }

                for item in all_data:
                    value = item.get("value", {})
                    if isinstance(value, dict):
                        if "patterns" in value:
                            patterns["high_ctr_patterns"].extend(value.get("patterns", []))
                        if "video_patterns" in value:
                            patterns["video_patterns"].extend(value.get("video_patterns", []))

                # Save all patterns
                self.client.table("agent_memory").insert({
                    "key": f"all_winning_patterns_{datetime.now().isoformat()}",
                    "value": patterns,
                    "type": "all_winning_patterns",
                }).execute()

                return {
                    "patterns_found": sum(len(p) for p in patterns.values()),
                    "patterns": patterns,
                    "thinking": thinking.get("final_reasoning"),
                }

            return {"error": "Supabase client not available"}

        except Exception as e:
            logger.error(f"Pattern finding error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _analyze_meta_performance(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze Meta ad performance."""
        return await self._learn_from_meta(input_data, thinking)

    def _extract_patterns(self, ads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns from Meta ads."""
        patterns = []

        for ad in ads:
            spend = float(ad.get("spend", 0))
            clicks = int(ad.get("clicks", 0))
            impressions = int(ad.get("impressions", 0))
            ctr = float(ad.get("ctr", 0))

            if ctr > 2.0 or spend > 100:  # High performing
                pattern = {
                    "ad_id": ad.get("ad_id"),
                    "ad_name": ad.get("ad_name"),
                    "ctr": ctr,
                    "spend": spend,
                    "clicks": clicks,
                    "pattern_type": "high_performer",
                }
                patterns.append(pattern)

        return patterns

