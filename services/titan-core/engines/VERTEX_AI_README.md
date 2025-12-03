# Vertex AI Integration Service

**Agent 23 of 30 - ULTIMATE Production Plan**

Real Vertex AI integration for Gemini 2.0, Imagen 3.0, and advanced video analysis capabilities.

## Overview

This service provides production-ready integration with Google Cloud's Vertex AI platform, enabling:

- **Video Analysis** - Multimodal understanding of video ads with scene detection, object recognition, and sentiment analysis
- **Image Generation** - Create marketing images with Imagen 3.0
- **Text Embeddings** - Semantic search and similarity matching
- **Ad Copy Generation** - AI-powered marketing copy variants
- **Competitor Analysis** - Extract winning patterns from competitor ads
- **Chat Capabilities** - Interactive marketing consultation
- **Multimodal Analysis** - Combine video, images, and text for comprehensive insights

## Features

### ✅ Real Implementation
- Actual Vertex AI SDK calls (NO mock data)
- Production-ready error handling
- Type hints throughout
- Comprehensive logging
- Graceful degradation when dependencies unavailable

### ✅ Complete API Coverage
- Gemini 2.0 Flash for video/image analysis
- Imagen 3.0 for image generation/editing
- Text Embedding 004 for embeddings
- Chat sessions with context

### ✅ Marketing-Optimized
- Ad copy generation with style variants
- Hook improvement for viral potential
- Competitor intelligence extraction
- Storyboard generation for video ads
- Engagement scoring (0-100)

## Installation

### Requirements

```bash
pip install google-cloud-aiplatform pillow numpy
```

Already included in `/home/user/geminivideo/services/titan-core/requirements.txt`.

### Authentication

Set up Google Cloud credentials:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Or use gcloud CLI:

```bash
gcloud auth application-default login
gcloud config set project your-project-id
```

## Quick Start

```python
from engines.vertex_ai import VertexAIService

# Initialize service
service = VertexAIService(
    project_id="your-project-id",
    location="us-central1"
)

# Analyze a video
analysis = service.analyze_video("gs://bucket/video.mp4")
print(f"Summary: {analysis.summary}")
print(f"Hook Quality: {analysis.hook_quality}/100")
print(f"Recommendations: {analysis.recommendations}")

# Generate ad copy
variants = service.generate_ad_copy(
    product_info="Smart fitness watch with AI coaching",
    style="urgent",
    num_variants=3
)

# Improve a hook
better_hooks = service.improve_hook(
    current_hook="Check out our new watch!",
    target_emotion="FOMO"
)

# Generate images
images = service.generate_image(
    prompt="Fitness watch on runner's wrist, sunset, professional photography",
    aspect_ratio="9:16",
    num_images=2
)
```

## API Reference

### VideoAnalysis Dataclass

```python
@dataclass
class VideoAnalysis:
    summary: str                              # 2-3 sentence overview
    scenes: List[Dict[str, Any]]              # Key scenes with timestamps
    objects_detected: List[str]               # Visible objects/products
    text_detected: List[str]                  # OCR text from video
    audio_transcript: str                     # Speech transcription
    sentiment: str                            # positive/negative/neutral/mixed
    recommendations: List[str]                # Improvement suggestions
    hook_quality: Optional[float]             # 0-100 score for first 3 seconds
    engagement_score: Optional[float]         # 0-100 predicted engagement
    marketing_insights: Dict[str, Any]        # Target audience, USPs, etc.
    raw_response: Optional[str]               # Full LLM response
```

### VertexAIService Class

#### Initialization

```python
service = VertexAIService(
    project_id: str,                    # GCP project ID
    location: str = "us-central1",      # GCP region
    gemini_model: str = "gemini-2.0-flash-exp",
    imagen_model: str = "imagen-3.0-generate-001"
)
```

#### Video Analysis

```python
def analyze_video(
    video_gcs_uri: str,        # gs://bucket/video.mp4 or local path
    prompt: Optional[str]      # Custom analysis prompt
) -> VideoAnalysis
```

**Returns**: Comprehensive video analysis with marketing insights.

#### Image Analysis

```python
def analyze_image(
    image_gcs_uri: str,        # gs://bucket/image.jpg or local path
    prompt: str                # Analysis question
) -> str
```

**Returns**: Image analysis text response.

#### Ad Copy Generation

```python
def generate_ad_copy(
    product_info: str,         # Product description
    style: str,                # "casual", "professional", "urgent", etc.
    num_variants: int = 3      # Number of variants
) -> List[str]
```

**Returns**: List of optimized ad copy variants (50-100 words each).

#### Hook Improvement

```python
def improve_hook(
    current_hook: str,         # Current video/ad hook
    target_emotion: str        # "curiosity", "urgency", "FOMO", etc.
) -> List[str]
```

**Returns**: 5 improved hook variations.

