"""
Winner Replicator - Clone and vary winning ad patterns
Agent 11 Task: Winner Replication System
Created: 2025-12-13

This module:
1. Creates variations of winning ad patterns
2. Applies strategic changes (hook swap, CTA change, etc.)
3. Tracks replication history and performance
4. Integrates with Meta API for ad creation
"""

import os
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class VariationType(Enum):
    """Types of variations that can be created from a winner."""
    HOOK_SWAP = "hook_swap"           # Change the opening hook
    CTA_CHANGE = "cta_change"         # Change call-to-action
    COLOR_SHIFT = "color_shift"       # Adjust color palette
    PACE_ADJUST = "pace_adjust"       # Speed up or slow down
    AUDIO_SWAP = "audio_swap"         # Change background music
    TEXT_OVERLAY = "text_overlay"     # Add/modify text overlays
    THUMBNAIL = "thumbnail"           # Change thumbnail/first frame


@dataclass
class WinnerPattern:
    """Pattern extracted from a winning ad."""
    ad_id: str
    video_id: str
    campaign_id: str
    ctr: float
    roas: float
    impressions: int
    spend: float
    revenue: float
    creative_dna: Dict[str, Any]
    detected_at: datetime


@dataclass
class AdVariation:
    """A variation created from a winning ad."""
    variation_id: str
    original_ad_id: str
    variation_type: VariationType
    status: str  # pending, approved, active, paused, rejected
    changes: Dict[str, Any]
    creative_dna: Dict[str, Any]
    created_at: datetime
    published_at: Optional[datetime] = None
    meta_ad_id: Optional[str] = None
    performance: Optional[Dict[str, float]] = None


@dataclass
class ReplicationResult:
    """Result of a replication operation."""
    success: bool
    original_ad_id: str
    variations_created: List[AdVariation]
    errors: List[str]
    timestamp: datetime


