# Pretrained Hook Detector

**Agent 17 of 30** - Production-grade hook detection using pretrained BERT/RoBERTa models

## Overview

The `PretrainedHookDetector` uses state-of-the-art transformer models from HuggingFace to detect and analyze marketing hooks in ad copy. This is a **zero-mock implementation** that leverages real pretrained models for production use.

## Features

- **Real Pretrained Models**: Uses HuggingFace transformers (no mock data)
- **Zero-Shot Classification**: Classifies 12 different hook types without training
- **Sentiment Analysis**: RoBERTa-based sentiment detection
- **Batch Processing**: Efficient processing of multiple hooks
- **GPU Support**: Automatic CUDA detection and utilization
- **Comprehensive Analysis**: Hook strength, attention scores, curiosity metrics
- **Pattern Extraction**: Learn from successful hooks
- **Hook Variants**: Generate alternative versions

## Models Used

| Model | Purpose | Source |
|-------|---------|--------|
| `facebook/bart-large-mnli` | Zero-shot hook classification | HuggingFace |
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | Sentiment analysis | HuggingFace |

## Hook Types Detected

1. **Curiosity Gap** - Creates mystery and intrigue
2. **Transformation** - Promises dramatic change
3. **Urgency/Scarcity** - Limited time/availability
4. **Social Proof** - Testimonials and validation
5. **Pattern Interrupt** - Unexpected statements
6. **Question** - Engaging questions
7. **Negative Hook** - Addresses pain points
8. **Story Hook** - Narrative techniques
9. **Statistic Hook** - Numbers and data
10. **Controversy Hook** - Contrarian viewpoints
11. **Benefit Stack** - Multiple value propositions
12. **Pain Agitate** - Agitates problems before solutions

## Installation

```bash
# Install dependencies
pip install torch transformers numpy

# For GPU support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Quick Start

```python
from pretrained_hook_detector import PretrainedHookDetector

# Initialize (auto-detects GPU/CPU)
detector = PretrainedHookDetector()

# Detect hook in single text
result = detector.detect_hook("What if you could 10X your revenue in 30 days?")

print(f"Primary Type: {result.primary_hook_type.value}")
print(f"Hook Strength: {result.hook_strength:.3f}")
print(f"Sentiment: {result.sentiment}")
print(f"Suggestions: {result.improvement_suggestions}")
```

## Usage Examples

### 1. Basic Hook Detection

```python
detector = PretrainedHookDetector()

hook = "Limited time: Get 50% off before midnight!"
result = detector.detect_hook(hook)

print(f"Type: {result.primary_hook_type.value}")
# Output: Type: urgency_scarcity

print(f"Strength: {result.hook_strength:.3f}")
# Output: Strength: 0.782

print(f"Attention Score: {result.attention_score:.3f}")
# Output: Attention Score: 0.850
```

### 2. Batch Processing

```python
hooks = [
    "What if you could double your sales?",
    "Join 10,000+ successful entrepreneurs",
    "The secret to viral content revealed"
]

results = detector.detect_hooks_batch(hooks)

for result in results:
    print(f"{result.text} -> {result.primary_hook_type.value}")
```

### 3. Hook Analysis

```python
successful_hooks = [
    "What if you could 3X your sales?",
    "Limited offer: Save $500 today",
    "10,000 customers trust our system"
]

analysis = detector.analyze_hooks(successful_hooks)

print(f"Average Strength: {analysis.avg_hook_strength:.3f}")
print(f"Primary Type: {analysis.primary_hook.value}")
print(f"Distribution: {analysis.hook_distribution}")
```

### 4. Hook Comparison

```python
hooks = [
    "Save money today",
    "SHOCKING: You're being overcharged!",
    "What if you could save 50%?"
]

comparison = detector.compare_hooks(hooks)

print(f"Best Overall: {comparison['best_overall']}")
print(f"Best Attention: {comparison['best_attention']}")
print(f"Best Curiosity: {comparison['best_curiosity']}")
```

### 5. Hook Ranking

```python
hooks = [
    "Save 20% today",
    "WARNING: You're losing money",
    "Discover unlimited traffic secrets"
]

