# Gemini 2.0 Flash Thinking Upgrade Guide

## Overview
This guide documents the comprehensive upgrade to **Gemini 2.0 Flash Thinking** (December 2024 release) across the AI Council and video intelligence systems.

## What's New in Gemini 2.0

### Gemini 2.0 Flash Thinking (`gemini-2.0-flash-thinking-exp-1219`)
- **Extended Reasoning**: Chain-of-thought capabilities for deep analysis
- **Higher Token Limit**: 8,192 output tokens (vs 2,048 in previous versions)
- **Better Multimodal**: Improved video and image understanding
- **Native Tool Use**: Built-in function calling
- **Streaming Support**: Real-time response generation

### Gemini 2.0 Flash (`gemini-2.0-flash-exp`)
- **2x Faster**: Than Gemini 1.5 Pro
- **Better Quality**: Improved reasoning and accuracy
- **Multimodal Excellence**: Video, image, audio analysis
- **Cost Efficient**: Lower pricing than Pro models

### Gemini 2.0 Pro (`gemini-2.0-pro-exp`)
- **Most Powerful**: For critical scoring and final verdicts
- **Best Quality**: Highest accuracy for complex tasks
- **Advanced Reasoning**: Superior analytical capabilities

## Upgraded Components

### 1. AI Council (`council_of_titans.py`)

#### Changes
- **Model**: Upgraded from `gemini-3-pro-preview` → `gemini-2.0-flash-thinking-exp-1219`
- **Generation Config**: Optimized for thinking mode
  - Temperature: 1.0 (higher for creative reasoning)
  - Max Tokens: 8,192 (up from 2,048)
- **Enhanced Prompts**: Chain-of-thought reasoning for better analysis

#### Usage
```python
from ai_council.council_of_titans import council

# Evaluate script with Gemini 2.0 Thinking
result = await council.evaluate_script(
    script="Your ad script here...",
    visual_features={"has_human_face": True, "hook_type": "pattern_interrupt"}
)

print(f"Final Score: {result['final_score']}")
print(f"Gemini 2.0 Score: {result['breakdown']['gemini_2_0_thinking']['score']}")
```

#### New Weights (Updated November 2025)
- Claude 4 Opus (Psychology): **40%**
- Gemini 2.0 Flash Thinking: **35%**
- GPT-4o (Logic): **15%**
- DeepCTR (Data): **10%**

### 2. Vertex AI Service (`vertex_ai.py`)

#### New Features

##### Model Selection Based on Task Complexity
```python
from engines.vertex_ai import VertexAIService, GEMINI_2_0_FLASH_THINKING

service = VertexAIService(project_id="your-project")

# Simple task - Fast model
analysis = service.analyze_video(
    video_gcs_uri="gs://bucket/video.mp4",
    task_complexity="simple"  # Uses gemini-2.0-flash-exp
)

# Complex task - Thinking model
analysis = service.analyze_video(
    video_gcs_uri="gs://bucket/video.mp4",
    task_complexity="complex"  # Uses gemini-2.0-flash-thinking-exp-1219
)

# Critical task - Pro model
analysis = service.analyze_video(
    video_gcs_uri="gs://bucket/video.mp4",
    task_complexity="critical"  # Uses gemini-2.0-pro-exp
)
```

##### Streaming Support
```python
# Enable streaming for real-time feedback
analysis = service.analyze_video(
    video_gcs_uri="gs://bucket/video.mp4",
    task_complexity="complex",
    use_streaming=True  # Stream responses as they're generated
)

print(f"Analysis completed in {analysis.thinking_time_ms}ms")
print(f"Model used: {analysis.model_used}")
```

##### Structured JSON Schema Output
```python
# Define expected output schema
schema = {
    "hook_quality": "number (0-100)",
    "engagement_score": "number (0-100)",
    "key_scenes": ["array of scene descriptions"],
    "recommendations": ["array of improvements"]
}

# Get structured output
result = service.analyze_video_with_schema(
    video_gcs_uri="gs://bucket/video.mp4",
    analysis_schema=schema,
    task_complexity="complex"
)
```

