"""
Meta Marketing API v19.0 Usage Examples
Real production-grade integration examples for RealMetaAdsManager.

SETUP:
1. Install dependencies: pip install facebook-business
2. Get credentials from Meta Developer Portal:
   - Create a Meta App
   - Get Access Token with ads_management permission
   - Get Ad Account ID from Meta Ads Manager
3. Set environment variables or pass credentials directly
"""

import os
from meta import (
    RealMetaAdsManager,
    CampaignObjective,
    OptimizationGoal,
    BillingEvent,
    RetryConfig
)

# ==================== INITIALIZATION ====================

def initialize_client():
    """Initialize the Meta Ads Manager client."""

    # Option 1: From environment variables
    manager = RealMetaAdsManager(
        access_token=os.getenv('META_ACCESS_TOKEN'),
        ad_account_id=os.getenv('META_AD_ACCOUNT_ID'),
        app_secret=os.getenv('META_APP_SECRET'),  # Optional but recommended
        app_id=os.getenv('META_APP_ID')  # Optional
    )

    # Option 2: Direct credentials
    # manager = RealMetaAdsManager(
    #     access_token='YOUR_ACCESS_TOKEN',
    #     ad_account_id='123456789',  # Can include or omit 'act_' prefix
    #     app_secret='YOUR_APP_SECRET'
    # )

    # Option 3: With custom retry configuration
    # custom_retry = RetryConfig(
    #     max_retries=5,
    #     base_delay=2.0,
    #     max_delay=120.0,
    #     exponential_base=2.5
    # )
    # manager = RealMetaAdsManager(
    #     access_token=token,
    #     ad_account_id=account_id,
    #     retry_config=custom_retry
    # )

    return manager


# ==================== CAMPAIGN MANAGEMENT ====================

def create_video_campaign_example(manager: RealMetaAdsManager):
    """Create a traffic campaign for video ads."""

    campaign_id = manager.create_campaign(
        name="Summer Video Campaign 2024",
        objective=CampaignObjective.OUTCOME_TRAFFIC,
        daily_budget_cents=5000,  # $50/day
        status="PAUSED",  # Start paused for review
        special_ad_categories=None  # Add ['CREDIT'] if advertising credit services
    )

    print(f"Campaign created: {campaign_id}")
    return campaign_id


def manage_campaign_lifecycle(manager: RealMetaAdsManager, campaign_id: str):
    """Demonstrate campaign lifecycle management."""

    # Get campaign details
    campaign = manager.get_campaign(campaign_id)
    print(f"Campaign: {campaign['name']}, Status: {campaign['status']}")

    # Update campaign
    manager.update_campaign(
        campaign_id,
        name="Updated Summer Campaign 2024",
        daily_budget=7500  # Increase to $75/day
    )

    # Activate campaign
    manager.activate_campaign(campaign_id)
    print("Campaign activated")

    # Pause campaign
    manager.pause_campaign(campaign_id)
    print("Campaign paused")

    # Delete campaign (be careful!)
    # manager.delete_campaign(campaign_id)


# ==================== AD SET MANAGEMENT ====================

def create_ad_set_with_targeting(manager: RealMetaAdsManager, campaign_id: str):
    """Create an ad set with detailed targeting."""

    # Build targeting specification
    targeting = manager.build_targeting(
        countries=['US', 'CA', 'GB'],
        age_min=25,
        age_max=45,
        genders=[1, 2],  # 1=male, 2=female
        interests=[
            {'id': '6003139266461', 'name': 'Video games'},
            {'id': '6003107902433', 'name': 'Technology'}
        ],
        device_platforms=['mobile', 'desktop'],
        publisher_platforms=['facebook', 'instagram'],
        facebook_positions=['feed', 'story']
    )

    # Create ad set
    ad_set_id = manager.create_ad_set(
        campaign_id=campaign_id,
        name="US/CA/GB Tech Enthusiasts 25-45",
        daily_budget_cents=2000,  # $20/day
        targeting=targeting,
        optimization_goal='LINK_CLICKS',
        billing_event='IMPRESSIONS',
        bid_strategy='LOWEST_COST_WITHOUT_CAP',
        status='PAUSED'
    )

    print(f"Ad set created: {ad_set_id}")
    return ad_set_id


def update_ad_set_budget(manager: RealMetaAdsManager, ad_set_id: str):
    """Update ad set budget and targeting."""

    # Get current ad set
    ad_set = manager.get_ad_set(ad_set_id)
    print(f"Current budget: ${int(ad_set['daily_budget'])/100}")

    # Update budget
    manager.update_ad_set(
        ad_set_id,
        daily_budget=3000,  # Increase to $30/day
        status='ACTIVE'
    )
    print("Ad set updated and activated")


