"""
Unified Conversion Hub - Single Source of Truth for All Conversions

This module provides a centralized system for tracking, deduplicating, and
attributing conversions from multiple sources (Meta CAPI, Meta Pixel, HubSpot,
AnyTrack). It supports multiple attribution models and provides true ROAS
calculation across all channels.

Agent 15 of 30 - ULTIMATE Production Plan
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from collections import defaultdict, Counter
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

from db.redis_client import set_cache, get_cache, delete_cache
from db.models import UnifiedConversion as UnifiedConversionModel
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


class ConversionSource(Enum):
    """Sources from which conversions can be tracked."""
    META_CAPI = "meta_capi"
    META_PIXEL = "meta_pixel"
    HUBSPOT = "hubspot"
    ANYTRACK = "anytrack"
    MANUAL = "manual"


class AttributionModel(Enum):
    """Attribution models for conversion attribution."""
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"


@dataclass
class Touchpoint:
    """Represents a single touchpoint in the customer journey."""
    source: str
    campaign_id: str
    ad_id: Optional[str]
    timestamp: datetime
    channel: str  # facebook, google, email, organic, etc.
    interaction_type: str  # click, view, impression

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'source': self.source,
            'campaign_id': self.campaign_id,
            'ad_id': self.ad_id,
            'timestamp': self.timestamp.isoformat(),
            'channel': self.channel,
            'interaction_type': self.interaction_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Touchpoint':
        """Create from dictionary."""
        return cls(
            source=data['source'],
            campaign_id=data['campaign_id'],
            ad_id=data.get('ad_id'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            channel=data['channel'],
            interaction_type=data['interaction_type']
        )


@dataclass
class UnifiedConversion:
    """Unified conversion record from all sources."""
    id: str
    external_ids: Dict[str, str]  # source -> external_id mapping
    contact_email: Optional[str]
    contact_id: Optional[str]
    value: float
    currency: str
    conversion_type: str
    sources: List[ConversionSource]
    touchpoints: List[Touchpoint]
    attributed_campaign_id: Optional[str]
    attributed_ad_id: Optional[str]
    attribution_model: AttributionModel
    first_touch_at: datetime
    converted_at: datetime
    is_offline: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'external_ids': self.external_ids,
            'contact_email': self.contact_email,
            'contact_id': self.contact_id,
            'value': self.value,
            'currency': self.currency,
            'conversion_type': self.conversion_type,
            'sources': [s.value for s in self.sources],
            'touchpoints': [tp.to_dict() for tp in self.touchpoints],
            'attributed_campaign_id': self.attributed_campaign_id,
            'attributed_ad_id': self.attributed_ad_id,
            'attribution_model': self.attribution_model.value,
            'first_touch_at': self.first_touch_at.isoformat(),
            'converted_at': self.converted_at.isoformat(),
            'is_offline': self.is_offline,
            'metadata': self.metadata
        }


class ConversionHub:
    """Unified conversion tracking across all sources."""

    def __init__(
        self,
        meta_capi_client,
        hubspot_client,
        anytrack_client,
        database_session
    ):
        """
        Initialize with all integration clients.

        Args:
            meta_capi_client: Meta Conversions API client
            hubspot_client: HubSpot API client
            anytrack_client: AnyTrack API client
            database_session: SQLAlchemy AsyncSession for database operations
        """
        self.meta_capi = meta_capi_client
        self.hubspot = hubspot_client
        self.anytrack = anytrack_client
        self.db_session = database_session

        # Redis cache TTL (1 hour for hot data)
        self.cache_ttl = 3600

        logger.info("ConversionHub initialized with PostgreSQL + Redis")

    # ========== Conversion Ingestion ==========

    def ingest_conversion(
        self,
        source: ConversionSource,
        event_data: Dict[str, Any]
    ) -> str:
        """
        Ingest conversion from any source, return unified_conversion_id.

        Args:
            source: Source of the conversion
            event_data: Raw event data from the source

        Returns:
            Unified conversion ID

        Raises:
            ValueError: If source is invalid or data is malformed
        """
        try:
            if source == ConversionSource.META_CAPI:
                return self.ingest_from_meta_capi(event_data)
            elif source == ConversionSource.META_PIXEL:
                return self.ingest_from_meta_pixel(event_data)
            elif source == ConversionSource.HUBSPOT:
                return self.ingest_from_hubspot(event_data)
            elif source == ConversionSource.ANYTRACK:
                return self.ingest_from_anytrack(event_data)
            else:
                raise ValueError(f"Unsupported conversion source: {source}")
        except Exception as e:
            logger.error(f"Failed to ingest conversion from {source}: {e}")
            raise

    def ingest_from_meta_capi(self, event_data: Dict[str, Any]) -> str:
        """Ingest conversion from Meta Conversions API."""
        try:
            conversion = UnifiedConversion(
                id=self._generate_conversion_id(event_data),
                external_ids={'meta_capi': event_data.get('event_id', '')},
                contact_email=event_data.get('user_data', {}).get('em'),
                contact_id=None,
                value=float(event_data.get('custom_data', {}).get('value', 0)),
                currency=event_data.get('custom_data', {}).get('currency', 'USD'),
                conversion_type=event_data.get('event_name', 'Purchase'),
                sources=[ConversionSource.META_CAPI],
                touchpoints=[],
                attributed_campaign_id=event_data.get('custom_data', {}).get('campaign_id'),
                attributed_ad_id=event_data.get('custom_data', {}).get('ad_id'),
                attribution_model=AttributionModel.LAST_TOUCH,
                first_touch_at=datetime.fromtimestamp(event_data.get('event_time', 0)),
                converted_at=datetime.fromtimestamp(event_data.get('event_time', 0)),
                is_offline=False,
                metadata=event_data.get('custom_data', {})
            )

            self._store_conversion(conversion)
            logger.info(f"Ingested Meta CAPI conversion: {conversion.id}")
            return conversion.id
        except Exception as e:
            logger.error(f"Failed to ingest Meta CAPI conversion: {e}")
            raise

    def ingest_from_meta_pixel(self, event_data: Dict[str, Any]) -> str:
        """Ingest conversion from Meta Pixel."""
        try:
            conversion = UnifiedConversion(
                id=self._generate_conversion_id(event_data),
                external_ids={'meta_pixel': event_data.get('fbp', '')},
                contact_email=event_data.get('user_data', {}).get('em'),
                contact_id=None,
                value=float(event_data.get('value', 0)),
                currency=event_data.get('currency', 'USD'),
                conversion_type=event_data.get('event_name', 'Purchase'),
                sources=[ConversionSource.META_PIXEL],
                touchpoints=[],
                attributed_campaign_id=event_data.get('campaign_id'),
                attributed_ad_id=event_data.get('ad_id'),
                attribution_model=AttributionModel.LAST_TOUCH,
                first_touch_at=datetime.fromtimestamp(event_data.get('event_time', 0)),
                converted_at=datetime.fromtimestamp(event_data.get('event_time', 0)),
                is_offline=False,
                metadata=event_data
            )

            self._store_conversion(conversion)
            logger.info(f"Ingested Meta Pixel conversion: {conversion.id}")
            return conversion.id
        except Exception as e:
            logger.error(f"Failed to ingest Meta Pixel conversion: {e}")
            raise

    def ingest_from_hubspot(self, deal_data: Dict[str, Any]) -> str:
        """Ingest conversion from HubSpot deal."""
        try:
            conversion = UnifiedConversion(
                id=self._generate_conversion_id(deal_data),
                external_ids={'hubspot': str(deal_data.get('id', ''))},
                contact_email=deal_data.get('properties', {}).get('contact_email'),
                contact_id=deal_data.get('properties', {}).get('contact_id'),
                value=float(deal_data.get('properties', {}).get('amount', 0)),
                currency=deal_data.get('properties', {}).get('currency', 'USD'),
                conversion_type='Deal',
                sources=[ConversionSource.HUBSPOT],
                touchpoints=[],
                attributed_campaign_id=deal_data.get('properties', {}).get('campaign_id'),
                attributed_ad_id=None,
                attribution_model=AttributionModel.FIRST_TOUCH,
                first_touch_at=datetime.fromisoformat(
                    deal_data.get('properties', {}).get('createdate', datetime.now().isoformat())
                ),
                converted_at=datetime.fromisoformat(
                    deal_data.get('properties', {}).get('closedate', datetime.now().isoformat())
                ),
                is_offline=True,
                metadata=deal_data.get('properties', {})
            )

            self._store_conversion(conversion)
            logger.info(f"Ingested HubSpot conversion: {conversion.id}")
            return conversion.id
        except Exception as e:
            logger.error(f"Failed to ingest HubSpot conversion: {e}")
            raise

    def ingest_from_anytrack(self, conversion_data: Dict[str, Any]) -> str:
        """Ingest conversion from AnyTrack."""
        try:
            conversion = UnifiedConversion(
                id=self._generate_conversion_id(conversion_data),
                external_ids={'anytrack': conversion_data.get('conversion_id', '')},
                contact_email=conversion_data.get('email'),
                contact_id=conversion_data.get('contact_id'),
                value=float(conversion_data.get('revenue', 0)),
                currency=conversion_data.get('currency', 'USD'),
                conversion_type=conversion_data.get('event_type', 'Purchase'),
                sources=[ConversionSource.ANYTRACK],
                touchpoints=[],
                attributed_campaign_id=conversion_data.get('campaign_id'),
                attributed_ad_id=conversion_data.get('ad_id'),
                attribution_model=AttributionModel.LAST_TOUCH,
                first_touch_at=datetime.fromisoformat(
                    conversion_data.get('timestamp', datetime.now().isoformat())
                ),
                converted_at=datetime.fromisoformat(
                    conversion_data.get('timestamp', datetime.now().isoformat())
                ),
                is_offline=False,
                metadata=conversion_data
            )

            self._store_conversion(conversion)
            logger.info(f"Ingested AnyTrack conversion: {conversion.id}")
            return conversion.id
        except Exception as e:
            logger.error(f"Failed to ingest AnyTrack conversion: {e}")
            raise

    # ========== Deduplication ==========

    def deduplicate_conversions(
        self,
        window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Deduplicate conversions across sources.

        Args:
            window_hours: Time window for deduplication

        Returns:
            Deduplication statistics
        """
        try:
            duplicates_found = 0
            conversions_merged = 0

            # Get all conversions within window
            cutoff_time = datetime.now() - timedelta(hours=window_hours)
            recent_conversions = self._get_conversions_since(cutoff_time)

            # Group by dedup key
            dedup_groups: Dict[str, List[UnifiedConversion]] = defaultdict(list)
            for conv in recent_conversions:
                if conv.contact_email and conv.value > 0:
                    key = self._generate_dedup_key(
                        conv.contact_email,
                        conv.value,
                        conv.converted_at
                    )
                    dedup_groups[key].append(conv)

            # Merge duplicates
            for key, group in dedup_groups.items():
                if len(group) > 1:
                    duplicates_found += len(group) - 1
                    conversion_ids = [c.id for c in group]
                    self.merge_duplicates(conversion_ids)
                    conversions_merged += 1

            result = {
                'duplicates_found': duplicates_found,
                'conversions_merged': conversions_merged,
                'window_hours': window_hours,
                'processed_at': datetime.now().isoformat()
            }

            logger.info(f"Deduplication complete: {result}")
            return result
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            raise

    def _generate_dedup_key(
        self,
        email: str,
        value: float,
        timestamp: datetime
    ) -> str:
        """Generate deduplication key."""
        # Round timestamp to nearest hour and value to 2 decimals
        hour_key = timestamp.replace(minute=0, second=0, microsecond=0).isoformat()
        value_key = f"{value:.2f}"

        # Create hash
        key_string = f"{email.lower()}:{value_key}:{hour_key}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def find_duplicates(
        self,
        conversion: UnifiedConversion
    ) -> List[UnifiedConversion]:
        """Find potential duplicate conversions."""
        try:
            duplicates = []

            if not conversion.contact_email:
                return duplicates

            # Search within 24-hour window
            time_window = timedelta(hours=24)
            start_time = conversion.converted_at - time_window
            end_time = conversion.converted_at + time_window

            # Get candidates
            candidates = self._get_conversions_in_range(start_time, end_time)

            for candidate in candidates:
                if candidate.id == conversion.id:
                    continue

                # Check for duplicate criteria
                if (candidate.contact_email == conversion.contact_email and
                    abs(candidate.value - conversion.value) < 0.01 and
                    candidate.currency == conversion.currency):
                    duplicates.append(candidate)

            return duplicates
        except Exception as e:
            logger.error(f"Failed to find duplicates: {e}")
            return []

    def merge_duplicates(
        self,
        conversion_ids: List[str]
    ) -> str:
        """
        Merge duplicate conversions into one.

        Args:
            conversion_ids: List of conversion IDs to merge

        Returns:
            ID of the merged conversion
        """
        try:
            if len(conversion_ids) < 2:
                raise ValueError("Need at least 2 conversions to merge")

            # Load all conversions
            conversions = [self._load_conversion(cid) for cid in conversion_ids]
            conversions = [c for c in conversions if c is not None]

            if not conversions:
                raise ValueError("No valid conversions found")

            # Use the oldest conversion as base
            conversions.sort(key=lambda c: c.converted_at)
            primary = conversions[0]

            # Merge data from others
            for conv in conversions[1:]:
                # Merge external IDs
                primary.external_ids.update(conv.external_ids)

                # Merge sources
                for source in conv.sources:
                    if source not in primary.sources:
                        primary.sources.append(source)

                # Merge touchpoints
                for tp in conv.touchpoints:
                    if tp not in primary.touchpoints:
                        primary.touchpoints.append(tp)

                # Update metadata
                primary.metadata.update(conv.metadata)

                # Mark as merged
                self._mark_conversion_merged(conv.id, primary.id)

            # Update primary conversion
            self._store_conversion(primary)

            logger.info(f"Merged {len(conversions)} conversions into {primary.id}")
            return primary.id
        except Exception as e:
            logger.error(f"Failed to merge conversions: {e}")
            raise

    # ========== Attribution ==========

    def attribute_to_campaign(
        self,
        conversion_id: str,
        model: AttributionModel = AttributionModel.LAST_TOUCH
    ) -> Dict[str, float]:
        """
        Attribute conversion to campaigns.

        Args:
            conversion_id: ID of conversion to attribute
            model: Attribution model to use

        Returns:
            Campaign attribution weights {campaign_id: weight}
        """
        try:
            conversion = self._load_conversion(conversion_id)
            if not conversion:
                raise ValueError(f"Conversion not found: {conversion_id}")

            touchpoints = conversion.touchpoints
            if not touchpoints:
                return {}

            # Sort by timestamp
            touchpoints.sort(key=lambda tp: tp.timestamp)

            attribution: Dict[str, float] = defaultdict(float)

            if model == AttributionModel.FIRST_TOUCH:
                attribution[touchpoints[0].campaign_id] = 1.0

            elif model == AttributionModel.LAST_TOUCH:
                attribution[touchpoints[-1].campaign_id] = 1.0

            elif model == AttributionModel.LINEAR:
                weight = 1.0 / len(touchpoints)
                for tp in touchpoints:
                    attribution[tp.campaign_id] += weight

            elif model == AttributionModel.TIME_DECAY:
                # Exponential decay with half-life of 7 days
                total_weight = 0.0
                weights = []

                for tp in touchpoints:
                    days_ago = (conversion.converted_at - tp.timestamp).days
                    weight = 0.5 ** (days_ago / 7.0)
                    weights.append((tp.campaign_id, weight))
                    total_weight += weight

                for campaign_id, weight in weights:
                    attribution[campaign_id] += weight / total_weight

            elif model == AttributionModel.POSITION_BASED:
                # 40% first, 40% last, 20% distributed
                if len(touchpoints) == 1:
                    attribution[touchpoints[0].campaign_id] = 1.0
                elif len(touchpoints) == 2:
                    attribution[touchpoints[0].campaign_id] = 0.5
                    attribution[touchpoints[-1].campaign_id] = 0.5
                else:
                    attribution[touchpoints[0].campaign_id] = 0.4
                    attribution[touchpoints[-1].campaign_id] = 0.4

                    middle_weight = 0.2 / (len(touchpoints) - 2)
                    for tp in touchpoints[1:-1]:
                        attribution[tp.campaign_id] += middle_weight

            # Update conversion
            conversion.attribution_model = model
            if attribution:
                primary_campaign = max(attribution.items(), key=lambda x: x[1])[0]
                conversion.attributed_campaign_id = primary_campaign

            self._store_conversion(conversion)

            return dict(attribution)
        except Exception as e:
            logger.error(f"Attribution failed: {e}")
            raise

    def get_touchpoints(
        self,
        conversion_id: str
    ) -> List[Touchpoint]:
        """Get all touchpoints for conversion."""
        try:
            conversion = self._load_conversion(conversion_id)
            if not conversion:
                return []
            return conversion.touchpoints
        except Exception as e:
            logger.error(f"Failed to get touchpoints: {e}")
            return []

    def add_touchpoint(
        self,
        conversion_id: str,
        touchpoint: Touchpoint
    ) -> bool:
        """Add touchpoint to conversion."""
        try:
            conversion = self._load_conversion(conversion_id)
            if not conversion:
                return False

            conversion.touchpoints.append(touchpoint)

            # Update first touch
            if touchpoint.timestamp < conversion.first_touch_at:
                conversion.first_touch_at = touchpoint.timestamp

            self._store_conversion(conversion)
            logger.info(f"Added touchpoint to conversion {conversion_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add touchpoint: {e}")
            return False

    # ========== ROAS Calculation ==========

    def calculate_true_roas(
        self,
        campaign_id: str,
        ad_spend: float,
        include_offline: bool = True,
        attribution_model: AttributionModel = AttributionModel.LAST_TOUCH,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> float:
        """
        Calculate true ROAS from all conversion sources.

        Args:
            campaign_id: Campaign ID
            ad_spend: Total ad spend
            include_offline: Include offline conversions
            attribution_model: Attribution model to use
            date_range: Optional date range filter

        Returns:
            ROAS value
        """
        try:
            if ad_spend <= 0:
                logger.warning(f"Invalid ad spend: {ad_spend}")
                return 0.0

            # Get all conversions
            conversions = self._get_conversions_by_campaign(
                campaign_id,
                date_range
            )

            # Filter offline if needed
            if not include_offline:
                conversions = [c for c in conversions if not c.is_offline]

            # Calculate attributed revenue
            total_revenue = 0.0
            for conv in conversions:
                attribution = self.attribute_to_campaign(conv.id, attribution_model)
                weight = attribution.get(campaign_id, 0.0)
                total_revenue += conv.value * weight

            roas = total_revenue / ad_spend
            logger.info(f"Campaign {campaign_id} ROAS: {roas:.2f}")
            return roas
        except Exception as e:
            logger.error(f"ROAS calculation failed: {e}")
            return 0.0

    def calculate_blended_roas(
        self,
        campaign_ids: List[str],
        total_spend: float
    ) -> float:
        """Calculate blended ROAS across campaigns."""
        try:
            if total_spend <= 0:
                return 0.0

            total_revenue = 0.0
            for campaign_id in campaign_ids:
                conversions = self._get_conversions_by_campaign(campaign_id)
                total_revenue += sum(c.value for c in conversions)

            return total_revenue / total_spend
        except Exception as e:
            logger.error(f"Blended ROAS calculation failed: {e}")
            return 0.0

    # ========== Conversion Path Analysis ==========

    def get_conversion_path(
        self,
        contact_id: str
    ) -> List[Touchpoint]:
        """Get full conversion path for contact."""
        try:
            conversions = self._get_conversions_by_contact(contact_id)
            all_touchpoints = []

            for conv in conversions:
                all_touchpoints.extend(conv.touchpoints)

            # Sort by timestamp
            all_touchpoints.sort(key=lambda tp: tp.timestamp)
            return all_touchpoints
        except Exception as e:
            logger.error(f"Failed to get conversion path: {e}")
            return []

    def analyze_conversion_paths(
        self,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Analyze common conversion paths."""
        try:
            conversions = self._get_all_conversions(date_range)

            path_patterns = []
            channel_sequences = []

            for conv in conversions:
                if conv.touchpoints:
                    path = [tp.channel for tp in sorted(conv.touchpoints, key=lambda x: x.timestamp)]
                    path_patterns.append(' -> '.join(path))
                    channel_sequences.extend(path)

            # Count patterns
            pattern_counts = Counter(path_patterns)
            channel_counts = Counter(channel_sequences)

            return {
                'total_paths': len(path_patterns),
                'unique_patterns': len(pattern_counts),
                'top_patterns': pattern_counts.most_common(10),
                'top_channels': channel_counts.most_common(10),
                'avg_touchpoints': self.get_avg_touchpoints_to_convert()
            }
        except Exception as e:
            logger.error(f"Path analysis failed: {e}")
            return {}

    def get_avg_touchpoints_to_convert(self) -> float:
        """Get average touchpoints before conversion."""
        try:
            conversions = self._get_all_conversions()
            if not conversions:
                return 0.0

            total_touchpoints = sum(len(c.touchpoints) for c in conversions)
            return total_touchpoints / len(conversions)
        except Exception as e:
            logger.error(f"Failed to calculate avg touchpoints: {e}")
            return 0.0

    # ========== Reporting ==========

    def generate_attribution_report(
        self,
        date_range: Tuple[datetime, datetime],
        model: AttributionModel = AttributionModel.LAST_TOUCH,
        group_by: str = "campaign"
    ) -> Dict[str, Any]:
        """Generate attribution report."""
        try:
            conversions = self._get_all_conversions(date_range)

            # Aggregate by group
            groups: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
                'conversions': 0,
                'revenue': 0.0,
                'attributed_revenue': 0.0
            })

            for conv in conversions:
                attribution = self.attribute_to_campaign(conv.id, model)

                for campaign_id, weight in attribution.items():
                    group_key = campaign_id if group_by == "campaign" else conv.conversion_type

                    groups[group_key]['conversions'] += 1
                    groups[group_key]['revenue'] += conv.value
                    groups[group_key]['attributed_revenue'] += conv.value * weight

            return {
                'date_range': {
                    'start': date_range[0].isoformat(),
                    'end': date_range[1].isoformat()
                },
                'attribution_model': model.value,
                'group_by': group_by,
                'groups': dict(groups),
                'total_conversions': len(conversions),
                'total_revenue': sum(c.value for c in conversions)
            }
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise

    def get_conversions_by_source(
        self,
        source: ConversionSource,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[UnifiedConversion]:
        """Get conversions filtered by source."""
        try:
            conversions = self._get_all_conversions(date_range)
            return [c for c in conversions if source in c.sources]
        except Exception as e:
            logger.error(f"Failed to get conversions by source: {e}")
            return []

    def export_conversions(
        self,
        date_range: Tuple[datetime, datetime],
        format: str = "csv"
    ) -> str:
        """Export conversions to file."""
        try:
            conversions = self._get_all_conversions(date_range)

            if format == "csv":
                return self._export_to_csv(conversions)
            elif format == "json":
                return json.dumps([c.to_dict() for c in conversions], indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

    # ========== Sync Operations ==========

    def sync_all_sources(self) -> Dict[str, int]:
        """Sync conversions from all sources."""
        try:
            results = {}

            # Sync Meta CAPI
            try:
                meta_count = self._sync_meta_capi()
                results['meta_capi'] = meta_count
            except Exception as e:
                logger.error(f"Meta CAPI sync failed: {e}")
                results['meta_capi'] = 0

            # Sync HubSpot
            try:
                hubspot_count = self._sync_hubspot()
                results['hubspot'] = hubspot_count
            except Exception as e:
                logger.error(f"HubSpot sync failed: {e}")
                results['hubspot'] = 0

            # Sync AnyTrack
            try:
                anytrack_count = self._sync_anytrack()
                results['anytrack'] = anytrack_count
            except Exception as e:
                logger.error(f"AnyTrack sync failed: {e}")
                results['anytrack'] = 0

            logger.info(f"Sync completed: {results}")
            return results
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise

    def get_sync_status(self) -> Dict[str, Any]:
        """Get last sync status for all sources."""
        try:
            return self.db.get('sync_status', {
                'meta_capi': {'last_sync': None, 'status': 'never'},
                'hubspot': {'last_sync': None, 'status': 'never'},
                'anytrack': {'last_sync': None, 'status': 'never'}
            })
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {}

    # ========== Internal Helper Methods ==========

    def _generate_conversion_id(self, data: Dict[str, Any]) -> str:
        """Generate unique conversion ID."""
        key_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    async def _store_conversion(self, conversion: UnifiedConversion) -> None:
        """Store conversion in PostgreSQL and Redis cache."""
        try:
            # Convert to database model
            db_conversion = UnifiedConversionModel(
                id=conversion.id,
                external_ids=conversion.external_ids,
                contact_email=conversion.contact_email,
                contact_id=conversion.contact_id,
                value=float(conversion.value),
                currency=conversion.currency,
                conversion_type=conversion.conversion_type,
                sources=[s.value for s in conversion.sources],
                touchpoints=[tp.to_dict() for tp in conversion.touchpoints],
                attributed_campaign_id=conversion.attributed_campaign_id,
                attributed_ad_id=conversion.attributed_ad_id,
                attribution_model=conversion.attribution_model.value,
                first_touch_at=conversion.first_touch_at,
                converted_at=conversion.converted_at,
                is_offline=conversion.is_offline,
                metadata=conversion.metadata
            )

            # Check if exists (for update)
            result = await self.db_session.execute(
                select(UnifiedConversionModel).where(UnifiedConversionModel.id == conversion.id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                for key, value in conversion.to_dict().items():
                    if key not in ['created_at']:
                        setattr(existing, key, value)
            else:
                # Add new
                self.db_session.add(db_conversion)

            await self.db_session.commit()

            # Cache in Redis for fast access
            set_cache(f"conversion:{conversion.id}", conversion.to_dict(), self.cache_ttl)

            logger.debug(f"Stored conversion {conversion.id} in PostgreSQL + Redis")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to store conversion: {e}")
            raise

    async def _load_conversion(self, conversion_id: str) -> Optional[UnifiedConversion]:
        """Load conversion from Redis cache or PostgreSQL."""
        try:
            # Try Redis cache first
            cached_data = get_cache(f"conversion:{conversion_id}")
            if cached_data:
                # Reconstruct from cached dict
                return self._dict_to_conversion(cached_data)

            # Load from PostgreSQL
            result = await self.db_session.execute(
                select(UnifiedConversionModel).where(UnifiedConversionModel.id == conversion_id)
            )
            db_conversion = result.scalar_one_or_none()

            if not db_conversion:
                return None

            # Convert to dataclass
            conversion = UnifiedConversion(
                id=db_conversion.id,
                external_ids=db_conversion.external_ids,
                contact_email=db_conversion.contact_email,
                contact_id=db_conversion.contact_id,
                value=float(db_conversion.value),
                currency=db_conversion.currency,
                conversion_type=db_conversion.conversion_type,
                sources=[ConversionSource(s) for s in db_conversion.sources],
                touchpoints=[Touchpoint.from_dict(tp) for tp in db_conversion.touchpoints],
                attributed_campaign_id=db_conversion.attributed_campaign_id,
                attributed_ad_id=db_conversion.attributed_ad_id,
                attribution_model=AttributionModel(db_conversion.attribution_model),
                first_touch_at=db_conversion.first_touch_at,
                converted_at=db_conversion.converted_at,
                is_offline=db_conversion.is_offline,
                metadata=db_conversion.metadata
            )

            # Cache for future lookups
            set_cache(f"conversion:{conversion_id}", conversion.to_dict(), self.cache_ttl)

            return conversion
        except Exception as e:
            logger.error(f"Failed to load conversion {conversion_id}: {e}")
            return None

    def _dict_to_conversion(self, data: Dict[str, Any]) -> UnifiedConversion:
        """Convert dictionary to UnifiedConversion object."""
        return UnifiedConversion(
            id=data['id'],
            external_ids=data['external_ids'],
            contact_email=data.get('contact_email'),
            contact_id=data.get('contact_id'),
            value=data['value'],
            currency=data['currency'],
            conversion_type=data['conversion_type'],
            sources=[ConversionSource(s) for s in data['sources']],
            touchpoints=[Touchpoint.from_dict(tp) for tp in data['touchpoints']],
            attributed_campaign_id=data.get('attributed_campaign_id'),
            attributed_ad_id=data.get('attributed_ad_id'),
            attribution_model=AttributionModel(data['attribution_model']),
            first_touch_at=datetime.fromisoformat(data['first_touch_at']),
            converted_at=datetime.fromisoformat(data['converted_at']),
            is_offline=data['is_offline'],
            metadata=data.get('metadata', {})
        )

    async def _get_conversions_since(self, cutoff: datetime) -> List[UnifiedConversion]:
        """Get all conversions since cutoff time."""
        try:
            result = await self.db_session.execute(
                select(UnifiedConversionModel)
                .where(UnifiedConversionModel.converted_at >= cutoff)
                .order_by(UnifiedConversionModel.converted_at.desc())
            )
            db_conversions = result.scalars().all()

            conversions = []
            for db_conv in db_conversions:
                conv = UnifiedConversion(
                    id=db_conv.id,
                    external_ids=db_conv.external_ids,
                    contact_email=db_conv.contact_email,
                    contact_id=db_conv.contact_id,
                    value=float(db_conv.value),
                    currency=db_conv.currency,
                    conversion_type=db_conv.conversion_type,
                    sources=[ConversionSource(s) for s in db_conv.sources],
                    touchpoints=[Touchpoint.from_dict(tp) for tp in db_conv.touchpoints],
                    attributed_campaign_id=db_conv.attributed_campaign_id,
                    attributed_ad_id=db_conv.attributed_ad_id,
                    attribution_model=AttributionModel(db_conv.attribution_model),
                    first_touch_at=db_conv.first_touch_at,
                    converted_at=db_conv.converted_at,
                    is_offline=db_conv.is_offline,
                    metadata=db_conv.metadata
                )
                conversions.append(conv)

            return conversions
        except Exception as e:
            logger.error(f"Failed to get conversions since {cutoff}: {e}")
            return []

    async def _get_conversions_in_range(
        self,
        start: datetime,
        end: datetime
    ) -> List[UnifiedConversion]:
        """Get conversions in date range."""
        try:
            result = await self.db_session.execute(
                select(UnifiedConversionModel)
                .where(and_(
                    UnifiedConversionModel.converted_at >= start,
                    UnifiedConversionModel.converted_at <= end
                ))
                .order_by(UnifiedConversionModel.converted_at.desc())
            )
            db_conversions = result.scalars().all()

            conversions = []
            for db_conv in db_conversions:
                conv = UnifiedConversion(
                    id=db_conv.id,
                    external_ids=db_conv.external_ids,
                    contact_email=db_conv.contact_email,
                    contact_id=db_conv.contact_id,
                    value=float(db_conv.value),
                    currency=db_conv.currency,
                    conversion_type=db_conv.conversion_type,
                    sources=[ConversionSource(s) for s in db_conv.sources],
                    touchpoints=[Touchpoint.from_dict(tp) for tp in db_conv.touchpoints],
                    attributed_campaign_id=db_conv.attributed_campaign_id,
                    attributed_ad_id=db_conv.attributed_ad_id,
                    attribution_model=AttributionModel(db_conv.attribution_model),
                    first_touch_at=db_conv.first_touch_at,
                    converted_at=db_conv.converted_at,
                    is_offline=db_conv.is_offline,
                    metadata=db_conv.metadata
                )
                conversions.append(conv)

            return conversions
        except Exception as e:
            logger.error(f"Failed to get conversions in range: {e}")
            return []

    async def _get_conversions_by_campaign(
        self,
        campaign_id: str,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[UnifiedConversion]:
        """Get conversions for campaign."""
        try:
            query = select(UnifiedConversionModel).where(
                UnifiedConversionModel.attributed_campaign_id == campaign_id
            )

            if date_range:
                start, end = date_range
                query = query.where(and_(
                    UnifiedConversionModel.converted_at >= start,
                    UnifiedConversionModel.converted_at <= end
                ))

            result = await self.db_session.execute(query)
            db_conversions = result.scalars().all()

            conversions = []
            for db_conv in db_conversions:
                conv = UnifiedConversion(
                    id=db_conv.id,
                    external_ids=db_conv.external_ids,
                    contact_email=db_conv.contact_email,
                    contact_id=db_conv.contact_id,
                    value=float(db_conv.value),
                    currency=db_conv.currency,
                    conversion_type=db_conv.conversion_type,
                    sources=[ConversionSource(s) for s in db_conv.sources],
                    touchpoints=[Touchpoint.from_dict(tp) for tp in db_conv.touchpoints],
                    attributed_campaign_id=db_conv.attributed_campaign_id,
                    attributed_ad_id=db_conv.attributed_ad_id,
                    attribution_model=AttributionModel(db_conv.attribution_model),
                    first_touch_at=db_conv.first_touch_at,
                    converted_at=db_conv.converted_at,
                    is_offline=db_conv.is_offline,
                    metadata=db_conv.metadata
                )
                conversions.append(conv)

            return conversions
        except Exception as e:
            logger.error(f"Failed to get conversions by campaign: {e}")
            return []

    async def _get_conversions_by_contact(self, contact_id: str) -> List[UnifiedConversion]:
        """Get all conversions for contact."""
        try:
            result = await self.db_session.execute(
                select(UnifiedConversionModel).where(
                    UnifiedConversionModel.contact_id == contact_id
                )
            )
            db_conversions = result.scalars().all()

            conversions = []
            for db_conv in db_conversions:
                conv = UnifiedConversion(
                    id=db_conv.id,
                    external_ids=db_conv.external_ids,
                    contact_email=db_conv.contact_email,
                    contact_id=db_conv.contact_id,
                    value=float(db_conv.value),
                    currency=db_conv.currency,
                    conversion_type=db_conv.conversion_type,
                    sources=[ConversionSource(s) for s in db_conv.sources],
                    touchpoints=[Touchpoint.from_dict(tp) for tp in db_conv.touchpoints],
                    attributed_campaign_id=db_conv.attributed_campaign_id,
                    attributed_ad_id=db_conv.attributed_ad_id,
                    attribution_model=AttributionModel(db_conv.attribution_model),
                    first_touch_at=db_conv.first_touch_at,
                    converted_at=db_conv.converted_at,
                    is_offline=db_conv.is_offline,
                    metadata=db_conv.metadata
                )
                conversions.append(conv)

            return conversions
        except Exception as e:
            logger.error(f"Failed to get conversions by contact: {e}")
            return []

    async def _get_all_conversions(
        self,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[UnifiedConversion]:
        """Get all conversions, optionally filtered by date."""
        try:
            query = select(UnifiedConversionModel)

            if date_range:
                start, end = date_range
                query = query.where(and_(
                    UnifiedConversionModel.converted_at >= start,
                    UnifiedConversionModel.converted_at <= end
                ))

            query = query.order_by(UnifiedConversionModel.converted_at.desc())

            result = await self.db_session.execute(query)
            db_conversions = result.scalars().all()

            conversions = []
            for db_conv in db_conversions:
                conv = UnifiedConversion(
                    id=db_conv.id,
                    external_ids=db_conv.external_ids,
                    contact_email=db_conv.contact_email,
                    contact_id=db_conv.contact_id,
                    value=float(db_conv.value),
                    currency=db_conv.currency,
                    conversion_type=db_conv.conversion_type,
                    sources=[ConversionSource(s) for s in db_conv.sources],
                    touchpoints=[Touchpoint.from_dict(tp) for tp in db_conv.touchpoints],
                    attributed_campaign_id=db_conv.attributed_campaign_id,
                    attributed_ad_id=db_conv.attributed_ad_id,
                    attribution_model=AttributionModel(db_conv.attribution_model),
                    first_touch_at=db_conv.first_touch_at,
                    converted_at=db_conv.converted_at,
                    is_offline=db_conv.is_offline,
                    metadata=db_conv.metadata
                )
                conversions.append(conv)

            return conversions
        except Exception as e:
            logger.error(f"Failed to get all conversions: {e}")
            return []

    async def _mark_conversion_merged(self, old_id: str, new_id: str) -> None:
        """Mark conversion as merged in PostgreSQL and Redis."""
        try:
            # Update in database
            result = await self.db_session.execute(
                select(UnifiedConversionModel).where(UnifiedConversionModel.id == old_id)
            )
            db_conversion = result.scalar_one_or_none()

            if db_conversion:
                db_conversion.is_merged = True
                db_conversion.merged_into = new_id
                await self.db_session.commit()

            # Update Redis cache
            set_cache(f"merged:{old_id}", new_id, self.cache_ttl * 24)  # Keep for 24 hours
            delete_cache(f"conversion:{old_id}")

            logger.info(f"Marked conversion {old_id} as merged into {new_id}")
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to mark conversion as merged: {e}")

    def _export_to_csv(self, conversions: List[UnifiedConversion]) -> str:
        """Export conversions to CSV format."""
        lines = ["id,email,value,currency,type,converted_at,sources"]

        for c in conversions:
            sources = ','.join([s.value for s in c.sources])
            line = f"{c.id},{c.contact_email},{c.value},{c.currency},{c.conversion_type},{c.converted_at.isoformat()},{sources}"
            lines.append(line)

        return '\n'.join(lines)

    def _sync_meta_capi(self) -> int:
        """Sync conversions from Meta CAPI."""
        # Implementation would call meta_capi.get_recent_conversions()
        return 0

    def _sync_hubspot(self) -> int:
        """Sync conversions from HubSpot."""
        # Implementation would call hubspot.get_recent_deals()
        return 0

    def _sync_anytrack(self) -> int:
        """Sync conversions from AnyTrack."""
        # Implementation would call anytrack.get_recent_conversions()
        return 0