#### Model Selection Logic
```python
def select_model_for_task(task_complexity: str):
    """
    - "simple": gemini-2.0-flash-exp (fast, cheap)
    - "complex": gemini-2.0-flash-thinking-exp-1219 (thorough reasoning)
    - "critical": gemini-2.0-pro-exp (best quality)
    """
```

### 3. Deep Video Intelligence (`deep_video_intelligence.py`)

#### Changes
- **Model**: Confirmed `gemini-2.0-flash-thinking-exp-1219`
- **Fallback**: `gemini-1.5-pro-002` for reliability
- **Generation Config**: Thinking mode optimized
- **Enhanced JSON Schema**: Structured output for all analysis layers

#### Usage
```python
from engines.deep_video_intelligence import DeepVideoIntelligence

dvi = DeepVideoIntelligence()

# Perform multi-layer analysis
analysis = dvi.analyze_video("path/to/video.mp4")

print(f"Technical Metrics: {analysis['technical_metrics']}")
print(f"Semantic Analysis: {analysis['semantic_analysis']}")
print(f"Psychological Profile: {analysis['psychological_profile']}")
print(f"Deep Ad Score: {analysis['deep_ad_score']}")
```

#### Enhanced Features
1. **Semantic Analysis**: Chain-of-thought frame analysis
2. **Psychology Analysis**: Deep reasoning for trigger identification
3. **Structured Output**: Validated JSON schemas
4. **Better Error Handling**: Graceful fallbacks with detailed error messages

## Configuration

### Environment Variables
```bash
# Required
export GEMINI_API_KEY="your-gemini-api-key"
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"

# Optional - Override default models
export GEMINI_MODEL_ID="gemini-2.0-flash-thinking-exp-1219"
export GEMINI_MODEL="gemini-2.0-flash-thinking-exp-1219"
```

### Generation Configs

#### Fast Config (Simple Tasks)
```python
config_fast = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}
```

#### Thinking Config (Complex Tasks)
```python
config_thinking = {
    "temperature": 1.0,  # Higher for creative reasoning
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,  # Thinking models need more tokens
}
```

#### Precise Config (Critical Tasks)
```python
config_precise = {
    "temperature": 0.3,  # Lower for factual accuracy
    "top_p": 0.8,
    "top_k": 20,
    "max_output_tokens": 4096,
}
```

## Model Comparison

| Model | Speed | Quality | Cost | Use Case |
|-------|-------|---------|------|----------|
| **Gemini 2.0 Flash** | ⚡⚡⚡ | ⭐⭐⭐ | 💰 | Quick analysis, pre-filtering |
| **Gemini 2.0 Flash Thinking** | ⚡⚡ | ⭐⭐⭐⭐ | 💰💰 | Complex scoring, deep analysis |
| **Gemini 2.0 Pro** | ⚡ | ⭐⭐⭐⭐⭐ | 💰💰💰 | Final verdicts, critical decisions |
| **Gemini 1.5 Pro** | ⚡⚡ | ⭐⭐⭐ | 💰💰 | Fallback/stable option |

## Error Handling

### Model Fallback Chain
1. Try primary model (e.g., `gemini-2.0-flash-thinking-exp-1219`)
2. If fails, fallback to `gemini-1.5-pro-002`
3. If both fail, return structured error with default values

### Example Error Handling
```python
try:
    analysis = service.analyze_video(video_uri, task_complexity="complex")
    if analysis.model_used == "error":
        logger.warning(f"Analysis failed: {analysis.summary}")
        # Handle gracefully with fallback data
except Exception as e:
    logger.error(f"Critical error: {e}")
    # Implement retry logic or alert
```

## Performance Optimizations

### 1. Model Caching
```python
# Models are cached per instance to avoid reloading
# Cache key: model_name
self._model_cache[model_name] = GenerativeModel(model_name)
```

