#!/usr/bin/env python3
"""
Meta Ads Library API - Usage Examples
Demonstrates how to use the RealMetaAdsLibrary class
"""

import os
from pathlib import Path
from meta_ads_library import RealMetaAdsLibrary, meta_ads_library


def example_search_ads():
    """Example: Search for ads in Meta Ads Library"""
    print("=" * 60)
    print("Example 1: Search Ads")
    print("=" * 60)

    # Search for e-commerce product ads
    ads = meta_ads_library.search_ads(
        search_terms="skincare product",
        countries=['US', 'GB'],
        media_type='VIDEO',
        limit=20
    )

    print(f"\nFound {len(ads)} ads")

    if ads:
        # Print first ad details
        ad = ads[0]
        print("\nFirst ad details:")
        print(f"  ID: {ad.get('id')}")
        print(f"  Page: {ad.get('page_name')}")
        print(f"  Body: {ad.get('ad_creative_body', '')[:100]}...")
        print(f"  Impressions: {ad.get('impressions')}")
        print(f"  Spend: {ad.get('spend')}")

    return ads


def example_analyze_top_performers():
    """Example: Analyze top-performing ads"""
    print("\n" + "=" * 60)
    print("Example 2: Analyze Top Performers")
    print("=" * 60)

    # Analyze top performers in fitness niche
    analysis = meta_ads_library.analyze_top_performers(
        niche_keywords="fitness workout",
        min_impressions=50000,
        limit=30
    )

    print(f"\nTotal ads analyzed: {analysis.get('total_ads_analyzed', 0)}")

    # Copy patterns
    copy_patterns = analysis.get('copy_patterns', {})
    if copy_patterns:
        print("\nCopy Patterns:")
        for pattern, data in copy_patterns.items():
            print(f"  {pattern}: {data.get('count', 0)} ads ({data.get('percentage', 0)}%)")

    # Timing patterns
    timing = analysis.get('timing_patterns', {})
    if timing and 'best_launch_days' in timing:
        print("\nBest Launch Days:")
        for day_info in timing['best_launch_days']:
            print(f"  {day_info['day']}: {day_info['count']} ads ({day_info['percentage']}%)")

    # Spend analysis
    spend = analysis.get('spend_analysis', {})
    if spend:
        print(f"\nSpend Analysis:")
        print(f"  Average: ${spend.get('avg', 0):,.2f}")
        print(f"  Range: ${spend.get('min', 0):,.2f} - ${spend.get('max', 0):,.2f}")
        print(f"  Total: ${spend.get('total', 0):,.2f}")

    return analysis


def example_download_video():
    """Example: Download video from ad"""
    print("\n" + "=" * 60)
    print("Example 3: Download Ad Video")
    print("=" * 60)

    # First, search for ads with videos
    ads = meta_ads_library.search_ads(
        search_terms="video ad",
        countries=['US'],
        media_type='VIDEO',
        limit=5
    )

    if not ads:
        print("No ads found to download")
        return

    # Find first ad with video URL
    for ad in ads:
        video_url = ad.get('video_url')
        if video_url:
            print(f"\nDownloading video from ad: {ad.get('id')}")

            # Create output directory
            output_dir = Path('/tmp/meta_ads_videos')
            output_dir.mkdir(parents=True, exist_ok=True)

            # Download video
            output_path = output_dir / f"ad_{ad.get('id')}.mp4"
            downloaded_path = meta_ads_library.download_video(
                video_url=video_url,
                output_path=str(output_path)
            )

            if downloaded_path:
                print(f"✅ Video downloaded to: {downloaded_path}")
            else:
                print("❌ Failed to download video")

            break
    else:
        print("No ads with video URLs found")


def example_custom_analysis():
    """Example: Custom pattern analysis"""
    print("\n" + "=" * 60)
    print("Example 4: Custom Analysis")
    print("=" * 60)

    # Search for specific niche
    ads = meta_ads_library.search_ads(
        search_terms="online course education",
        countries=['US'],
        media_type='VIDEO',
        limit=50
    )

    if not ads:
        print("No ads found")
        return

    print(f"\nAnalyzing {len(ads)} ads...")

    # Custom analysis: Count call-to-action types
    cta_keywords = {
        'learn_more': ['learn more', 'discover', 'find out'],
        'sign_up': ['sign up', 'register', 'join', 'enroll'],
        'get_started': ['get started', 'start now', 'begin'],
        'shop_now': ['shop now', 'buy now', 'order']
    }

    cta_counts = {cta_type: 0 for cta_type in cta_keywords}

    for ad in ads:
        body = ad.get('ad_creative_body', '').lower()
        title = ad.get('ad_creative_link_title', '').lower()
        text = f"{body} {title}"

        for cta_type, keywords in cta_keywords.items():
            if any(keyword in text for keyword in keywords):
                cta_counts[cta_type] += 1

    print("\nCTA Analysis:")
    total = sum(cta_counts.values())
    for cta_type, count in sorted(cta_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(ads) * 100) if ads else 0
        print(f"  {cta_type}: {count} ads ({percentage:.1f}%)")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Meta Ads Library API - Usage Examples" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")

    # Check if API is enabled
    if not meta_ads_library.enabled:
        print("\n❌ Meta Ads Library API is not configured!")
        print("\nTo enable, set these environment variables:")
        print("  export META_ACCESS_TOKEN='your_access_token'")
        print("  export META_APP_ID='your_app_id'")
        print("  export META_APP_SECRET='your_app_secret'")
        print("\nRunning with mock/demo mode only...\n")
        return

    print("\n✅ Meta Ads Library API is configured and ready!\n")

    try:
        # Run examples
        example_search_ads()
        example_analyze_top_performers()
        # example_download_video()  # Commented out to avoid downloads
        example_custom_analysis()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
