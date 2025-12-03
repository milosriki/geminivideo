"""
HubSpot Integration - Production Test Suite

Tests real API functionality (requires valid HUBSPOT_ACCESS_TOKEN)
"""

import os
import unittest
from datetime import datetime, timedelta
from hubspot import HubSpotIntegration, DealStage, Contact, Deal


class TestHubSpotIntegration(unittest.TestCase):
    """Test suite for HubSpot CRM integration."""
    
    @classmethod
    def setUpClass(cls):
        """Initialize HubSpot client."""
        token = os.getenv('HUBSPOT_ACCESS_TOKEN')
        if not token:
            raise ValueError("HUBSPOT_ACCESS_TOKEN environment variable required")
        
        cls.hubspot = HubSpotIntegration(access_token=token)
        cls.test_email = f"test+{int(datetime.now().timestamp())}@example.com"
    
    def test_01_sync_contact(self):
        """Test contact creation/sync."""
        contact_id = self.hubspot.sync_contact(
            email=self.test_email,
            properties={
                "firstname": "Test",
                "lastname": "User",
                "phone": "+1-555-TEST",
                "lifecyclestage": "lead"
            }
        )
        
        self.assertIsNotNone(contact_id)
        self.assertTrue(len(contact_id) > 0)
        
        # Store for other tests
        self.__class__.test_contact_id = contact_id
    
    def test_02_get_contact(self):
        """Test contact retrieval."""
        contact = self.hubspot.get_contact(self.__class__.test_contact_id)
        
        self.assertIsInstance(contact, Contact)
        self.assertEqual(contact.email, self.test_email)
        self.assertEqual(contact.first_name, "Test")
        self.assertEqual(contact.last_name, "User")
    
    def test_03_add_utm_tracking(self):
        """Test UTM parameter addition."""
        success = self.hubspot.add_utm_to_contact(
            contact_id=self.__class__.test_contact_id,
            utm_campaign="test_campaign",
            utm_source="test_source",
            utm_medium="test_medium"
        )
        
        self.assertTrue(success)
    
    def test_04_create_deal(self):
        """Test deal creation."""
        deal_id = self.hubspot.create_deal(
            contact_id=self.__class__.test_contact_id,
            deal_name="Test Deal",
            amount=5000.00,
            stage=DealStage.APPOINTMENT_SCHEDULED
        )
        
        self.assertIsNotNone(deal_id)
        self.assertTrue(len(deal_id) > 0)
        
        # Store for other tests
        self.__class__.test_deal_id = deal_id
    
    def test_05_attribute_to_campaign(self):
        """Test campaign attribution."""
        success = self.hubspot.attribute_deal_to_campaign(
            deal_id=self.__class__.test_deal_id,
            campaign_id="test_campaign_001",
            meta_ad_id="123456789"
        )
        
        self.assertTrue(success)
    
    def test_06_update_deal_stage(self):
        """Test deal stage progression."""
        stages = [
            DealStage.QUALIFIED_TO_BUY,
            DealStage.PRESENTATION_SCHEDULED,
            DealStage.DECISION_MAKER_BOUGHT_IN,
            DealStage.CONTRACT_SENT
        ]
        
        for stage in stages:
            success = self.hubspot.update_deal_stage(
                self.__class__.test_deal_id,
                stage
            )
            self.assertTrue(success)
    
    def test_07_get_deal(self):
        """Test deal retrieval."""
        deal = self.hubspot.get_deal(self.__class__.test_deal_id)
        
        self.assertIsInstance(deal, Deal)
        self.assertEqual(deal.name, "Test Deal")
        self.assertEqual(deal.amount, 5000.00)
        self.assertEqual(deal.contact_id, self.__class__.test_contact_id)
    
    def test_08_close_deal(self):
        """Test closing deal."""
        success = self.hubspot.update_deal_stage(
            self.__class__.test_deal_id,
            DealStage.CLOSED_WON
        )
        
        self.assertTrue(success)
    
    def test_09_calculate_sales_cycle(self):
        """Test sales cycle calculation."""
        days = self.hubspot.calculate_sales_cycle(
            self.__class__.test_contact_id
        )
        
        self.assertGreaterEqual(days, 0)
    
    def test_10_get_pipeline_value(self):
        """Test pipeline value calculation."""
        pipeline_value = self.hubspot.get_pipeline_value(
            pipeline="default",
            by_stage=True
        )
        
        self.assertIsInstance(pipeline_value, dict)
    
    def test_11_get_conversion_rates(self):
        """Test conversion rate calculation."""
        conversion_rates = self.hubspot.get_conversion_rates(
            pipeline="default"
        )
        
        self.assertIsInstance(conversion_rates, dict)
    
    def test_12_calculate_roas(self):
        """Test ROAS calculation."""
        roas = self.hubspot.calculate_actual_roas(
            campaign_id="test_campaign_001",
            ad_spend=1000.00,
            include_pending=False
        )
        
        self.assertGreaterEqual(roas, 0.0)
    
    def test_13_webhook_handling(self):
        """Test webhook event handling."""
        result = self.hubspot.handle_webhook(
            event_type="deal.propertyChange",
            payload={
                "objectId": self.__class__.test_deal_id,
                "propertyName": "dealstage",
                "propertyValue": "closedwon"
            }
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["action"], "deal_updated")


class TestDataModels(unittest.TestCase):
    """Test data model structures."""
    
    def test_deal_stage_enum(self):
        """Test DealStage enum values."""
        self.assertEqual(
            DealStage.APPOINTMENT_SCHEDULED.value,
            "appointmentscheduled"
        )
        self.assertEqual(
            DealStage.CLOSED_WON.value,
            "closedwon"
        )
    
    def test_contact_dataclass(self):
        """Test Contact dataclass."""
        contact = Contact(
            id="123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone="+1-555-0100",
            company="Test Co",
            lifecycle_stage="lead",
            lead_source="organic",
            utm_campaign="test",
            utm_source="google",
            created_at=datetime.now()
        )
        
        self.assertEqual(contact.id, "123")
        self.assertEqual(contact.email, "test@example.com")
    
    def test_deal_dataclass(self):
        """Test Deal dataclass."""
        deal = Deal(
            id="456",
            name="Test Deal",
            amount=10000.00,
            stage=DealStage.QUALIFIED_TO_BUY,
            contact_id="123",
            campaign_id="campaign_001",
            close_date=datetime.now() + timedelta(days=5),
            created_at=datetime.now(),
            pipeline="default"
        )
        
        self.assertEqual(deal.id, "456")
        self.assertEqual(deal.amount, 10000.00)
        self.assertEqual(deal.stage, DealStage.QUALIFIED_TO_BUY)


if __name__ == "__main__":
    # Run tests
    print("=" * 70)
    print("HubSpot Integration - Production Test Suite")
    print("=" * 70)
    print("\nIMPORTANT: Set HUBSPOT_ACCESS_TOKEN environment variable")
    print("Tests will create real contacts and deals in your HubSpot account\n")
    
    unittest.main(verbosity=2)
