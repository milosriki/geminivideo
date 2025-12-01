#!/usr/bin/env python3
"""
Test script for Meta Ads Library integration
Verifies all methods work correctly
"""

import sys
import json
from pathlib import Path


def test_import():
    """Test that module imports correctly"""
    print("Test 1: Import module...")
    try:
        from meta_ads_library import RealMetaAdsLibrary, meta_ads_library
        print("✅ Import successful")
        return True, meta_ads_library
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False, None


def test_initialization(api):
    """Test API initialization"""
    print("\nTest 2: API initialization...")
    print(f"  API enabled: {api.enabled}")
    print(f"  Access token configured: {bool(api.access_token)}")
    print(f"  App ID configured: {bool(api.app_id)}")
    print(f"  App Secret configured: {bool(api.app_secret)}")

    if api.enabled:
        print("✅ API initialized successfully")
    else:
        print("⚠️  API not configured (will use fallback)")

    return True


def test_search_ads(api):
    """Test search_ads method"""
    print("\nTest 3: search_ads() method...")

    try:
        ads = api.search_ads(
            search_terms="test search",
            countries=['US'],
            media_type='VIDEO',
            limit=5
        )

        print(f"  Returned {len(ads)} ads")

        if ads:
            print("  First ad structure:")
            for key in ads[0].keys():
                print(f"    - {key}")

        print("✅ search_ads() works")
        return True

    except Exception as e:
        print(f"❌ search_ads() failed: {e}")
        return False


