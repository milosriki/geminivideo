# PRO-GRADE AUTO-CAPTION SYSTEM

Complete auto-caption system for creating winning video ads using OpenAI Whisper AI.

## Features

### Core Features
- **OpenAI Whisper Integration**: Multiple model sizes (tiny, base, small, medium, large, large-v3)
- **GPU Acceleration**: Blazing fast transcription with CUDA support
- **Word-Level Timestamps**: Precise timing for animated captions
- **Multi-Language Support**: Auto-detect or specify 99+ languages
- **Speaker Diarization**: Identify who is speaking when (requires HuggingFace token)
- **Custom Vocabulary**: Built-in fitness terminology enhancement
- **Profanity Filtering**: Automatically censor inappropriate language
- **SRT/VTT Export**: Standard subtitle formats for all platforms

### Caption Styles

#### 1. Instagram Style
- Word-by-word pop animation
- Color highlight for each word
- Perfect for Reels and Stories

#### 2. YouTube Style
- Sentence blocks at bottom
- Classic subtitle appearance
- Professional and readable

#### 3. Karaoke Style
- Full sentence visible
- Word-by-word highlight as spoken
- Engaging and easy to follow

#### 4. TikTok Style
- Centered, bold, animated
- Large text with shadows
- Optimized for vertical video

#### 5. Hormozi Style (Most Popular for Ads)
- BIG BOLD words
- One or few words at a time
- Centered on screen
- High impact and attention-grabbing

### Customization Options
- Font family, size, color
- Highlight colors
- Background/box styling
- Border width and color
- Shadow effects
- Position (centered, bottom, custom)
- Animation settings
- Uppercase/lowercase
- Max words per caption
- Caption timing optimization

## Installation

### 1. Install FFmpeg
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### 2. Install Python Dependencies
```bash
# Basic installation
pip install -r requirements_captions.txt

# For GPU support (CUDA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For speaker diarization (optional)
pip install pyannote.audio
```

### 3. Set Up HuggingFace Token (Optional, for Speaker Diarization)
```bash
# Get token from https://huggingface.co/settings/tokens
export HF_TOKEN="your_huggingface_token_here"
```

## Quick Start

### Basic Usage

```python
from auto_captions import AutoCaptionSystem, CaptionStyle, WhisperModelSize

# Initialize system
system = AutoCaptionSystem(
    model_size=WhisperModelSize.BASE,
    enable_profanity_filter=True
)

# Process video with Hormozi-style captions
result = system.process_video(
    video_path="my_video.mp4",
    output_dir="output",
    caption_style=CaptionStyle.HORMOZI,
    burn_captions=True
)

print(f"Captioned video: {result['captioned_video_path']}")
```

### Command Line Usage

```bash
# Basic usage
python auto_captions.py my_video.mp4 --style hormozi

# Specify output directory
python auto_captions.py my_video.mp4 --output-dir captions --style tiktok

# Use larger model for better accuracy
python auto_captions.py my_video.mp4 --model medium --style instagram

# Enable speaker diarization
python auto_captions.py my_video.mp4 --diarization --hf-token YOUR_TOKEN

# Custom styling
python auto_captions.py my_video.mp4 \
    --style hormozi \
    --font-size 80 \
    --font-color yellow \
    --highlight-color cyan

# Skip burning (only generate SRT/VTT)
python auto_captions.py my_video.mp4 --no-burn
```

## Advanced Usage

### Custom Style Configuration

```python
from auto_captions import CaptionStyleConfig, CaptionStyle

# Create custom style
custom_style = CaptionStyleConfig(
    font_family="Arial-Bold",
    font_size=72,
    font_color="cyan",
    highlight_color="magenta",
    box_color="black@0.9",
    border_width=4,
    border_color="black",
    shadow_enabled=True,
    shadow_x=4,
    shadow_y=4,
    all_caps=True,
    max_words_per_line=3
)

# Use custom style
result = system.process_video(
    video_path="video.mp4",
    caption_style=CaptionStyle.HORMOZI,
    style_config=custom_style
)
```

### Speaker Diarization

```python
# Initialize with diarization enabled
system = AutoCaptionSystem(
    model_size=WhisperModelSize.SMALL,
    enable_diarization=True,
    hf_token="your_hf_token"
)

# Process with speaker detection
result = system.process_video(
    video_path="interview.mp4",
    num_speakers=2  # Expected number of speakers
)

# Check speaker assignments
for caption in result['captions']:
    print(f"{caption['speaker']}: {caption['text']}")
```

### Multi-Language Support

```python
# Auto-detect language
system = AutoCaptionSystem(language=None)

# Or specify language
system = AutoCaptionSystem(language="es")  # Spanish
system = AutoCaptionSystem(language="fr")  # French
system = AutoCaptionSystem(language="de")  # German

# Supported languages: en, es, fr, de, it, pt, nl, pl, ru, zh, ja, ko, and 90+ more
```