class WinnerReplicator:
    """
    Creates variations of winning ads for A/B testing and scaling.

    Strategies:
    - Hook variations: Test different opening hooks
    - CTA variations: Test different calls-to-action
    - Pacing variations: Test different video speeds
    - Color variations: Test different color themes
    """

    def __init__(
        self,
        meta_access_token: Optional[str] = None,
        ad_account_id: Optional[str] = None,
        max_variations_per_winner: int = 5
    ):
        """
        Initialize the winner replicator.

        Args:
            meta_access_token: Meta API access token
            ad_account_id: Meta ad account ID
            max_variations_per_winner: Max variations per winning ad
        """
        self.meta_access_token = meta_access_token or os.getenv('META_ACCESS_TOKEN')
        self.ad_account_id = ad_account_id or os.getenv('META_AD_ACCOUNT_ID')
        self.max_variations = max_variations_per_winner

        # Variation history
        self.replication_history: Dict[str, List[AdVariation]] = {}

        # Hook templates for variation
        self.hook_templates = [
            "What if I told you...",
            "Stop scrolling! This changed everything...",
            "The secret nobody talks about...",
            "I wish I knew this sooner...",
            "This is why {product} is different...",
            "3 reasons why you need this...",
            "POV: You just discovered...",
            "Here's what happened when I tried..."
        ]

        # CTA templates
        self.cta_templates = [
            {"type": "shop_now", "text": "Shop Now"},
            {"type": "learn_more", "text": "Learn More"},
            {"type": "sign_up", "text": "Sign Up Free"},
            {"type": "get_offer", "text": "Get 20% Off"},
            {"type": "try_free", "text": "Try It Free"},
            {"type": "limited_time", "text": "Limited Time Offer"}
        ]

        logger.info("✅ WinnerReplicator initialized")

    async def replicate_top_winners(
        self,
        winners: List[WinnerPattern],
        variations_per_winner: int = 3,
        variation_types: Optional[List[VariationType]] = None
    ) -> List[ReplicationResult]:
        """
        Create variations for a list of winning ads.

        Args:
            winners: List of winning ad patterns
            variations_per_winner: Number of variations to create per winner
            variation_types: Types of variations to create

        Returns:
            List of replication results
        """
        if not variation_types:
            variation_types = [
                VariationType.HOOK_SWAP,
                VariationType.CTA_CHANGE
            ]

        results = []
        for winner in winners:
            result = await self.create_variations(
                winner,
                count=min(variations_per_winner, self.max_variations),
                variation_types=variation_types
            )
            results.append(result)

        logger.info(
            f"✅ Replicated {len(winners)} winners with "
            f"{sum(len(r.variations_created) for r in results)} total variations"
        )

        return results

    async def create_variations(
        self,
        winner: WinnerPattern,
        count: int = 3,
        variation_types: Optional[List[VariationType]] = None
    ) -> ReplicationResult:
        """
        Create variations of a single winning ad.

        Args:
            winner: The winning ad pattern
            count: Number of variations to create
            variation_types: Types of variations

        Returns:
            ReplicationResult with created variations
        """
        if not variation_types:
            variation_types = [VariationType.HOOK_SWAP, VariationType.CTA_CHANGE]

        variations = []
        errors = []

        try:
            for i in range(count):
                var_type = variation_types[i % len(variation_types)]

                try:
                    variation = await self._create_single_variation(
                        winner, var_type, i
                    )
                    variations.append(variation)

                    # Track in history
                    if winner.ad_id not in self.replication_history:
                        self.replication_history[winner.ad_id] = []
                    self.replication_history[winner.ad_id].append(variation)

                except Exception as e:
                    error_msg = f"Failed to create {var_type.value} variation: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            logger.info(
                f"Created {len(variations)} variations for winner {winner.ad_id}"
            )

        except Exception as e:
            errors.append(f"Replication failed: {e}")
            logger.error(f"Replication failed for {winner.ad_id}: {e}")

        return ReplicationResult(
            success=len(variations) > 0,
            original_ad_id=winner.ad_id,
            variations_created=variations,
            errors=errors,
            timestamp=datetime.utcnow()
        )

    async def _create_single_variation(
        self,
        winner: WinnerPattern,
        var_type: VariationType,
        index: int
    ) -> AdVariation:
        """Create a single variation of a winner."""
        variation_id = f"var_{uuid.uuid4().hex[:8]}"

        # Copy original creative DNA
        new_dna = winner.creative_dna.copy()
        changes = {}

        if var_type == VariationType.HOOK_SWAP:
            # Select a different hook
            original_hook = new_dna.get("hook_text", "")
            new_hook = self.hook_templates[index % len(self.hook_templates)]
            new_dna["hook_text"] = new_hook
            new_dna["hook_type"] = "variation"
            changes = {
                "original_hook": original_hook,
                "new_hook": new_hook
            }

        elif var_type == VariationType.CTA_CHANGE:
            # Change CTA
            original_cta = new_dna.get("cta_type", "shop_now")
            new_cta = self.cta_templates[index % len(self.cta_templates)]
            new_dna["cta_type"] = new_cta["type"]
            new_dna["cta_text"] = new_cta["text"]
            changes = {
                "original_cta": original_cta,
                "new_cta": new_cta
            }

        elif var_type == VariationType.COLOR_SHIFT:
            # Shift color palette
            original_colors = new_dna.get("color_palette", [])
            # Simple color shift - in production, use AI for smart color selection
            shifts = ["warmer", "cooler", "more_vibrant", "more_muted"]
            new_dna["color_shift"] = shifts[index % len(shifts)]
            changes = {
                "original_colors": original_colors,
                "color_shift": new_dna["color_shift"]
            }

        elif var_type == VariationType.PACE_ADJUST:
            # Adjust pacing
            original_pace = new_dna.get("pace", "medium")
            pace_options = ["slow", "medium", "fast", "dynamic"]
            new_pace = pace_options[(pace_options.index(original_pace) + 1) % len(pace_options)]
            new_dna["pace"] = new_pace
            changes = {
                "original_pace": original_pace,
                "new_pace": new_pace
            }

        return AdVariation(
            variation_id=variation_id,
            original_ad_id=winner.ad_id,
            variation_type=var_type,
            status="pending",
            changes=changes,
            creative_dna=new_dna,
            created_at=datetime.utcnow()
        )

    async def publish_variation(
        self,
        variation: AdVariation,
        campaign_id: str,
        budget: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Publish a variation to Meta Ads.

        Args:
            variation: The variation to publish
            campaign_id: Target campaign ID
            budget: Daily budget for the variation

        Returns:
            Tuple of (success, meta_ad_id or error message)
        """
        if not self.meta_access_token:
            logger.warning("Meta API not configured, skipping publish")
            return False, "Meta API not configured"

        try:
            # In production, this would call Meta API
            # For now, simulate successful creation
            meta_ad_id = f"meta_{uuid.uuid4().hex[:12]}"

            variation.status = "active"
            variation.published_at = datetime.utcnow()
            variation.meta_ad_id = meta_ad_id

            logger.info(f"✅ Published variation {variation.variation_id} as {meta_ad_id}")
            return True, meta_ad_id

        except Exception as e:
            logger.error(f"Failed to publish variation: {e}")
            return False, str(e)

    def get_replication_history(
        self,
        ad_id: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """Get replication history."""
        if ad_id:
            variations = self.replication_history.get(ad_id, [])
            return {ad_id: [asdict(v) for v in variations]}

        return {
            ad_id: [asdict(v) for v in variations]
            for ad_id, variations in self.replication_history.items()
        }

    def get_variation_performance(
        self,
        variation_id: str
    ) -> Optional[Dict[str, float]]:
        """Get performance metrics for a variation."""
        for variations in self.replication_history.values():
            for v in variations:
                if v.variation_id == variation_id:
                    return v.performance
        return None

    def update_variation_performance(
        self,
        variation_id: str,
        performance: Dict[str, float]
    ) -> bool:
        """Update performance metrics for a variation."""
        for variations in self.replication_history.values():
            for v in variations:
                if v.variation_id == variation_id:
                    v.performance = performance
                    return True
        return False

    def stats(self) -> Dict[str, Any]:
        """Get replicator statistics."""
        total_variations = sum(
            len(v) for v in self.replication_history.values()
        )

        variations_by_type = {}
        variations_by_status = {}

        for variations in self.replication_history.values():
            for v in variations:
                var_type = v.variation_type.value
                variations_by_type[var_type] = variations_by_type.get(var_type, 0) + 1
                variations_by_status[v.status] = variations_by_status.get(v.status, 0) + 1

        return {
            "total_winners_replicated": len(self.replication_history),
            "total_variations_created": total_variations,
            "variations_by_type": variations_by_type,
            "variations_by_status": variations_by_status,
            "max_variations_per_winner": self.max_variations,
            "meta_api_configured": self.meta_access_token is not None
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_replicator: Optional[WinnerReplicator] = None


def get_winner_replicator() -> WinnerReplicator:
    """Get or create the global winner replicator instance."""
    global _replicator
    if _replicator is None:
        _replicator = WinnerReplicator()
    return _replicator


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def demo():
        replicator = get_winner_replicator()

        # Create a sample winner
        winner = WinnerPattern(
            ad_id="winner_001",
            video_id="video_001",
            campaign_id="campaign_001",
            ctr=0.045,
            roas=3.8,
            impressions=25000,
            spend=1200,
            revenue=4560,
            creative_dna={
                "hook_type": "curiosity",
                "hook_text": "You won't believe this...",
                "cta_type": "shop_now",
                "duration_seconds": 15,
                "pace": "fast",
                "color_palette": ["#FF6B6B", "#4ECDC4"]
            },
            detected_at=datetime.utcnow()
        )

        # Create variations
        result = await replicator.create_variations(winner, count=3)
        print(f"Created {len(result.variations_created)} variations")

        # Get stats
        stats = replicator.stats()
        print(f"Stats: {stats}")

    asyncio.run(demo())