# Rank by different metrics
by_strength = detector.rank_hooks(hooks, metric="strength")
by_attention = detector.rank_hooks(hooks, metric="attention")
by_curiosity = detector.rank_hooks(hooks, metric="curiosity")

for hook, score in by_strength:
    print(f"[{score:.3f}] {hook}")
```

### 6. Improvement Suggestions

```python
weak_hook = "Buy our product"
result = detector.detect_hook(weak_hook)

print(f"Strength: {result.hook_strength:.3f}")
print("Suggestions:")
for suggestion in result.improvement_suggestions:
    print(f"  - {suggestion}")

# Output:
# Strength: 0.235
# Suggestions:
#   - Hook is too short - aim for 5-15 words
#   - Consider adding power words like 'discover', 'proven'
#   - Add specific numbers or statistics
#   - Create more curiosity gap
```

### 7. Pattern Extraction

```python
successful_hooks = [
    "What if you could 10X your results?",
    "What if doubling income was easy?",
    "Discover the secret to viral content",
    "Limited time: Save 50% today"
]

patterns = detector.extract_hook_patterns(successful_hooks)

print(f"Common Types: {patterns['common_hook_types']}")
print(f"Avg Length: {patterns['avg_length']} words")
print(f"Common Words: {patterns['common_words']}")
print(f"Patterns: {patterns['common_patterns']}")
```

### 8. Hook Variants

```python
original = "double your sales with email marketing"
variants = detector.generate_hook_variants(original, num_variants=5)

print("Original:", original)
print("\nVariants:")
for variant in variants:
    print(f"  - {variant}")

# Output:
#   - What if double your sales with email marketing?
#   - Don't miss: double your sales with email marketing
#   - Discover how double your sales with email marketing
#   - 10,000+ people use: double your sales with email marketing
#   - 3X your results: double your sales with email marketing
```

## API Reference

### Classes

#### `HookType(Enum)`
Enumeration of 12 hook types.

#### `HookResult(dataclass)`
Result of hook detection:
- `text`: Original text
- `primary_hook_type`: Main hook type detected
- `hook_types`: All types with confidence scores
- `hook_strength`: Overall strength (0-1)
- `sentiment`: positive/negative/neutral
- `sentiment_score`: Sentiment confidence
- `attention_score`: Attention-grabbing score
- `improvement_suggestions`: List of suggestions

#### `HookAnalysis(dataclass)`
Analysis across multiple hooks:
- `hooks_detected`: Number of hooks
- `primary_hook`: Most common type
- `hook_distribution`: Type distribution
- `avg_hook_strength`: Average strength
- `strongest_hook_text`: Best hook
- `weakest_hook_text`: Weakest hook

### Methods

#### `detect_hook(text, threshold=0.3) -> HookResult`
Detect hook type and strength in single text.

#### `detect_hooks_batch(texts, threshold=0.3) -> List[HookResult]`
Batch detection for multiple texts.

#### `classify_hook_type(text) -> List[Tuple[HookType, float]]`
Classify into hook types with confidence scores.

#### `score_hook_strength(text) -> float`
Calculate overall hook strength (0-1).

#### `analyze_sentiment(text) -> Tuple[str, float]`
Analyze sentiment (label, confidence).

#### `suggest_improvement(text, target_hook_type=None) -> List[str]`
Generate improvement suggestions.

#### `generate_hook_variants(text, num_variants=3) -> List[str]`
Create hook variations.

#### `analyze_hooks(texts) -> HookAnalysis`
Comprehensive analysis across texts.

#### `compare_hooks(hooks) -> Dict[str, Any]`
Compare multiple hooks.

#### `rank_hooks(hooks, metric="strength") -> List[Tuple[str, float]]`
Rank hooks by metric (strength/attention/curiosity/sentiment).

#### `extract_hook_patterns(successful_hooks) -> Dict[str, Any]`
Extract patterns from successful hooks.

#### `match_pattern(text, patterns) -> List[Tuple[str, float]]`
Match text against known patterns.

#### `get_model_info() -> Dict[str, Any]`
Get loaded model information.

#### `warmup() -> None`
Warmup models with dummy input.

## Performance

### Speed
- Single detection: ~200-500ms (GPU) / ~800-1200ms (CPU)
- Batch processing: ~100-200ms per item (GPU) / ~500-800ms (CPU)
- First run: Slower due to model download/loading

### Memory
- GPU: ~2-3GB VRAM
- CPU: ~1-2GB RAM

### Optimization Tips

```python
# 1. Use GPU if available
detector = PretrainedHookDetector(device="cuda")