### Batch Processing

```python
import os
from pathlib import Path

# Initialize once
system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)

# Process multiple videos
video_dir = "videos"
for video_file in os.listdir(video_dir):
    if video_file.endswith(('.mp4', '.mov', '.avi')):
        video_path = os.path.join(video_dir, video_file)

        result = system.process_video(
            video_path=video_path,
            output_dir=f"output/{Path(video_file).stem}",
            caption_style=CaptionStyle.HORMOZI
        )

        print(f"Processed: {video_file}")
```

### Export Only (No Burn-In)

```python
# Generate SRT and VTT files without burning captions
result = system.process_video(
    video_path="video.mp4",
    generate_srt=True,
    generate_vtt=True,
    burn_captions=False
)

print(f"SRT: {result['srt_path']}")
print(f"VTT: {result['vtt_path']}")
```

## Model Comparison

| Model | Size | Speed (GPU) | Speed (CPU) | Accuracy | Recommended For |
|-------|------|-------------|-------------|----------|-----------------|
| tiny | 39 MB | Very Fast | Fast | Good | Quick tests, real-time |
| base | 74 MB | Fast | Moderate | Good | Most use cases |
| small | 244 MB | Moderate | Slow | Better | Professional work |
| medium | 769 MB | Slow | Very Slow | Best | High accuracy needed |
| large | 1550 MB | Very Slow | Extremely Slow | Best | Maximum accuracy |
| large-v3 | 1550 MB | Very Slow | Extremely Slow | Best | Latest model |

**Recommendation for Video Ads**: Use `base` or `small` for best balance of speed and accuracy.

## Caption Style Guide

### When to Use Each Style

#### Hormozi Style
- **Best for**: Sales videos, VSLs, fitness content, coaching
- **Characteristics**: Maximum attention, one powerful word at a time
- **Example Use**: "BUILD YOUR DREAM BODY"

#### TikTok Style
- **Best for**: Short-form content, vertical videos, viral content
- **Characteristics**: Bold, centered, high energy
- **Example Use**: Trending TikTok videos

#### Instagram Style
- **Best for**: Reels, Stories, aesthetic content
- **Characteristics**: Smooth word-by-word animation
- **Example Use**: Fashion, lifestyle, beauty content

#### YouTube Style
- **Best for**: Long-form content, tutorials, professional videos
- **Characteristics**: Traditional subtitles at bottom
- **Example Use**: Educational content, interviews

#### Karaoke Style
- **Best for**: Music videos, sing-alongs, lyric videos
- **Characteristics**: Full text with word highlighting
- **Example Use**: Music content, song tutorials

## Performance Tips

### GPU Acceleration
```python
import torch

# Check if GPU is available
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("No GPU available, using CPU")

# Force GPU usage
system = AutoCaptionSystem(device="cuda")

# Force CPU usage
system = AutoCaptionSystem(device="cpu")
```

### Optimize Processing Time
- Use `tiny` or `base` model for speed
- Enable GPU acceleration (10-50x faster)
- Reduce video resolution before processing
- Use `fp16=True` for faster inference (GPU only)
- Process in batches to amortize model loading time

### Memory Management
```python
# Clear GPU memory between videos
import torch
torch.cuda.empty_cache()

# Use smaller model for limited memory
system = AutoCaptionSystem(model_size=WhisperModelSize.TINY)
```

## Fitness Vocabulary

Built-in enhancement for fitness terms:

- "repetitions" → "reps"
- "cardiovascular" → "cardio"
- "macronutrients" → "macros"
- "personal record" → "PR"
- "high intensity interval training" → "HIIT"
- "body mass index" → "BMI"
- "total daily energy expenditure" → "TDEE"
- And many more...

```python
# Enable fitness vocabulary
system = AutoCaptionSystem(enable_fitness_vocab=True)
```

## Profanity Filter

Automatically censor inappropriate language:

```python
# Enable profanity filter (default: enabled)
system = AutoCaptionSystem(enable_profanity_filter=True)

# Process video
result = system.process_video("video.mp4")

# All profanity will be replaced with "***"
```

## Troubleshooting

### FFmpeg Not Found
```bash
# Verify FFmpeg is installed
ffmpeg -version

# If not found, install it
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS
```

### CUDA Out of Memory
```python
# Use smaller model
system = AutoCaptionSystem(model_size=WhisperModelSize.TINY)

# Or force CPU
system = AutoCaptionSystem(device="cpu")
```

### Slow Transcription
```python
# Enable GPU
system = AutoCaptionSystem(device="cuda")

# Use smaller model
system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)

# Reduce beam size for faster decoding
transcriber.transcribe(video_path, beam_size=1)
```

