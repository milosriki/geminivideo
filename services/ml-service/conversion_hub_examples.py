"""
Practical Usage Examples for Unified Conversion Hub

This file demonstrates real-world usage patterns for the ConversionHub.
"""

from datetime import datetime, timedelta
from conversion_hub import (
    ConversionHub,
    ConversionSource,
    AttributionModel,
    Touchpoint,
    UnifiedConversion
)


# ==================== SETUP ====================

def setup_conversion_hub():
    """Initialize the conversion hub with all clients."""
    from meta_capi_client import MetaConversionsAPI
    from hubspot_client import HubSpotClient
    from anytrack_client import AnyTrackClient
    from database_service import DatabaseService

    hub = ConversionHub(
        meta_capi_client=MetaConversionsAPI(),
        hubspot_client=HubSpotClient(),
        anytrack_client=AnyTrackClient(),
        database_service=DatabaseService()
    )

    return hub


# ==================== INGESTION EXAMPLES ====================

def example_ingest_meta_conversion():
    """Example: Ingest a conversion from Meta CAPI."""
    hub = setup_conversion_hub()

    # Meta CAPI event data
    meta_event = {
        'event_id': 'evt_abc123',
        'event_time': int(datetime.now().timestamp()),
        'event_name': 'Purchase',
        'user_data': {
            'em': 'customer@example.com',
            'ph': '1234567890'
        },
        'custom_data': {
            'value': 149.99,
            'currency': 'USD',
            'campaign_id': 'camp_123',
            'ad_id': 'ad_456',
            'content_ids': ['product_789']
        }
    }

    # Ingest the conversion
    conversion_id = hub.ingest_conversion(
        ConversionSource.META_CAPI,
        meta_event
    )

    print(f"✓ Meta conversion ingested: {conversion_id}")
    return conversion_id


def example_ingest_hubspot_deal():
    """Example: Ingest a closed deal from HubSpot."""
    hub = setup_conversion_hub()

    # HubSpot deal data
    deal_data = {
        'id': '12345678',
        'properties': {
            'dealname': 'Enterprise Plan - Acme Corp',
            'amount': '5000.00',
            'currency': 'USD',
            'contact_email': 'procurement@acme.com',
            'contact_id': 'contact_999',
            'campaign_id': 'camp_linkedin_enterprise',
            'createdate': (datetime.now() - timedelta(days=30)).isoformat(),
            'closedate': datetime.now().isoformat(),
            'dealstage': 'closedwon',
            'pipeline': 'enterprise_sales'
        }
    }

    # Ingest the deal as a conversion
    conversion_id = hub.ingest_conversion(
        ConversionSource.HUBSPOT,
        deal_data
    )

    print(f"✓ HubSpot deal ingested: {conversion_id}")
    return conversion_id


# ==================== DEDUPLICATION EXAMPLES ====================

def example_deduplicate_conversions():
    """Example: Deduplicate conversions across sources."""
    hub = setup_conversion_hub()

    # Run deduplication with 24-hour window
    results = hub.deduplicate_conversions(window_hours=24)

    print(f"Deduplication Results:")
    print(f"  - Duplicates found: {results['duplicates_found']}")
    print(f"  - Conversions merged: {results['conversions_merged']}")
    print(f"  - Window: {results['window_hours']} hours")

    return results


def example_manual_duplicate_check():
    """Example: Manually check for duplicates before ingestion."""
    hub = setup_conversion_hub()

    # Create a test conversion
    conversion_id = example_ingest_meta_conversion()
    conversion = hub._load_conversion(conversion_id)

    # Find potential duplicates
    duplicates = hub.find_duplicates(conversion)

    if duplicates:
        print(f"⚠ Found {len(duplicates)} potential duplicates")

        # Merge if duplicates found
        all_ids = [conversion.id] + [d.id for d in duplicates]
        merged_id = hub.merge_duplicates(all_ids)
        print(f"✓ Merged into: {merged_id}")
    else:
        print("✓ No duplicates found")

    return duplicates


# ==================== ATTRIBUTION EXAMPLES ====================

def example_last_touch_attribution():
    """Example: Attribute conversion using last-touch model."""
    hub = setup_conversion_hub()

    conversion_id = example_ingest_meta_conversion()

    # Add customer journey touchpoints
    touchpoints = [
        Touchpoint(
            source="facebook",
            campaign_id="camp_awareness",
            ad_id="ad_001",
            timestamp=datetime.now() - timedelta(days=14),
            channel="facebook",
            interaction_type="impression"
        ),
        Touchpoint(
            source="google",
            campaign_id="camp_search",
            ad_id="ad_002",
            timestamp=datetime.now() - timedelta(days=7),
            channel="google",
            interaction_type="click"
        ),
        Touchpoint(
            source="email",
            campaign_id="camp_nurture",
            ad_id=None,
            timestamp=datetime.now() - timedelta(days=1),
            channel="email",
            interaction_type="click"
        )
    ]

    # Add touchpoints to conversion
    for tp in touchpoints:
        hub.add_touchpoint(conversion_id, tp)

    # Apply last-touch attribution
    attribution = hub.attribute_to_campaign(
        conversion_id,
        AttributionModel.LAST_TOUCH
    )

    print("Last-Touch Attribution:")
    for campaign_id, weight in attribution.items():
        print(f"  {campaign_id}: {weight * 100:.0f}%")

    return attribution


