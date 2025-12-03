#!/usr/bin/env python3
"""
Quick Demo: PretrainedHookDetector
Shows basic usage with real pretrained models
"""

from pretrained_hook_detector import PretrainedHookDetector, HookType


def main():
    print("=" * 80)
    print("PRETRAINED HOOK DETECTOR - QUICK DEMO")
    print("Agent 17 of 30: Real BERT/RoBERTa Hook Detection")
    print("=" * 80)

    # Initialize detector (will auto-detect GPU/CPU)
    print("\n[1] Initializing detector with pretrained models...")
    print("    Loading: cardiffnlp/twitter-roberta-base-sentiment-latest")
    print("    Loading: facebook/bart-large-mnli")
    detector = PretrainedHookDetector()

    # Example hooks
    test_hooks = [
        "What if you could 10X your revenue in 30 days?",
        "Limited time: Get 50% off before midnight!",
        "10,000+ marketers use this secret strategy",
        "The shocking truth they don't want you to know",
        "From $0 to $100K in just 6 months"
    ]

    print("\n[2] Analyzing 5 different hooks...")
    print("-" * 80)

    for i, hook in enumerate(test_hooks, 1):
        result = detector.detect_hook(hook)

        print(f"\n{i}. {hook}")
        print(f"   Primary Hook Type: {result.primary_hook_type.value.upper()}")
        print(f"   Hook Strength: {result.hook_strength:.2%}")
        print(f"   Attention Score: {result.attention_score:.2%}")
        print(f"   Sentiment: {result.sentiment.upper()} ({result.sentiment_score:.2%})")

        print(f"   Top Hook Types:")
        for hook_type, score in result.hook_types[:3]:
            print(f"     - {hook_type.value}: {score:.2%}")

        if result.improvement_suggestions:
            print(f"   Suggestions: {result.improvement_suggestions[0]}")

    # Batch analysis
    print("\n" + "-" * 80)
    print("[3] Batch Analysis of All Hooks")
    print("-" * 80)

    analysis = detector.analyze_hooks(test_hooks)

    print(f"\nTotal Hooks Analyzed: {analysis.hooks_detected}")
    print(f"Primary Hook Type: {analysis.primary_hook.value.upper()}")
    print(f"Average Hook Strength: {analysis.avg_hook_strength:.2%}")

    print(f"\nHook Type Distribution:")
    for hook_type, percentage in sorted(
        analysis.hook_distribution.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {hook_type}: {percentage:.0%}")

    print(f"\nStrongest Hook: {analysis.strongest_hook_text}")
    print(f"Weakest Hook: {analysis.weakest_hook_text}")

    # Hook comparison
    print("\n" + "-" * 80)
    print("[4] Comparing Hook Variations")
    print("-" * 80)

    comparison_hooks = [
        "Save money on your bills",
        "SHOCKING: You're being overcharged!",
        "What if you could cut costs by 50%?"
    ]

    comparison = detector.compare_hooks(comparison_hooks)

    print("\nComparing 3 variations:")
    for hook_data in comparison['hooks']:
        print(f"\n  '{hook_data['text']}'")
        print(f"    Strength: {hook_data['strength']:.2%}")
        print(f"    Attention: {hook_data['attention']:.2%}")
        print(f"    Type: {hook_data['primary_type']}")

    print(f"\nWinner (Overall): {comparison['best_overall']}")
    print(f"Winner (Attention): {comparison['best_attention']}")

    # Hook ranking
    print("\n" + "-" * 80)
    print("[5] Ranking Hooks by Strength")
    print("-" * 80)

    ranked = detector.rank_hooks(test_hooks, metric="strength")

    print("\nTop to Bottom:")
    for i, (hook, score) in enumerate(ranked, 1):
        print(f"{i}. [{score:.2%}] {hook}")

    # Pattern extraction
    print("\n" + "-" * 80)
    print("[6] Extracting Patterns from Successful Hooks")
    print("-" * 80)

    patterns = detector.extract_hook_patterns(test_hooks)

    print(f"\nCommon Hook Types: {patterns['common_hook_types']}")
    print(f"Average Length: {patterns['avg_length']} words")
    print(f"Average Strength: {patterns['avg_strength']:.2%}")
    print(f"Common Words: {', '.join(patterns['common_words'][:8])}")
    print(f"Common Patterns: {', '.join(patterns['common_patterns'])}")

    # Model info
    print("\n" + "-" * 80)
    print("[7] Model Information")
    print("-" * 80)

    info = detector.get_model_info()

    print(f"\nSentiment Model: {info['sentiment_model']}")
    print(f"Classification Model: {info['classification_model']}")
    print(f"Device: {info['device'].upper()}")
    print(f"CUDA Available: {info['cuda_available']}")
    if info.get('cuda_device_name'):
        print(f"GPU: {info['cuda_device_name']}")

    print(f"\nSupported Hook Types ({len(info['hook_types'])}):")
    for hook_type in info['hook_types']:
        print(f"  - {hook_type}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("All features working with real pretrained models!")
    print("=" * 80)


if __name__ == "__main__":
    main()
