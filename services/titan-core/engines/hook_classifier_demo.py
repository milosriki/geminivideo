"""
Demo script for HookClassifier
Shows how to use the BERT-based hook pattern classifier
"""
import logging
from hook_classifier import HookClassifier, get_hook_classifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_basic_classification():
    """Demonstrate basic hook classification"""
    print("\n" + "="*80)
    print("DEMO 1: Basic Hook Classification")
    print("="*80)

    classifier = get_hook_classifier()

    # Test hooks
    test_hooks = [
        "This one weird trick will change everything...",
        "From $0 to $10,000 in just 30 days",
        "Only 3 spots left - grab yours now!",
        "My client just made $50k using this exact method",
        "Stop everything you're doing right now",
        "Are you making these 5 costly mistakes?",
        "Never waste money on ads again",
        "Let me tell you about the day I lost it all...",
        "347% increase proven by Stanford study",
        "Everything they taught you about marketing is wrong"
    ]

    for hook in test_hooks:
        result = classifier.classify(hook)
        print(f"\nHook: '{hook}'")
        print(f"  Primary Type: {result.primary_hook} (confidence: {result.confidence:.2%})")
        print(f"  Hook Strength: {result.hook_strength:.2f}/1.0")
        print(f"  Top 3 Types: {', '.join([f'{t}({s:.1%})' for t, s in result.secondary_hooks[:3]])}")


def demo_video_script_analysis():
    """Demonstrate video script analysis"""
    print("\n" + "="*80)
    print("DEMO 2: Video Script Analysis")
    print("="*80)

    classifier = get_hook_classifier()

    # Sample video script
    script = """
    Stop wasting money on Facebook ads that don't convert!
    I'm about to reveal the secret strategy that took my client from $500/day in ad spend
    to $50,000 in monthly revenue.

    [3s]

    Most people think you need a huge budget to succeed with Facebook ads.
    They think you need fancy video equipment, professional actors, and a massive
    production budget. But that couldn't be further from the truth.

    The real secret is understanding hook patterns and how to trigger emotional responses
    in your audience within the first 3 seconds of your video.
    """

    result = classifier.classify_video_script(script, hook_end_marker="[3s]")

    print(f"\nScript Analysis:")
    print(f"  Hook: '{result['hook']['text']}'")
    print(f"  Hook Type: {result['hook']['classification']['primary_type']}")
    print(f"  Confidence: {result['hook']['classification']['confidence']:.2%}")
    print(f"  Hook Strength: {result['hook']['strength']:.2f}")
    print(f"  Word Count: {result['hook']['word_count']} words")
    print(f"  Hook-to-Body Ratio: {result['hook_to_body_ratio']:.2%}")
    print(f"\n  Secondary Types:")
    for hook_type, score in result['hook']['classification']['secondary_types']:
        print(f"    - {hook_type}: {score:.2%}")


def demo_batch_analysis():
    """Demonstrate analyzing multiple top-performing hooks"""
    print("\n" + "="*80)
    print("DEMO 3: Analyzing Top Performer Hooks (Simulated)")
    print("="*80)

    classifier = get_hook_classifier()

    # Simulate hooks from top-performing ads
    top_performer_hooks = [
        "This secret method made my client $50k in 30 days",
        "From broke to $10k/month - here's how",
        "Stop wasting money on ads that don't work!",
        "Only 24 hours left to get this exclusive deal",
        "Are you making these 3 fatal ad mistakes?",
        "Watch this complete transformation in 60 seconds",
        "10,000+ businesses have already switched to this",
        "Everything you know about video ads is wrong",
        "Never run another unprofitable ad campaign",
        "Studies show this increases ROAS by 347%"
    ]

    analysis = classifier.analyze_top_performer_hooks(top_performer_hooks)

    print(f"\nTop Performer Analysis:")
    print(f"  Total Hooks Analyzed: {analysis['total_hooks_analyzed']}")
    print(f"  Average Confidence: {analysis['avg_confidence']:.2%}")
    print(f"  Average Hook Strength: {analysis['avg_strength']:.2f}")
    print(f"  Dominant Pattern: {analysis['dominant_pattern']}")

    print(f"\n  Top 3 Patterns:")
    for pattern in analysis['top_patterns']:
        print(f"    - {pattern['type']}: {pattern['count']} ads ({pattern['percentage']:.1f}%)")

    print(f"\n  Hook Type Distribution:")
    for hook_type, count in sorted(
        analysis['hook_type_distribution'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        if count > 0:
            print(f"    - {hook_type}: {count}")

    print(f"\n  Recommendations:")
    for rec in analysis['recommendations']:
        print(f"    {rec}")


def demo_hook_examples():
    """Show example hooks for each type"""
    print("\n" + "="*80)
    print("DEMO 4: Example Hooks by Type")
    print("="*80)

    classifier = get_hook_classifier()
    examples = classifier.get_hook_examples()

    for hook_type, example_list in examples.items():
        print(f"\n{hook_type.upper().replace('_', ' ')}:")
        for i, example in enumerate(example_list[:2], 1):
            print(f"  {i}. {example}")


def demo_training_data_format():
    """Show how training data should be formatted"""
    print("\n" + "="*80)
    print("DEMO 5: Training Data Format")
    print("="*80)

    print("\nTo fine-tune the classifier on your own data, use this format:")
    print("\ntrain_data = [")
    print("    {'text': 'Stop wasting money on ads!', 'label': 'negative_hook'},")
    print("    {'text': 'From $0 to $10k in 30 days', 'label': 'transformation'},")
    print("    {'text': 'Only 3 spots left!', 'label': 'urgency_scarcity'},")
    print("    # ... more examples")
    print("]")
    print("\nclassifier.train(")
    print("    train_data=train_data,")
    print("    val_data=val_data,  # Optional")
    print("    num_epochs=3,")
    print("    batch_size=16")
    print(")")

    print("\nAvailable hook types:")
    for hook_type in HookClassifier.HOOK_TYPES:
        print(f"  - {hook_type}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("BERT-BASED HOOK PATTERN CLASSIFIER - DEMO")
    print("="*80)

    try:
        demo_basic_classification()
        demo_video_script_analysis()
        demo_batch_analysis()
        demo_hook_examples()
        demo_training_data_format()

        print("\n" + "="*80)
        print("✅ All demos completed successfully!")
        print("="*80)

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print("\n⚠️ Note: transformers and torch must be installed to run the classifier")
        print("Install with: pip install transformers torch")