# 2. Batch process for efficiency
results = detector.detect_hooks_batch(many_hooks)

# 3. Warmup before production
detector.warmup()

# 4. Cache models locally
detector = PretrainedHookDetector(cache_dir="./model_cache")
```

## Testing

Run the comprehensive test suite:

```bash
python test_pretrained_hook_detector.py
```

Tests cover:
1. Basic detection
2. Batch processing
3. Hook analysis
4. Hook comparison
5. Hook ranking
6. Improvement suggestions
7. Pattern extraction
8. Hook variants
9. Model information
10. Warmup

## Error Handling

All methods include comprehensive error handling:

```python
try:
    result = detector.detect_hook(text)
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Detection error: {e}")
```

## Integration Example

```python
from pretrained_hook_detector import PretrainedHookDetector

class AdCopyAnalyzer:
    def __init__(self):
        self.detector = PretrainedHookDetector()
        self.detector.warmup()

    def analyze_campaign(self, ad_copies):
        """Analyze multiple ad copies."""
        results = self.detector.detect_hooks_batch(ad_copies)
        analysis = self.detector.analyze_hooks(ad_copies)

        return {
            'individual_results': results,
            'overall_analysis': analysis,
            'top_performers': self.detector.rank_hooks(
                ad_copies,
                metric="strength"
            )[:3]
        }

    def optimize_hook(self, hook):
        """Optimize a single hook."""
        result = self.detector.detect_hook(hook)

        if result.hook_strength < 0.5:
            variants = self.detector.generate_hook_variants(hook)
            return {
                'original': hook,
                'strength': result.hook_strength,
                'suggestions': result.improvement_suggestions,
                'variants': variants
            }

        return {'original': hook, 'strength': result.hook_strength}
```

## Architecture

```
PretrainedHookDetector
├── Model Loading
│   ├── BART-Large-MNLI (Zero-shot classification)
│   └── RoBERTa-Base-Sentiment (Sentiment analysis)
├── Detection Pipeline
│   ├── Zero-shot classification → Hook types
│   ├── Sentiment analysis → Emotional tone
│   ├── Attention scoring → Power words, patterns
│   └── Curiosity scoring → Gap detection
├── Analysis Pipeline
│   ├── Batch processing
│   ├── Pattern extraction
│   └── Comparison/ranking
└── Suggestion Engine
    ├── Rule-based improvements
    └── Variant generation
```

## Limitations

1. **Model Download**: First run downloads ~1.5GB of models
2. **Speed**: CPU inference slower than GPU (3-5x)
3. **Context**: Works best with short hooks (<50 words)
4. **Language**: Optimized for English text
5. **Training**: Uses zero-shot (no fine-tuning on hook data)

## Future Enhancements

- [ ] Fine-tune models on hook-specific datasets
- [ ] Add multi-language support
- [ ] Implement A/B testing recommendations
- [ ] Add industry-specific hook patterns
- [ ] Integrate with ad performance data
- [ ] Add real-time hook generation

## Credits

- **Models**: HuggingFace Transformers
- **Framework**: PyTorch
- **Agent**: #17 of 30 in ULTIMATE production plan

## License

Part of the Titan-Core video intelligence system.