def example_position_based_attribution():
    """Example: Apply position-based (U-shaped) attribution."""
    hub = setup_conversion_hub()

    conversion_id = example_ingest_meta_conversion()

    # Add touchpoints (same as above)
    # ... (add touchpoints)

    # Apply position-based attribution (40% first, 40% last, 20% middle)
    attribution = hub.attribute_to_campaign(
        conversion_id,
        AttributionModel.POSITION_BASED
    )

    print("Position-Based Attribution (40/20/40):")
    for campaign_id, weight in attribution.items():
        print(f"  {campaign_id}: {weight * 100:.0f}%")

    return attribution


def example_compare_attribution_models():
    """Example: Compare different attribution models."""
    hub = setup_conversion_hub()

    conversion_id = example_ingest_meta_conversion()
    # ... (add touchpoints)

    print("Attribution Model Comparison:")
    print("-" * 60)

    for model in AttributionModel:
        attribution = hub.attribute_to_campaign(conversion_id, model)

        print(f"\n{model.name}:")
        for campaign_id, weight in attribution.items():
            print(f"  {campaign_id}: {weight * 100:.1f}%")


# ==================== ROAS CALCULATION EXAMPLES ====================

def example_calculate_campaign_roas():
    """Example: Calculate true ROAS for a campaign."""
    hub = setup_conversion_hub()

    # Campaign details
    campaign_id = "camp_123"
    ad_spend = 10000.0  # $10,000 spent

    # Calculate ROAS with different settings
    date_range = (
        datetime.now() - timedelta(days=30),
        datetime.now()
    )

    # Last-touch ROAS (online only)
    roas_online = hub.calculate_true_roas(
        campaign_id=campaign_id,
        ad_spend=ad_spend,
        include_offline=False,
        attribution_model=AttributionModel.LAST_TOUCH,
        date_range=date_range
    )

    # Last-touch ROAS (including offline)
    roas_total = hub.calculate_true_roas(
        campaign_id=campaign_id,
        ad_spend=ad_spend,
        include_offline=True,
        attribution_model=AttributionModel.LAST_TOUCH,
        date_range=date_range
    )

    print(f"Campaign ROAS Analysis:")
    print(f"  Online ROAS: {roas_online:.2f}x")
    print(f"  Total ROAS (incl. offline): {roas_total:.2f}x")
    print(f"  Offline impact: +{((roas_total/roas_online - 1) * 100):.1f}%")

    return roas_total


def example_blended_roas():
    """Example: Calculate blended ROAS across multiple campaigns."""
    hub = setup_conversion_hub()

    campaigns = ["camp_123", "camp_456", "camp_789"]
    total_spend = 50000.0  # $50,000 total

    blended_roas = hub.calculate_blended_roas(
        campaign_ids=campaigns,
        total_spend=total_spend
    )

    print(f"Blended ROAS: {blended_roas:.2f}x")
    return blended_roas


# ==================== PATH ANALYSIS EXAMPLES ====================

def example_analyze_customer_journey():
    """Example: Analyze a customer's full conversion path."""
    hub = setup_conversion_hub()

    contact_id = "contact_123"

    # Get full conversion path
    path = hub.get_conversion_path(contact_id)

    print(f"Customer Journey for {contact_id}:")
    print(f"  Total touchpoints: {len(path)}")
    print(f"\n  Journey:")

    for i, tp in enumerate(path, 1):
        print(f"    {i}. {tp.channel} ({tp.interaction_type}) - {tp.campaign_id}")
        print(f"       {tp.timestamp.strftime('%Y-%m-%d %H:%M')}")

    return path


def example_path_pattern_analysis():
    """Example: Analyze common conversion path patterns."""
    hub = setup_conversion_hub()

    # Analyze paths from last 30 days
    date_range = (
        datetime.now() - timedelta(days=30),
        datetime.now()
    )

    analysis = hub.analyze_conversion_paths(date_range)

    print("Conversion Path Analysis:")
    print(f"  Total paths analyzed: {analysis['total_paths']}")
    print(f"  Unique patterns: {analysis['unique_patterns']}")
    print(f"  Avg touchpoints: {analysis['avg_touchpoints']:.1f}")

    print("\n  Top 5 Conversion Paths:")
    for pattern, count in analysis['top_patterns'][:5]:
        print(f"    {pattern} ({count} conversions)")

    print("\n  Top Channels:")
    for channel, count in analysis['top_channels'][:5]:
        print(f"    {channel}: {count} touchpoints")

    return analysis


# ==================== REPORTING EXAMPLES ====================

