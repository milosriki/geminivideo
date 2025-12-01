"""
Meta Conversion API Tracker - Real revenue tracking from Meta Ads
Tracks actual conversion values for Thompson Sampling optimization
"""
import os
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class MetaConversionTracker:
    """
    Tracks real conversion values from Meta Conversion API.
    Provides actual revenue data for Thompson Sampling budget optimization.
    """

    def __init__(self):
        """Initialize Meta Conversion Tracker"""
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        # Load credentials
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        self.pixel_id = os.getenv("META_PIXEL_ID")  # Optional

        if not self.access_token or not self.ad_account_id:
            logger.warning(
                "Meta credentials not configured. Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID "
                "to enable real conversion tracking."
            )

        logger.info("✅ Meta Conversion Tracker initialized")

    def get_ad_conversions(
        self,
        ad_id: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get conversion data for a specific ad.

        Args:
            ad_id: Meta Ad ID
            days_back: Number of days to look back (default: 7)

        Returns:
            Dictionary with conversion metrics and revenue
        """
        if not self.access_token:
            logger.error("META_ACCESS_TOKEN not configured")
            return {'error': 'META_ACCESS_TOKEN not set', 'conversions': 0, 'revenue': 0.0}

        try:
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Meta Ads Insights API
            params = {
                'access_token': self.access_token,
                'fields': ','.join([
                    'ad_id',
                    'ad_name',
                    'spend',
                    'actions',
                    'action_values',
                    'conversions',
                    'conversion_values',
                    'purchase_roas'
                ]),
                'time_range': json.dumps({
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                })
            }

            url = f"{self.base_url}/{ad_id}/insights"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data.get('data'):
                return {
                    'success': True,
                    'ad_id': ad_id,
                    'conversions': 0,
                    'revenue': 0.0,
                    'spend': 0.0,
                    'roas': 0.0
                }

            ad_data = data['data'][0]

            # Extract conversion count
            conversions = 0
            actions = ad_data.get('actions', [])
            for action in actions:
                if action.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    conversions = int(action.get('value', 0))
                    break

            # Extract revenue (action_values)
            revenue = 0.0
            action_values = ad_data.get('action_values', [])
            for value in action_values:
                if value.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    revenue = float(value.get('value', 0))
                    break

            # If no revenue in action_values, try conversion_values
            if revenue == 0.0:
                conversion_values = ad_data.get('conversion_values', [])
                if conversion_values:
                    revenue = sum(float(cv.get('value', 0)) for cv in conversion_values)

            spend = float(ad_data.get('spend', 0))
            roas = revenue / spend if spend > 0 else 0.0

            result = {
                'success': True,
                'ad_id': ad_id,
                'ad_name': ad_data.get('ad_name', 'Unknown'),
                'conversions': conversions,
                'revenue': revenue,
                'spend': spend,
                'roas': roas,
                'fetched_at': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Fetched conversions for ad {ad_id}: {conversions} conversions, ${revenue:.2f} revenue")

            return result

        except requests.RequestException as e:
            logger.error(f"Meta API request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'conversions': 0,
                'revenue': 0.0
            }
        except Exception as e:
            logger.error(f"Failed to get ad conversions: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'conversions': 0,
                'revenue': 0.0
            }

    def get_campaign_conversions(
        self,
        campaign_id: str,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get conversion data for an entire campaign.

        Args:
            campaign_id: Meta Campaign ID
            days_back: Number of days to look back (default: 7)

        Returns:
            Dictionary with campaign conversion metrics
        """
        if not self.access_token:
            logger.error("META_ACCESS_TOKEN not configured")
            return {'error': 'META_ACCESS_TOKEN not set', 'total_revenue': 0.0}

        try:
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Meta Campaign Insights API
            params = {
                'access_token': self.access_token,
                'fields': ','.join([
                    'campaign_id',
                    'campaign_name',
                    'spend',
                    'actions',
                    'action_values',
                    'purchase_roas'
                ]),
                'time_range': json.dumps({
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                })
            }

            url = f"{self.base_url}/{campaign_id}/insights"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data.get('data'):
                return {
                    'success': True,
                    'campaign_id': campaign_id,
                    'total_conversions': 0,
                    'total_revenue': 0.0,
                    'total_spend': 0.0,
                    'roas': 0.0
                }

            campaign_data = data['data'][0]

            # Extract total conversions
            total_conversions = 0
            actions = campaign_data.get('actions', [])
            for action in actions:
                if action.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    total_conversions = int(action.get('value', 0))
                    break

            # Extract total revenue
            total_revenue = 0.0
            action_values = campaign_data.get('action_values', [])
            for value in action_values:
                if value.get('action_type') in ['purchase', 'offsite_conversion.fb_pixel_purchase']:
                    total_revenue = float(value.get('value', 0))
                    break

            total_spend = float(campaign_data.get('spend', 0))
            roas = total_revenue / total_spend if total_spend > 0 else 0.0

            result = {
                'success': True,
                'campaign_id': campaign_id,
                'campaign_name': campaign_data.get('campaign_name', 'Unknown'),
                'total_conversions': total_conversions,
                'total_revenue': total_revenue,
                'total_spend': total_spend,
                'roas': roas,
                'fetched_at': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Campaign {campaign_id}: {total_conversions} conversions, ${total_revenue:.2f} revenue")

            return result

        except Exception as e:
            logger.error(f"Failed to get campaign conversions: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'total_revenue': 0.0
            }

    def get_variant_revenue(
        self,
        variant_id: str,
        variant_type: str = 'ad'
    ) -> float:
        """
        Get actual revenue for a specific variant (ad or campaign).
        This is used by Thompson Sampling for budget optimization.

        Args:
            variant_id: Meta Ad or Campaign ID
            variant_type: Type of variant ('ad' or 'campaign')

        Returns:
            Total revenue as float
        """
        try:
            if variant_type == 'ad':
                result = self.get_ad_conversions(variant_id, days_back=7)
            elif variant_type == 'campaign':
                result = self.get_campaign_conversions(variant_id, days_back=7)
            else:
                logger.warning(f"Unknown variant type: {variant_type}")
                return 0.0

            if not result.get('success'):
                logger.warning(f"Failed to get revenue for variant {variant_id}: {result.get('error')}")
                return 0.0

            revenue = result.get('revenue') or result.get('total_revenue', 0.0)
            return float(revenue)

        except Exception as e:
            logger.error(f"Failed to get variant revenue: {e}")
            return 0.0

    def track_conversion_event(
        self,
        event_name: str,
        event_time: Optional[datetime] = None,
        value: Optional[float] = None,
        currency: str = "USD",
        user_data: Optional[Dict] = None,
        custom_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send a conversion event to Meta Conversion API (server-side tracking).
        Useful for tracking conversions that happen outside Meta (e.g., HubSpot sales).

        Args:
            event_name: Event name (e.g., 'Purchase', 'Lead')
            event_time: When the event occurred (default: now)
            value: Conversion value in currency units
            currency: Currency code (default: USD)
            user_data: User information (email, phone, etc.)
            custom_data: Additional custom data

        Returns:
            Dictionary with API response
        """
        if not self.pixel_id or not self.access_token:
            logger.warning("META_PIXEL_ID or META_ACCESS_TOKEN not configured for Conversion API")
            return {
                'success': False,
                'error': 'META_PIXEL_ID or META_ACCESS_TOKEN not set'
            }

        try:
            if event_time is None:
                event_time = datetime.utcnow()

            # Build event payload
            event_data = {
                'event_name': event_name,
                'event_time': int(event_time.timestamp()),
                'action_source': 'website'
            }

            if value is not None:
                event_data['value'] = value
                event_data['currency'] = currency

            if user_data:
                event_data['user_data'] = user_data

            if custom_data:
                event_data['custom_data'] = custom_data

            # Send to Conversion API
            url = f"{self.base_url}/{self.pixel_id}/events"
            payload = {
                'data': [event_data],
                'access_token': self.access_token
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            logger.info(f"✅ Sent conversion event to Meta: {event_name}, value: ${value}")

            return {
                'success': True,
                'event_name': event_name,
                'response': result
            }

        except Exception as e:
            logger.error(f"Failed to track conversion event: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
meta_conversion_tracker = MetaConversionTracker()