### Poor Accuracy
```python
# Use larger model
system = AutoCaptionSystem(model_size=WhisperModelSize.MEDIUM)

# Provide initial prompt for context
transcriber.transcribe(
    video_path,
    initial_prompt="This is a fitness video about building muscle."
)

# Specify language explicitly
system = AutoCaptionSystem(language="en")
```

### Speaker Diarization Not Working
```bash
# Install pyannote.audio
pip install pyannote.audio

# Set HuggingFace token
export HF_TOKEN="your_token"

# Accept pyannote model license at:
# https://huggingface.co/pyannote/speaker-diarization-3.1
```

## API Reference

### AutoCaptionSystem

```python
system = AutoCaptionSystem(
    model_size=WhisperModelSize.BASE,    # Whisper model size
    device=None,                          # 'cuda' or 'cpu' (auto-detect)
    language=None,                        # Language code or None for auto-detect
    enable_diarization=False,             # Enable speaker diarization
    hf_token=None,                        # HuggingFace token
    enable_profanity_filter=True,         # Filter profanity
    enable_fitness_vocab=True             # Enhance fitness terms
)

result = system.process_video(
    video_path="video.mp4",              # Input video path
    output_dir="output",                  # Output directory
    caption_style=CaptionStyle.HORMOZI,   # Caption style
    style_config=None,                    # Custom style config
    generate_srt=True,                    # Generate SRT file
    generate_vtt=True,                    # Generate VTT file
    burn_captions=True,                   # Burn into video
    num_speakers=None                     # Expected speakers (diarization)
)
```

### Result Dictionary

```python
{
    "video_path": "input.mp4",
    "transcription": {...},              # Full Whisper result
    "words": [...],                      # Word-level timestamps
    "captions": [...],                   # Caption segments
    "language": "en",                    # Detected language
    "srt_path": "output.srt",           # SRT file path
    "vtt_path": "output.vtt",           # VTT file path
    "captioned_video_path": "output.mp4" # Final video path
}
```

## Examples

### Example 1: Fitness Ad (Hormozi Style)

```python
from auto_captions import AutoCaptionSystem, CaptionStyle, CaptionStyleConfig

# Hormozi-style for fitness ad
style = CaptionStyleConfig(
    font_size=80,
    font_color="yellow",
    all_caps=True,
    max_words_per_line=2
)

system = AutoCaptionSystem(
    model_size=WhisperModelSize.SMALL,
    enable_fitness_vocab=True
)

result = system.process_video(
    video_path="fitness_ad.mp4",
    caption_style=CaptionStyle.HORMOZI,
    style_config=style
)
```

### Example 2: Instagram Reel

```python
# Instagram-optimized captions
style = CaptionStyleConfig(
    font_size=56,
    font_color="white",
    highlight_color="#FF0080",
    position_y="h-th-100",
    max_words_per_line=4
)

system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)

result = system.process_video(
    video_path="reel.mp4",
    caption_style=CaptionStyle.INSTAGRAM,
    style_config=style
)
```

### Example 3: Interview with Multiple Speakers

```python
# Interview with speaker diarization
system = AutoCaptionSystem(
    model_size=WhisperModelSize.SMALL,
    enable_diarization=True,
    hf_token=os.environ.get("HF_TOKEN")
)

result = system.process_video(
    video_path="interview.mp4",
    caption_style=CaptionStyle.YOUTUBE,
    num_speakers=2
)

# Export with speaker labels
for caption in result['captions']:
    print(f"[{caption['speaker']}] {caption['text']}")
```

## Best Practices

### For Maximum Engagement
1. Use **Hormozi style** for sales/coaching content
2. Keep captions **short and punchy** (2-4 words)
3. Use **high contrast colors** (yellow on black, white on black)
4. Position captions **center screen** for mobile
5. Enable **ALL CAPS** for emphasis
6. Add **shadows** for readability

### For Professional Content
1. Use **YouTube style** for traditional look
2. Keep captions **at bottom** of frame
3. Use **white text with black border**
4. Limit to **40 characters per line**
5. Time captions for **comfortable reading pace**

### For Social Media
1. **TikTok/Instagram style** for vertical videos
2. **Bold, large text** (size 60+)
3. **Animated entrance** for each word
4. **Centered positioning** for mobile viewing
5. **Emoji support** for personality

## License

This auto-caption system uses:
- OpenAI Whisper (MIT License)
- PyTorch (BSD License)
- FFmpeg (LGPL/GPL License)
- pyannote.audio (MIT License)

## Support

For issues, questions, or feature requests, please check:
1. This README
2. Demo examples in `demo_auto_captions.py`
3. FFmpeg documentation: https://ffmpeg.org/
4. Whisper documentation: https://github.com/openai/whisper

## Credits

Built with:
- OpenAI Whisper for transcription
- pyannote.audio for speaker diarization
- FFmpeg for video processing
- PyTorch for deep learning

---

**Start creating winning video ads with professional auto-captions today!**