# ==================== CREATIVE & AD MANAGEMENT ====================

def create_video_ad_complete_flow(manager: RealMetaAdsManager, ad_set_id: str):
    """Complete flow: upload video, create creative, create ad."""

    # Step 1: Upload video
    video_id = manager.upload_video(
        video_path='/path/to/your/video.mp4',
        title='Summer Product Demo Video'
    )
    print(f"Video uploaded: {video_id}")

    # Step 2: Create ad creative
    creative_id = manager.create_ad_creative(
        name='Summer Demo Creative',
        video_id=video_id,
        message='Check out our amazing summer products! Limited time offer.',
        link='https://yourwebsite.com/summer-sale',
        call_to_action_type='SHOP_NOW',
        page_id='YOUR_FACEBOOK_PAGE_ID'  # Get from Meta Business Manager
    )
    print(f"Creative created: {creative_id}")

    # Step 3: Create ad
    ad_id = manager.create_ad(
        ad_set_id=ad_set_id,
        creative_id=creative_id,
        name='Summer Sale Video Ad',
        status='PAUSED'
    )
    print(f"Ad created: {ad_id}")

    return ad_id


def create_image_ad_flow(manager: RealMetaAdsManager, ad_set_id: str):
    """Create an image-based ad."""

    # Upload image
    image_hash = manager.upload_image('/path/to/image.jpg')
    print(f"Image uploaded: {image_hash}")

    # Create creative
    creative_id = manager.create_ad_creative(
        name='Product Image Creative',
        image_hash=image_hash,
        message='Don\'t miss our exclusive deals!',
        link='https://yourwebsite.com/products',
        call_to_action_type='LEARN_MORE'
    )

    # Create ad
    ad_id = manager.create_ad(
        ad_set_id=ad_set_id,
        creative_id=creative_id,
        name='Product Image Ad',
        status='PAUSED'
    )

    return ad_id


# ==================== INSIGHTS & REPORTING ====================

def get_campaign_performance(manager: RealMetaAdsManager, campaign_id: str):
    """Retrieve campaign performance metrics."""

    # Get insights for last 7 days
    insights = manager.get_campaign_insights(
        campaign_id=campaign_id,
        fields=[
            'impressions', 'clicks', 'spend', 'reach', 'frequency',
            'cpm', 'cpc', 'ctr', 'video_views', 'video_view_time',
            'actions', 'conversions'
        ],
        date_preset='last_7d'
    )

    for insight in insights:
        print(f"Date: {insight.get('date_start')} to {insight.get('date_stop')}")
        print(f"Impressions: {insight.get('impressions')}")
        print(f"Clicks: {insight.get('clicks')}")
        print(f"Spend: ${float(insight.get('spend', 0))}")
        print(f"CTR: {insight.get('ctr')}%")
        print(f"CPM: ${insight.get('cpm')}")
        print(f"CPC: ${insight.get('cpc')}")
        print("---")

    return insights


def get_campaign_insights_by_age_gender(manager: RealMetaAdsManager, campaign_id: str):
    """Get insights broken down by age and gender."""

    insights = manager.get_campaign_insights(
        campaign_id=campaign_id,
        fields=['impressions', 'clicks', 'spend', 'ctr'],
        date_preset='last_30d',
        breakdowns=['age', 'gender']
    )

    for insight in insights:
        print(f"Age: {insight.get('age')}, Gender: {insight.get('gender')}")
        print(f"  Impressions: {insight.get('impressions')}, CTR: {insight.get('ctr')}%")

    return insights


def get_custom_date_range_insights(manager: RealMetaAdsManager, campaign_id: str):
    """Get insights for custom date range."""

    insights = manager.get_campaign_insights(
        campaign_id=campaign_id,
        fields=['impressions', 'clicks', 'spend'],
        time_range={
            'since': '2024-01-01',
            'until': '2024-01-31'
        }
    )

    return insights


def get_ad_level_performance(manager: RealMetaAdsManager, ad_id: str):
    """Get individual ad performance."""

    insights = manager.get_ad_insights(
        ad_id=ad_id,
        fields=['impressions', 'clicks', 'spend', 'actions', 'conversions'],
        date_preset='last_7d'
    )

    print(f"Ad Performance:")
    print(f"Impressions: {insights.get('impressions')}")
    print(f"Clicks: {insights.get('clicks')}")
    print(f"Spend: ${insights.get('spend')}")

    # Parse actions (likes, comments, shares, etc.)
    actions = insights.get('actions', [])
    for action in actions:
        print(f"{action['action_type']}: {action['value']}")

    return insights


