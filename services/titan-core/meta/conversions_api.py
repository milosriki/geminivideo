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
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

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


class MetaCAPI:
    """
    Meta Conversions API for server-side event tracking.

    This class provides a comprehensive interface to Meta's Conversions API,
    handling event creation, PII hashing, deduplication, and batch operations.
    """

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
        Track purchase conversion.

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
            event_id=event_id or self.generate_event_id()
        )

        return self._send_event(event)

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
