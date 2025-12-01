# BERT-Based Hook Pattern Classifier

Production-ready ML classifier for analyzing video ad hooks using transformer models.

## Overview

The HookClassifier uses BERT (Bidirectional Encoder Representations from Transformers) to classify video script hooks into 10 distinct pattern types. This enables data-driven insights into which hook types perform best for your campaigns.

## Hook Types

The classifier identifies 10 hook patterns:

1. **curiosity_gap** - Creates information gaps that viewers want filled
   - "This one weird trick will change everything..."
   - "You won't believe what happened next"
   - "The secret nobody wants you to know"

2. **transformation** - Shows before/after, results, changes
   - "From $0 to $10k in 30 days"
   - "Before I was struggling, now I'm thriving"
   - "Watch this complete transformation"

3. **urgency_scarcity** - Limited time, exclusive, FOMO-driven
   - "Only 24 hours left to get this deal"
   - "Limited spots available - act now"
   - "This offer expires tonight"

4. **social_proof** - Testimonials, reviews, client results
   - "Over 10,000 customers have already transformed their lives"
   - "Client just hit $50k using this exact strategy"
   - "My student made $5k in the first week"

5. **pattern_interrupt** - Unexpected, shocking, breaks expectations
   - "Stop what you're doing right now"
   - "Everyone is doing this wrong"
   - "Throw away everything you thought you knew"

6. **question** - Direct questions that engage viewer
   - "Are you making these costly mistakes?"
   - "What if I told you there's a better way?"
   - "How would your life change if...?"

7. **negative_hook** - Warns about mistakes, things to avoid
   - "Stop wasting money on ads that don't work"
   - "The 5 mistakes killing your business"
   - "Never do this in your videos"

8. **story_hook** - Narrative-based, personal stories
   - "Three months ago, I was living in my car..."
   - "Let me tell you about the worst day of my life"
   - "I'll never forget the moment I realized"

9. **statistic_hook** - Data-driven, numbers, percentages
   - "95% of businesses fail because of this"
   - "Studies show this increases conversions by 347%"
   - "$10 million in revenue from one video"

10. **controversy_hook** - Contrarian, challenges conventional wisdom
    - "Everything you know about marketing is wrong"
    - "The industry doesn't want you to know this"
    - "Why the experts are lying to you"

## Installation

```bash
pip install transformers torch
```

Already included in titan-core requirements.txt

## Basic Usage

### 1. Classify a Single Hook

```python
from engines.hook_classifier import get_hook_classifier

# Get classifier instance (lazy loaded)
classifier = get_hook_classifier()

# Classify a hook
result = classifier.classify("Stop wasting money on ads that don't work!")

print(f"Primary Hook: {result.primary_hook}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Hook Strength: {result.hook_strength:.2f}")
print(f"All Scores: {result.all_scores}")
```

### 2. Analyze a Video Script

```python
script = """
Stop wasting money on Facebook ads that don't convert!
I'm about to reveal the secret strategy that took my client
from $500/day to $50,000 in monthly revenue.
[3s]
Most people think you need a huge budget...
"""

result = classifier.classify_video_script(
    script,
    hook_end_marker="[3s]"
)

print(f"Hook Type: {result['hook']['classification']['primary_type']}")
print(f"Hook Strength: {result['hook']['strength']:.2f}")
print(f"Word Count: {result['hook']['word_count']}")
```

### 3. Analyze Top Performer Hooks

```python
# Hooks from your best-performing ads
top_hooks = [
    "This secret method made my client $50k",
    "From broke to $10k/month - here's how",
    "Stop wasting money on ads that don't work!",
    # ... more hooks
]

analysis = classifier.analyze_top_performer_hooks(top_hooks)

print(f"Dominant Pattern: {analysis['dominant_pattern']}")
print(f"Top 3 Patterns: {analysis['top_patterns']}")
print(f"Recommendations: {analysis['recommendations']}")
```

### 4. Batch Classification

```python
hooks = ["Hook 1", "Hook 2", "Hook 3", ...]
results = classifier.batch_classify(hooks, batch_size=32)

for hook, result in zip(hooks, results):
    print(f"{hook} -> {result.primary_hook} ({result.confidence:.2%})")
```

## Integration with Meta Learning Agent

The classifier is automatically integrated with the Meta Learning Agent:

```python
from meta_learning_agent import meta_learning_agent

# Run learning cycle
result = meta_learning_agent.run_learning_cycle(days_back=30)

# Hook patterns now use ML classification
hook_patterns = result['patterns']['hook_patterns']

# Access ML insights
ml_analysis = hook_patterns['_ml_analysis']
print(f"Dominant Pattern: {ml_analysis['dominant_pattern']}")
print(f"Average Confidence: {ml_analysis['avg_confidence']:.2%}")
print(f"ML Recommendations: {ml_analysis['ml_recommendations']}")
```

## Fine-Tuning on Custom Data

Train the classifier on your own labeled hook data:

```python
# Prepare training data
train_data = [
    {'text': 'Stop wasting money on ads!', 'label': 'negative_hook'},
    {'text': 'From $0 to $10k in 30 days', 'label': 'transformation'},
    {'text': 'Only 3 spots left!', 'label': 'urgency_scarcity'},
    # ... at least 50-100 examples per class recommended
]

# Optional validation data
val_data = [
    {'text': 'Never make this mistake again', 'label': 'negative_hook'},
    # ... 10-20% of training data size
]

# Train
result = classifier.train(
    train_data=train_data,
    val_data=val_data,
    num_epochs=3,
    learning_rate=2e-5,
    batch_size=16
)

print(f"Training complete: {result['output_dir']}")
print(f"Metrics: {result['metrics']}")
```

