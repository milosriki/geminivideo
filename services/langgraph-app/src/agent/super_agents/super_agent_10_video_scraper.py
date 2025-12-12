"""Super Agent 10: Video Scraper - Scrapes videos from accounts, copies patterns, finds winning videos."""

from typing import Any, Dict, List, Optional
import logging
import os
import requests
from datetime import datetime

from agent.super_agents.base_super_agent import SuperAgent
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class VideoScraperAgent(SuperAgent):
    """Expert in video scraping - scrapes videos from accounts, copies patterns, finds winning videos."""

    def __init__(self, **kwargs):
        super().__init__(
            name="VideoScraperAgent",
            description=(
                "Video scraper expert. Scrapes videos from Meta accounts immediately, "
                "copies winning video patterns, finds top-performing videos, and extracts "
                "patterns for video ad creation."
            ),
            domains=[
                "Video Scraping",
                "Pattern Extraction",
                "Video Analysis",
                "Winning Video Identification",
                "Creative Copying",
            ],
            thinking_steps=4,
            **kwargs,
        )
        self.meta_access_token = os.getenv("META_ACCESS_TOKEN")
        self.base_url = "https://graph.facebook.com/v19.0"
        self.client = supabase_client.client

    async def _execute_with_reasoning(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        thinking: Dict[str, Any],
    ) -> Any:
        """Execute video scraping operations."""
        operation = input_data.get("operation", "scrape_videos")

        if operation == "scrape_videos":
            return await self._scrape_videos(input_data, thinking)
        elif operation == "copy_video_patterns":
            return await self._copy_video_patterns(input_data, thinking)
        elif operation == "find_winning_videos":
            return await self._find_winning_videos(input_data, thinking)
        elif operation == "extract_patterns":
            return await self._extract_patterns(input_data, thinking)
        else:
            return {
                "operation": operation,
                "thinking": thinking.get("final_reasoning"),
                "status": "processed",
            }

    async def _scrape_videos(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scrape videos from Meta account immediately."""
        if not self.meta_access_token:
            return {"error": "META_ACCESS_TOKEN not configured"}

        try:
            page_id = input_data.get("page_id")
            limit = input_data.get("limit", 50)

            # Scrape videos from page
            url = f"{self.base_url}/{page_id}/videos"
            params = {
                "access_token": self.meta_access_token,
                "fields": ",".join([
                    "id",
                    "description",
                    "created_time",
                    "length",
                    "source",
                    "picture",
                    "likes.summary(true)",
                    "comments.summary(true)",
                    "shares.summary(true)",
                ]),
                "limit": limit,
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            videos = data.get("data", [])

            # Save scraped videos
            scraped_videos = []
            if self.client:
                for video in videos:
                    video_data = {
                        "video_id": video.get("id"),
                        "description": video.get("description", ""),
                        "created_time": video.get("created_time"),
                        "length": video.get("length", 0),
                        "source": video.get("source"),
                        "picture": video.get("picture"),
                        "engagement": {
                            "likes": video.get("likes", {}).get("summary", {}).get("total_count", 0),
                            "comments": video.get("comments", {}).get("summary", {}).get("total_count", 0),
                            "shares": video.get("shares", {}).get("summary", {}).get("total_count", 0),
                        },
                    }

                    self.client.table("agent_memory").insert({
                        "key": f"scraped_video_{video.get('id')}",
                        "value": video_data,
                        "type": "scraped_video",
                        "metadata": {
                            "source": "meta_page",
                            "page_id": page_id,
                            "scraped_at": datetime.now().isoformat(),
                        },
                    }).execute()

                    scraped_videos.append(video_data)

            logger.info(f"✅ Scraped {len(videos)} videos from page {page_id}")

            return {
                "videos_scraped": len(videos),
                "videos": scraped_videos[:10],  # Return first 10
                "thinking": thinking.get("final_reasoning"),
            }

        except Exception as e:
            logger.error(f"Video scraping error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _copy_video_patterns(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Copy winning video patterns."""
        try:
            # Get winning videos from memory
            if self.client:
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .eq("type", "scraped_video")
                    .order("created_at", desc=True)
                    .limit(100)
                    .execute()
                )

                videos = result.data or []

                # Extract patterns from high-engagement videos
                patterns = []
                for video_item in videos:
                    video_data = video_item.get("value", {})
                    engagement = video_data.get("engagement", {})
                    total_engagement = (
                        engagement.get("likes", 0) +
                        engagement.get("comments", 0) +
                        engagement.get("shares", 0)
                    )

                    if total_engagement > 100:  # High engagement threshold
                        pattern = {
                            "video_id": video_data.get("video_id"),
                            "description": video_data.get("description", "")[:200],
                            "length": video_data.get("length", 0),
                            "engagement": total_engagement,
                            "pattern_type": "high_engagement",
                        }
                        patterns.append(pattern)

                # Save patterns
                if patterns:
                    self.client.table("agent_memory").insert({
                        "key": f"video_patterns_{datetime.now().isoformat()}",
                        "value": {"patterns": patterns},
                        "type": "video_patterns",
                    }).execute()

                return {
                    "patterns_copied": len(patterns),
                    "patterns": patterns[:10],
                    "thinking": thinking.get("final_reasoning"),
                }

            return {"error": "Supabase client not available"}

        except Exception as e:
            logger.error(f"Pattern copying error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _find_winning_videos(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Find top-performing winning videos."""
        try:
            if self.client:
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .eq("type", "scraped_video")
                    .order("created_at", desc=True)
                    .limit(200)
                    .execute()
                )

                videos = result.data or []

                # Rank by engagement
                ranked_videos = []
                for video_item in videos:
                    video_data = video_item.get("value", {})
                    engagement = video_data.get("engagement", {})
                    total_engagement = (
                        engagement.get("likes", 0) +
                        engagement.get("comments", 0) +
                        engagement.get("shares", 0) * 2  # Shares weighted more
                    )

                    ranked_videos.append({
                        "video_id": video_data.get("video_id"),
                        "description": video_data.get("description", "")[:200],
                        "engagement_score": total_engagement,
                        "video_data": video_data,
                    })

                # Sort by engagement
                ranked_videos.sort(key=lambda x: x["engagement_score"], reverse=True)
                winning_videos = ranked_videos[:10]  # Top 10

                return {
                    "winning_videos": winning_videos,
                    "total_analyzed": len(videos),
                    "thinking": thinking.get("final_reasoning"),
                }

            return {"error": "Supabase client not available"}

        except Exception as e:
            logger.error(f"Winning video finding error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

    async def _extract_patterns(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract patterns from scraped videos."""
        try:
            if self.client:
                result = (
                    self.client.table("agent_memory")
                    .select("*")
                    .eq("type", "scraped_video")
                    .order("created_at", desc=True)
                    .limit(100)
                    .execute()
                )

                videos = result.data or []

                # Extract common patterns
                patterns = {
                    "common_lengths": [],
                    "common_themes": [],
                    "high_engagement_elements": [],
                }

                for video_item in videos:
                    video_data = video_item.get("value", {})
                    length = video_data.get("length", 0)
                    description = video_data.get("description", "")

                    if length > 0:
                        patterns["common_lengths"].append(length)

                    if description:
                        # Extract keywords (simplified)
                        words = description.lower().split()
                        patterns["common_themes"].extend(words[:5])

                # Find most common
                from collections import Counter
                patterns["most_common_length"] = Counter(patterns["common_lengths"]).most_common(1)[0][0] if patterns["common_lengths"] else 0
                patterns["most_common_themes"] = [word for word, count in Counter(patterns["common_themes"]).most_common(10)]

                return {
                    "patterns": patterns,
                    "videos_analyzed": len(videos),
                    "thinking": thinking.get("final_reasoning"),
                }

            return {"error": "Supabase client not available"}

        except Exception as e:
            logger.error(f"Pattern extraction error: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