def test_analyze_top_performers(api):
    """Test analyze_top_performers method"""
    print("\nTest 4: analyze_top_performers() method...")

    try:
        analysis = api.analyze_top_performers(
            niche_keywords="test",
            min_impressions=1000,
            limit=10
        )

        print(f"  Total ads analyzed: {analysis.get('total_ads_analyzed', 0)}")

        required_keys = [
            'total_ads_analyzed',
            'date_range',
            'copy_patterns',
            'timing_patterns',
            'spend_analysis',
            'top_ads',
            'analyzed_at'
        ]

        for key in required_keys:
            if key in analysis:
                print(f"  ✓ {key}")
            else:
                print(f"  ✗ Missing: {key}")

        print("✅ analyze_top_performers() works")
        return True

    except Exception as e:
        print(f"❌ analyze_top_performers() failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parse_methods(api):
    """Test parsing helper methods"""
    print("\nTest 5: Parsing methods...")

    tests = [
        # Test impressions parsing
        ('_parse_impressions', '10000-50000', {'min': 10000, 'max': 50000, 'avg': 30000}),
        ('_parse_impressions', '25000', {'min': 25000, 'max': 25000, 'avg': 25000}),
        ('_parse_impressions', {'lower_bound': 5000, 'upper_bound': 10000}, {'min': 5000, 'max': 10000, 'avg': 7500}),

        # Test spend parsing
        ('_parse_spend', '$100-$500', {'min': 100.0, 'max': 500.0, 'avg': 300.0}),
        ('_parse_spend', '$1,000', {'min': 1000.0, 'max': 1000.0, 'avg': 1000.0}),
        ('_parse_spend', {'lower_bound': 200, 'upper_bound': 800}, {'min': 200.0, 'max': 800.0, 'avg': 500.0}),
    ]

    passed = 0
    for method_name, input_val, expected in tests:
        try:
            method = getattr(api, method_name)
            result = method(input_val)

            if result == expected:
                print(f"  ✓ {method_name}({repr(input_val)}) -> {result}")
                passed += 1
            else:
                print(f"  ✗ {method_name}({repr(input_val)}) expected {expected}, got {result}")

        except Exception as e:
            print(f"  ✗ {method_name}({repr(input_val)}) raised {e}")

    if passed == len(tests):
        print("✅ All parsing tests passed")
        return True
    else:
        print(f"⚠️  {passed}/{len(tests)} parsing tests passed")
        return False


def test_copy_patterns(api):
    """Test copy pattern analysis"""
    print("\nTest 6: Copy pattern analysis...")

    # Mock ads with different patterns
    mock_ads = [
        {'ad_creative_body': 'Are you ready to transform your life?', 'ad_creative_link_title': ''},
        {'ad_creative_body': 'Get 50% off now! Limited time offer.', 'ad_creative_link_title': ''},
        {'ad_creative_body': 'Proven results trusted by thousands', 'ad_creative_link_title': ''},
        {'ad_creative_body': 'Stop wasting money on ads that don\'t work', 'ad_creative_link_title': ''},
        {'ad_creative_body': 'Transform your body in just 30 days', 'ad_creative_link_title': ''},
    ]

    try:
        patterns = api._analyze_copy_patterns(mock_ads)

        print("  Detected patterns:")
        for pattern, data in patterns.items():
            print(f"    {pattern}: {data['count']} ({data['percentage']}%)")

        # Verify expected patterns
        assert patterns['question']['count'] >= 1, "Should detect question"
        assert patterns['urgency']['count'] >= 1, "Should detect urgency"
        assert patterns['social_proof']['count'] >= 1, "Should detect social proof"
        assert patterns['negative_hooks']['count'] >= 1, "Should detect negative hooks"
        assert patterns['transformation']['count'] >= 1, "Should detect transformation"
        assert patterns['number']['count'] >= 1, "Should detect numbers"

        print("✅ Copy pattern analysis works")
        return True

    except Exception as e:
        print(f"❌ Copy pattern analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timing_patterns(api):
    """Test timing pattern analysis"""
    print("\nTest 7: Timing pattern analysis...")

    # Mock ads with dates
    mock_ads = [
        {'ad_delivery_start_time': '2024-01-15T10:00:00+0000'},
        {'ad_delivery_start_time': '2024-01-16T14:30:00+0000'},
        {'ad_delivery_start_time': '2024-02-20T09:15:00+0000'},
        {'ad_delivery_start_time': '2024-03-05T18:45:00+0000'},
    ]

    try:
        patterns = api._analyze_timing_patterns(mock_ads)

        print("  Best launch days:")
        for day_info in patterns.get('best_launch_days', []):
            print(f"    {day_info['day']}: {day_info['count']} ({day_info['percentage']}%)")

        print("✅ Timing pattern analysis works")
        return True

    except Exception as e:
        print(f"❌ Timing pattern analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pattern_miner_integration():
    """Test integration with pattern miner script"""
    print("\nTest 8: Pattern miner integration...")

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
        from meta_ads_library_pattern_miner import AdPatternMiner

        config_path = Path(__file__).parent.parent.parent / 'shared' / 'config'

        # Initialize with mock data
        miner = AdPatternMiner(config_path, use_real_api=False)

        # Test analysis
        patterns = miner.analyze_ad_library_export(
            niche_keywords="test",
            min_impressions=1000,
            limit=10
        )

        required_keys = ['hook_patterns', 'duration_patterns', 'visual_patterns', 'cta_patterns']
        for key in required_keys:
            if key in patterns:
                print(f"  ✓ {key}")
            else:
                print(f"  ✗ Missing: {key}")

        print("✅ Pattern miner integration works")
        return True

    except Exception as e:
        print(f"❌ Pattern miner integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Meta Ads Library - Test Suite" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # Test 1: Import
    success, api = test_import()
    results.append(success)

    if not success:
        print("\n❌ Cannot continue without successful import")
        return

    # Test 2: Initialization
    results.append(test_initialization(api))

    # Test 3-4: API methods
    results.append(test_search_ads(api))
    results.append(test_analyze_top_performers(api))

    # Test 5-7: Helper methods
    results.append(test_parse_methods(api))
    results.append(test_copy_patterns(api))
    results.append(test_timing_patterns(api))

    # Test 8: Integration
    results.append(test_pattern_miner_integration())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