## Hook Strength Calculation

Hook strength (0.0-1.0) is calculated based on:

1. **Primary Classification Confidence** (main factor)
2. **Ensemble Effect** - Multiple strong hook signals
3. **Power Words** - Presence of trigger words (secret, proven, shocking, etc.)
4. **Questions** - Engagement through questions
5. **Emphasis** - Exclamation points

## API Reference

### HookClassifier

#### `__init__(model_name, device, lazy_load, cache_dir)`
- `model_name`: HuggingFace model or local path (default: "bert-base-uncased")
- `device`: 'cpu', 'cuda', 'mps', or None for auto-detect
- `lazy_load`: Only load model when first needed (default: True)
- `cache_dir`: Model cache directory

#### `classify(text) -> HookClassification`
Classify a single hook text.

Returns:
- `primary_hook`: Most likely hook type
- `confidence`: Confidence score (0-1)
- `secondary_hooks`: List of (type, score) tuples
- `all_scores`: Dict of all hook type scores
- `hook_strength`: Overall hook strength (0-1)

#### `classify_video_script(transcript, hook_end_marker, hook_duration_seconds) -> Dict`
Analyze a video script, separating hook from body.

#### `batch_classify(texts, batch_size) -> List[HookClassification]`
Classify multiple hooks efficiently.

#### `train(train_data, val_data, output_dir, num_epochs, learning_rate, batch_size) -> Dict`
Fine-tune the classifier on custom data.

#### `analyze_top_performer_hooks(hooks) -> Dict`
Analyze multiple hooks to identify dominant patterns.

#### `get_hook_examples() -> Dict[str, List[str]]`
Get example hooks for each type.

## Performance Considerations

### Device Selection
- **CUDA (GPU)**: Best performance, ~10-50x faster than CPU
- **MPS (Apple Silicon)**: Good performance on M1/M2 Macs
- **CPU**: Slower but works everywhere

### Lazy Loading
By default, the model is lazy loaded (only loads when first used). This saves startup time.

```python
# Lazy load (default)
classifier = HookClassifier(lazy_load=True)

# Eager load
classifier = HookClassifier(lazy_load=False)
```

### Batch Processing
For multiple hooks, use `batch_classify()` for better performance:

```python
# Good - processes in batches
results = classifier.batch_classify(hooks, batch_size=32)

# Less efficient - one at a time
results = [classifier.classify(h) for h in hooks]
```

## Model Storage

Models are cached in `~/.cache/geminivideo/models/` by default.

Fine-tuned models are saved to `~/.cache/geminivideo/models/hook_classifier_finetuned/`

## Fallback Behavior

If transformers/torch are not installed, the Meta Learning Agent falls back to keyword-based hook analysis automatically.

## Examples & Demo

Run the demo script to see all features:

```bash
cd /home/user/geminivideo/services/titan-core/engines
python hook_classifier_demo.py
```

## Best Practices

1. **Collect Training Data**: Label 50-100 examples per hook type for best results
2. **Fine-Tune Regularly**: Retrain on your best-performing hooks monthly
3. **Monitor Confidence**: Low confidence (<0.6) may indicate unclear hooks
4. **Use Hook Strength**: Aim for hooks with strength >0.7
5. **Test Multiple Types**: Don't rely on just one hook pattern

## Troubleshooting

### ImportError: No module named 'transformers'
```bash
pip install transformers torch
```

### CUDA out of memory
Reduce batch size or use CPU:
```python
classifier = HookClassifier(device='cpu')
```

### Low classification confidence
- Ensure hooks are clear and well-written
- Fine-tune on your specific domain data
- Check that hooks match the 10 defined types

## Integration Examples

### With Video Script Generator
```python
from engines.hook_classifier import get_hook_classifier

classifier = get_hook_classifier()

# Generate script
script = video_generator.generate_script(...)

# Analyze hook
analysis = classifier.classify_video_script(script)

# Optimize if hook strength is low
if analysis['hook']['strength'] < 0.7:
    print("⚠️ Hook strength low - consider revising")
```

### With A/B Testing Framework
```python
# Test two hook variants
hook_a = "Stop wasting money on ads!"
hook_b = "Are you wasting money on ads?"

result_a = classifier.classify(hook_a)
result_b = classifier.classify(hook_b)

print(f"Hook A: {result_a.primary_hook} (strength: {result_a.hook_strength})")
print(f"Hook B: {result_b.primary_hook} (strength: {result_b.hook_strength})")
```

## Future Enhancements

- [ ] Multi-language support
- [ ] Video thumbnail analysis integration
- [ ] Real-time hook scoring API endpoint
- [ ] Automated A/B test variant generation
- [ ] Industry-specific fine-tuned models

## Support

For issues or questions:
1. Check demo script: `python hook_classifier_demo.py`
2. Review logs for detailed error messages
3. Ensure transformers and torch are installed
4. Verify Python 3.8+ is being used

---

**Version**: 1.0.0
**Last Updated**: 2025-12-01
**Maintained By**: Agent 2 - Hook Pattern ML Classifier Engineer