### 2. Streaming for Large Videos
```python
# Use streaming to get progressive results
analysis = service.analyze_video(
    video_uri,
    use_streaming=True  # Reduces perceived latency
)
```

### 3. Task Complexity Optimization
```python
# Use appropriate model for the task
# Don't use Thinking model for simple tasks - waste of time/money
- Simple checks → Gemini 2.0 Flash (fast, cheap)
- Deep analysis → Gemini 2.0 Flash Thinking (thorough)
- Final scoring → Gemini 2.0 Pro (best quality)
```

## Migration Guide

### From Gemini 1.5 Pro
```python
# Old
service = VertexAIService(gemini_model="gemini-1.5-pro")

# New (automatic upgrade)
service = VertexAIService()  # Defaults to gemini-2.0-flash-exp
```

### From Generic Gemini API
```python
# Old
import google.generativeai as genai
model = genai.GenerativeModel("gemini-pro")

# New
model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-1219")
model.generation_config = {
    "temperature": 1.0,
    "max_output_tokens": 8192
}
```

## Testing

### Quick Test
```python
from engines.vertex_ai import VertexAIService

# Initialize service
service = VertexAIService(project_id="your-project")

# Test model selection
for complexity in ["simple", "complex", "critical"]:
    model_name, config = service.select_model_for_task(complexity)
    print(f"{complexity}: {model_name} with {config['max_output_tokens']} tokens")
```

### Validation Script
See `test_gemini_2_0_upgrade.py` for comprehensive tests.

## Troubleshooting

### Issue: Model not found
**Solution**: Model may not be available in your region. Use fallback:
```python
export GEMINI_MODEL_ID="gemini-1.5-pro-002"
```

### Issue: Token limit exceeded
**Solution**: Increase max_output_tokens or split analysis:
```python
config_thinking["max_output_tokens"] = 12000  # Max for thinking models
```

### Issue: Slow responses
**Solution**: Use faster model for non-critical tasks:
```python
analysis = service.analyze_video(video_uri, task_complexity="simple")
```

## Best Practices

1. **Use Thinking Mode for Analysis**: Complex scoring benefits from chain-of-thought
2. **Stream Large Requests**: Enable streaming for videos > 30 seconds
3. **Cache System Prompts**: Use ephemeral caching (Claude) or model caching
4. **Validate JSON Output**: Always check for required fields
5. **Monitor Token Usage**: Track costs by logging token consumption
6. **Implement Fallbacks**: Always have a stable fallback model

## Cost Optimization

### Strategy
1. **Pre-filter with Flash**: Use Gemini 2.0 Flash for quick checks
2. **Deep analysis with Thinking**: Only use thinking mode when needed
3. **Final verdict with Pro**: Reserve Pro for critical decisions only

### Example Pipeline
```python
# Stage 1: Quick check (Flash)
quick_score = service.analyze_video(uri, task_complexity="simple")

if quick_score.engagement_score > 70:
    # Stage 2: Deep analysis (Thinking)
    deep_analysis = service.analyze_video(uri, task_complexity="complex")

    if deep_analysis.engagement_score > 85:
        # Stage 3: Final verdict (Pro)
        final_verdict = service.analyze_video(uri, task_complexity="critical")
```

## References

- [Gemini 2.0 Documentation](https://ai.google.dev/gemini-api/docs)
- [Vertex AI Python SDK](https://cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk)
- [Google Generative AI SDK](https://github.com/google/generative-ai-python)

## Changelog

### Version 2.0 (December 2024)
- ✅ Upgraded to Gemini 2.0 Flash Thinking
- ✅ Added model selection based on task complexity
- ✅ Implemented streaming support
- ✅ Enhanced structured JSON output
- ✅ Improved error handling and fallbacks
- ✅ Added model caching
- ✅ Updated generation configs for thinking mode

### Version 1.0 (Previous)
- Used Gemini 1.5 Pro / Gemini 3 Pro Preview
- Basic video analysis
- No streaming
- Limited error handling