#### Competitor Analysis

```python
def analyze_competitor_ad(
    video_uri: str             # Competitor video URI/path
) -> Dict[str, Any]
```

**Returns**: Deep competitive intelligence insights.

#### Image Generation

```python
def generate_image(
    prompt: str,               # Image description
    aspect_ratio: str = "1:1", # "1:1", "16:9", "9:16", "4:3", "3:4"
    num_images: int = 1        # Number of images
) -> List[bytes]
```

**Returns**: List of generated image bytes.

#### Image Editing

```python
def edit_image(
    image_bytes: bytes,        # Original image
    edit_prompt: str           # Editing instruction
) -> bytes
```

**Returns**: Edited image bytes.

#### Text Embeddings

```python
def embed_text(text: str) -> np.ndarray
def embed_texts(texts: List[str]) -> np.ndarray
```

**Returns**: Embedding vector(s) for semantic search.

#### Image Embeddings

```python
def embed_image(image_bytes: bytes) -> np.ndarray
```

**Returns**: Image embedding vector (via description).

#### Multimodal Analysis

```python
def multimodal_analysis(
    video_uri: str,            # Video URI/path
    images: List[str],         # List of image URIs/paths
    text_prompt: str           # Analysis question
) -> str
```

**Returns**: Combined analysis of all modalities.

#### Storyboard Generation

```python
def generate_storyboard(
    product_description: str,  # Product info
    style: str                 # "modern", "energetic", "luxury", etc.
) -> List[Dict[str, Any]]
```

**Returns**: 6-scene video ad storyboard with image generation prompts.

#### Chat

```python
def start_chat(
    system_instruction: Optional[str]
) -> ChatSession

def chat(
    chat_session: ChatSession,
    message: str
) -> str
```

**Returns**: Interactive chat for marketing consultation.

## Usage Examples

### Example 1: Full Video Analysis Pipeline

```python
from engines.vertex_ai import VertexAIService

service = VertexAIService(project_id="my-project")

# Upload video to GCS first (or use local path for testing)
video_uri = "gs://my-bucket/new-ad.mp4"

# Analyze video
analysis = service.analyze_video(video_uri)

# Check performance metrics
if analysis.hook_quality < 70:
    print("⚠️ Hook needs improvement!")
    improved_hooks = service.improve_hook(
        current_hook=analysis.scenes[0]["description"],
        target_emotion="curiosity"
    )
    print("Better hooks:", improved_hooks)

if analysis.engagement_score < 60:
    print("📊 Recommendations:")
    for rec in analysis.recommendations:
        print(f"  - {rec}")

# Extract learnings
print(f"Target Audience: {analysis.marketing_insights.get('target_audience')}")
print(f"Key USPs: {analysis.marketing_insights.get('key_selling_points')}")
```

### Example 2: Competitor Benchmarking

```python
# Analyze multiple competitors
competitors = [
    "gs://bucket/competitor1.mp4",
    "gs://bucket/competitor2.mp4",
    "gs://bucket/competitor3.mp4"
]

insights = []
for video in competitors:
    result = service.analyze_competitor_ad(video)
    insights.append(result)

# Find best performer
best = max(insights, key=lambda x: x["engagement_score"])
print(f"Best hook: {best['hook_quality']}/100")
print(f"Winning patterns: {best['insights']}")
```

### Example 3: Generate Ad Variants

```python
product = """
Revolutionary AI-powered vacuum cleaner:
- Self-emptying base
- 60-day capacity
- Smart mapping
- Pet hair specialist
- $499 (save $100 today)
"""

# Generate multiple styles
styles = ["urgent", "professional", "casual", "humorous"]

all_variants = {}
for style in styles:
    variants = service.generate_ad_copy(product, style, num_variants=2)
    all_variants[style] = variants

# A/B test them
for style, variants in all_variants.items():
    print(f"\n{style.upper()} STYLE:")
    for i, copy in enumerate(variants, 1):
        print(f"  {i}. {copy}")
```

### Example 4: Create Full Video Campaign

```python
# 1. Generate storyboard
storyboard = service.generate_storyboard(
    product_description="Smart home security camera with AI",
    style="modern"
)

# 2. Generate visuals for each scene
scene_images = []
for scene in storyboard:
    images = service.generate_image(
        prompt=scene["image_prompt"],
        aspect_ratio="9:16",
        num_images=1
    )
    scene_images.append(images[0])

    # Save for video production
    with open(f"scene_{scene['timestamp']}.jpg", "wb") as f:
        f.write(images[0])

# 3. Generate voiceover script
chat = service.start_chat(
    system_instruction="You are a professional voiceover script writer."
)

for scene in storyboard:
    script = service.chat(
        chat,
        f"Write 3-second voiceover for: {scene['description']}"
    )
    scene["voiceover"] = script

print("✅ Campaign assets generated!")
```

