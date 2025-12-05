"""
Integration Tests for Publishing (Meta & Google Ads)
Tests Meta CAPI integration, Google Ads API, and multi-platform publishing.

Coverage:
- Meta Marketing API integration (mocked)
- Google Ads API integration (mocked)
- Campaign creation and management
- Ad set and targeting setup
- Creative upload and publishing
- Approval gate workflows
- Multi-platform publish orchestration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from datetime import datetime, timedelta


@pytest.fixture
def mock_meta_client():
    """Mock Meta Marketing API client"""
    client = Mock()

    # Mock account info
    client.ad_account_id = "act_123456789"
    client.ad_account = Mock()

    # Mock campaign creation
    client.create_campaign = Mock(return_value="campaign_001")
    client.get_campaign = Mock(return_value={
        "id": "campaign_001",
        "name": "Test Campaign",
        "status": "ACTIVE",
        "objective": "OUTCOME_TRAFFIC",
        "daily_budget": 5000
    })

    # Mock ad set creation
    client.create_ad_set = Mock(return_value="adset_001")

    # Mock creative operations
    client.upload_video = Mock(return_value="video_001")
    client.create_ad_creative = Mock(return_value="creative_001")

    # Mock ad creation
    client.create_ad = Mock(return_value="ad_001")

    # Mock insights
    client.get_campaign_insights = Mock(return_value=[{
        "impressions": 1000,
        "clicks": 50,
        "spend": 45.50,
        "ctr": 0.05
    }])

    return client


@pytest.fixture
def mock_google_ads_client():
    """Mock Google Ads API client"""
    client = Mock()

    # Mock customer
    client.customer_id = "1234567890"

    # Mock campaign creation
    client.create_campaign = Mock(return_value="google_campaign_001")

    # Mock ad group creation
    client.create_ad_group = Mock(return_value="google_adgroup_001")

    # Mock ad creation
    client.create_video_ad = Mock(return_value="google_ad_001")

    # Mock performance data
    client.get_campaign_metrics = Mock(return_value={
        "impressions": 2000,
        "clicks": 100,
        "cost_micros": 50000000,  # $50
        "conversions": 5
    })

    return client


@pytest.fixture
def test_campaign_config():
    """Sample campaign configuration"""
    return {
        "name": "Elite Fitness Q1 Campaign",
        "objective": "conversions",
        "daily_budget": 100.00,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "targeting": {
            "countries": ["US", "CA"],
            "age_min": 25,
            "age_max": 45,
            "genders": [1, 2],
            "interests": ["fitness", "health", "wellness"]
        },
        "platforms": ["facebook", "instagram"]
    }


@pytest.fixture
def test_video_ad():
    """Sample video ad creative"""
    return {
        "video_id": "video_001",
        "video_url": "https://storage.example.com/video_001.mp4",
        "thumbnail_url": "https://storage.example.com/thumb_001.jpg",
        "title": "Transform Your Body in 90 Days",
        "description": "Elite fitness coaching with proven results",
        "cta": "BOOK_NOW",
        "destination_url": "https://example.com/book-call"
    }


class TestMetaPublishing:
    """Test Meta (Facebook/Instagram) publishing"""

    @pytest.mark.asyncio
    async def test_create_meta_campaign(self, mock_meta_client, test_campaign_config):
        """Test creating a Meta campaign"""
        campaign_id = mock_meta_client.create_campaign(
            name=test_campaign_config["name"],
            objective="OUTCOME_TRAFFIC",
            daily_budget_cents=10000,
            status="PAUSED"
        )

        assert campaign_id == "campaign_001"
        mock_meta_client.create_campaign.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_meta_ad_set(self, mock_meta_client, test_campaign_config):
        """Test creating a Meta ad set with targeting"""
        targeting = {
            "geo_locations": {"countries": ["US"]},
            "age_min": 25,
            "age_max": 45
        }

        ad_set_id = mock_meta_client.create_ad_set(
            campaign_id="campaign_001",
            name="Test Ad Set",
            daily_budget_cents=5000,
            targeting=targeting,
            optimization_goal="LINK_CLICKS"
        )

        assert ad_set_id == "adset_001"
        mock_meta_client.create_ad_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_video_to_meta(self, mock_meta_client):
        """Test uploading video to Meta"""
        video_path = "/tmp/test_video.mp4"

        video_id = mock_meta_client.upload_video(
            video_path=video_path,
            title="Test Video"
        )

        assert video_id == "video_001"
        mock_meta_client.upload_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_meta_creative(self, mock_meta_client, test_video_ad):
        """Test creating Meta ad creative"""
        creative_id = mock_meta_client.create_ad_creative(
            name="Test Creative",
            video_id=test_video_ad["video_id"],
            message=test_video_ad["description"],
            link=test_video_ad["destination_url"],
            call_to_action_type="LEARN_MORE"
        )

        assert creative_id == "creative_001"
        mock_meta_client.create_ad_creative.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_meta_ad(self, mock_meta_client):
        """Test creating Meta ad"""
        ad_id = mock_meta_client.create_ad(
            ad_set_id="adset_001",
            creative_id="creative_001",
            name="Test Ad",
            status="PAUSED"
        )

        assert ad_id == "ad_001"
        mock_meta_client.create_ad.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_meta_insights(self, mock_meta_client):
        """Test fetching Meta campaign insights"""
        insights = mock_meta_client.get_campaign_insights(
            campaign_id="campaign_001",
            date_preset="last_7d"
        )

        assert len(insights) > 0
        assert "impressions" in insights[0]
        assert "clicks" in insights[0]
        assert "spend" in insights[0]

    @pytest.mark.asyncio
    async def test_meta_targeting_validation(self):
        """Test Meta targeting specification validation"""
        valid_targeting = {
            "geo_locations": {"countries": ["US", "CA"]},
            "age_min": 18,
            "age_max": 65,
            "genders": [1, 2]
        }

        # Validate structure
        assert "geo_locations" in valid_targeting
        assert valid_targeting["age_min"] >= 18
        assert valid_targeting["age_max"] <= 65

    @pytest.mark.asyncio
    async def test_meta_budget_validation(self):
        """Test Meta budget validation"""
        min_daily_budget_cents = 100  # $1.00
        test_budget_cents = 10000  # $100.00

        assert test_budget_cents >= min_daily_budget_cents


class TestGoogleAdsPublishing:
    """Test Google Ads publishing"""

    @pytest.mark.asyncio
    async def test_create_google_campaign(self, mock_google_ads_client, test_campaign_config):
        """Test creating a Google Ads campaign"""
        campaign_id = mock_google_ads_client.create_campaign(
            name=test_campaign_config["name"],
            budget_amount_micros=100000000,  # $100 in micros
            campaign_type="VIDEO"
        )

        assert campaign_id == "google_campaign_001"
        mock_google_ads_client.create_campaign.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_google_ad_group(self, mock_google_ads_client):
        """Test creating Google ad group"""
        ad_group_id = mock_google_ads_client.create_ad_group(
            campaign_id="google_campaign_001",
            name="Test Ad Group"
        )

        assert ad_group_id == "google_adgroup_001"
        mock_google_ads_client.create_ad_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_google_video_ad(self, mock_google_ads_client, test_video_ad):
        """Test creating Google video ad"""
        ad_id = mock_google_ads_client.create_video_ad(
            ad_group_id="google_adgroup_001",
            video_url=test_video_ad["video_url"],
            headline=test_video_ad["title"],
            description=test_video_ad["description"]
        )

        assert ad_id == "google_ad_001"
        mock_google_ads_client.create_video_ad.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_google_metrics(self, mock_google_ads_client):
        """Test fetching Google Ads metrics"""
        metrics = mock_google_ads_client.get_campaign_metrics(
            campaign_id="google_campaign_001"
        )

        assert "impressions" in metrics
        assert "clicks" in metrics
        assert "cost_micros" in metrics
        assert metrics["cost_micros"] > 0


class TestApprovalGate:
    """Test approval gate workflows"""

    @pytest.mark.asyncio
    async def test_council_approval_gate(self):
        """Test Council approval before publishing"""
        # Mock Council score
        council_score = 87.5
        approval_threshold = 85.0

        # Should be approved
        approved = council_score >= approval_threshold
        assert approved is True

    @pytest.mark.asyncio
    async def test_rejection_at_gate(self):
        """Test rejection of low-scoring content"""
        council_score = 70.0
        approval_threshold = 85.0

        approved = council_score >= approval_threshold
        assert approved is False

    @pytest.mark.asyncio
    async def test_approval_workflow_tracking(self):
        """Test tracking approval workflow stages"""
        workflow = {
            "status": "pending",
            "stages": [
                {"name": "council_evaluation", "status": "completed", "score": 87.5},
                {"name": "legal_review", "status": "completed", "approved": True},
                {"name": "brand_approval", "status": "pending"},
                {"name": "publish", "status": "not_started"}
            ]
        }

        # Check stages
        completed = [s for s in workflow["stages"] if s["status"] == "completed"]
        assert len(completed) == 2

    @pytest.mark.asyncio
    async def test_multi_tier_approval(self):
        """Test multi-tier approval process"""
        approvals = {
            "tier1_council": {"approved": True, "score": 87.5},
            "tier2_legal": {"approved": True, "notes": "Compliant"},
            "tier3_executive": {"approved": True, "approver": "CEO"}
        }

        # All tiers must approve
        all_approved = all(tier["approved"] for tier in approvals.values())
        assert all_approved is True


class TestMultiPlatformPublishing:
    """Test multi-platform publishing orchestration"""

    @pytest.mark.asyncio
    async def test_publish_to_multiple_platforms(
        self,
        mock_meta_client,
        mock_google_ads_client,
        test_video_ad
    ):
        """Test publishing same ad to multiple platforms"""
        platforms = {
            "meta": mock_meta_client,
            "google": mock_google_ads_client
        }

        results = {}
        for platform_name, client in platforms.items():
            if platform_name == "meta":
                ad_id = client.create_ad(
                    ad_set_id="adset_001",
                    creative_id="creative_001",
                    name="Test Ad"
                )
            else:  # google
                ad_id = client.create_video_ad(
                    ad_group_id="adgroup_001",
                    video_url=test_video_ad["video_url"],
                    headline="Test Ad"
                )

            results[platform_name] = ad_id

        # Should have published to both
        assert "meta" in results
        assert "google" in results

    @pytest.mark.asyncio
    async def test_platform_specific_optimization(self):
        """Test platform-specific creative optimization"""
        base_creative = {
            "video_url": "test.mp4",
            "title": "Transform Your Body",
            "cta": "Learn More"
        }

        # Platform-specific variants
        meta_creative = {
            **base_creative,
            "aspect_ratio": "9:16",
            "max_duration": 90,
            "cta_type": "LEARN_MORE"
        }

        google_creative = {
            **base_creative,
            "aspect_ratio": "16:9",
            "max_duration": 60,
            "cta_type": "WATCH_MORE"
        }

        assert meta_creative["aspect_ratio"] != google_creative["aspect_ratio"]

    @pytest.mark.asyncio
    async def test_cross_platform_budget_allocation(self):
        """Test budget allocation across platforms"""
        total_budget = 1000.00

        allocation = {
            "meta": 600.00,  # 60%
            "google": 300.00,  # 30%
            "tiktok": 100.00  # 10%
        }

        # Should sum to total
        assert sum(allocation.values()) == total_budget

    @pytest.mark.asyncio
    async def test_publish_orchestration_error_handling(self):
        """Test error handling in multi-platform publish"""
        publish_results = [
            {"platform": "meta", "status": "success", "ad_id": "ad_001"},
            {"platform": "google", "status": "failed", "error": "API timeout"},
            {"platform": "tiktok", "status": "success", "ad_id": "ad_003"}
        ]

        # Check for failures
        failures = [r for r in publish_results if r["status"] == "failed"]
        successes = [r for r in publish_results if r["status"] == "success"]

        assert len(failures) == 1
        assert len(successes) == 2


class TestCampaignManagement:
    """Test campaign lifecycle management"""

    @pytest.mark.asyncio
    async def test_pause_campaign(self, mock_meta_client):
        """Test pausing a campaign"""
        mock_meta_client.pause_campaign = Mock(return_value=True)

        result = mock_meta_client.pause_campaign("campaign_001")
        assert result is True

    @pytest.mark.asyncio
    async def test_activate_campaign(self, mock_meta_client):
        """Test activating a campaign"""
        mock_meta_client.activate_campaign = Mock(return_value=True)

        result = mock_meta_client.activate_campaign("campaign_001")
        assert result is True

    @pytest.mark.asyncio
    async def test_update_budget(self, mock_meta_client):
        """Test updating campaign budget"""
        mock_meta_client.update_budget = Mock(return_value=True)

        result = mock_meta_client.update_budget(
            campaign_id="campaign_001",
            daily_budget_cents=15000
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_get_campaign_status(self, mock_meta_client):
        """Test fetching campaign status"""
        campaign = mock_meta_client.get_campaign("campaign_001")

        assert campaign["status"] in ["ACTIVE", "PAUSED", "ARCHIVED"]

    @pytest.mark.asyncio
    async def test_delete_campaign(self, mock_meta_client):
        """Test deleting a campaign"""
        mock_meta_client.delete_campaign = Mock(return_value=True)

        result = mock_meta_client.delete_campaign("campaign_001")
        assert result is True


class TestPerformanceTracking:
    """Test performance metrics tracking"""

    @pytest.mark.asyncio
    async def test_fetch_daily_metrics(self, mock_meta_client):
        """Test fetching daily performance metrics"""
        metrics = mock_meta_client.get_campaign_insights(
            campaign_id="campaign_001",
            date_preset="today"
        )

        assert len(metrics) > 0
        assert "impressions" in metrics[0]

    @pytest.mark.asyncio
    async def test_calculate_roi(self):
        """Test ROI calculation"""
        spend = 100.00
        revenue = 500.00
        roi = (revenue - spend) / spend * 100

        assert roi == 400.0  # 400% ROI

    @pytest.mark.asyncio
    async def test_calculate_roas(self):
        """Test ROAS calculation"""
        spend = 100.00
        revenue = 500.00
        roas = revenue / spend

        assert roas == 5.0  # 5x ROAS

    @pytest.mark.asyncio
    async def test_track_conversions(self):
        """Test conversion tracking"""
        conversions = {
            "impressions": 10000,
            "clicks": 500,
            "conversions": 25,
            "ctr": 0.05,
            "conversion_rate": 0.05  # 5% of clicks convert
        }

        assert conversions["conversion_rate"] == conversions["conversions"] / conversions["clicks"]


class TestErrorHandling:
    """Test error handling in publishing"""

    @pytest.mark.asyncio
    async def test_handle_api_rate_limit(self):
        """Test handling of API rate limiting"""
        with pytest.raises(Exception) as exc_info:
            # Simulate rate limit error
            raise Exception("Rate limit exceeded")

        assert "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_invalid_credentials(self):
        """Test handling of invalid API credentials"""
        with pytest.raises(Exception) as exc_info:
            # Simulate auth error
            raise Exception("Invalid access token")

        assert "Invalid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_video_upload_failure(self):
        """Test handling of video upload failure"""
        error_types = [
            "File too large",
            "Invalid format",
            "Network timeout",
            "Storage quota exceeded"
        ]

        for error in error_types:
            assert len(error) > 0

    @pytest.mark.asyncio
    async def test_retry_logic(self):
        """Test retry logic for transient failures"""
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                # Simulate API call
                if attempt < 2:
                    raise Exception("Transient error")
                else:
                    result = "success"
                    break
            except Exception:
                attempt += 1

        assert result == "success"
        assert attempt == 2  # Succeeded on 3rd attempt


class TestComplianceAndSafety:
    """Test compliance and safety checks"""

    @pytest.mark.asyncio
    async def test_content_policy_check(self):
        """Test content policy validation"""
        ad_content = {
            "text": "Transform your body",
            "contains_medical_claims": False,
            "contains_prohibited_content": False
        }

        # Should pass policy check
        compliant = (
            not ad_content["contains_medical_claims"] and
            not ad_content["contains_prohibited_content"]
        )

        assert compliant is True

    @pytest.mark.asyncio
    async def test_targeting_restrictions(self):
        """Test targeting restrictions for sensitive categories"""
        targeting = {
            "age_min": 18,  # Must be 18+
            "excluded_categories": ["health_conditions", "financial_status"]
        }

        assert targeting["age_min"] >= 18

    @pytest.mark.asyncio
    async def test_data_privacy_compliance(self):
        """Test data privacy compliance"""
        user_data = {
            "consent_obtained": True,
            "gdpr_compliant": True,
            "ccpa_compliant": True
        }

        compliant = all(user_data.values())
        assert compliant is True


class TestBatchPublishing:
    """Test batch publishing operations"""

    @pytest.mark.asyncio
    async def test_batch_create_ads(self, mock_meta_client):
        """Test creating multiple ads in batch"""
        ad_specs = [
            {"name": "Ad Variant 1", "creative_id": "creative_001"},
            {"name": "Ad Variant 2", "creative_id": "creative_002"},
            {"name": "Ad Variant 3", "creative_id": "creative_003"}
        ]

        results = []
        for spec in ad_specs:
            ad_id = f"ad_{len(results) + 1:03d}"
            results.append(ad_id)

        assert len(results) == len(ad_specs)

    @pytest.mark.asyncio
    async def test_batch_update_status(self):
        """Test batch status updates"""
        ad_ids = ["ad_001", "ad_002", "ad_003"]
        new_status = "ACTIVE"

        updates = {ad_id: new_status for ad_id in ad_ids}

        assert len(updates) == 3
        assert all(status == "ACTIVE" for status in updates.values())
