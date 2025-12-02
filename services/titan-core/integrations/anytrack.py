"""
Anytrack API Integration for Affiliate/Conversion Tracking.

Real implementation with full error handling, cross-platform sync,
and attribution tracking. NO mock data.
"""

import requests
import logging
import csv
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ConversionType(Enum):
    """Conversion event types."""
    SALE = "sale"
    LEAD = "lead"
    SIGNUP = "signup"
    CUSTOM = "custom"


@dataclass
class AnytrackConversion:
    """Anytrack conversion data structure."""
    id: str
    click_id: str
    conversion_type: ConversionType
    revenue: float
    currency: str
    source: str
    campaign_id: str
    ad_id: Optional[str]
    timestamp: datetime
    sub_ids: Dict[str, str]
    ip_address: Optional[str]
    user_agent: Optional[str]


@dataclass
class AffiliatePerformance:
    """Affiliate performance metrics."""
    affiliate_id: str
    clicks: int
    conversions: int
    revenue: float
    epc: float  # Earnings per click
    conversion_rate: float


class AnytrackAPIError(Exception):
    """Anytrack API error."""
    pass


class AnytrackIntegration:
    """Anytrack API integration for affiliate/conversion tracking."""

    BASE_URL = "https://api.anytrack.io/v1"

    def __init__(self, api_key: str, account_id: str):
        """
        Initialize Anytrack client.

        Args:
            api_key: Anytrack API key
            account_id: Anytrack account ID
        """
        self.api_key = api_key
        self.account_id = account_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Account-ID": account_id
        })
        logger.info(f"Initialized Anytrack client for account {account_id}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make API request with error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            API response data

        Raises:
            AnytrackAPIError: On API errors
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"Anytrack API error: {e.response.status_code}"
            if e.response.text:
                error_msg += f" - {e.response.text}"
            logger.error(error_msg)
            raise AnytrackAPIError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            raise AnytrackAPIError(error_msg)

    # Conversion Tracking

    def track_conversion(
        self,
        click_id: str,
        conversion_type: ConversionType,
        revenue: float = 0,
        currency: str = "USD",
        order_id: str = None,
        custom_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Track a conversion event.

        Args:
            click_id: Click identifier
            conversion_type: Type of conversion
            revenue: Conversion revenue
            currency: Currency code
            order_id: Order/transaction ID
            custom_data: Custom conversion data

        Returns:
            Conversion tracking response
        """
        payload = {
            "click_id": click_id,
            "conversion_type": conversion_type.value,
            "revenue": revenue,
            "currency": currency,
            "timestamp": datetime.utcnow().isoformat(),
            "order_id": order_id,
            "custom_data": custom_data or {}
        }

        logger.info(f"Tracking {conversion_type.value} conversion for click {click_id}")
        return self._make_request("POST", "conversions", data=payload)

    def track_sale(
        self,
        click_id: str,
        revenue: float,
        currency: str = "USD",
        order_id: str = None,
        product_id: str = None
    ) -> Dict[str, Any]:
        """
        Track a sale conversion.

        Args:
            click_id: Click identifier
            revenue: Sale amount
            currency: Currency code
            order_id: Order ID
            product_id: Product identifier

        Returns:
            Sale tracking response
        """
        custom_data = {"product_id": product_id} if product_id else None
        return self.track_conversion(
            click_id=click_id,
            conversion_type=ConversionType.SALE,
            revenue=revenue,
            currency=currency,
            order_id=order_id,
            custom_data=custom_data
        )

    def track_lead(
        self,
        click_id: str,
        lead_id: str = None,
        value: float = 0
    ) -> Dict[str, Any]:
        """
        Track a lead conversion.

        Args:
            click_id: Click identifier
            lead_id: Lead identifier
            value: Lead value

        Returns:
            Lead tracking response
        """
        custom_data = {"lead_id": lead_id} if lead_id else None
        return self.track_conversion(
            click_id=click_id,
            conversion_type=ConversionType.LEAD,
            revenue=value,
            custom_data=custom_data
        )

    # Conversion Retrieval

    def get_conversions(
        self,
        date_from: datetime,
        date_to: datetime,
        source: str = None,
        campaign_id: str = None
    ) -> List[AnytrackConversion]:
        """
        Get conversions for date range.

        Args:
            date_from: Start date
            date_to: End date
            source: Filter by traffic source
            campaign_id: Filter by campaign

        Returns:
            List of conversions
        """
        params = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat()
        }

        if source:
            params["source"] = source
        if campaign_id:
            params["campaign_id"] = campaign_id

        logger.info(f"Fetching conversions from {date_from} to {date_to}")
        response = self._make_request("GET", "conversions", params=params)

        return [
            AnytrackConversion(
                id=conv["id"],
                click_id=conv["click_id"],
                conversion_type=ConversionType(conv["conversion_type"]),
                revenue=float(conv["revenue"]),
                currency=conv["currency"],
                source=conv["source"],
                campaign_id=conv["campaign_id"],
                ad_id=conv.get("ad_id"),
                timestamp=datetime.fromisoformat(conv["timestamp"]),
                sub_ids=conv.get("sub_ids", {}),
                ip_address=conv.get("ip_address"),
                user_agent=conv.get("user_agent")
            )
            for conv in response.get("data", [])
        ]

    def get_conversions_by_source(
        self,
        source_id: str,
        date_range: tuple = None
    ) -> List[AnytrackConversion]:
        """
        Get conversions by traffic source.

        Args:
            source_id: Traffic source identifier
            date_range: (start_date, end_date) tuple, defaults to last 30 days

        Returns:
            List of conversions
        """
        if date_range:
            date_from, date_to = date_range
        else:
            date_to = datetime.utcnow()
            date_from = date_to - timedelta(days=30)

        return self.get_conversions(
            date_from=date_from,
            date_to=date_to,
            source=source_id
        )

    def get_conversion_details(
        self,
        conversion_id: str
    ) -> AnytrackConversion:
        """
        Get detailed conversion info.

        Args:
            conversion_id: Conversion identifier

        Returns:
            Conversion details
        """
        logger.info(f"Fetching details for conversion {conversion_id}")
        response = self._make_request("GET", f"conversions/{conversion_id}")

        conv = response["data"]
        return AnytrackConversion(
            id=conv["id"],
            click_id=conv["click_id"],
            conversion_type=ConversionType(conv["conversion_type"]),
            revenue=float(conv["revenue"]),
            currency=conv["currency"],
            source=conv["source"],
            campaign_id=conv["campaign_id"],
            ad_id=conv.get("ad_id"),
            timestamp=datetime.fromisoformat(conv["timestamp"]),
            sub_ids=conv.get("sub_ids", {}),
            ip_address=conv.get("ip_address"),
            user_agent=conv.get("user_agent")
        )

    # Cross-Platform Sync

    def sync_with_meta_capi(
        self,
        conversion: AnytrackConversion,
        meta_capi_client
    ) -> bool:
        """
        Sync conversion to Meta CAPI.

        Args:
            conversion: Conversion to sync
            meta_capi_client: Meta CAPI client instance

        Returns:
            Success status
        """
        try:
            logger.info(f"Syncing conversion {conversion.id} to Meta CAPI")

            # Map Anytrack conversion to Meta event
            event_data = {
                "event_name": "Purchase" if conversion.conversion_type == ConversionType.SALE else "Lead",
                "event_time": int(conversion.timestamp.timestamp()),
                "action_source": "website",
                "user_data": {
                    "client_ip_address": conversion.ip_address,
                    "client_user_agent": conversion.user_agent
                },
                "custom_data": {
                    "value": conversion.revenue,
                    "currency": conversion.currency,
                    "content_ids": [conversion.id]
                }
            }

            # Send to Meta CAPI
            meta_capi_client.send_event(event_data)
            logger.info(f"Successfully synced conversion {conversion.id} to Meta CAPI")
            return True

        except Exception as e:
            logger.error(f"Failed to sync to Meta CAPI: {str(e)}")
            return False

    def sync_with_hubspot(
        self,
        conversion: AnytrackConversion,
        hubspot_client
    ) -> bool:
        """
        Sync conversion to HubSpot as deal.

        Args:
            conversion: Conversion to sync
            hubspot_client: HubSpot client instance

        Returns:
            Success status
        """
        try:
            logger.info(f"Syncing conversion {conversion.id} to HubSpot")

            # Create HubSpot deal
            deal_data = {
                "properties": {
                    "dealname": f"Conversion {conversion.id}",
                    "amount": conversion.revenue,
                    "dealstage": "closedwon" if conversion.conversion_type == ConversionType.SALE else "qualifiedtobuy",
                    "pipeline": "default",
                    "closedate": conversion.timestamp.isoformat(),
                    "source": conversion.source,
                    "campaign": conversion.campaign_id
                }
            }

            hubspot_client.create_deal(deal_data)
            logger.info(f"Successfully synced conversion {conversion.id} to HubSpot")
            return True

        except Exception as e:
            logger.error(f"Failed to sync to HubSpot: {str(e)}")
            return False

    # Attribution

    def calculate_attribution(
        self,
        conversion_id: str
    ) -> Dict[str, Any]:
        """
        Get attribution data for conversion.

        Args:
            conversion_id: Conversion identifier

        Returns:
            Attribution data including model and touchpoint weights
        """
        logger.info(f"Calculating attribution for conversion {conversion_id}")
        return self._make_request("GET", f"conversions/{conversion_id}/attribution")

    def get_touchpoints(
        self,
        conversion_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all touchpoints for a conversion.

        Args:
            conversion_id: Conversion identifier

        Returns:
            List of touchpoints in customer journey
        """
        logger.info(f"Fetching touchpoints for conversion {conversion_id}")
        response = self._make_request("GET", f"conversions/{conversion_id}/touchpoints")
        return response.get("data", [])

    # Affiliate Analytics

    def get_affiliate_performance(
        self,
        affiliate_id: str,
        date_range: tuple = None
    ) -> AffiliatePerformance:
        """
        Get affiliate performance metrics.

        Args:
            affiliate_id: Affiliate identifier
            date_range: (start_date, end_date) tuple, defaults to last 30 days

        Returns:
            Affiliate performance data
        """
        if date_range:
            date_from, date_to = date_range
        else:
            date_to = datetime.utcnow()
            date_from = date_to - timedelta(days=30)

        params = {
            "affiliate_id": affiliate_id,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat()
        }

        logger.info(f"Fetching performance for affiliate {affiliate_id}")
        response = self._make_request("GET", "affiliates/performance", params=params)

        data = response["data"]
        return AffiliatePerformance(
            affiliate_id=affiliate_id,
            clicks=data["clicks"],
            conversions=data["conversions"],
            revenue=float(data["revenue"]),
            epc=float(data["epc"]),
            conversion_rate=float(data["conversion_rate"])
        )

    def get_top_affiliates(
        self,
        metric: str = "revenue",
        limit: int = 10,
        date_range: tuple = None
    ) -> List[AffiliatePerformance]:
        """
        Get top performing affiliates.

        Args:
            metric: Sort metric (revenue, conversions, epc, conversion_rate)
            limit: Number of affiliates to return
            date_range: (start_date, end_date) tuple, defaults to last 30 days

        Returns:
            List of top affiliate performances
        """
        if date_range:
            date_from, date_to = date_range
        else:
            date_to = datetime.utcnow()
            date_from = date_to - timedelta(days=30)

        params = {
            "sort_by": metric,
            "limit": limit,
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat()
        }

        logger.info(f"Fetching top {limit} affiliates by {metric}")
        response = self._make_request("GET", "affiliates/top", params=params)

        return [
            AffiliatePerformance(
                affiliate_id=aff["affiliate_id"],
                clicks=aff["clicks"],
                conversions=aff["conversions"],
                revenue=float(aff["revenue"]),
                epc=float(aff["epc"]),
                conversion_rate=float(aff["conversion_rate"])
            )
            for aff in response.get("data", [])
        ]

    # Reporting

    def get_daily_report(
        self,
        date: datetime
    ) -> Dict[str, Any]:
        """
        Get daily conversion report.

        Args:
            date: Report date

        Returns:
            Daily report with aggregated metrics
        """
        params = {
            "date": date.strftime("%Y-%m-%d")
        }

        logger.info(f"Fetching daily report for {date.strftime('%Y-%m-%d')}")
        return self._make_request("GET", "reports/daily", params=params)

    def export_conversions_csv(
        self,
        date_range: tuple,
        output_path: str
    ) -> str:
        """
        Export conversions to CSV.

        Args:
            date_range: (start_date, end_date) tuple
            output_path: Output file path

        Returns:
            Path to exported CSV file
        """
        date_from, date_to = date_range
        conversions = self.get_conversions(date_from, date_to)

        logger.info(f"Exporting {len(conversions)} conversions to {output_path}")

        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'id', 'click_id', 'conversion_type', 'revenue', 'currency',
                'source', 'campaign_id', 'ad_id', 'timestamp', 'ip_address'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for conv in conversions:
                writer.writerow({
                    'id': conv.id,
                    'click_id': conv.click_id,
                    'conversion_type': conv.conversion_type.value,
                    'revenue': conv.revenue,
                    'currency': conv.currency,
                    'source': conv.source,
                    'campaign_id': conv.campaign_id,
                    'ad_id': conv.ad_id or '',
                    'timestamp': conv.timestamp.isoformat(),
                    'ip_address': conv.ip_address or ''
                })

        logger.info(f"Successfully exported conversions to {output_path}")
        return output_path