### Example 5: Semantic Search for Similar Ads

```python
# Build ad database with embeddings
ad_database = [
    "Fitness watch ad with transformation story",
    "Luxury watch ad with celebrity endorsement",
    "Budget smartwatch ad with features list",
    "Activity tracker ad for athletes"
]

# Generate embeddings
embeddings = service.embed_texts(ad_database)

# Search query
query = "High-end fitness device for serious runners"
query_embedding = service.embed_text(query)

# Calculate similarities
import numpy as np
similarities = np.dot(embeddings, query_embedding)
similarities /= (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding))

# Get top match
top_idx = np.argmax(similarities)
print(f"Most similar ad: {ad_database[top_idx]}")
print(f"Similarity score: {similarities[top_idx]:.3f}")
```

## Error Handling

The service includes comprehensive error handling:

```python
# Graceful degradation
analysis = service.analyze_video("invalid-path.mp4")
# Returns VideoAnalysis with error message, doesn't crash

# Library availability checks
if not VERTEXAI_AVAILABLE:
    print("⚠️ Vertex AI SDK not installed")
    # Service won't initialize

# API errors
images = service.generate_image("test prompt")
if not images:
    print("Image generation failed, check logs")
```

## Performance & Costs

### Gemini 2.0 Flash
- **Video Analysis**: ~$0.002-0.005 per video (varies by length)
- **Text Generation**: ~$0.0001 per request
- **Latency**: 2-10 seconds depending on video length

### Imagen 3.0
- **Image Generation**: ~$0.02 per image
- **Image Editing**: ~$0.04 per image
- **Latency**: 3-8 seconds per image

### Text Embeddings
- **Cost**: ~$0.00001 per text
- **Latency**: <100ms for single text, <1s for batches

### Optimization Tips

1. **Batch Processing**: Use `embed_texts()` for multiple embeddings
2. **Caching**: Store analysis results to avoid re-analyzing
3. **Smart Sampling**: For long videos, analyze key frames only
4. **Async Operations**: Run multiple analyses in parallel
5. **GCS Storage**: Keep videos in GCS for faster access

## Integration Points

### With Titan Core Services

```python
# Save analysis to Supabase
from services.supabase_connector import supabase_connector

analysis = service.analyze_video(video_uri)
supabase_connector.save_analysis(video_uri, analysis.__dict__)

# Use with Meta Publisher
from meta.meta_publisher import MetaPublisher

# Generate creative variants
variants = service.generate_ad_copy(product_info, "urgent", 5)

# Test each variant
publisher = MetaPublisher()
for copy in variants:
    creative_id = publisher.create_ad(copy, images[0])
    # Track performance...
```

### With ML Service

```python
# Combine Vertex AI with local ML models
from engines.vertex_ai import VertexAIService
from engines.pretrained_hook_detector import PretrainedHookDetector

vertex = VertexAIService(project_id="...")
hook_detector = PretrainedHookDetector()

# Dual analysis
vertex_analysis = vertex.analyze_video(video_uri)
hook_analysis = hook_detector.analyze_video(video_path)

# Ensemble results
final_score = (vertex_analysis.hook_quality + hook_analysis["hook_score"]) / 2
```

## Troubleshooting

### Authentication Errors

```bash
# Check credentials
gcloud auth application-default print-access-token

# Set project
gcloud config set project YOUR_PROJECT_ID

# Verify APIs enabled
gcloud services enable aiplatform.googleapis.com
```

### Import Errors

```bash
# Reinstall SDK
pip install --upgrade google-cloud-aiplatform

# Check Python version (3.9+ required)
python --version
```

### API Quota Issues

Check quotas in [GCP Console](https://console.cloud.google.com/iam-admin/quotas)

- Increase Gemini API QPM limit
- Enable billing if needed
- Use exponential backoff for retries

## Testing

Run the demo:

```bash
cd /home/user/geminivideo/services/titan-core/engines
export GOOGLE_CLOUD_PROJECT=your-project-id
python vertex_ai_demo.py
```

## File Structure

```
/home/user/geminivideo/services/titan-core/engines/
├── vertex_ai.py              # Main service (746 lines)
├── vertex_ai_demo.py          # Usage examples
└── VERTEX_AI_README.md        # This file
```

## Next Steps

1. **Test with Real Videos**: Upload sample ads to GCS
2. **Integrate with Pipeline**: Connect to video processing workflow
3. **Build Ad Database**: Store embeddings for semantic search
4. **A/B Testing**: Generate variants and track performance
5. **Monitoring**: Set up logging and metrics

## Support

For issues:
1. Check GCP Console for API errors
2. Verify authentication is working
3. Review logs for detailed error messages
4. Ensure video/image files are accessible

---

**Agent 23 Complete** ✅

Real Vertex AI integration with NO mock data, production-ready error handling, and comprehensive marketing-focused capabilities.
