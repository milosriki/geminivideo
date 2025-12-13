"""
Meta Conversions API (CAPI) implementation for server-side event tracking.

This module provides a production-ready interface to Meta's Conversions API,
enabling server-side tracking of user events for better attribution and
privacy-compliant tracking.
"""

from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.event_request import EventRequest
from facebook_business.adobjects.serverside.user_data import UserData
from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.content import Content
from facebook_business.adobjects.serverside.action_source import ActionSource
from facebook_business.api import FacebookAdsApi
import hashlib
import time
import logging
import uuid
import httpx
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class UserInfo:
    """User information for CAPI events with PII fields."""

    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    external_id: Optional[str] = None
    client_ip_address: Optional[str] = None
    client_user_agent: Optional[str] = None
    fbc: Optional[str] = None  # Facebook click ID
    fbp: Optional[str] = None  # Facebook browser ID

    def get_matching_score(self) -> int:
        """
        Calculate user matching score for iOS 14.5+ attribution.
        More user data = better attribution matching.

        Returns:
            Score from 0-100 indicating match quality
        """
        score = 0
        # High-value identifiers (30 points each)
        if self.email: score += 30
        if self.phone: score += 30
        if self.external_id: score += 30

        # Medium-value identifiers (10 points each)
        if self.fbc: score += 10
        if self.fbp: score += 10

        # Low-value identifiers (5 points each)
        if self.first_name: score += 5
        if self.last_name: score += 5
        if self.client_ip_address: score += 5
        if self.client_user_agent: score += 5

        return min(score, 100)


@dataclass
class EventDeduplication:
    """Tracks event deduplication for attribution recovery."""

    event_id: str
    timestamp: datetime
    event_name: str
    source: str  # "pixel" or "capi"

    def is_expired(self, ttl_hours: int = 48) -> bool:
        """Check if deduplication record has expired."""
        return datetime.now() - self.timestamp > timedelta(hours=ttl_hours)


@dataclass
class AttributionMetrics:
    """Tracks attribution recovery metrics for iOS 14.5+."""

    total_events: int = 0
    pixel_events: int = 0
    capi_events: int = 0
    deduplicated_events: int = 0
    ios_recovered_events: int = 0
    match_quality_scores: List[int] = field(default_factory=list)

    def get_recovery_rate(self) -> float:
        """Calculate attribution recovery rate."""
        if self.total_events == 0:
            return 0.0
        return (self.ios_recovered_events / self.total_events) * 100

    def get_average_match_quality(self) -> float:
        """Get average user matching quality score."""
        if not self.match_quality_scores:
            return 0.0
        return sum(self.match_quality_scores) / len(self.match_quality_scores)