def example_attribution_report():
    """Example: Generate comprehensive attribution report."""
    hub = setup_conversion_hub()

    # Generate report for last month
    date_range = (
        datetime.now() - timedelta(days=30),
        datetime.now()
    )

    report = hub.generate_attribution_report(
        date_range=date_range,
        model=AttributionModel.TIME_DECAY,
        group_by="campaign"
    )

    print("Attribution Report:")
    print(f"  Period: {report['date_range']['start']} to {report['date_range']['end']}")
    print(f"  Model: {report['attribution_model']}")
    print(f"  Total conversions: {report['total_conversions']}")
    print(f"  Total revenue: ${report['total_revenue']:,.2f}")

    print("\n  By Campaign:")
    for campaign_id, stats in report['groups'].items():
        print(f"    {campaign_id}:")
        print(f"      Conversions: {stats['conversions']}")
        print(f"      Revenue: ${stats['revenue']:,.2f}")
        print(f"      Attributed: ${stats['attributed_revenue']:,.2f}")

    return report


def example_export_conversions():
    """Example: Export conversions for external analysis."""
    hub = setup_conversion_hub()

    date_range = (
        datetime.now() - timedelta(days=30),
        datetime.now()
    )

    # Export as CSV
    csv_data = hub.export_conversions(date_range, format="csv")
    print(f"✓ Exported {len(csv_data.splitlines())} rows as CSV")

    # Export as JSON
    json_data = hub.export_conversions(date_range, format="json")
    print(f"✓ Exported conversions as JSON")

    return csv_data


# ==================== SYNC EXAMPLES ====================

def example_sync_all_sources():
    """Example: Sync conversions from all sources."""
    hub = setup_conversion_hub()

    # Sync all sources
    results = hub.sync_all_sources()

    print("Sync Results:")
    for source, count in results.items():
        print(f"  {source}: {count} conversions synced")

    return results


def example_check_sync_status():
    """Example: Check sync status for all sources."""
    hub = setup_conversion_hub()

    status = hub.get_sync_status()

    print("Sync Status:")
    for source, info in status.items():
        print(f"  {source}:")
        print(f"    Last sync: {info.get('last_sync', 'Never')}")
        print(f"    Status: {info.get('status', 'Unknown')}")

    return status


# ==================== ADVANCED WORKFLOWS ====================

def example_complete_workflow():
    """
    Example: Complete workflow from ingestion to reporting.

    This demonstrates a real-world scenario:
    1. Ingest conversions from multiple sources
    2. Deduplicate
    3. Add touchpoint data
    4. Apply attribution
    5. Calculate ROAS
    6. Generate reports
    """
    hub = setup_conversion_hub()

    print("=" * 60)
    print("COMPLETE CONVERSION TRACKING WORKFLOW")
    print("=" * 60)

    # Step 1: Sync all sources
    print("\n1. Syncing conversions from all sources...")
    sync_results = hub.sync_all_sources()
    total_synced = sum(sync_results.values())
    print(f"   ✓ Synced {total_synced} conversions")

    # Step 2: Deduplicate
    print("\n2. Deduplicating conversions...")
    dedup_results = hub.deduplicate_conversions(window_hours=24)
    print(f"   ✓ Merged {dedup_results['conversions_merged']} duplicates")

    # Step 3: Calculate ROAS for campaigns
    print("\n3. Calculating campaign ROAS...")
    campaigns = ["camp_123", "camp_456", "camp_789"]
    for campaign_id in campaigns:
        roas = hub.calculate_true_roas(
            campaign_id=campaign_id,
            ad_spend=10000.0,
            include_offline=True,
            attribution_model=AttributionModel.TIME_DECAY
        )
        print(f"   {campaign_id}: {roas:.2f}x ROAS")

    # Step 4: Analyze conversion paths
    print("\n4. Analyzing conversion paths...")
    path_analysis = hub.analyze_conversion_paths()
    print(f"   ✓ Avg touchpoints: {path_analysis.get('avg_touchpoints', 0):.1f}")

    # Step 5: Generate attribution report
    print("\n5. Generating attribution report...")
    report = hub.generate_attribution_report(
        date_range=(datetime.now() - timedelta(days=30), datetime.now()),
        model=AttributionModel.POSITION_BASED,
        group_by="campaign"
    )
    print(f"   ✓ Report generated: {report['total_conversions']} conversions")

    # Step 6: Export data
    print("\n6. Exporting conversion data...")
    csv_export = hub.export_conversions(
        date_range=(datetime.now() - timedelta(days=30), datetime.now()),
        format="csv"
    )
    print(f"   ✓ Exported {len(csv_export.splitlines())} rows")

    print("\n" + "=" * 60)
    print("✓ WORKFLOW COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    print("Unified Conversion Hub - Usage Examples")
    print("\nRun individual functions to see examples:")
    print("  - example_ingest_meta_conversion()")
    print("  - example_calculate_campaign_roas()")
    print("  - example_compare_attribution_models()")
    print("  - example_path_pattern_analysis()")
    print("  - example_complete_workflow()")
