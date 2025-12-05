# Voice Generation Quick Reference

## 🚀 Quick Start (1 minute)

### 1. Generate Voiceover (OpenAI)
```bash
curl -X POST http://localhost:8002/api/voice/generate \
  -H "Content-Type: application/json" \
  -d '{"script": "Your text here", "voice_id": "nova", "provider": "openai"}'
```

### 2. Get Voice Library
```bash
curl http://localhost:8002/api/voice/library?provider=openai
```

### 3. Sync to Video
```bash
curl -X POST http://localhost:8002/api/voice/sync \
  -H "Content-Type: application/json" \
  -d '{"audio_path": "/path/to/audio.mp3", "video_path": "/path/to/video.mp4"}'
```

---

## 🎙️ OpenAI Voices

| Voice | Description | Best For |
|-------|-------------|----------|
| `alloy` | Neutral, balanced | Corporate, tutorials |
| `echo` | Male, clear | Professional, authoritative |
| `fable` | British male, authoritative | Luxury, premium brands |
| `onyx` | Deep male, dramatic | Movie trailers, serious topics |
| `nova` | Female, warm | Friendly, approachable |
| `shimmer` | Female, energetic | Exciting, urgent CTAs |

---

## 📋 Common Use Cases

### Professional Ad Voiceover
```json
{
  "script": "Transform your business today",
  "voice_id": "nova",
  "provider": "openai",
  "model": "tts-1-hd",
  "speed": 1.0
}
```

### Urgent Call-to-Action
```json
{
  "script": "Limited time! Act now!",
  "voice_id": "shimmer",
  "provider": "openai",
  "speed": 1.2
}
```

### Authoritative Brand Voice
```json
{
  "script": "The industry leader in innovation",
  "voice_id": "onyx",
  "provider": "openai",
  "speed": 0.95
}
```

---

## 🎛️ Settings Guide

### Speed
- `0.75` - Slow (storytelling)
- `1.0` - Normal ✓
- `1.25` - Fast (energetic)
- `1.5+` - Very fast (urgent)

### Volume (sync)
- `0.8` - Quieter
- `1.0` - Normal ✓
- `1.2` - Louder
- `1.5+` - Much louder

### Fade Effects (sync)
- `fade_in: 0.5` - 0.5s fade in
- `fade_out: 1.0` - 1.0s fade out

---

## 💰 Pricing

### OpenAI TTS
- `tts-1`: $15/1M chars (~$0.015/1K)
- `tts-1-hd`: $30/1M chars (~$0.030/1K)
- **30-sec ad** (~150 chars) = **$0.0045**

### ElevenLabs
- **Free**: 10K chars/month
- **Starter**: $5/mo - 30K chars
- **Creator**: $22/mo - 100K chars
- **Pro**: $99/mo - 500K chars

---

## 🌍 Languages (ElevenLabs)

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `es` | Spanish |
| `fr` | French | `de` | German |
| `it` | Italian | `pt` | Portuguese |
| `pl` | Polish | `nl` | Dutch |
| `ja` | Japanese | `ko` | Korean |
| `zh` | Chinese | `hi` | Hindi |
| `ar` | Arabic | `ru` | Russian |
| `tr` | Turkish | ... | 15+ more |

---

## 🔧 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/voice/generate` | POST | Generate voiceover |
| `/api/voice/clone` | POST | Clone voice (ElevenLabs) |
| `/api/voice/library` | GET | List available voices |
| `/api/voice/sync` | POST | Add voiceover to video |
| `/api/voice/{id}` | DELETE | Delete cloned voice |
| `/api/voice/generate-multilingual` | POST | Multi-language generation |
| `/api/pro/job/{id}` | GET | Check async job status |

---

## 🎯 Integration Examples

### With Video Pipeline
```python
# 1. Generate voiceover
audio = await voice_gen.generate_voiceover(
    script="Your ad script",
    voice_id="nova"
)

# 2. Sync to video
video = await voice_gen.sync_to_video(
    audio_path=audio,
    video_path="ad.mp4",
    volume=1.2
)

# 3. Render final
final = pro_renderer.render(video, platform="instagram")
```

### A/B Testing
```python
voices = ["nova", "shimmer", "onyx"]
for voice in voices:
    audio = await voice_gen.generate_voiceover(
        script="Try our product!",
        voice_id=voice
    )
    # Test each variant
```

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "API key not configured" | Set `OPENAI_API_KEY` in `.env` |
| Voice cloning fails | Use 3-10 samples, 30-90s each |
| Audio out of sync | Check video has audio track |
| Poor quality | Use `tts-1-hd` instead of `tts-1` |

---

## 📊 Performance

| Provider | Speed | Quality | Cost |
|----------|-------|---------|------|
| OpenAI tts-1 | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | 💰 Cheap |
| OpenAI tts-1-hd | ⚡⚡ Medium | ⭐⭐⭐⭐ High | 💰💰 Medium |
| ElevenLabs | ⚡ Slower | ⭐⭐⭐⭐⭐ Best | 💰💰💰 Premium |

---

## ⚡ One-Liners

### Generate + Sync
```bash
# Generate voiceover and sync to video in one command
curl -X POST http://localhost:8002/api/voice/generate -d '{"script":"Text","voice_id":"nova"}' | \
  jq -r '.output_path' | \
  xargs -I {} curl -X POST http://localhost:8002/api/voice/sync -d "{\"audio_path\":\"{}\",\"video_path\":\"ad.mp4\"}"
```

### Test All Voices
```bash
for voice in alloy echo fable onyx nova shimmer; do
  curl -X POST http://localhost:8002/api/voice/generate \
    -d "{\"script\":\"Test\",\"voice_id\":\"$voice\"}";
done
```

---

## 📖 Full Documentation

See `VOICE_GENERATION_README.md` for complete documentation.

---

## 🎬 Ready to Use!

```bash
# 1. Set API key
export OPENAI_API_KEY=your_key

# 2. Generate voiceover
curl -X POST http://localhost:8002/api/voice/generate \
  -H "Content-Type: application/json" \
  -d '{"script": "Hello world!", "voice_id": "nova"}'

# 3. Check output
ls -lh /tmp/geminivideo/voiceovers/
```

**Voice is CRITICAL for professional ads!** 🚀
