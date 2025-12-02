"""
HubSpot Integration Usage Examples

Demonstrates real-world usage of the HubSpot CRM integration
for tracking the 5-day sales cycle.
"""

import os
from datetime import datetime, timedelta
from hubspot import HubSpotIntegration, DealStage

# Initialize with your HubSpot private app access token
HUBSPOT_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
hubspot = HubSpotIntegration(access_token=HUBSPOT_TOKEN)


def example_1_new_lead_from_ad():
    """Example: New lead from Meta ad campaign"""
    
    # 1. Create/sync contact from ad lead
    contact_id = hubspot.sync_contact(
        email="john.doe@example.com",
        properties={
            "firstname": "John",
            "lastname": "Doe",
            "phone": "+1-555-0123",
            "lifecyclestage": "lead",
            "hs_lead_status": "NEW"
        }
    )
    
    # 2. Add UTM tracking from ad
    hubspot.add_utm_to_contact(
        contact_id=contact_id,
        utm_campaign="meta_video_may_2024",
        utm_source="facebook",
        utm_medium="cpc"
    )
    
    # 3. Create initial deal
    deal_id = hubspot.create_deal(
        contact_id=contact_id,
        deal_name="Video Production - John Doe",
        amount=5000.00,
        stage=DealStage.APPOINTMENT_SCHEDULED,
        properties={
            "description": "Enterprise video production package"
        }
    )
    
    # 4. Attribute to Meta campaign
    hubspot.attribute_deal_to_campaign(
        deal_id=deal_id,
        campaign_id="meta_video_may_2024",
        meta_ad_id="120210123456789012345"
    )
    
    print(f"✓ Created contact {contact_id} and deal {deal_id}")
    return contact_id, deal_id


def example_2_track_sales_progression(deal_id: str):
    """Example: Track deal through 5-day sales cycle"""
    
    # Day 1: Appointment scheduled
    hubspot.update_deal_stage(deal_id, DealStage.APPOINTMENT_SCHEDULED)
    
    # Day 2: Qualified buyer
    hubspot.update_deal_stage(deal_id, DealStage.QUALIFIED_TO_BUY)
    
    # Day 3: Presentation scheduled
    hubspot.update_deal_stage(deal_id, DealStage.PRESENTATION_SCHEDULED)
    
    # Day 4: Decision maker bought in
    hubspot.update_deal_stage(deal_id, DealStage.DECISION_MAKER_BOUGHT_IN)
    
    # Day 5: Contract sent
    hubspot.update_deal_stage(deal_id, DealStage.CONTRACT_SENT)
    
    # Day 5: Closed won!
    hubspot.update_deal_stage(deal_id, DealStage.CLOSED_WON)
    
    # Get deal history
    history = hubspot.get_deal_history(deal_id)
    
    print(f"✓ Deal progressed through {len(history)} stages")
    for change in history:
        print(f"  {change.from_stage} → {change.to_stage} ({change.time_in_stage_hours:.1f}h)")
    
    return history


def example_3_calculate_roas():
    """Example: Calculate actual ROAS from closed deals"""
    
    campaign_id = "meta_video_may_2024"
    ad_spend = 2500.00  # Spent $2,500 on ads
    
    # Get all closed deals
    closed_deals = hubspot.get_closed_deals_by_campaign(campaign_id)
    
    total_revenue = sum(deal.amount for deal in closed_deals)
    
    print(f"\nCampaign Performance:")
    print(f"  Ad Spend: ${ad_spend:,.2f}")
    print(f"  Closed Deals: {len(closed_deals)}")
    print(f"  Total Revenue: ${total_revenue:,.2f}")
    
    # Calculate true ROAS
    roas = hubspot.calculate_actual_roas(
        campaign_id=campaign_id,
        ad_spend=ad_spend,
        include_pending=False  # Only closed deals
    )
    
    print(f"  Actual ROAS: {roas:.2f}x")
    
    # Calculate with pipeline (probabilistic)
    roas_with_pipeline = hubspot.calculate_actual_roas(
        campaign_id=campaign_id,
        ad_spend=ad_spend,
        include_pending=True  # Include pipeline at probability
    )
    
    print(f"  Projected ROAS: {roas_with_pipeline:.2f}x")
    
    return roas, roas_with_pipeline


def example_4_sales_cycle_analytics():
    """Example: Analyze sales cycle performance"""
    
    # Get average sales cycle
    avg_cycle = hubspot.get_avg_sales_cycle(
        pipeline="default",
        days_back=90
    )
    
    print(f"\nSales Cycle Analytics (90 days):")
    print(f"  Average cycle: {avg_cycle:.1f} days")
    
    # Get pipeline value
    pipeline_value = hubspot.get_pipeline_value(
        pipeline="default",
        by_stage=True
    )
    
    print(f"\nPipeline Value by Stage:")
    for stage, value in pipeline_value.items():
        print(f"  {stage}: ${value:,.2f}")
    
    # Get conversion rates
    conversion_rates = hubspot.get_conversion_rates(pipeline="default")
    
    print(f"\nStage Conversion Rates:")
    for stage_pair, rate in conversion_rates.items():
        print(f"  {stage_pair}: {rate:.1f}%")
    
    return avg_cycle, pipeline_value, conversion_rates


def example_5_webhook_handler():
    """Example: Handle HubSpot webhook events"""
    
    # Simulate webhook payload
    webhook_payload = {
        "eventType": "deal.propertyChange",
        "objectId": "12345678901",
        "propertyName": "dealstage",
        "propertyValue": "closedwon"
    }
    
    result = hubspot.handle_webhook(
        event_type="deal.propertyChange",
        payload=webhook_payload
    )
    
    print(f"\nWebhook processed: {result['status']}")
    print(f"  Action: {result['action']}")
    print(f"  Deal ID: {result['deal_id']}")
    
    return result


def example_6_full_sales_cycle():
    """Complete example: Lead to closed deal with tracking"""
    
    print("=" * 60)
    print("COMPLETE 5-DAY SALES CYCLE EXAMPLE")
    print("=" * 60)
    
    # New lead from Meta ad
    print("\n[Day 0] New lead from Meta ad...")
    contact_id, deal_id = example_1_new_lead_from_ad()
    
    # Progress through stages
    print("\n[Days 1-5] Progressing through sales cycle...")
    history = example_2_track_sales_progression(deal_id)
    
    # Calculate sales cycle
    print("\n[Analysis] Calculating sales cycle...")
    cycle_days = hubspot.calculate_sales_cycle(contact_id)
    print(f"✓ Sales cycle completed in {cycle_days} days")
    
    # Calculate ROAS
    print("\n[Analysis] Calculating campaign ROAS...")
    roas, projected_roas = example_3_calculate_roas()
    
    # Analytics
    print("\n[Analysis] Sales analytics...")
    example_4_sales_cycle_analytics()
    
    print("\n" + "=" * 60)
    print("✓ Complete sales cycle tracked successfully!")
    print("=" * 60)


if __name__ == "__main__":
    # Run examples
    try:
        example_6_full_sales_cycle()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure to set HUBSPOT_ACCESS_TOKEN environment variable")
