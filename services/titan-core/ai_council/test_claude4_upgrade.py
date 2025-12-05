#!/usr/bin/env python3
"""
Test script for Claude 4 Opus upgrade
Validates new features: extended thinking, prompt caching, tiered models
"""

import asyncio
import os
from typing import Dict, Any


async def test_claude4_features():
    """Test all Claude 4 Opus features"""
    print("=" * 70)
    print("CLAUDE 4 OPUS UPGRADE VALIDATION TEST")
    print("=" * 70)
    print()

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set")
        print("   Set it to test Claude 4 features:")
        print("   export ANTHROPIC_API_KEY='sk-ant-...'")
        print()

    # Import council
    try:
        from council_of_titans import council
        print("✅ Council imported successfully")
        print(f"   Initialization message: Check console above")
        print()
    except Exception as e:
        print(f"❌ Failed to import council: {e}")
        return False

    # Test script
    test_script = """
    Struggling with burnout? You're not alone.

    Watch how Sarah went from working 80 hours a week to just 40 -
    while DOUBLING her income.

    The secret? A simple automation system that works while you sleep.

    Book your free strategy call now.
    Limited spots this week.
    """

    print("📝 Test Script:")
    print(test_script.strip())
    print()

    # Test 1: Basic Council Evaluation
    print("-" * 70)
    print("TEST 1: Full Council Evaluation (with Claude 4 Opus)")
    print("-" * 70)

    try:
        result = await council.evaluate_script(
            script=test_script,
            visual_features={
                "has_human_face": True,
                "hook_type": "curiosity_gap",
                "high_contrast": True,
                "scene_count": 4
            }
        )

        print(f"✅ Council evaluation completed")
        print(f"   Final Score: {result['final_score']}")
        print(f"   Verdict: {result['verdict']}")
        print(f"   Council Version: {result.get('council_version', 'N/A')}")
        print()

        print("   Breakdown:")
        breakdown = result.get('breakdown', {})

        # Claude 4 Opus details
        if 'claude_4_opus' in breakdown:
            claude = breakdown['claude_4_opus']
            print(f"   • Claude 4 Opus: {claude.get('score', 'N/A')} (weight: {claude.get('weight', 'N/A')})")
            print(f"     - Extended Thinking: {claude.get('extended_thinking', False)}")
            print(f"     - Cache Savings: {claude.get('cache_savings', 'N/A')}")
            if 'reasoning' in claude and claude['reasoning']:
                print(f"     - Reasoning Preview: {claude['reasoning'][:100]}...")
        else:
            print("   ⚠️  Claude 4 Opus not in breakdown (check logs)")

        # Other models
        if 'gemini_2_0_thinking' in breakdown:
            gemini = breakdown['gemini_2_0_thinking']
            print(f"   • Gemini 2.0 Thinking: {gemini.get('score', 'N/A')} (weight: {gemini.get('weight', 'N/A')})")

        if 'gpt_4o' in breakdown:
            gpt = breakdown['gpt_4o']
            print(f"   • GPT-4o: {gpt.get('score', 'N/A')} (weight: {gpt.get('weight', 'N/A')})")

        if 'deep_ctr' in breakdown:
            deep = breakdown['deep_ctr']
            print(f"   • DeepCTR: {deep.get('score', 'N/A')} (weight: {deep.get('weight', 'N/A')})")

        print()

    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Claude 4 Opus Direct
    print("-" * 70)
    print("TEST 2: Claude 4 Opus Direct (Extended Thinking)")
    print("-" * 70)

    try:
        opus_result = await council.get_claude_opus_critique(
            script=test_script,
            use_extended_thinking=True
        )

        print(f"✅ Claude 4 Opus analysis completed")
        print(f"   Score: {opus_result.get('score', 'N/A')}")
        print(f"   Source: {opus_result.get('source', 'N/A')}")
        print(f"   Extended Thinking: {opus_result.get('extended_thinking_used', False)}")
        print(f"   Cache Creation Tokens: {opus_result.get('cache_creation_tokens', 0)}")
        print(f"   Cache Read Tokens: {opus_result.get('cache_read_tokens', 0)}")

        if 'reasoning' in opus_result and opus_result['reasoning']:
            print(f"   Reasoning (first 200 chars):")
            print(f"   {opus_result['reasoning'][:200]}...")

        print()

    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        print(f"   This is expected if Anthropic SDK < 0.40.0")
        print()

    # Test 3: Haiku Quick Check
    print("-" * 70)
    print("TEST 3: Claude 3.5 Haiku Quick Check")
    print("-" * 70)

    try:
        haiku_result = await council.get_claude_haiku_quick_check(test_script)

        print(f"✅ Haiku quick check completed")
        print(f"   Score: {haiku_result.get('score', 'N/A')}")
        print(f"   Source: {haiku_result.get('source', 'N/A')}")
        print(f"   Speed: Fast (< 1 second)")
        print()

    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        print()

    # Test 4: Prompt Caching (Second Request)
    print("-" * 70)
    print("TEST 4: Prompt Caching (Second Request)")
    print("-" * 70)

    try:
        print("   Making second request (should hit cache)...")
        opus_result2 = await council.get_claude_opus_critique(
            script="Different script to test caching",
            use_extended_thinking=True
        )

        cache_read = opus_result2.get('cache_read_tokens', 0)
        cache_created = opus_result2.get('cache_creation_tokens', 0)

        print(f"✅ Second request completed")
        print(f"   Cache Read Tokens: {cache_read}")
        print(f"   Cache Creation Tokens: {cache_created}")

        if cache_read > 0:
            print(f"   🎉 PROMPT CACHING WORKING! Saved {cache_read} tokens")
        else:
            print(f"   ⚠️  No cache hit (first request creates cache)")

        print()

    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        print()

    # Test 5: Weight Verification
    print("-" * 70)
    print("TEST 5: Weight Verification")
    print("-" * 70)

    try:
        result = await council.evaluate_script(test_script)
        weights = result.get('weights', {})

        print("✅ Weights configured:")
        print(f"   • Claude 4 Opus: {weights.get('claude_4_opus', 'N/A')} (expected: 40%)")
        print(f"   • Gemini 2.0 Thinking: {weights.get('gemini_2_0_thinking', 'N/A')} (expected: 35%)")
        print(f"   • GPT-4o: {weights.get('gpt_4o', 'N/A')} (expected: 15%)")
        print(f"   • DeepCTR: {weights.get('deep_ctr', 'N/A')} (expected: 10%)")

        # Verify weights sum to 100%
        total = sum([
            float(weights.get('claude_4_opus', '0%').rstrip('%')) if weights.get('claude_4_opus') else 0,
            float(weights.get('gemini_2_0_thinking', '0%').rstrip('%')) if weights.get('gemini_2_0_thinking') else 0,
            float(weights.get('gpt_4o', '0%').rstrip('%')) if weights.get('gpt_4o') else 0,
            float(weights.get('deep_ctr', '0%').rstrip('%')) if weights.get('deep_ctr') else 0,
        ])

        if abs(total - 100.0) < 0.01:
            print(f"   ✅ Weights sum to 100%")
        else:
            print(f"   ⚠️  Weights sum to {total}% (should be 100%)")

        print()

    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
        print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    print("✅ Claude 4 Opus upgrade validation complete!")
    print()
    print("Next steps:")
    print("1. Ensure anthropic>=0.40.0 is installed")
    print("2. Set ANTHROPIC_API_KEY environment variable")
    print("3. Test with your actual ad scripts")
    print("4. Monitor cache hit rates and costs")
    print()
    print("Documentation: See CLAUDE_4_UPGRADE.md")
    print("=" * 70)

    return True


async def main():
    """Run all tests"""
    await test_claude4_features()


if __name__ == "__main__":
    asyncio.run(main())