class MetaCAPI:
    """
    Meta Conversions API for server-side event tracking.

    This class provides a comprehensive interface to Meta's Conversions API,
    handling event creation, PII hashing, deduplication, and batch operations.

    Features:
    - Server-side conversion tracking
    - iOS 14.5+ attribution recovery
    - Event deduplication with pixel events
    - Advanced user matching for better attribution
    - Real-time attribution metrics
    """

    API_VERSION = "v19.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
    DEDUPLICATION_TTL_HOURS = 48  # Meta's deduplication window
    MAX_BATCH_SIZE = 1000

    def __init__(self, pixel_id: str, access_token: str, test_event_code: str = None):
        """
        Initialize CAPI client.

        Args:
            pixel_id: Meta Pixel ID
            access_token: Meta API access token
            test_event_code: Optional test event code for debugging (enables Test Events in Events Manager)
        """
        self.pixel_id = pixel_id
        self.access_token = access_token
        self.test_event_code = test_event_code

        # Initialize Facebook Ads API
        FacebookAdsApi.init(access_token=access_token)

        # Event deduplication cache (event_id -> EventDeduplication)
        self._deduplication_cache: Dict[str, EventDeduplication] = {}

        # Attribution recovery metrics
        self.attribution_metrics = AttributionMetrics()

        # Track sent event IDs to prevent duplicate sends
        self._sent_event_ids: Set[str] = set()

        # Event retry queue for failed sends
        self._retry_queue: List[Event] = []

        logger.info(
            f"Initialized Meta CAPI client for pixel {pixel_id}"
            + (f" with test event code {test_event_code}" if test_event_code else "")
        )

    def _hash_pii(self, value: str) -> str:
        """
        SHA256 hash PII data as required by Meta.

        Meta requires PII to be normalized and hashed:
        1. Trim whitespace
        2. Convert to lowercase
        3. SHA256 hash

        Args:
            value: Raw PII value

        Returns:
            SHA256 hashed value
        """
        if not value:
            return None

        # Normalize: trim and lowercase
        normalized = value.strip().lower()

        # Hash with SHA256
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _build_user_data(self, user: UserInfo) -> UserData:
        """
        Build UserData object with hashed PII.

        Args:
            user: UserInfo object containing user details

        Returns:
            UserData object with properly hashed PII fields
        """
        user_data = UserData()

        # Hash PII fields
        if user.email:
            user_data.email = self._hash_pii(user.email)
        if user.phone:
            user_data.phone = self._hash_pii(user.phone)
        if user.first_name:
            user_data.first_name = self._hash_pii(user.first_name)
        if user.last_name:
            user_data.last_name = self._hash_pii(user.last_name)
        if user.city:
            user_data.city = self._hash_pii(user.city)
        if user.state:
            user_data.state = self._hash_pii(user.state)
        if user.zip_code:
            user_data.zip_code = self._hash_pii(user.zip_code)
        if user.country:
            user_data.country = self._hash_pii(user.country)
        if user.external_id:
            user_data.external_id = self._hash_pii(user.external_id)

        # Non-PII fields (not hashed)
        if user.client_ip_address:
            user_data.client_ip_address = user.client_ip_address
        if user.client_user_agent:
            user_data.client_user_agent = user.client_user_agent
        if user.fbc:
            user_data.fbc = user.fbc
        if user.fbp:
            user_data.fbp = user.fbp

        return user_data

    def _is_duplicate_event(self, event_id: str) -> bool:
        """
        Check if event has already been sent (server-side deduplication).

        Args:
            event_id: Event ID to check

        Returns:
            True if event is duplicate, False otherwise
        """
        # Clean up expired entries first
        self._cleanup_deduplication_cache()

        # Check if we've already sent this event
        if event_id in self._sent_event_ids:
            logger.warning(f"Duplicate event detected (already sent): {event_id}")
            self.attribution_metrics.deduplicated_events += 1
            return True

        # Check deduplication cache (for pixel/CAPI coordination)
        if event_id in self._deduplication_cache:
            dedup_record = self._deduplication_cache[event_id]
            if not dedup_record.is_expired(self.DEDUPLICATION_TTL_HOURS):
                logger.info(
                    f"Event {event_id} deduplicated with {dedup_record.source} "
                    f"(sent {dedup_record.timestamp})"
                )
                self.attribution_metrics.deduplicated_events += 1
                return True

        return False

    def _cleanup_deduplication_cache(self):
        """Remove expired entries from deduplication cache."""
        expired_ids = [
            event_id
            for event_id, record in self._deduplication_cache.items()
            if record.is_expired(self.DEDUPLICATION_TTL_HOURS)
        ]

        for event_id in expired_ids:
            del self._deduplication_cache[event_id]

        if expired_ids:
            logger.debug(f"Cleaned up {len(expired_ids)} expired deduplication records")

    def _register_event(self, event_id: str, event_name: str, source: str = "capi"):
        """
        Register event in deduplication cache.

        Args:
            event_id: Event ID
            event_name: Event name
            source: Event source ("capi" or "pixel")
        """
        self._deduplication_cache[event_id] = EventDeduplication(
            event_id=event_id,
            timestamp=datetime.now(),
            event_name=event_name,
            source=source
        )
        self._sent_event_ids.add(event_id)

    def _validate_event(self, event: Event, user: UserInfo) -> tuple[bool, Optional[str]]:
        """
        Validate event before sending.

        Args:
            event: Event to validate
            user: User information

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not event.event_name:
            return False, "Event name is required"

        if not event.event_id:
            return False, "Event ID is required for deduplication"

        # Validate user matching quality for iOS 14.5+ attribution
        match_score = user.get_matching_score()
        if match_score < 30:
            logger.warning(
                f"Low user matching score ({match_score}) - may reduce attribution quality. "
                "Consider adding email, phone, or external_id for better iOS 14.5+ recovery."
            )

        return True, None

    def _track_ios_attribution(self, user: UserInfo, event_name: str):
        """
        Track iOS 14.5+ attribution recovery metrics.

        Args:
            user: User information
            event_name: Event name
        """
        match_score = user.get_matching_score()
        self.attribution_metrics.match_quality_scores.append(match_score)

        # Events with good matching quality likely to recover iOS attribution
        if match_score >= 60:
            self.attribution_metrics.ios_recovered_events += 1
            logger.debug(f"iOS attribution recovery likely for {event_name} (score: {match_score})")

    async def _send_event_with_retry(
        self,
        event: Event,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Send event with retry logic for resilience.

        Args:
            event: Event to send
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            API response dictionary

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return self._send_event(event)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Event send failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Event send failed after {max_retries} attempts: {str(e)}")

        raise last_exception

    def _send_event(self, event: Event) -> Dict[str, Any]:
        """
        Send a single event to Meta CAPI.

        Args:
            event: Event object to send

        Returns:
            API response dictionary

        Raises:
            Exception: If API request fails
        """
        event_request = EventRequest(
            events=[event],
            pixel_id=self.pixel_id,
            test_event_code=self.test_event_code
        )

        try:
            response = event_request.execute()
            logger.info(f"Successfully sent event: {event.event_name}")
            return {
                'success': True,
                'events_received': response.events_received,
                'messages': response.messages,
                'fbtrace_id': response.fbtrace_id
            }
        except Exception as e:
            logger.error(f"Failed to send event {event.event_name}: {str(e)}")
            raise

    def send_purchase_event(
        self,
        user: UserInfo,
        value: float,
        currency: str = "USD",
        content_ids: List[str] = None,
        content_type: str = "product",
        order_id: str = None,
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Track purchase conversion with iOS 14.5+ attribution recovery.

        Args:
            user: User information
            value: Purchase value
            currency: Currency code (default: USD)
            content_ids: List of product IDs
            content_type: Type of content (product, product_group)
            order_id: Unique order identifier
            event_id: Event ID for deduplication with pixel

        Returns:
            API response dictionary
        """
        # Generate event ID if not provided
        if not event_id:
            event_id = self.generate_event_id()

        # Check for duplicates
        if self._is_duplicate_event(event_id):
            return {
                'success': False,
                'message': 'Duplicate event detected',
                'event_id': event_id,
                'deduplicated': True
            }

        user_data = self._build_user_data(user)

        custom_data = CustomData(
            value=value,
            currency=currency,
            content_type=content_type
        )

        if content_ids:
            custom_data.content_ids = content_ids
        if order_id:
            custom_data.order_id = order_id

        event = Event(
            event_name='Purchase',
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            action_source=ActionSource.WEBSITE,
            event_id=event_id
        )

        # Validate event
        is_valid, error = self._validate_event(event, user)
        if not is_valid:
            logger.error(f"Event validation failed: {error}")
            return {
                'success': False,
                'message': error,
                'event_id': event_id
            }

        # Track iOS attribution
        self._track_ios_attribution(user, 'Purchase')
        self.attribution_metrics.total_events += 1
        self.attribution_metrics.capi_events += 1

        # Send event and register for deduplication
        response = self._send_event(event)
        self._register_event(event_id, 'Purchase', 'capi')

        return response

    def send_lead_event(
        self,
        user: UserInfo,
        lead_id: str = None,
        content_name: str = None,
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Track lead form submission.

        Args:
            user: User information
            lead_id: Unique lead identifier
            content_name: Name of lead form or content
            event_id: Event ID for deduplication

        Returns:
            API response dictionary
        """
        user_data = self._build_user_data(user)

        custom_data = CustomData()
        if content_name:
            custom_data.content_name = content_name
        if lead_id:
            custom_data.content_ids = [lead_id]

        event = Event(
            event_name='Lead',
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            action_source=ActionSource.WEBSITE,
            event_id=event_id or self.generate_event_id()
        )

        return self._send_event(event)

    def send_view_content_event(
        self,
        user: UserInfo,
        content_id: str,
        content_name: str = None,
        content_category: str = None,
        value: float = None,
        currency: str = "USD",
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Track content view.

        Args:
            user: User information
            content_id: ID of viewed content
            content_name: Name of content
            content_category: Category of content
            value: Optional value associated with view
            currency: Currency code
            event_id: Event ID for deduplication

        Returns:
            API response dictionary
        """
        user_data = self._build_user_data(user)

        custom_data = CustomData(
            content_ids=[content_id],
            content_type='product'
        )

        if content_name:
            custom_data.content_name = content_name
        if content_category:
            custom_data.content_category = content_category
        if value is not None:
            custom_data.value = value
            custom_data.currency = currency

        event = Event(
            event_name='ViewContent',
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            action_source=ActionSource.WEBSITE,
            event_id=event_id or self.generate_event_id()
        )

        return self._send_event(event)

    def send_add_to_cart_event(
        self,
        user: UserInfo,
        content_id: str,
        value: float,
        currency: str = "USD",
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Track add to cart.

        Args:
            user: User information
            content_id: Product ID added to cart
            value: Product value
            currency: Currency code
            event_id: Event ID for deduplication

        Returns:
            API response dictionary
        """
        user_data = self._build_user_data(user)

        custom_data = CustomData(
            content_ids=[content_id],
            content_type='product',
            value=value,
            currency=currency
        )

        event = Event(
            event_name='AddToCart',
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            action_source=ActionSource.WEBSITE,
            event_id=event_id or self.generate_event_id()
        )

        return self._send_event(event)

    def send_initiate_checkout_event(
        self,
        user: UserInfo,
        content_ids: List[str],
        value: float,
        currency: str = "USD",
        num_items: int = 1,
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Track checkout initiation.

        Args:
            user: User information
            content_ids: List of product IDs in checkout
            value: Total checkout value
            currency: Currency code
            num_items: Number of items
            event_id: Event ID for deduplication

        Returns:
            API response dictionary
        """
        user_data = self._build_user_data(user)

        custom_data = CustomData(
            content_ids=content_ids,
            content_type='product',
            value=value,
            currency=currency,
            num_items=num_items
        )

        event = Event(
            event_name='InitiateCheckout',
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            action_source=ActionSource.WEBSITE,
            event_id=event_id or self.generate_event_id()
        )

        return self._send_event(event)

    def send_complete_registration_event(
        self,
        user: UserInfo,
        content_name: str = None,
        status: str = "complete",
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Track registration completion.

        Args:
            user: User information
            content_name: Name of registration form
            status: Registration status
            event_id: Event ID for deduplication

        Returns:
            API response dictionary
        """
        user_data = self._build_user_data(user)

        custom_data = CustomData()
        if content_name:
            custom_data.content_name = content_name
        custom_data.status = status

        event = Event(
            event_name='CompleteRegistration',
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            action_source=ActionSource.WEBSITE,
            event_id=event_id or self.generate_event_id()
        )

        return self._send_event(event)

    def send_custom_event(
        self,
        user: UserInfo,
        event_name: str,
        custom_data: Dict[str, Any] = None,
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Send custom event.

        Args:
            user: User information
            event_name: Custom event name
            custom_data: Dictionary of custom data
            event_id: Event ID for deduplication

        Returns:
            API response dictionary
        """
        user_data = self._build_user_data(user)

        custom_data_obj = CustomData()
        if custom_data:
            for key, value in custom_data.items():
                setattr(custom_data_obj, key, value)

        event = Event(
            event_name=event_name,
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data_obj,
            action_source=ActionSource.WEBSITE,
            event_id=event_id or self.generate_event_id()
        )

        return self._send_event(event)

    def batch_events(self, events: List[Event]) -> Dict[str, Any]:
        """
        Send multiple events in one request.

        Meta CAPI supports batching up to 1000 events per request for efficiency.

        Args:
            events: List of Event objects to send

        Returns:
            API response dictionary

        Raises:
            ValueError: If more than 1000 events provided
            Exception: If API request fails
        """
        if len(events) > 1000:
            raise ValueError("Maximum 1000 events per batch request")

        event_request = EventRequest(
            events=events,
            pixel_id=self.pixel_id,
            test_event_code=self.test_event_code
        )

        try:
            response = event_request.execute()
            logger.info(f"Successfully sent batch of {len(events)} events")
            return {
                'success': True,
                'events_received': response.events_received,
                'messages': response.messages,
                'fbtrace_id': response.fbtrace_id
            }
        except Exception as e:
            logger.error(f"Failed to send batch events: {str(e)}")
            raise

    def generate_event_id(self) -> str:
        """
        Generate unique event ID for deduplication with pixel.

        Event IDs are used to deduplicate events sent via both pixel (browser)
        and CAPI (server). If the same event_id is sent from both sources,
        Meta will only count it once.

        Returns:
            Unique event ID (UUID4)
        """
        return str(uuid.uuid4())

    def deduplicate_with_pixel(self, event_id: str) -> bool:
        """
        Check if event was already sent via pixel.

        This is a helper method for client-side integration. The actual
        deduplication happens on Meta's servers when the same event_id
        is used for both pixel and CAPI events.

        Args:
            event_id: Event ID to check

        Returns:
            True if event_id is valid for deduplication

        Note:
            This method validates the event_id format. Actual deduplication
            logic is handled by Meta's platform when processing events.
        """
        if not event_id:
            logger.warning("Empty event_id provided for deduplication")
            return False

        # Validate UUID format
        try:
            uuid.UUID(event_id)
            return True
        except ValueError:
            logger.warning(f"Invalid event_id format for deduplication: {event_id}")
            return False

    def register_pixel_event(self, event_id: str, event_name: str):
        """
        Register that a pixel event was sent for deduplication.

        Call this when you know a pixel event was fired on the client-side
        to prevent duplicate CAPI sends.

        Args:
            event_id: Event ID from pixel
            event_name: Event name
        """
        self._register_event(event_id, event_name, source="pixel")
        self.attribution_metrics.pixel_events += 1
        logger.debug(f"Registered pixel event: {event_name} ({event_id})")

    def get_attribution_metrics(self) -> Dict[str, Any]:
        """
        Get current attribution recovery metrics.

        Returns:
            Dictionary with attribution metrics including:
            - total_events: Total events tracked
            - capi_events: Events sent via CAPI
            - pixel_events: Events sent via pixel
            - deduplicated_events: Events deduplicated
            - ios_recovered_events: Events likely to recover iOS attribution
            - recovery_rate: Percentage of attribution recovery
            - avg_match_quality: Average user matching quality score
        """
        metrics = self.attribution_metrics

        return {
            'total_events': metrics.total_events,
            'capi_events': metrics.capi_events,
            'pixel_events': metrics.pixel_events,
            'deduplicated_events': metrics.deduplicated_events,
            'ios_recovered_events': metrics.ios_recovered_events,
            'recovery_rate': f"{metrics.get_recovery_rate():.1f}%",
            'avg_match_quality': f"{metrics.get_average_match_quality():.1f}",
            'deduplication_cache_size': len(self._deduplication_cache),
        }

    def reset_metrics(self):
        """Reset attribution metrics (useful for testing or periodic resets)."""
        self.attribution_metrics = AttributionMetrics()
        logger.info("Attribution metrics reset")

    async def send_event_async(
        self,
        event_name: str,
        user: UserInfo,
        custom_data: Dict[str, Any] = None,
        event_id: str = None
    ) -> Dict[str, Any]:
        """
        Async method to send custom event with retry logic.

        Args:
            event_name: Name of the event
            user: User information
            custom_data: Custom event data
            event_id: Optional event ID for deduplication

        Returns:
            API response dictionary
        """
        if not event_id:
            event_id = self.generate_event_id()

        # Check for duplicates
        if self._is_duplicate_event(event_id):
            return {
                'success': False,
                'message': 'Duplicate event detected',
                'event_id': event_id,
                'deduplicated': True
            }

        user_data = self._build_user_data(user)

        custom_data_obj = CustomData()
        if custom_data:
            for key, value in custom_data.items():
                setattr(custom_data_obj, key, value)

        event = Event(
            event_name=event_name,
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data_obj,
            action_source=ActionSource.WEBSITE,
            event_id=event_id
        )

        # Validate event
        is_valid, error = self._validate_event(event, user)
        if not is_valid:
            logger.error(f"Event validation failed: {error}")
            return {
                'success': False,
                'message': error,
                'event_id': event_id
            }

        # Track iOS attribution
        self._track_ios_attribution(user, event_name)
        self.attribution_metrics.total_events += 1
        self.attribution_metrics.capi_events += 1

        # Send with retry logic
        response = await self._send_event_with_retry(event)
        self._register_event(event_id, event_name, 'capi')

        return response

    def validate_user_data_quality(self, user: UserInfo) -> Dict[str, Any]:
        """
        Validate and score user data quality for attribution.

        Args:
            user: User information to validate

        Returns:
            Dictionary with validation results:
            - score: Match quality score (0-100)
            - grade: Letter grade (A-F)
            - has_email: Whether email is present
            - has_phone: Whether phone is present
            - has_external_id: Whether external ID is present
            - recommendations: List of recommendations to improve matching
        """
        score = user.get_matching_score()

        # Grade based on score
        if score >= 90:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        elif score >= 45:
            grade = "D"
        else:
            grade = "F"

        # Generate recommendations
        recommendations = []
        if not user.email:
            recommendations.append("Add email for +30 points (highest value identifier)")
        if not user.phone:
            recommendations.append("Add phone for +30 points (highest value identifier)")
        if not user.external_id:
            recommendations.append("Add external_id (customer ID) for +30 points")
        if not user.fbc and not user.fbp:
            recommendations.append("Add Facebook click ID (fbc) or browser ID (fbp) for +10 points")

        return {
            'score': score,
            'grade': grade,
            'has_email': bool(user.email),
            'has_phone': bool(user.phone),
            'has_external_id': bool(user.external_id),
            'has_facebook_ids': bool(user.fbc or user.fbp),
            'recommendations': recommendations,
            'ios_attribution_recovery': "Excellent" if score >= 75 else "Good" if score >= 60 else "Fair" if score >= 45 else "Poor"
        }


class MetaConversionsAPI:
    """
    Direct HTTP implementation of Meta Conversions API (alternative to Facebook SDK).

    This class provides a lightweight HTTP-based interface using httpx
    for server-side event tracking without requiring the Facebook Business SDK.
    """

    API_VERSION = "v19.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

    def __init__(self, pixel_id: str, access_token: str):
        """
        Initialize Conversions API client.

        Args:
            pixel_id: Meta Pixel ID
            access_token: Meta API access token
        """
        self.pixel_id = pixel_id
        self.access_token = access_token
        self.endpoint = f"{self.BASE_URL}/{pixel_id}/events"
        self._event_cache: Dict[str, datetime] = {}

    def _hash_user_data(self, value: str) -> str:
        """Hash user data with SHA256."""
        if not value:
            return None
        return hashlib.sha256(value.lower().strip().encode()).hexdigest()

    def _deduplicate_event(self, event_id: str, ttl_hours: int = 48) -> bool:
        """
        Check if event was already sent.

        Args:
            event_id: Event ID to check
            ttl_hours: Time-to-live in hours for deduplication

        Returns:
            True if event is duplicate, False otherwise
        """
        # Clean expired entries
        now = datetime.now()
        expired = [
            eid for eid, timestamp in self._event_cache.items()
            if now - timestamp > timedelta(hours=ttl_hours)
        ]
        for eid in expired:
            del self._event_cache[eid]

        # Check if event exists
        if event_id in self._event_cache:
            logger.warning(f"Duplicate event detected: {event_id}")
            return True

        return False

    async def send_event(
        self,
        event_name: str,
        event_time: int,
        user_data: Dict[str, Any],
        custom_data: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        action_source: str = "website",
        event_source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a conversion event to Meta API.

        Args:
            event_name: Name of the event (e.g., "Purchase", "Lead")
            event_time: Unix timestamp of the event
            user_data: User information dictionary with fields:
                - em: Email (will be hashed)
                - ph: Phone (will be hashed)
                - fn: First name (will be hashed)
                - ln: Last name (will be hashed)
                - ct: City (will be hashed)
                - st: State (will be hashed)
                - zp: Zip code (will be hashed)
                - country: Country code (will be hashed)
                - external_id: External user ID (will be hashed)
                - client_ip_address: Client IP (not hashed)
                - client_user_agent: User agent (not hashed)
                - fbc: Facebook click ID (not hashed)
                - fbp: Facebook browser ID (not hashed)
            custom_data: Optional custom event data (e.g., value, currency, content_ids)
            event_id: Unique event ID for deduplication
            action_source: Where the event occurred (website, app, etc.)
            event_source_url: URL where event occurred

        Returns:
            API response dictionary
        """
        # Generate event ID if not provided
        if not event_id:
            event_id = str(uuid.uuid4())

        # Check deduplication
        if self._deduplicate_event(event_id):
            return {
                'success': False,
                'message': 'Duplicate event',
                'event_id': event_id
            }

        # Hash PII fields in user_data
        hashed_user_data = {}
        pii_fields = ['em', 'ph', 'fn', 'ln', 'ct', 'st', 'zp', 'country', 'external_id']
        non_pii_fields = ['client_ip_address', 'client_user_agent', 'fbc', 'fbp']

        for field in pii_fields:
            if field in user_data and user_data[field]:
                hashed_user_data[field] = [self._hash_user_data(user_data[field])]

        for field in non_pii_fields:
            if field in user_data and user_data[field]:
                hashed_user_data[field] = user_data[field]

        # Build event payload
        event_data = {
            "event_name": event_name,
            "event_time": event_time,
            "event_id": event_id,
            "action_source": action_source,
            "user_data": hashed_user_data
        }

        if custom_data:
            event_data["custom_data"] = custom_data

        if event_source_url:
            event_data["event_source_url"] = event_source_url

        # Build request payload
        payload = {
            "data": [event_data],
            "access_token": self.access_token
        }

        # Send to API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()

                result = response.json()

                # Register event in cache
                self._event_cache[event_id] = datetime.now()

                logger.info(f"Successfully sent event: {event_name} ({event_id})")

                return {
                    'success': True,
                    'event_id': event_id,
                    'events_received': result.get('events_received', 0),
                    'fbtrace_id': result.get('fbtrace_id'),
                    'messages': result.get('messages', [])
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error sending event: {e.response.status_code} - {e.response.text}")
                raise

            except Exception as e:
                logger.error(f"Failed to send event: {str(e)}")
                raise

    async def send_purchase(
        self,
        email: str,
        value: float,
        currency: str = "USD",
        order_id: Optional[str] = None,
        content_ids: Optional[List[str]] = None,
        client_ip_address: Optional[str] = None,
        client_user_agent: Optional[str] = None,
        event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a purchase event.

        Args:
            email: User email
            value: Purchase value
            currency: Currency code
            order_id: Order ID
            content_ids: Product IDs
            client_ip_address: Client IP address
            client_user_agent: User agent string
            event_id: Event ID for deduplication

        Returns:
            API response
        """
        user_data = {
            'em': email,
            'client_ip_address': client_ip_address,
            'client_user_agent': client_user_agent
        }

        custom_data = {
            'value': value,
            'currency': currency
        }

        if order_id:
            custom_data['order_id'] = order_id
        if content_ids:
            custom_data['content_ids'] = content_ids

        return await self.send_event(
            event_name='Purchase',
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            event_id=event_id
        )


# Example Usage
"""
# Using Facebook SDK-based implementation (recommended)
from services.titan_core.meta.conversions_api import MetaCAPI, UserInfo

# Initialize CAPI client
capi = MetaCAPI(
    pixel_id="YOUR_PIXEL_ID",
    access_token="YOUR_ACCESS_TOKEN",
    test_event_code="TEST12345"  # Optional, for testing
)

# Track a purchase with full user data for iOS 14.5+ attribution recovery
user = UserInfo(
    email="customer@example.com",
    phone="+1234567890",
    first_name="John",
    last_name="Doe",
    city="San Francisco",
    state="CA",
    zip_code="94102",
    country="US",
    external_id="user_12345",  # Your internal customer ID
    client_ip_address="1.2.3.4",
    client_user_agent="Mozilla/5.0...",
    fbc="fb.1.1234567890.AbCdEfGhIjKlMnOpQrStUvWxYz",  # Facebook click ID from URL
    fbp="fb.1.1234567890.1234567890"  # Facebook browser ID from cookie
)

# Validate user data quality before sending
quality = capi.validate_user_data_quality(user)
print(f"User matching quality: {quality['grade']} ({quality['score']}/100)")
print(f"iOS attribution recovery: {quality['ios_attribution_recovery']}")

# Send purchase event
response = capi.send_purchase_event(
    user=user,
    value=99.99,
    currency="USD",
    content_ids=["product_123"],
    order_id="order_456",
    event_id="unique_event_id_123"  # Same ID used in pixel for deduplication
)

print(f"Event sent: {response}")

# Get attribution metrics
metrics = capi.get_attribution_metrics()
print(f"Attribution recovery rate: {metrics['recovery_rate']}")
print(f"Average match quality: {metrics['avg_match_quality']}")

# Using HTTP-based implementation (lightweight alternative)
from services.titan_core.meta.conversions_api import MetaConversionsAPI

api = MetaConversionsAPI(
    pixel_id="YOUR_PIXEL_ID",
    access_token="YOUR_ACCESS_TOKEN"
)

# Send purchase with async
import asyncio

async def track_purchase():
    response = await api.send_purchase(
        email="customer@example.com",
        value=99.99,
        currency="USD",
        order_id="order_456",
        content_ids=["product_123"],
        client_ip_address="1.2.3.4",
        client_user_agent="Mozilla/5.0..."
    )
    print(response)

asyncio.run(track_purchase())
"""
