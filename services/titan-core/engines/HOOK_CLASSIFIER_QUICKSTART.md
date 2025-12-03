# Hook Classifier - Quick Start Guide

## Installation

```bash
cd /home/user/geminivideo/services/titan-core
pip install -r requirements.txt
```

This installs `transformers>=4.35.0` and `torch` which are required for the ML classifier.

## 5-Minute Quick Start

### 1. Basic Classification

```python
from engines.hook_classifier import get_hook_classifier

# Get classifier instance
classifier = get_hook_classifier()

# Classify a hook
result = classifier.classify("Stop wasting money on ads that don't work!")

print(f"Hook Type: {result.primary_hook}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Strength: {result.hook_strength:.2f}")
```

**Output:**
```
Hook Type: negative_hook
Confidence: 87.3%
Strength: 0.78
```

### 2. Analyze Your Top Performers

```python
# Your best-performing ad hooks
top_hooks = [
    "This secret method made my client $50k",
    "From broke to $10k/month in 30 days",
    "Stop wasting money on Facebook ads!",
]

analysis = classifier.analyze_top_performer_hooks(top_hooks)

print(f"Dominant Pattern: {analysis['dominant_pattern']}")
print(f"Recommendations:")
for rec in analysis['recommendations']:
    print(f"  {rec}")
```

### 3. Use with Meta Learning Agent (Automatic)

```python
from meta_learning_agent import meta_learning_agent

# Run learning cycle - automatically uses ML classifier
result = meta_learning_agent.run_learning_cycle(days_back=30)

# Access ML insights
patterns = result['patterns']['hook_patterns']
ml_analysis = patterns['_ml_analysis']

print(f"Dominant Hook: {ml_analysis['dominant_pattern']}")
print(f"Avg Confidence: {ml_analysis['avg_confidence']:.2%}")
```

## Run Demo

```bash
cd /home/user/geminivideo/services/titan-core/engines
python hook_classifier_demo.py
```

This shows:
- Basic classification
- Video script analysis
- Batch processing
- Hook examples for each type

## Run Tests

```bash
cd /home/user/geminivideo/services/titan-core/engines
python test_hook_classifier.py
```

## 10 Hook Types

1. **curiosity_gap** - Creates information gaps
2. **transformation** - Before/after, results
3. **urgency_scarcity** - Limited time, FOMO
4. **social_proof** - Testimonials, results
5. **pattern_interrupt** - Unexpected, shocking
6. **question** - Engages with questions
7. **negative_hook** - Warns about mistakes
8. **story_hook** - Personal narratives
9. **statistic_hook** - Data-driven, numbers
10. **controversy_hook** - Challenges conventional wisdom

## Performance Tips

### Use GPU for Speed
```python
# Automatically uses GPU if available
classifier = get_hook_classifier()

# Or force CPU
from engines.hook_classifier import HookClassifier
classifier = HookClassifier(device='cpu')
```

### Batch Processing
```python
# Efficient for multiple hooks
hooks = ["Hook 1", "Hook 2", "Hook 3", ...]
results = classifier.batch_classify(hooks, batch_size=32)
```

## Integration Points

### 1. Video Script Generator
Analyze generated hooks before production:
```python
script = generate_script(...)
analysis = classifier.classify_video_script(script)

if analysis['hook']['strength'] < 0.7:
    print("⚠️ Weak hook - regenerate")
```

### 2. A/B Testing
Compare hook variants:
```python
hooks = ["Variant A", "Variant B", "Variant C"]
results = classifier.batch_classify(hooks)

best = max(results, key=lambda r: r.hook_strength)
print(f"Best hook: {best.primary_hook} (strength: {best.hook_strength})")
```

### 3. Campaign Analysis
Analyze all campaigns automatically via Meta Learning Agent (already integrated).

## Fine-Tuning (Optional)

Train on your own data:
```python
train_data = [
    {'text': 'Your hook text', 'label': 'transformation'},
    {'text': 'Another hook', 'label': 'urgency_scarcity'},
    # ... 50-100 examples per type recommended
]

result = classifier.train(
    train_data=train_data,
    num_epochs=3,
    batch_size=16
)
```

## Troubleshooting

### Import Error
```bash
pip install transformers torch
```

### CUDA Out of Memory
```python
classifier = HookClassifier(device='cpu', lazy_load=True)
```

### Low Confidence
- Ensure hooks are clear and well-written
- Fine-tune on your domain-specific data
- Check hooks match the 10 defined types

## Next Steps

1. ✅ Run demo: `python hook_classifier_demo.py`
2. ✅ Test integration: `python test_hook_classifier.py`
3. ✅ Analyze your top performers
4. ✅ Fine-tune on your data (optional)
5. ✅ Integrate with video generation pipeline

## Full Documentation

See [HOOK_CLASSIFIER_README.md](./HOOK_CLASSIFIER_README.md) for complete API reference.

---

**Ready to use!** The classifier is production-ready and automatically integrated with Meta Learning Agent.
