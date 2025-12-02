"""
Unit tests for Anytrack Integration.

Tests all methods with mocked HTTP responses to ensure proper API integration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os

from anytrack import (
    AnytrackIntegration,
    AnytrackConversion,
    AffiliatePerformance,
    ConversionType,
    AnytrackAPIError
)


class TestAnytrackIntegration(unittest.TestCase):
    """Test Anytrack integration methods."""

    def setUp(self):
        """Set up test client."""
        self.api_key = "test_api_key_12345"
        self.account_id = "test_account_67890"
        self.client = AnytrackIntegration(
            api_key=self.api_key,
            account_id=self.account_id
        )

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.account_id, self.account_id)
        self.assertEqual(
            self.client.session.headers["Authorization"],
            f"Bearer {self.api_key}"
        )
        self.assertEqual(
            self.client.session.headers["X-Account-ID"],
            self.account_id
        )

    @patch('anytrack.requests.Session.request')
    def test_track_conversion(self, mock_request):
        """Test tracking a conversion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "conversion_id": "conv_123"
        }
        mock_request.return_value = mock_response

        result = self.client.track_conversion(
            click_id="clk_abc",
            conversion_type=ConversionType.SALE,
            revenue=99.99,
            currency="USD",
            order_id="ORD-123"
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["conversion_id"], "conv_123")
        mock_request.assert_called_once()

    @patch('anytrack.requests.Session.request')
    def test_track_sale(self, mock_request):
        """Test tracking a sale."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "conversion_id": "conv_456"
        }
        mock_request.return_value = mock_response

        result = self.client.track_sale(
            click_id="clk_xyz",
            revenue=149.99,
            currency="USD",
            order_id="ORD-456",
            product_id="PROD-001"
        )

        self.assertEqual(result["status"], "success")

    @patch('anytrack.requests.Session.request')
    def test_track_lead(self, mock_request):
        """Test tracking a lead."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "conversion_id": "conv_789"
        }
        mock_request.return_value = mock_response

        result = self.client.track_lead(
            click_id="clk_lead",
            lead_id="LEAD-123",
            value=25.0
        )

        self.assertEqual(result["status"], "success")

    @patch('anytrack.requests.Session.request')
    def test_get_conversions(self, mock_request):
        """Test getting conversions."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "conv_1",
                    "click_id": "clk_1",
                    "conversion_type": "sale",
                    "revenue": "99.99",
                    "currency": "USD",
                    "source": "facebook",
                    "campaign_id": "camp_1",
                    "ad_id": "ad_1",
                    "timestamp": "2025-12-01T10:00:00",
                    "sub_ids": {"sub1": "value1"},
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0"
                }
            ]
        }
        mock_request.return_value = mock_response

        date_from = datetime(2025, 12, 1)
        date_to = datetime(2025, 12, 2)
        conversions = self.client.get_conversions(date_from, date_to)

        self.assertEqual(len(conversions), 1)
        self.assertEqual(conversions[0].id, "conv_1")
        self.assertEqual(conversions[0].revenue, 99.99)
        self.assertEqual(conversions[0].conversion_type, ConversionType.SALE)

    @patch('anytrack.requests.Session.request')
    def test_get_conversion_details(self, mock_request):
        """Test getting conversion details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "conv_detail",
                "click_id": "clk_detail",
                "conversion_type": "lead",
                "revenue": "50.00",
                "currency": "USD",
                "source": "google",
                "campaign_id": "camp_2",
                "timestamp": "2025-12-01T12:00:00",
                "sub_ids": {},
                "ip_address": "10.0.0.1",
                "user_agent": "Chrome"
            }
        }
        mock_request.return_value = mock_response

        conversion = self.client.get_conversion_details("conv_detail")

        self.assertEqual(conversion.id, "conv_detail")
        self.assertEqual(conversion.conversion_type, ConversionType.LEAD)
        self.assertEqual(conversion.revenue, 50.0)

    @patch('anytrack.requests.Session.request')
    def test_calculate_attribution(self, mock_request):
        """Test attribution calculation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "last_click",
            "weights": {"touchpoint_1": 1.0}
        }
        mock_request.return_value = mock_response

        attribution = self.client.calculate_attribution("conv_123")

        self.assertEqual(attribution["model"], "last_click")
        self.assertIn("weights", attribution)

    @patch('anytrack.requests.Session.request')
    def test_get_touchpoints(self, mock_request):
        """Test getting touchpoints."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "type": "click",
                    "source": "facebook",
                    "timestamp": "2025-12-01T09:00:00"
                },
                {
                    "type": "view",
                    "source": "google",
                    "timestamp": "2025-12-01T08:00:00"
                }
            ]
        }
        mock_request.return_value = mock_response

        touchpoints = self.client.get_touchpoints("conv_123")

        self.assertEqual(len(touchpoints), 2)
        self.assertEqual(touchpoints[0]["type"], "click")
        self.assertEqual(touchpoints[1]["source"], "google")

    @patch('anytrack.requests.Session.request')
    def test_get_affiliate_performance(self, mock_request):
        """Test getting affiliate performance."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "clicks": 1000,
                "conversions": 50,
                "revenue": "5000.00",
                "epc": "5.00",
                "conversion_rate": "0.05"
            }
        }
        mock_request.return_value = mock_response

        perf = self.client.get_affiliate_performance("aff_123")

        self.assertEqual(perf.affiliate_id, "aff_123")
        self.assertEqual(perf.clicks, 1000)
        self.assertEqual(perf.conversions, 50)
        self.assertEqual(perf.revenue, 5000.0)
        self.assertEqual(perf.epc, 5.0)
        self.assertEqual(perf.conversion_rate, 0.05)

    @patch('anytrack.requests.Session.request')
    def test_get_top_affiliates(self, mock_request):
        """Test getting top affiliates."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "affiliate_id": "aff_1",
                    "clicks": 2000,
                    "conversions": 100,
                    "revenue": "10000.00",
                    "epc": "5.00",
                    "conversion_rate": "0.05"
                },
                {
                    "affiliate_id": "aff_2",
                    "clicks": 1500,
                    "conversions": 60,
                    "revenue": "6000.00",
                    "epc": "4.00",
                    "conversion_rate": "0.04"
                }
            ]
        }
        mock_request.return_value = mock_response

        top_affs = self.client.get_top_affiliates(metric="revenue", limit=2)

        self.assertEqual(len(top_affs), 2)
        self.assertEqual(top_affs[0].affiliate_id, "aff_1")
        self.assertEqual(top_affs[0].revenue, 10000.0)

    @patch('anytrack.requests.Session.request')
    def test_get_daily_report(self, mock_request):
        """Test getting daily report."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_revenue": 15000.0,
            "total_conversions": 150,
            "avg_order_value": 100.0
        }
        mock_request.return_value = mock_response

        report = self.client.get_daily_report(datetime(2025, 12, 1))

        self.assertEqual(report["total_revenue"], 15000.0)
        self.assertEqual(report["total_conversions"], 150)

    @patch('anytrack.requests.Session.request')
    def test_api_error_handling(self, mock_request):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = Exception("HTTP 400")
        mock_request.return_value = mock_response

        with self.assertRaises(Exception):
            self.client.track_conversion(
                click_id="invalid",
                conversion_type=ConversionType.SALE
            )

    def test_sync_with_meta_capi(self):
        """Test Meta CAPI sync."""
        mock_meta_client = Mock()
        mock_meta_client.send_event.return_value = True

        conversion = AnytrackConversion(
            id="conv_meta",
            click_id="clk_meta",
            conversion_type=ConversionType.SALE,
            revenue=199.99,
            currency="USD",
            source="facebook",
            campaign_id="camp_fb",
            ad_id="ad_fb",
            timestamp=datetime.utcnow(),
            sub_ids={},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )

        result = self.client.sync_with_meta_capi(conversion, mock_meta_client)

        self.assertTrue(result)
        mock_meta_client.send_event.assert_called_once()

    def test_sync_with_hubspot(self):
        """Test HubSpot sync."""
        mock_hubspot_client = Mock()
        mock_hubspot_client.create_deal.return_value = {"id": "deal_123"}

        conversion = AnytrackConversion(
            id="conv_hs",
            click_id="clk_hs",
            conversion_type=ConversionType.LEAD,
            revenue=50.0,
            currency="USD",
            source="google",
            campaign_id="camp_g",
            ad_id=None,
            timestamp=datetime.utcnow(),
            sub_ids={},
            ip_address="10.0.0.1",
            user_agent="Chrome"
        )

        result = self.client.sync_with_hubspot(conversion, mock_hubspot_client)

        self.assertTrue(result)
        mock_hubspot_client.create_deal.assert_called_once()

    @patch('anytrack.open', create=True)
    @patch('anytrack.requests.Session.request')
    def test_export_conversions_csv(self, mock_request, mock_open):
        """Test CSV export."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "conv_csv",
                    "click_id": "clk_csv",
                    "conversion_type": "sale",
                    "revenue": "299.99",
                    "currency": "USD",
                    "source": "tiktok",
                    "campaign_id": "camp_tt",
                    "timestamp": "2025-12-01T15:00:00",
                    "sub_ids": {},
                    "ip_address": "172.16.0.1"
                }
            ]
        }
        mock_request.return_value = mock_response

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        date_from = datetime(2025, 12, 1)
        date_to = datetime(2025, 12, 2)

        csv_path = self.client.export_conversions_csv(
            date_range=(date_from, date_to),
            output_path="/tmp/test.csv"
        )

        self.assertEqual(csv_path, "/tmp/test.csv")
        mock_open.assert_called_once_with("/tmp/test.csv", 'w', newline='')


if __name__ == "__main__":
    unittest.main()
