"""
HubSpot CRM Integration for 5-Day Sales Cycle Tracking

Real HubSpot API v3 integration for:
- Contact and deal management
- Sales cycle analytics
- Campaign attribution
- Pipeline tracking
- ROAS calculation

Agent 13 of 30 - ULTIMATE Production Plan
"""

import hubspot
from hubspot.crm.contacts import ApiException as ContactsApiException
from hubspot.crm.deals import ApiException as DealsApiException
from hubspot.crm.companies import ApiException as CompaniesApiException
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import time

# Configure logging
logger = logging.getLogger(__name__)


class DealStage(Enum):
    """HubSpot deal pipeline stages."""
    APPOINTMENT_SCHEDULED = "appointmentscheduled"
    QUALIFIED_TO_BUY = "qualifiedtobuy"
    PRESENTATION_SCHEDULED = "presentationscheduled"
    DECISION_MAKER_BOUGHT_IN = "decisionmakerboughtin"
    CONTRACT_SENT = "contractsent"
    CLOSED_WON = "closedwon"
    CLOSED_LOST = "closedlost"


class LifecycleStage(Enum):
    """HubSpot contact lifecycle stages."""
    SUBSCRIBER = "subscriber"
    LEAD = "lead"
    MQL = "marketingqualifiedlead"
    SQL = "salesqualifiedlead"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
    EVANGELIST = "evangelist"
    OTHER = "other"


@dataclass
class Contact:
    """HubSpot contact data model."""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    company: Optional[str]
    lifecycle_stage: str
    lead_source: Optional[str]
    utm_campaign: Optional[str]
    utm_source: Optional[str]
    created_at: datetime


@dataclass
class Deal:
    """HubSpot deal data model."""
    id: str
    name: str
    amount: float
    stage: DealStage
    contact_id: str
    campaign_id: Optional[str]
    close_date: Optional[datetime]
    created_at: datetime
    pipeline: str


@dataclass
class StageChange:
    """Deal stage transition tracking."""
    deal_id: str
    from_stage: str
    to_stage: str
    timestamp: datetime
    time_in_stage_hours: float


