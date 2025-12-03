#!/usr/bin/env python3
"""
Test script to verify transitions library functionality
"""

import sys
sys.path.insert(0, '/home/user/geminivideo/services/video-agent/pro')

from transitions_library import (
    TransitionLibrary,
    TransitionParams,
    EasingFunction,
    TransitionCategory
)


def main():
    print("=" * 70)
    print("PROFESSIONAL TRANSITIONS LIBRARY - VERIFICATION TEST")
    print("=" * 70)

    # Initialize library
    library = TransitionLibrary()

    # Test 1: Library Statistics
    print("\n[TEST 1] Library Statistics")
    print("-" * 70)
    stats = library.get_stats()
    print(f"✓ Total Transitions: {stats['total_transitions']}")
    print(f"✓ Directional Transitions: {stats['directional_transitions']}")
    print(f"✓ Categories: {len(stats['categories'])}")

    # Test 2: Category Breakdown
    print("\n[TEST 2] Transitions by Category")
    print("-" * 70)
    for category, count in sorted(stats['categories'].items()):
        print(f"  {category:.<20} {count:>3} transitions")

    # Test 3: Get specific transitions
    print("\n[TEST 3] Sample Transition Details")
    print("-" * 70)
    test_transitions = ["fade", "circleopen", "slideleft", "pixelize", "zoomin"]
    for name in test_transitions:
        trans = library.get_transition(name)
        if trans:
            print(f"✓ {trans.name:.<30} [{trans.category.value}]")

    # Test 4: Generate FFmpeg filters
    print("\n[TEST 4] FFmpeg Filter Generation")
    print("-" * 70)
    result = library.apply_transition(
        clip1_duration=10.0,
        clip2_duration=8.0,
        transition_name="fade",
        duration=2.0
    )
    if result:
        print(f"Transition: fade")
        print(f"Filter: {result['filter']}")
        print(f"Offset: {result['offset']}s")
        print(f"Total Duration: {result['total_duration']}s")

    # Test 5: Create and use preset
    print("\n[TEST 5] Transition Presets")
    print("-" * 70)
    params = TransitionParams(
        duration=1.5,
        easing=EasingFunction.EASE_IN_OUT
    )
    success = library.create_preset(
        "cinematic_fade",
        "fade",
        params,
        "Smooth cinematic fade"
    )
    print(f"✓ Preset created: {'Success' if success else 'Failed'}")

    preset_result = library.apply_preset("cinematic_fade", 5.0, 5.0)
    if preset_result:
        print(f"✓ Preset applied: {preset_result['filter']}")

    # Test 6: Search functionality
    print("\n[TEST 6] Search Transitions")
    print("-" * 70)
    search_results = library.search_transitions("blur")
    print(f"Search 'blur': {len(search_results)} results")
    for trans in search_results[:3]:
        print(f"  - {trans.name}")

    # Test 7: Category filtering
    print("\n[TEST 7] Filter by Category")
    print("-" * 70)
    dissolve_trans = library.get_category_transitions(TransitionCategory.DISSOLVE)
    print(f"Dissolve transitions: {len(dissolve_trans)}")
    for trans in dissolve_trans[:3]:
        print(f"  - {trans.name}")

    # Test 8: Preview generation
    print("\n[TEST 8] Transition Preview")
    print("-" * 70)
    preview = library.preview_transition("circleopen", duration=1.0)
    print(f"Transition: {preview['transition']['name']}")
    print(f"Duration: {preview['duration']}s")
    print(f"Filter: {preview['filter']}")

    # Test 9: All categories have transitions
    print("\n[TEST 9] Category Coverage")
    print("-" * 70)
    by_category = library.list_transitions_by_category()
    required_categories = [
        "dissolve", "wipe", "slide", "3d", "blur",
        "glitch", "light", "creative", "geometric"
    ]
    for cat in required_categories:
        count = len(by_category.get(cat, []))
        status = "✓" if count > 0 else "✗"
        print(f"{status} {cat:.<20} {count:>3} transitions")

    # Final Summary
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    print(f"Total Transitions: {stats['total_transitions']} (Required: 50+)")
    print(f"Status: {'✓ PASSED' if stats['total_transitions'] >= 50 else '✗ FAILED'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
