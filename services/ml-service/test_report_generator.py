#!/usr/bin/env python3
"""
Test script for Report Generator
Agent 18 - Demo report generation

Usage:
    python test_report_generator.py
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from reports.report_generator import ReportGenerator, ReportType, ReportFormat
from reports.pdf_builder import generate_pdf_report
from reports.excel_builder import generate_excel_report


async def test_report_generation():
    """Test generating all report types"""

    print("=" * 80)
    print("CAMPAIGN PERFORMANCE REPORT GENERATOR TEST")
    print("Agent 18 - Professional PDF & Excel Reports")
    print("=" * 80)
    print()

    # Initialize generator (without database for testing)
    generator = ReportGenerator(db_pool=None)

    # Set date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    report_types = [
        (ReportType.CAMPAIGN_PERFORMANCE, "Campaign Performance Report"),
        (ReportType.AD_CREATIVE_ANALYSIS, "Ad Creative Analysis Report"),
        (ReportType.AUDIENCE_INSIGHTS, "Audience Insights Report"),
        (ReportType.ROAS_BREAKDOWN, "ROAS Breakdown Report"),
        (ReportType.WEEKLY_SUMMARY, "Weekly Summary Report"),
        (ReportType.MONTHLY_EXECUTIVE, "Monthly Executive Report")
    ]

    for report_type, description in report_types:
        print(f"\n{'=' * 80}")
        print(f"Generating: {description}")
        print(f"{'=' * 80}\n")

        # Generate report content
        print("1. Generating report content...")
        report_data = await generator.generate_report(
            report_type=report_type,
            format=ReportFormat.PDF,
            start_date=start_date,
            end_date=end_date,
            company_name="Elite Marketing Agency",
            filters=None
        )

        print(f"   ✓ Report ID: {report_data['report_id']}")
        print(f"   ✓ Report Type: {report_data['report_type']}")
        print(f"   ✓ Status: {report_data['status']}")

        # Display summary
        content = report_data['content']
        print(f"\n2. Report Summary:")
        print(f"   - Date Range: {content['date_range']['start']} to {content['date_range']['end']}")
        print(f"   - Company: {content['company_name']}")

        data = content.get('data', {})
        if 'overall_metrics' in data:
            overall = data['overall_metrics']
            print(f"\n3. Key Metrics:")
            print(f"   - Total Spend: ${overall.get('total_spend', 0):,.2f}")
            print(f"   - Total Revenue: ${overall.get('total_revenue', 0):,.2f}")
            print(f"   - ROAS: {overall.get('overall_roas', 0):.2f}x")
            print(f"   - Conversions: {overall.get('total_conversions', 0):,}")
            print(f"   - CTR: {overall.get('overall_ctr', 0)*100:.2f}%")

        # Display insights
        insights = content.get('insights', [])
        if insights:
            print(f"\n4. Key Insights ({len(insights)}):")
            for i, insight in enumerate(insights, 1):
                print(f"   {i}. [{insight['type'].upper()}] {insight['title']}")
                print(f"      {insight['description']}")

        # Display recommendations
        recommendations = content.get('recommendations', [])
        if recommendations:
            print(f"\n5. Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
                print(f"      {rec['description']}")

        # Generate PDF
        print(f"\n6. Generating PDF...")
        pdf_filename = f"/tmp/test_report_{report_type.value}.pdf"
        pdf_path = generate_pdf_report(content, pdf_filename)
        print(f"   ✓ PDF saved: {pdf_path}")

        # Generate Excel
        print(f"\n7. Generating Excel...")
        excel_filename = f"/tmp/test_report_{report_type.value}.xlsx"
        excel_path = generate_excel_report(content, excel_filename)
        print(f"   ✓ Excel saved: {excel_path}")

        print(f"\n{'✓' * 40}")
        print(f"Report generated successfully!")
        print(f"{'✓' * 40}\n")

    print("\n" + "=" * 80)
    print("ALL REPORTS GENERATED SUCCESSFULLY")
    print("=" * 80)
    print("\nGenerated Files:")
    for report_type, _ in report_types:
        print(f"  - /tmp/test_report_{report_type.value}.pdf")
        print(f"  - /tmp/test_report_{report_type.value}.xlsx")
    print("\nOpen these files to review the professional report output!")
    print("=" * 80)


if __name__ == '__main__':
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "REPORT GENERATOR TEST SUITE" + " " * 31 + "║")
    print("║" + " " * 25 + "Agent 18 - Elite Reports" + " " * 30 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    try:
        asyncio.run(test_report_generation())
        print("\n✅ All tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