class HubSpotIntegration:
    """
    HubSpot CRM API v3 integration for sales cycle tracking.

    Provides real-time integration with HubSpot for:
    - Contact lifecycle management
    - Deal pipeline tracking
    - Sales cycle analytics
    - Campaign attribution
    - ROAS calculation from actual closed deals
    """

    def __init__(self, access_token: str):
        """
        Initialize HubSpot client with API access token.

        Args:
            access_token: HubSpot private app access token
        """
        self.client = hubspot.Client.create(access_token=access_token)
        self.contacts_api = self.client.crm.contacts
        self.deals_api = self.client.crm.deals
        self.companies_api = self.client.crm.companies
        logger.info("HubSpot integration initialized")

    # ============================================================================
    # Contact Management
    # ============================================================================

    def sync_contact(
        self,
        email: str,
        properties: Dict[str, Any]
    ) -> str:
        """
        Create or update contact, return contact_id.

        Args:
            email: Contact email (used as unique identifier)
            properties: Contact properties to set/update

        Returns:
            str: HubSpot contact ID

        Raises:
            ContactsApiException: If API call fails
        """
        try:
            # Ensure email is in properties
            properties['email'] = email

            # Try to get existing contact first
            existing = self.get_contact_by_email(email)

            if existing:
                # Update existing contact
                logger.info(f"Updating existing contact: {email}")
                self.update_contact(existing.id, properties)
                return existing.id
            else:
                # Create new contact
                logger.info(f"Creating new contact: {email}")
                simple_public_object_input = {
                    "properties": properties
                }

                api_response = self.contacts_api.basic_api.create(
                    simple_public_object_input=simple_public_object_input
                )

                contact_id = api_response.id
                logger.info(f"Created contact {contact_id} for {email}")
                return contact_id

        except ContactsApiException as e:
            logger.error(f"Error syncing contact {email}: {e}")
            raise

    def get_contact(self, contact_id: str) -> Contact:
        """
        Get contact by ID.

        Args:
            contact_id: HubSpot contact ID

        Returns:
            Contact: Contact data object

        Raises:
            ContactsApiException: If contact not found or API error
        """
        try:
            properties = [
                "email", "firstname", "lastname", "phone", "company",
                "lifecyclestage", "hs_lead_status", "hs_analytics_source",
                "hs_analytics_first_url", "utm_campaign", "utm_source",
                "utm_medium", "createdate"
            ]

            api_response = self.contacts_api.basic_api.get_by_id(
                contact_id=contact_id,
                properties=properties
            )

            props = api_response.properties

            return Contact(
                id=api_response.id,
                email=props.get('email', ''),
                first_name=props.get('firstname', ''),
                last_name=props.get('lastname', ''),
                phone=props.get('phone'),
                company=props.get('company'),
                lifecycle_stage=props.get('lifecyclestage', 'lead'),
                lead_source=props.get('hs_analytics_source'),
                utm_campaign=props.get('utm_campaign'),
                utm_source=props.get('utm_source'),
                created_at=datetime.fromisoformat(props.get('createdate', '').replace('Z', '+00:00'))
            )

        except ContactsApiException as e:
            logger.error(f"Error getting contact {contact_id}: {e}")
            raise

    def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """
        Get contact by email address.

        Args:
            email: Contact email

        Returns:
            Optional[Contact]: Contact if found, None otherwise
        """
        try:
            # Search for contact by email
            public_object_search_request = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email
                            }
                        ]
                    }
                ],
                "properties": [
                    "email", "firstname", "lastname", "phone", "company",
                    "lifecyclestage", "utm_campaign", "utm_source", "createdate"
                ],
                "limit": 1
            }

            api_response = self.contacts_api.search_api.do_search(
                public_object_search_request=public_object_search_request
            )

            if api_response.total > 0:
                result = api_response.results[0]
                props = result.properties

                return Contact(
                    id=result.id,
                    email=props.get('email', ''),
                    first_name=props.get('firstname', ''),
                    last_name=props.get('lastname', ''),
                    phone=props.get('phone'),
                    company=props.get('company'),
                    lifecycle_stage=props.get('lifecyclestage', 'lead'),
                    lead_source=props.get('hs_analytics_source'),
                    utm_campaign=props.get('utm_campaign'),
                    utm_source=props.get('utm_source'),
                    created_at=datetime.fromisoformat(props.get('createdate', '').replace('Z', '+00:00'))
                )

            return None

        except ContactsApiException as e:
            logger.error(f"Error searching for contact {email}: {e}")
            return None

    def update_contact(
        self,
        contact_id: str,
        properties: Dict[str, Any]
    ) -> bool:
        """
        Update contact properties.

        Args:
            contact_id: HubSpot contact ID
            properties: Properties to update

        Returns:
            bool: True if successful

        Raises:
            ContactsApiException: If update fails
        """
        try:
            simple_public_object_input = {
                "properties": properties
            }

            self.contacts_api.basic_api.update(
                contact_id=contact_id,
                simple_public_object_input=simple_public_object_input
            )

            logger.info(f"Updated contact {contact_id}")
            return True

        except ContactsApiException as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            raise

    def add_utm_to_contact(
        self,
        contact_id: str,
        utm_campaign: str,
        utm_source: str,
        utm_medium: str = None
    ) -> bool:
        """
        Add UTM tracking parameters to contact.

        Args:
            contact_id: HubSpot contact ID
            utm_campaign: Campaign identifier
            utm_source: Traffic source
            utm_medium: Marketing medium (optional)

        Returns:
            bool: True if successful
        """
        properties = {
            "utm_campaign": utm_campaign,
            "utm_source": utm_source
        }

        if utm_medium:
            properties["utm_medium"] = utm_medium

        return self.update_contact(contact_id, properties)

    # ============================================================================
    # Deal Management
    # ============================================================================

    def create_deal(
        self,
        contact_id: str,
        deal_name: str,
        amount: float,
        stage: DealStage = DealStage.APPOINTMENT_SCHEDULED,
        pipeline: str = "default",
        properties: Dict[str, Any] = None
    ) -> str:
        """
        Create deal associated with contact.

        Args:
            contact_id: Associated contact ID
            deal_name: Deal name/title
            amount: Deal value in dollars
            stage: Initial deal stage
            pipeline: Pipeline ID
            properties: Additional custom properties

        Returns:
            str: Created deal ID

        Raises:
            DealsApiException: If creation fails
        """
        try:
            deal_props = {
                "dealname": deal_name,
                "amount": str(amount),
                "dealstage": stage.value,
                "pipeline": pipeline,
                "closedate": (datetime.now() + timedelta(days=5)).isoformat()
            }

            # Merge custom properties
            if properties:
                deal_props.update(properties)

            simple_public_object_input = {
                "properties": deal_props,
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 3  # Deal to Contact
                            }
                        ]
                    }
                ]
            }

            api_response = self.deals_api.basic_api.create(
                simple_public_object_input=simple_public_object_input
            )

            deal_id = api_response.id
            logger.info(f"Created deal {deal_id}: {deal_name} (${amount})")
            return deal_id

        except DealsApiException as e:
            logger.error(f"Error creating deal {deal_name}: {e}")
            raise

    def update_deal_stage(
        self,
        deal_id: str,
        stage: DealStage
    ) -> bool:
        """
        Update deal stage.

        Args:
            deal_id: Deal ID
            stage: New stage

        Returns:
            bool: True if successful
        """
        try:
            properties = {
                "dealstage": stage.value
            }

            # If moving to closed won, set close date to today
            if stage == DealStage.CLOSED_WON:
                properties["closedate"] = datetime.now().isoformat()

            simple_public_object_input = {
                "properties": properties
            }

            self.deals_api.basic_api.update(
                deal_id=deal_id,
                simple_public_object_input=simple_public_object_input
            )

            logger.info(f"Updated deal {deal_id} to stage {stage.value}")
            return True

        except DealsApiException as e:
            logger.error(f"Error updating deal {deal_id} stage: {e}")
            raise

    def get_deal(self, deal_id: str) -> Deal:
        """
        Get deal by ID.

        Args:
            deal_id: Deal ID

        Returns:
            Deal: Deal data object

        Raises:
            DealsApiException: If deal not found
        """
        try:
            properties = [
                "dealname", "amount", "dealstage", "pipeline",
                "closedate", "createdate", "campaign_id", "meta_ad_id"
            ]

            api_response = self.deals_api.basic_api.get_by_id(
                deal_id=deal_id,
                properties=properties,
                associations=["contacts"]
            )

            props = api_response.properties

            # Get associated contact ID
            contact_id = None
            if hasattr(api_response, 'associations') and api_response.associations:
                contacts = api_response.associations.get('contacts', {}).get('results', [])
                if contacts:
                    contact_id = contacts[0].id

            return Deal(
                id=api_response.id,
                name=props.get('dealname', ''),
                amount=float(props.get('amount', 0)),
                stage=DealStage(props.get('dealstage', 'appointmentscheduled')),
                contact_id=contact_id or '',
                campaign_id=props.get('campaign_id'),
                close_date=datetime.fromisoformat(props['closedate'].replace('Z', '+00:00')) if props.get('closedate') else None,
                created_at=datetime.fromisoformat(props.get('createdate', '').replace('Z', '+00:00')),
                pipeline=props.get('pipeline', 'default')
            )

        except DealsApiException as e:
            logger.error(f"Error getting deal {deal_id}: {e}")
            raise

    def get_deal_history(
        self,
        deal_id: str
    ) -> List[StageChange]:
        """
        Get deal stage change history using property history API.

        Args:
            deal_id: Deal ID

        Returns:
            List[StageChange]: Stage transitions with timing
        """
        try:
            # Get property history for dealstage
            api_response = self.deals_api.basic_api.get_by_id(
                deal_id=deal_id,
                properties=["dealstage"],
                properties_with_history=["dealstage"]
            )

            stage_changes = []

            if hasattr(api_response, 'properties_with_history'):
                history = api_response.properties_with_history.get('dealstage', [])

                for i in range(len(history) - 1):
                    current = history[i]
                    previous = history[i + 1]

                    timestamp = datetime.fromisoformat(current['timestamp'].replace('Z', '+00:00'))
                    prev_timestamp = datetime.fromisoformat(previous['timestamp'].replace('Z', '+00:00'))

                    time_diff = (timestamp - prev_timestamp).total_seconds() / 3600

                    stage_changes.append(StageChange(
                        deal_id=deal_id,
                        from_stage=previous['value'],
                        to_stage=current['value'],
                        timestamp=timestamp,
                        time_in_stage_hours=time_diff
                    ))

            return stage_changes

        except DealsApiException as e:
            logger.error(f"Error getting deal history for {deal_id}: {e}")
            return []

    # ============================================================================
    # Sales Cycle Analysis
    # ============================================================================

    def calculate_sales_cycle(
        self,
        contact_id: str
    ) -> int:
        """
        Calculate days from lead creation to first closed-won deal.

        Args:
            contact_id: Contact ID

        Returns:
            int: Days in sales cycle, -1 if no closed deal
        """
        try:
            # Get contact creation date
            contact = self.get_contact(contact_id)

            # Search for closed-won deals associated with this contact
            public_object_search_request = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "dealstage",
                                "operator": "EQ",
                                "value": DealStage.CLOSED_WON.value
                            },
                            {
                                "propertyName": "associations.contact",
                                "operator": "EQ",
                                "value": contact_id
                            }
                        ]
                    }
                ],
                "properties": ["closedate", "createdate"],
                "sorts": [{"propertyName": "closedate", "direction": "ASCENDING"}],
                "limit": 1
            }

            api_response = self.deals_api.search_api.do_search(
                public_object_search_request=public_object_search_request
            )

            if api_response.total > 0:
                deal = api_response.results[0]
                close_date = datetime.fromisoformat(
                    deal.properties['closedate'].replace('Z', '+00:00')
                )

                cycle_days = (close_date - contact.created_at).days
                logger.info(f"Sales cycle for contact {contact_id}: {cycle_days} days")
                return cycle_days

            return -1

        except Exception as e:
            logger.error(f"Error calculating sales cycle for {contact_id}: {e}")
            return -1

    def get_avg_sales_cycle(
        self,
        pipeline: str = "default",
        days_back: int = 90
    ) -> float:
        """
        Get average sales cycle in days for closed-won deals.

        Args:
            pipeline: Pipeline ID
            days_back: Look back this many days

        Returns:
            float: Average days from contact creation to deal close
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            # Search for closed-won deals in timeframe
            public_object_search_request = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "dealstage",
                                "operator": "EQ",
                                "value": DealStage.CLOSED_WON.value
                            },
                            {
                                "propertyName": "pipeline",
                                "operator": "EQ",
                                "value": pipeline
                            },
                            {
                                "propertyName": "closedate",
                                "operator": "GTE",
                                "value": int(cutoff_date.timestamp() * 1000)
                            }
                        ]
                    }
                ],
                "properties": ["closedate"],
                "limit": 100
            }

            api_response = self.deals_api.search_api.do_search(
                public_object_search_request=public_object_search_request
            )

            if api_response.total == 0:
                return 0.0

            total_days = 0
            count = 0

            for deal_result in api_response.results:
                # Get full deal with associations
                deal = self.get_deal(deal_result.id)

                if deal.contact_id:
                    cycle = self.calculate_sales_cycle(deal.contact_id)
                    if cycle > 0:
                        total_days += cycle
                        count += 1

            avg = total_days / count if count > 0 else 0.0
            logger.info(f"Average sales cycle ({pipeline}): {avg:.1f} days ({count} deals)")
            return avg

        except Exception as e:
            logger.error(f"Error calculating average sales cycle: {e}")
            return 0.0

    # ============================================================================
    # Campaign Attribution
    # ============================================================================

    def attribute_deal_to_campaign(
        self,
        deal_id: str,
        campaign_id: str,
        meta_ad_id: str = None
    ) -> bool:
        """
        Attribute deal to ad campaign for ROAS tracking.

        Args:
            deal_id: Deal ID
            campaign_id: Campaign identifier
            meta_ad_id: Meta Ads campaign ID (optional)

        Returns:
            bool: True if successful
        """
        properties = {
            "campaign_id": campaign_id
        }

        if meta_ad_id:
            properties["meta_ad_id"] = meta_ad_id

        try:
            simple_public_object_input = {
                "properties": properties
            }

            self.deals_api.basic_api.update(
                deal_id=deal_id,
                simple_public_object_input=simple_public_object_input
            )

            logger.info(f"Attributed deal {deal_id} to campaign {campaign_id}")
            return True

        except DealsApiException as e:
            logger.error(f"Error attributing deal {deal_id}: {e}")
            return False

    def get_closed_deals_by_campaign(
        self,
        campaign_id: str,
        date_range: Tuple[datetime, datetime] = None
    ) -> List[Deal]:
        """
        Get all closed-won deals for a campaign.

        Args:
            campaign_id: Campaign ID
            date_range: Optional (start_date, end_date) tuple

        Returns:
            List[Deal]: Closed-won deals attributed to campaign
        """
        try:
            filters = [
                {
                    "propertyName": "dealstage",
                    "operator": "EQ",
                    "value": DealStage.CLOSED_WON.value
                },
                {
                    "propertyName": "campaign_id",
                    "operator": "EQ",
                    "value": campaign_id
                }
            ]

            # Add date range filter if provided
            if date_range:
                start_date, end_date = date_range
                filters.append({
                    "propertyName": "closedate",
                    "operator": "BETWEEN",
                    "value": int(start_date.timestamp() * 1000),
                    "highValue": int(end_date.timestamp() * 1000)
                })

            public_object_search_request = {
                "filterGroups": [{"filters": filters}],
                "properties": [
                    "dealname", "amount", "dealstage", "closedate",
                    "createdate", "campaign_id", "meta_ad_id", "pipeline"
                ],
                "limit": 100
            }

            api_response = self.deals_api.search_api.do_search(
                public_object_search_request=public_object_search_request
            )

            deals = []
            for result in api_response.results:
                deal = self.get_deal(result.id)
                deals.append(deal)

            logger.info(f"Found {len(deals)} closed deals for campaign {campaign_id}")
            return deals

        except DealsApiException as e:
            logger.error(f"Error getting deals for campaign {campaign_id}: {e}")
            return []

    def calculate_actual_roas(
        self,
        campaign_id: str,
        ad_spend: float,
        include_pending: bool = False
    ) -> float:
        """
        Calculate true ROAS from closed deals vs ad spend.

        Args:
            campaign_id: Campaign ID
            ad_spend: Total ad spend in dollars
            include_pending: Include pipeline deals at close probability

        Returns:
            float: ROAS (revenue / spend)
        """
        try:
            # Get closed-won deals
            closed_deals = self.get_closed_deals_by_campaign(campaign_id)
            total_revenue = sum(deal.amount for deal in closed_deals)

            # Optionally include pipeline at probability
            if include_pending:
                # Get deals in pipeline (not closed-won or lost)
                public_object_search_request = {
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "propertyName": "campaign_id",
                                    "operator": "EQ",
                                    "value": campaign_id
                                },
                                {
                                    "propertyName": "dealstage",
                                    "operator": "NEQ",
                                    "value": DealStage.CLOSED_WON.value
                                },
                                {
                                    "propertyName": "dealstage",
                                    "operator": "NEQ",
                                    "value": DealStage.CLOSED_LOST.value
                                }
                            ]
                        }
                    ],
                    "properties": ["amount", "dealstage"],
                    "limit": 100
                }

                api_response = self.deals_api.search_api.do_search(
                    public_object_search_request=public_object_search_request
                )

                # Apply stage-based close probability
                stage_probability = {
                    DealStage.APPOINTMENT_SCHEDULED.value: 0.10,
                    DealStage.QUALIFIED_TO_BUY.value: 0.25,
                    DealStage.PRESENTATION_SCHEDULED.value: 0.50,
                    DealStage.DECISION_MAKER_BOUGHT_IN.value: 0.75,
                    DealStage.CONTRACT_SENT.value: 0.90
                }

                for result in api_response.results:
                    amount = float(result.properties.get('amount', 0))
                    stage = result.properties.get('dealstage', '')
                    probability = stage_probability.get(stage, 0)
                    total_revenue += amount * probability

            # Calculate ROAS
            if ad_spend <= 0:
                logger.warning(f"Invalid ad spend: {ad_spend}")
                return 0.0

            roas = total_revenue / ad_spend
            logger.info(f"Campaign {campaign_id} ROAS: {roas:.2f}x (${total_revenue:,.2f} / ${ad_spend:,.2f})")
            return roas

        except Exception as e:
            logger.error(f"Error calculating ROAS for campaign {campaign_id}: {e}")
            return 0.0

    # ============================================================================
    # Pipeline Analytics
    # ============================================================================

    def get_pipeline_value(
        self,
        pipeline: str = "default",
        by_stage: bool = False
    ) -> Dict[str, float]:
        """
        Get total pipeline value.

        Args:
            pipeline: Pipeline ID
            by_stage: Return breakdown by stage

        Returns:
            Dict[str, float]: Total value or stage breakdown
        """
        try:
            public_object_search_request = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "pipeline",
                                "operator": "EQ",
                                "value": pipeline
                            },
                            {
                                "propertyName": "dealstage",
                                "operator": "NEQ",
                                "value": DealStage.CLOSED_LOST.value
                            }
                        ]
                    }
                ],
                "properties": ["amount", "dealstage"],
                "limit": 1000
            }

            api_response = self.deals_api.search_api.do_search(
                public_object_search_request=public_object_search_request
            )

            if by_stage:
                stage_values = {}
                for result in api_response.results:
                    stage = result.properties.get('dealstage', 'unknown')
                    amount = float(result.properties.get('amount', 0))
                    stage_values[stage] = stage_values.get(stage, 0) + amount

                return stage_values
            else:
                total = sum(
                    float(result.properties.get('amount', 0))
                    for result in api_response.results
                )
                return {"total": total}

        except DealsApiException as e:
            logger.error(f"Error getting pipeline value: {e}")
            return {}

    def get_conversion_rates(
        self,
        pipeline: str = "default"
    ) -> Dict[str, float]:
        """
        Get stage-to-stage conversion rates.

        Args:
            pipeline: Pipeline ID

        Returns:
            Dict[str, float]: Stage conversion percentages
        """
        try:
            # Get all deals in pipeline
            public_object_search_request = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "pipeline",
                                "operator": "EQ",
                                "value": pipeline
                            }
                        ]
                    }
                ],
                "properties": ["dealstage"],
                "limit": 1000
            }

            api_response = self.deals_api.search_api.do_search(
                public_object_search_request=public_object_search_request
            )

            # Count deals at each stage
            stage_counts = {}
            for result in api_response.results:
                stage = result.properties.get('dealstage', 'unknown')
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

            # Calculate conversion rates
            stages_ordered = [
                DealStage.APPOINTMENT_SCHEDULED.value,
                DealStage.QUALIFIED_TO_BUY.value,
                DealStage.PRESENTATION_SCHEDULED.value,
                DealStage.DECISION_MAKER_BOUGHT_IN.value,
                DealStage.CONTRACT_SENT.value,
                DealStage.CLOSED_WON.value
            ]

            conversion_rates = {}
            for i in range(len(stages_ordered) - 1):
                from_stage = stages_ordered[i]
                to_stage = stages_ordered[i + 1]

                # Count how many progressed past this stage
                advanced_count = sum(
                    stage_counts.get(s, 0)
                    for s in stages_ordered[i + 1:]
                )

                total_at_stage = advanced_count + stage_counts.get(from_stage, 0)

                if total_at_stage > 0:
                    rate = (advanced_count / total_at_stage) * 100
                    conversion_rates[f"{from_stage}_to_{to_stage}"] = rate

            return conversion_rates

        except DealsApiException as e:
            logger.error(f"Error calculating conversion rates: {e}")
            return {}

    # ============================================================================
    # Webhook Handling
    # ============================================================================

    def handle_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle HubSpot webhook events for real-time updates.

        Args:
            event_type: Webhook event type (contact.creation, deal.propertyChange, etc.)
            payload: Webhook payload

        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            logger.info(f"Processing webhook: {event_type}")

            if event_type == "contact.creation":
                # New contact created
                contact_id = payload.get('objectId')
                return {
                    "status": "success",
                    "action": "contact_created",
                    "contact_id": contact_id
                }

            elif event_type == "deal.propertyChange":
                # Deal property changed
                deal_id = payload.get('objectId')
                property_name = payload.get('propertyName')
                property_value = payload.get('propertyValue')

                if property_name == "dealstage":
                    # Stage changed - calculate time in previous stage
                    logger.info(f"Deal {deal_id} moved to stage {property_value}")

                return {
                    "status": "success",
                    "action": "deal_updated",
                    "deal_id": deal_id,
                    "property": property_name
                }

            elif event_type == "deal.creation":
                # New deal created
                deal_id = payload.get('objectId')
                return {
                    "status": "success",
                    "action": "deal_created",
                    "deal_id": deal_id
                }

            else:
                logger.warning(f"Unhandled webhook type: {event_type}")
                return {
                    "status": "ignored",
                    "event_type": event_type
                }

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# ============================================================================
# HubSpot CRM API v3 Direct Integration with Ad Performance Tracking
# ============================================================================

import httpx
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


class HubSpotAPIError(Exception):
    """Custom exception for HubSpot API errors."""
    pass


class HubSpotCRM:
    """
    HubSpot CRM API v3 direct integration for ad performance tracking.

    Features:
    - Sync deals with ad performance metrics
    - Track 5-day sales cycles
    - Update deal stages based on ad performance
    - Create/update contacts with retry logic
    - Proper error handling and exponential backoff

    Agent 21 - Complete HubSpot CRM Integration
    """

    BASE_URL = "https://api.hubapi.com"
    MAX_RETRIES = 3
    RETRY_WAIT_MIN = 1  # seconds
    RETRY_WAIT_MAX = 10  # seconds

    def __init__(self, access_token: str):
        """
        Initialize HubSpot CRM client with API access token.

        Args:
            access_token: HubSpot private app access token
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=self.headers
        )
        logger.info("HubSpot CRM API v3 client initialized")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
        retry=retry_if_exception_type((httpx.HTTPError, HubSpotAPIError)),
        reraise=True
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request to HubSpot API with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Dict: Response JSON

        Raises:
            HubSpotAPIError: If API returns error response
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data,
                params=params
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 5))
                logger.warning(f"Rate limited. Retrying after {retry_after}s")
                await asyncio.sleep(retry_after)
                raise HubSpotAPIError("Rate limit exceeded")

            # Handle errors
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('message', f'HTTP {response.status_code}')
                logger.error(f"HubSpot API error: {error_msg}")
                raise HubSpotAPIError(f"API error: {error_msg}")

            return response.json() if response.text else {}

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during request to {endpoint}: {e}")
            raise

    # ============================================================================
    # Deal Management
    # ============================================================================

    async def get_deal(self, deal_id: str) -> Dict:
        """
        Get deal by ID.

        Args:
            deal_id: HubSpot deal ID

        Returns:
            Dict: Deal properties and metadata
        """
        endpoint = f"/crm/v3/objects/deals/{deal_id}"
        params = {
            "properties": [
                "dealname", "amount", "dealstage", "pipeline", "closedate",
                "createdate", "campaign_id", "meta_ad_id", "ad_spend",
                "ad_impressions", "ad_clicks", "ad_ctr", "ad_cpc", "ad_roas"
            ],
            "associations": ["contacts"]
        }

        try:
            response = await self._make_request("GET", endpoint, params=params)
            logger.info(f"Retrieved deal {deal_id}")
            return response
        except Exception as e:
            logger.error(f"Error getting deal {deal_id}: {e}")
            raise

    async def create_deal(
        self,
        properties: Dict[str, Any],
        contact_id: Optional[str] = None
    ) -> Dict:
        """
        Create new deal.

        Args:
            properties: Deal properties
            contact_id: Optional contact ID to associate

        Returns:
            Dict: Created deal data
        """
        endpoint = "/crm/v3/objects/deals"

        # Set default 5-day close date if not provided
        if "closedate" not in properties:
            close_date = datetime.now() + timedelta(days=5)
            properties["closedate"] = close_date.strftime("%Y-%m-%d")

        data = {"properties": properties}

        # Add contact association if provided
        if contact_id:
            data["associations"] = [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 3  # Deal to Contact
                        }
                    ]
                }
            ]

        try:
            response = await self._make_request("POST", endpoint, data=data)
            deal_id = response.get("id")
            logger.info(f"Created deal {deal_id}: {properties.get('dealname')}")
            return response
        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            raise

    async def update_deal(self, deal_id: str, properties: Dict[str, Any]) -> Dict:
        """
        Update deal properties.

        Args:
            deal_id: Deal ID to update
            properties: Properties to update

        Returns:
            Dict: Updated deal data
        """
        endpoint = f"/crm/v3/objects/deals/{deal_id}"
        data = {"properties": properties}

        try:
            response = await self._make_request("PATCH", endpoint, data=data)
            logger.info(f"Updated deal {deal_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            raise

    async def sync_ad_performance_to_deal(
        self,
        deal_id: str,
        ad_metrics: Dict[str, Any]
    ) -> bool:
        """
        Sync ad performance metrics to deal.

        Args:
            deal_id: Deal ID
            ad_metrics: Ad performance data
                {
                    "campaign_id": str,
                    "ad_spend": float,
                    "impressions": int,
                    "clicks": int,
                    "conversions": int,
                    "ctr": float,
                    "cpc": float,
                    "roas": float
                }

        Returns:
            bool: True if successful
        """
        try:
            # Map ad metrics to HubSpot deal properties
            properties = {
                "campaign_id": ad_metrics.get("campaign_id", ""),
                "ad_spend": str(ad_metrics.get("ad_spend", 0)),
                "ad_impressions": str(ad_metrics.get("impressions", 0)),
                "ad_clicks": str(ad_metrics.get("clicks", 0)),
                "ad_ctr": str(ad_metrics.get("ctr", 0)),
                "ad_cpc": str(ad_metrics.get("cpc", 0)),
                "ad_roas": str(ad_metrics.get("roas", 0))
            }

            await self.update_deal(deal_id, properties)
            logger.info(f"Synced ad performance to deal {deal_id}")
            return True

        except Exception as e:
            logger.error(f"Error syncing ad performance to deal {deal_id}: {e}")
            return False

    async def update_deal_stage_based_on_performance(
        self,
        deal_id: str,
        ad_metrics: Dict[str, Any],
        performance_thresholds: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Update deal stage based on ad performance metrics.

        Args:
            deal_id: Deal ID
            ad_metrics: Ad performance data
            performance_thresholds: Custom thresholds for stage progression
                {
                    "high_engagement_ctr": 0.05,  # 5% CTR
                    "qualified_roas": 2.0,  # 2x ROAS
                    "winning_roas": 5.0  # 5x ROAS
                }

        Returns:
            bool: True if stage updated
        """
        # Default thresholds
        thresholds = performance_thresholds or {
            "high_engagement_ctr": 0.05,
            "qualified_roas": 2.0,
            "winning_roas": 5.0
        }

        try:
            # Get current deal
            deal = await self.get_deal(deal_id)
            current_stage = deal.get("properties", {}).get("dealstage")

            # Determine new stage based on performance
            ctr = ad_metrics.get("ctr", 0)
            roas = ad_metrics.get("roas", 0)

            new_stage = None

            # High ROAS indicates strong performance
            if roas >= thresholds["winning_roas"]:
                new_stage = DealStage.CLOSED_WON.value
            elif roas >= thresholds["qualified_roas"]:
                new_stage = DealStage.CONTRACT_SENT.value
            elif ctr >= thresholds["high_engagement_ctr"]:
                new_stage = DealStage.QUALIFIED_TO_BUY.value

            # Only update if stage should progress
            if new_stage and new_stage != current_stage:
                properties = {"dealstage": new_stage}

                # Set close date if moving to closed won
                if new_stage == DealStage.CLOSED_WON.value:
                    properties["closedate"] = datetime.now().strftime("%Y-%m-%d")

                await self.update_deal(deal_id, properties)
                logger.info(
                    f"Updated deal {deal_id} from {current_stage} to {new_stage} "
                    f"(CTR: {ctr:.2%}, ROAS: {roas:.2f}x)"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating deal stage for {deal_id}: {e}")
            return False

    # ============================================================================
    # Sales Cycle Tracking
    # ============================================================================

    async def track_sales_cycle(self, deal_id: str) -> Dict[str, Any]:
        """
        Calculate 5-day sales cycle metrics for a deal.

        Args:
            deal_id: Deal ID

        Returns:
            Dict: Sales cycle metrics
                {
                    "deal_id": str,
                    "created_at": datetime,
                    "closed_at": datetime,
                    "cycle_days": int,
                    "target_days": 5,
                    "on_track": bool,
                    "stage_history": List[Dict],
                    "current_stage": str,
                    "velocity_score": float  # 0-100, higher is better
                }
        """
        try:
            # Get deal details
            deal = await self.get_deal(deal_id)
            props = deal.get("properties", {})

            created_at = datetime.fromisoformat(
                props.get("createdate", "").replace("Z", "+00:00")
            )
            close_date = props.get("closedate")
            current_stage = props.get("dealstage", "")

            # Calculate cycle metrics
            now = datetime.now(created_at.tzinfo)
            cycle_days = (now - created_at).days

            # Check if deal is closed
            is_closed = current_stage in [
                DealStage.CLOSED_WON.value,
                DealStage.CLOSED_LOST.value
            ]

            if is_closed and close_date:
                closed_at = datetime.fromisoformat(
                    close_date.replace("Z", "+00:00")
                )
                cycle_days = (closed_at - created_at).days
            else:
                closed_at = None

            # Calculate velocity score (0-100)
            # Perfect score if closed won in <= 5 days
            target_days = 5
            if is_closed and current_stage == DealStage.CLOSED_WON.value:
                velocity_score = max(0, 100 - ((cycle_days - target_days) * 10))
            elif cycle_days <= target_days:
                # Partial score for in-progress deals
                velocity_score = 50 + (cycle_days / target_days * 50)
            else:
                # Penalty for overdue deals
                velocity_score = max(0, 50 - ((cycle_days - target_days) * 5))

            metrics = {
                "deal_id": deal_id,
                "deal_name": props.get("dealname", ""),
                "created_at": created_at.isoformat(),
                "closed_at": closed_at.isoformat() if closed_at else None,
                "cycle_days": cycle_days,
                "target_days": target_days,
                "on_track": cycle_days <= target_days,
                "current_stage": current_stage,
                "is_closed": is_closed,
                "velocity_score": round(velocity_score, 2),
                "amount": float(props.get("amount", 0)),
                "campaign_id": props.get("campaign_id", "")
            }

            logger.info(
                f"Sales cycle for deal {deal_id}: {cycle_days} days "
                f"(velocity: {velocity_score:.1f})"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error tracking sales cycle for deal {deal_id}: {e}")
            raise

    async def get_deals_by_cycle_status(
        self,
        status: str = "on_track"
    ) -> List[Dict]:
        """
        Get deals filtered by sales cycle status.

        Args:
            status: Filter status ('on_track', 'overdue', 'closed')

        Returns:
            List[Dict]: Deals matching status
        """
        try:
            # Search for open deals
            endpoint = "/crm/v3/objects/deals/search"

            filters = [
                {
                    "propertyName": "dealstage",
                    "operator": "NEQ",
                    "value": DealStage.CLOSED_LOST.value
                }
            ]

            # Add status-specific filters
            cutoff_date = datetime.now() - timedelta(days=5)

            if status == "on_track":
                # Created within last 5 days, not closed
                filters.append({
                    "propertyName": "createdate",
                    "operator": "GTE",
                    "value": int(cutoff_date.timestamp() * 1000)
                })
                filters.append({
                    "propertyName": "dealstage",
                    "operator": "NEQ",
                    "value": DealStage.CLOSED_WON.value
                })
            elif status == "overdue":
                # Created more than 5 days ago, not closed
                filters.append({
                    "propertyName": "createdate",
                    "operator": "LT",
                    "value": int(cutoff_date.timestamp() * 1000)
                })
                filters.append({
                    "propertyName": "dealstage",
                    "operator": "NEQ",
                    "value": DealStage.CLOSED_WON.value
                })
            elif status == "closed":
                filters = [{
                    "propertyName": "dealstage",
                    "operator": "EQ",
                    "value": DealStage.CLOSED_WON.value
                }]

            data = {
                "filterGroups": [{"filters": filters}],
                "properties": [
                    "dealname", "amount", "dealstage", "createdate",
                    "closedate", "campaign_id"
                ],
                "limit": 100
            }

            response = await self._make_request("POST", endpoint, data=data)
            deals = response.get("results", [])

            logger.info(f"Found {len(deals)} deals with status '{status}'")
            return deals

        except Exception as e:
            logger.error(f"Error getting deals by cycle status: {e}")
            return []

    # ============================================================================
    # Contact Management
    # ============================================================================

    async def create_contact(self, properties: Dict[str, Any]) -> Dict:
        """
        Create new contact.

        Args:
            properties: Contact properties (must include email)

        Returns:
            Dict: Created contact data
        """
        endpoint = "/crm/v3/objects/contacts"

        if "email" not in properties:
            raise ValueError("Email is required to create contact")

        data = {"properties": properties}

        try:
            response = await self._make_request("POST", endpoint, data=data)
            contact_id = response.get("id")
            logger.info(f"Created contact {contact_id}: {properties.get('email')}")
            return response
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            raise

    async def update_contact(
        self,
        contact_id: str,
        properties: Dict[str, Any]
    ) -> Dict:
        """
        Update contact properties.

        Args:
            contact_id: Contact ID
            properties: Properties to update

        Returns:
            Dict: Updated contact data
        """
        endpoint = f"/crm/v3/objects/contacts/{contact_id}"
        data = {"properties": properties}

        try:
            response = await self._make_request("PATCH", endpoint, data=data)
            logger.info(f"Updated contact {contact_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            raise

    async def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """
        Get contact by email address.

        Args:
            email: Contact email

        Returns:
            Optional[Dict]: Contact data if found
        """
        endpoint = "/crm/v3/objects/contacts/search"

        data = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email
                        }
                    ]
                }
            ],
            "properties": [
                "email", "firstname", "lastname", "phone", "company",
                "lifecyclestage", "utm_campaign", "utm_source"
            ],
            "limit": 1
        }

        try:
            response = await self._make_request("POST", endpoint, data=data)
            results = response.get("results", [])

            if results:
                contact = results[0]
                logger.info(f"Found contact by email: {email}")
                return contact

            return None

        except Exception as e:
            logger.error(f"Error searching for contact {email}: {e}")
            return None

    async def sync_contact(
        self,
        email: str,
        properties: Dict[str, Any]
    ) -> str:
        """
        Create or update contact by email.

        Args:
            email: Contact email
            properties: Contact properties to set/update

        Returns:
            str: Contact ID
        """
        properties["email"] = email

        try:
            # Check if contact exists
            existing = await self.get_contact_by_email(email)

            if existing:
                # Update existing
                contact_id = existing.get("id")
                await self.update_contact(contact_id, properties)
                logger.info(f"Updated existing contact: {email}")
                return contact_id
            else:
                # Create new
                contact = await self.create_contact(properties)
                contact_id = contact.get("id")
                logger.info(f"Created new contact: {email}")
                return contact_id

        except Exception as e:
            logger.error(f"Error syncing contact {email}: {e}")
            raise

    # ============================================================================
    # Association Management
    # ============================================================================

    async def associate_deal_with_contact(
        self,
        deal_id: str,
        contact_id: str
    ) -> bool:
        """
        Associate deal with contact.

        Args:
            deal_id: Deal ID
            contact_id: Contact ID

        Returns:
            bool: True if successful
        """
        endpoint = (
            f"/crm/v3/objects/deals/{deal_id}/associations/"
            f"contacts/{contact_id}/deal_to_contact"
        )

        try:
            await self._make_request("PUT", endpoint)
            logger.info(f"Associated deal {deal_id} with contact {contact_id}")
            return True
        except Exception as e:
            logger.error(f"Error associating deal with contact: {e}")
            return False