def get_account_overview(manager: RealMetaAdsManager):
    """Get account-level overview."""

    insights = manager.get_account_insights(
        date_preset='last_30d',
        fields=['impressions', 'clicks', 'spend', 'reach', 'cpm', 'cpc', 'ctr']
    )

    print(f"Account Overview (Last 30 days):")
    print(f"Total Impressions: {insights.get('impressions')}")
    print(f"Total Clicks: {insights.get('clicks')}")
    print(f"Total Spend: ${insights.get('spend')}")
    print(f"Average CPM: ${insights.get('cpm')}")
    print(f"Average CPC: ${insights.get('cpc')}")

    return insights


# ==================== BUDGET MANAGEMENT ====================

def manage_campaign_budget(manager: RealMetaAdsManager, campaign_id: str):
    """Manage campaign budgets dynamically."""

    # Get current spend
    total_spend = manager.get_spend(campaign_id)
    print(f"Total campaign spend: ${total_spend}")

    # Get spend for specific date range
    spend_last_week = manager.get_spend(
        campaign_id,
        date_range=('2024-01-01', '2024-01-07')
    )
    print(f"Spend last week: ${spend_last_week}")

    # Update budget based on performance
    if total_spend < 100:
        # Increase budget if underspending
        manager.update_budget(campaign_id, daily_budget_cents=10000)
        print("Budget increased to $100/day")
    else:
        # Decrease budget if overspending
        manager.update_budget(campaign_id, daily_budget_cents=5000)
        print("Budget decreased to $50/day")


# ==================== ADVANCED TARGETING ====================

def create_lookalike_audience_targeting(manager: RealMetaAdsManager):
    """Create targeting with lookalike audiences."""

    targeting = manager.build_targeting(
        countries=['US'],
        age_min=18,
        age_max=65,
        lookalike_audiences=['123456789'],  # Your lookalike audience ID
        excluded_audiences=['987654321'],  # Exclude existing customers
        device_platforms=['mobile']
    )

    return targeting


def create_custom_geo_targeting(manager: RealMetaAdsManager):
    """Create custom geographic targeting."""

    # Custom geo locations with radius targeting
    geo_locations = {
        'countries': ['US'],
        'cities': [
            {'key': '2418779', 'radius': 25, 'distance_unit': 'mile'},  # New York
            {'key': '2490299', 'radius': 20, 'distance_unit': 'mile'}   # Los Angeles
        ],
        'regions': [
            {'key': '3847'},  # California
            {'key': '3875'}   # New York state
        ]
    }

    targeting = manager.build_targeting(
        geo_locations=geo_locations,
        age_min=21,
        age_max=55
    )

    return targeting


# ==================== HEALTH CHECK ====================

def check_api_health(manager: RealMetaAdsManager):
    """Perform health check on API connection."""

    health = manager.health_check()

    if health['status'] == 'healthy':
        print(f"✓ API Connected Successfully")
        print(f"  Account: {health['account_name']}")
        print(f"  Status: {health['account_status']}")
        print(f"  API Version: {health['api_version']}")
    else:
        print(f"✗ API Connection Failed")
        print(f"  Error: {health['error']}")

    return health


# ==================== COMPLETE WORKFLOW EXAMPLE ====================

def complete_campaign_workflow():
    """End-to-end campaign creation workflow."""

    # Initialize
    manager = initialize_client()

    # Health check
    check_api_health(manager)

    # Create campaign
    campaign_id = create_video_campaign_example(manager)

    # Create ad set with targeting
    ad_set_id = create_ad_set_with_targeting(manager, campaign_id)

    # Create video ad
    ad_id = create_video_ad_complete_flow(manager, ad_set_id)

    # Activate
    manager.activate_campaign(campaign_id)
    manager.update_ad_set(ad_set_id, status='ACTIVE')

    print(f"\n✓ Campaign launched successfully!")
    print(f"  Campaign ID: {campaign_id}")
    print(f"  Ad Set ID: {ad_set_id}")
    print(f"  Ad ID: {ad_id}")

    # Monitor performance (after some time)
    # insights = get_campaign_performance(manager, campaign_id)

    return campaign_id, ad_set_id, ad_id


if __name__ == '__main__':
    # Run complete workflow
    # complete_campaign_workflow()

    # Or run individual examples
    manager = initialize_client()
    health = check_api_health(manager)
    print(health)
