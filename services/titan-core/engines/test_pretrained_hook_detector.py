#!/usr/bin/env python3
"""
Test script for PretrainedHookDetector
Demonstrates real usage with pretrained BERT/RoBERTa models
"""

import logging
from pretrained_hook_detector import (
    PretrainedHookDetector,
    HookType,
    HookResult,
    HookAnalysis
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_detection():
    """Test basic hook detection."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Hook Detection")
    print("=" * 80)

    detector = PretrainedHookDetector()

    test_hooks = [
        "What if you could 10X your revenue in 30 days?",
        "Limited time: Get 50% off before midnight!",
        "10,000+ marketers use this secret strategy",
        "The shocking truth they don't want you to know",
        "From $0 to $100K in just 6 months"
    ]

    for hook in test_hooks:
        result = detector.detect_hook(hook)
        print(f"\nHook: {hook}")
        print(f"  Primary Type: {result.primary_hook_type.value}")
        print(f"  Strength: {result.hook_strength:.3f}")
        print(f"  Attention: {result.attention_score:.3f}")
        print(f"  Sentiment: {result.sentiment} ({result.sentiment_score:.3f})")
        print(f"  Top 3 Types:")
        for hook_type, score in result.hook_types[:3]:
            print(f"    - {hook_type.value}: {score:.3f}")


def test_batch_processing():
    """Test batch hook detection."""
    print("\n" + "=" * 80)
    print("TEST 2: Batch Processing")
    print("=" * 80)

    detector = PretrainedHookDetector()

    hooks = [
        "Discover the secret to effortless weight loss",
        "Why you're failing at social media (and how to fix it)",
        "Don't make these 5 deadly marketing mistakes",
        "Join 50,000+ successful entrepreneurs today",
        "This one weird trick changed everything"
    ]

    results = detector.detect_hooks_batch(hooks)

    print(f"\nProcessed {len(results)} hooks")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.text[:50]}...")
        print(f"   Type: {result.primary_hook_type.value}, Strength: {result.hook_strength:.3f}")


def test_hook_analysis():
    """Test hook analysis across multiple texts."""
    print("\n" + "=" * 80)
    print("TEST 3: Hook Analysis")
    print("=" * 80)

    detector = PretrainedHookDetector()

    successful_hooks = [
        "What if you could 3X your sales this month?",
        "Limited offer: Save $500 before Friday",
        "10,000 customers trust our proven system",
        "The uncomfortable truth about your business",
        "From zero to hero in 90 days"
    ]

    analysis = detector.analyze_hooks(successful_hooks)

    print(f"\nHooks Detected: {analysis.hooks_detected}")
    print(f"Primary Hook Type: {analysis.primary_hook.value}")
    print(f"Average Strength: {analysis.avg_hook_strength:.3f}")
    print(f"\nHook Distribution:")
    for hook_type, percentage in analysis.hook_distribution.items():
        print(f"  {hook_type}: {percentage:.1%}")
    print(f"\nStrongest: {analysis.strongest_hook_text}")
    print(f"Weakest: {analysis.weakest_hook_text}")


def test_hook_comparison():
    """Test hook comparison."""
    print("\n" + "=" * 80)
    print("TEST 4: Hook Comparison")
    print("=" * 80)

    detector = PretrainedHookDetector()

    hooks = [
        "Save money on your energy bills",
        "SHOCKING: Your energy company is ripping you off!",
        "What if you could cut your energy costs by 50%?"
    ]

    comparison = detector.compare_hooks(hooks)

    print("\nComparing hooks:")
    for hook_data in comparison['hooks']:
        print(f"\n'{hook_data['text']}'")
        print(f"  Type: {hook_data['primary_type']}")
        print(f"  Strength: {hook_data['strength']:.3f}")
        print(f"  Attention: {hook_data['attention']:.3f}")

    print(f"\nBest Overall: {comparison['best_overall']}")
    print(f"Best Attention: {comparison['best_attention']}")
    print(f"Best Curiosity: {comparison['best_curiosity']}")


def test_hook_ranking():
    """Test hook ranking."""
    print("\n" + "=" * 80)
    print("TEST 5: Hook Ranking")
    print("=" * 80)

    detector = PretrainedHookDetector()

    hooks = [
        "Save 20% today",
        "WARNING: You're losing money every day",
        "Discover the secret to unlimited traffic",
        "Join 100,000+ successful marketers"
    ]

    print("\nRanking by Strength:")
    ranked = detector.rank_hooks(hooks, metric="strength")
    for i, (hook, score) in enumerate(ranked, 1):
        print(f"{i}. [{score:.3f}] {hook}")

    print("\nRanking by Attention:")
    ranked = detector.rank_hooks(hooks, metric="attention")
    for i, (hook, score) in enumerate(ranked, 1):
        print(f"{i}. [{score:.3f}] {hook}")


def test_improvement_suggestions():
    """Test improvement suggestions."""
    print("\n" + "=" * 80)
    print("TEST 6: Improvement Suggestions")
    print("=" * 80)

    detector = PretrainedHookDetector()

    weak_hooks = [
        "Buy our product",
        "This is a really amazing and incredible opportunity that you should definitely check out",
        "How to do marketing"
    ]

    for hook in weak_hooks:
        result = detector.detect_hook(hook)
        print(f"\nHook: {hook}")
        print(f"Strength: {result.hook_strength:.3f}")
        print("Suggestions:")
        for suggestion in result.improvement_suggestions:
            print(f"  - {suggestion}")


def test_pattern_extraction():
    """Test pattern extraction."""
    print("\n" + "=" * 80)
    print("TEST 7: Pattern Extraction")
    print("=" * 80)

    detector = PretrainedHookDetector()

    successful_hooks = [
        "What if you could 10X your results?",
        "What if doubling your income was easy?",
        "Discover the secret to viral content",
        "Discover how to grow your audience 5X",
        "Limited time: Save 50% today",
        "Limited offer: Get 3 months free"
    ]

    patterns = detector.extract_hook_patterns(successful_hooks)

    print("\nExtracted Patterns:")
    print(f"Common Hook Types: {patterns['common_hook_types']}")
    print(f"Average Length: {patterns['avg_length']} words")
    print(f"Average Strength: {patterns['avg_strength']:.3f}")
    print(f"Common Words: {', '.join(patterns['common_words'][:5])}")
    print(f"Common Patterns: {', '.join(patterns['common_patterns'])}")


def test_hook_variants():
    """Test hook variant generation."""
    print("\n" + "=" * 80)
    print("TEST 8: Hook Variant Generation")
    print("=" * 80)

    detector = PretrainedHookDetector()

    original = "double your sales with email marketing"

    variants = detector.generate_hook_variants(original, num_variants=5)

    print(f"\nOriginal: {original}")
    print("\nVariants:")
    for i, variant in enumerate(variants, 1):
        print(f"{i}. {variant}")


def test_model_info():
    """Test model information."""
    print("\n" + "=" * 80)
    print("TEST 9: Model Information")
    print("=" * 80)

    detector = PretrainedHookDetector()

    info = detector.get_model_info()

    print("\nModel Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")


def test_warmup():
    """Test model warmup."""
    print("\n" + "=" * 80)
    print("TEST 10: Model Warmup")
    print("=" * 80)

    detector = PretrainedHookDetector()
    detector.warmup()
    print("Warmup completed successfully")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PRETRAINED HOOK DETECTOR TEST SUITE")
    print("Testing with Real HuggingFace Models")
    print("=" * 80)

    try:
        # Run tests
        test_basic_detection()
        test_batch_processing()
        test_hook_analysis()
        test_hook_comparison()
        test_hook_ranking()
        test_improvement_suggestions()
        test_pattern_extraction()
        test_hook_variants()
        test_model_info()
        test_warmup()

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
