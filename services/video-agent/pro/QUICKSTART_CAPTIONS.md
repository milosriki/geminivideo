# QUICK START: Auto-Captions

Get started with auto-captions in 5 minutes.

## Installation (2 minutes)

```bash
# 1. Install FFmpeg
sudo apt install ffmpeg  # Linux
brew install ffmpeg      # macOS

# 2. Install Python packages
pip install -r requirements_captions.txt

# 3. Verify setup
python test_captions_setup.py
```

## Your First Caption (30 seconds)

```python
from auto_captions import AutoCaptionSystem, CaptionStyle

# Initialize
system = AutoCaptionSystem()

# Process video
result = system.process_video(
    video_path="my_video.mp4",
    caption_style=CaptionStyle.HORMOZI
)

print(f"Done! {result['captioned_video_path']}")
```

## Command Line (10 seconds)

```bash
python auto_captions.py my_video.mp4 --style hormozi
```

## That's It!

Your video now has pro-grade captions.

### Output Files
- `my_video_captioned_hormozi.mp4` - Video with burned captions
- `my_video.srt` - Subtitle file
- `my_video.vtt` - WebVTT file

## Next Steps

### Try Different Styles

```bash
# TikTok style (centered, bold)
python auto_captions.py video.mp4 --style tiktok

# Instagram style (word-by-word pop)
python auto_captions.py video.mp4 --style instagram

# YouTube style (traditional subtitles)
python auto_captions.py video.mp4 --style youtube
```

### Custom Colors

```bash
python auto_captions.py video.mp4 \
    --style hormozi \
    --font-size 80 \
    --font-color cyan \
    --highlight-color magenta
```

### Use GPU for Speed

```python
system = AutoCaptionSystem(device="cuda")  # 10-50x faster
```

### Process Multiple Videos

```python
for video in ["ad1.mp4", "ad2.mp4", "ad3.mp4"]:
    result = system.process_video(video, caption_style=CaptionStyle.HORMOZI)
    print(f"✓ {video}")
```

## Common Issues

### "FFmpeg not found"
```bash
# Install FFmpeg first
sudo apt install ffmpeg
```

### "CUDA out of memory"
```python
# Use smaller model or CPU
system = AutoCaptionSystem(model_size=WhisperModelSize.TINY)
# or
system = AutoCaptionSystem(device="cpu")
```

### "Slow processing"
```python
# Enable GPU acceleration
system = AutoCaptionSystem(device="cuda")

# Or use faster model
system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)
```

## Caption Styles Comparison

| Style | Best For | Characteristics |
|-------|----------|----------------|
| **Hormozi** | Sales, Fitness, Coaching | Big words, one at a time, HIGH IMPACT |
| **TikTok** | Viral, Short-form | Centered, bold, animated |
| **Instagram** | Reels, Stories | Word-by-word pop, colorful |
| **YouTube** | Long-form, Tutorials | Traditional subtitles, bottom |
| **Karaoke** | Music, Lyrics | Full text with highlight |

## Performance Guide

| Model | Speed | Accuracy | Use When |
|-------|-------|----------|----------|
| tiny | Very Fast | Good | Testing |
| **base** | Fast | Good | **Most videos** |
| small | Moderate | Better | Important videos |
| medium | Slow | Best | Maximum quality |

**Recommendation**: Use `base` model with GPU for best balance.

## Video Format Support

Works with any video format FFmpeg supports:
- MP4, MOV, AVI, MKV, WebM, FLV
- Vertical (9:16), Square (1:1), Horizontal (16:9)
- Any resolution, any frame rate

## Language Support

Auto-detects 99+ languages:
- English, Spanish, French, German, Italian
- Portuguese, Dutch, Polish, Russian
- Chinese, Japanese, Korean
- And many more...

```python
# Auto-detect
system = AutoCaptionSystem(language=None)

# Or specify
system = AutoCaptionSystem(language="es")  # Spanish
```

## Full Documentation

- **Complete Guide**: `AUTO_CAPTIONS_README.md`
- **Demos**: `python demo_auto_captions.py`
- **Integration**: `integration_captions.py`
- **API Reference**: See README

## Support

Questions? Check:
1. This quick start
2. `AUTO_CAPTIONS_README.md`
3. Run demos: `python demo_auto_captions.py`

---

**Start creating winning video ads with captions in minutes!**
