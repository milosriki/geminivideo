"""
Example usage of Anytrack Integration.

Demonstrates real-world usage patterns for conversion tracking,
affiliate analytics, and cross-platform sync.
"""

import os
from datetime import datetime, timedelta
from anytrack import (
    AnytrackIntegration,
    ConversionType
)


def main():
    """Example Anytrack integration usage."""

    # Initialize client
    anytrack = AnytrackIntegration(
        api_key=os.getenv("ANYTRACK_API_KEY"),
        account_id=os.getenv("ANYTRACK_ACCOUNT_ID")
    )

    # Example 1: Track a sale conversion
    print("=== Tracking Sale Conversion ===")
    sale_response = anytrack.track_sale(
        click_id="clk_abc123xyz",
        revenue=99.99,
        currency="USD",
        order_id="ORD-12345",
        product_id="PROD-VIDEO-001"
    )
    print(f"Sale tracked: {sale_response}")

    # Example 2: Track a lead conversion
    print("\n=== Tracking Lead Conversion ===")
    lead_response = anytrack.track_lead(
        click_id="clk_def456uvw",
        lead_id="LEAD-98765",
        value=25.0
    )
    print(f"Lead tracked: {lead_response}")

    # Example 3: Get conversions for date range
    print("\n=== Fetching Conversions ===")
    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=7)

    conversions = anytrack.get_conversions(
        date_from=date_from,
        date_to=date_to,
        source="facebook_ads",
        campaign_id="camp_123"
    )

    print(f"Found {len(conversions)} conversions in last 7 days")
    for conv in conversions[:5]:  # Show first 5
        print(f"  - {conv.id}: ${conv.revenue} {conv.currency} ({conv.conversion_type.value})")

    # Example 4: Get conversion details
    if conversions:
        print("\n=== Conversion Details ===")
        detailed_conv = anytrack.get_conversion_details(conversions[0].id)
        print(f"Conversion ID: {detailed_conv.id}")
        print(f"Click ID: {detailed_conv.click_id}")
        print(f"Revenue: ${detailed_conv.revenue}")
        print(f"Source: {detailed_conv.source}")
        print(f"Campaign: {detailed_conv.campaign_id}")

    # Example 5: Get attribution data
    if conversions:
        print("\n=== Attribution Analysis ===")
        attribution = anytrack.calculate_attribution(conversions[0].id)
        print(f"Attribution model: {attribution.get('model')}")
        print(f"Touchpoint weights: {attribution.get('weights')}")

        # Get all touchpoints
        touchpoints = anytrack.get_touchpoints(conversions[0].id)
        print(f"Total touchpoints: {len(touchpoints)}")
        for tp in touchpoints:
            print(f"  - {tp['type']}: {tp['source']} ({tp['timestamp']})")

    # Example 6: Get affiliate performance
    print("\n=== Affiliate Performance ===")
    affiliate_perf = anytrack.get_affiliate_performance(
        affiliate_id="aff_12345",
        date_range=(date_from, date_to)
    )
    print(f"Affiliate: {affiliate_perf.affiliate_id}")
    print(f"Clicks: {affiliate_perf.clicks}")
    print(f"Conversions: {affiliate_perf.conversions}")
    print(f"Revenue: ${affiliate_perf.revenue:.2f}")
    print(f"EPC: ${affiliate_perf.epc:.2f}")
    print(f"Conversion Rate: {affiliate_perf.conversion_rate:.2%}")

    # Example 7: Get top affiliates
    print("\n=== Top Affiliates by Revenue ===")
    top_affiliates = anytrack.get_top_affiliates(
        metric="revenue",
        limit=5,
        date_range=(date_from, date_to)
    )

    for i, aff in enumerate(top_affiliates, 1):
        print(f"{i}. {aff.affiliate_id}: ${aff.revenue:.2f} ({aff.conversions} conversions)")

    # Example 8: Daily report
    print("\n=== Daily Report ===")
    report_date = datetime.utcnow() - timedelta(days=1)
    daily_report = anytrack.get_daily_report(report_date)
    print(f"Date: {report_date.strftime('%Y-%m-%d')}")
    print(f"Total Revenue: ${daily_report.get('total_revenue', 0):.2f}")
    print(f"Total Conversions: {daily_report.get('total_conversions', 0)}")
    print(f"Average Order Value: ${daily_report.get('avg_order_value', 0):.2f}")

    # Example 9: Export conversions to CSV
    print("\n=== Exporting Conversions ===")
    csv_path = anytrack.export_conversions_csv(
        date_range=(date_from, date_to),
        output_path="/tmp/anytrack_conversions.csv"
    )
    print(f"Conversions exported to: {csv_path}")

    # Example 10: Cross-platform sync (requires client instances)
    # Note: This example shows the API, actual sync requires Meta CAPI and HubSpot clients
    print("\n=== Cross-Platform Sync Example ===")
    print("To sync conversions:")
    print("1. Initialize Meta CAPI client")
    print("2. Call: anytrack.sync_with_meta_capi(conversion, meta_client)")
    print("3. Initialize HubSpot client")
    print("4. Call: anytrack.sync_with_hubspot(conversion, hubspot_client)")

    """
    # Actual sync code (when clients are available):

    from meta_capi import MetaCAPIClient
    from hubspot import HubSpotClient

    meta_client = MetaCAPIClient(access_token="...", pixel_id="...")
    hubspot_client = HubSpotClient(api_key="...")

    for conversion in conversions:
        # Sync to Meta
        anytrack.sync_with_meta_capi(conversion, meta_client)

        # Sync to HubSpot
        anytrack.sync_with_hubspot(conversion, hubspot_client)
    """


if __name__ == "__main__":
    main()
