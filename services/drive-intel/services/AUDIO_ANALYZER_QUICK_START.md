# Audio Analyzer - Quick Start Guide

## Installation

```bash
pip install transformers librosa soundfile scipy torch
```

## Basic Usage

### 1. Complete Video Analysis (One-Liner)

```python
from services.audio_analyzer import AudioAnalyzer

analyzer = AudioAnalyzer()
analysis = analyzer.analyze_video("video.mp4")

# Access results
print(analysis.transcript.text)                    # Transcription
print(analysis.emotion)                            # Detected emotion
print(analysis.pacing.words_per_minute)            # Speaking rate
print(analysis.audio_quality_score)                # Quality (0-100)
print(analysis.hook_timing)                        # Hook at X seconds
```

### 2. Individual Components

#### Transcription
```python
transcript = analyzer.transcribe("audio.wav")

print(transcript.text)                    # Full text
print(transcript.duration)                # Duration in seconds
print(transcript.confidence)              # Confidence score

# Word-level timestamps
for word in transcript.words[:5]:
    print(f"{word['word']}: {word['start']:.2f}s - {word['end']:.2f}s")
```

#### Emotion Detection
```python
emotion, confidence = analyzer.detect_speech_emotion("audio.wav")
print(f"{emotion} ({confidence:.2%})")

# Emotions: angry, calm, disgust, fear, happy, neutral, sad, surprise
```

#### Pacing Analysis
```python
pacing = analyzer.analyze_pacing("audio.wav")

print(f"WPM: {pacing.words_per_minute}")
print(f"Pauses: {pacing.pause_count}")
print(f"Speech ratio: {pacing.speech_ratio:.2%}")
```

#### Music vs Speech
```python
music_ratio, speech_ratio = analyzer.detect_music_vs_speech("audio.wav")
print(f"Music: {music_ratio:.2%}, Speech: {speech_ratio:.2%}")
```

#### Loudness Analysis
```python
lufs = analyzer.calculate_loudness_lufs("audio.wav")
peaks = analyzer.detect_loudness_peaks("audio.wav")

print(f"Loudness: {lufs:.2f} LUFS")
print(f"Peaks at: {[f'{p:.2f}s' for p in peaks]}")
```

#### Hook Detection
```python
hook_time = analyzer.detect_hook_timing("audio.wav")
moments = analyzer.detect_attention_moments("audio.wav")

print(f"First hook: {hook_time:.2f}s")
for m in moments:
    print(f"{m['type']} at {m['time']:.2f}s (intensity: {m['intensity']:.2f})")
```

#### Quality Assessment
```python
quality = analyzer.assess_audio_quality("audio.wav")

print(f"Score: {quality['overall_score']:.1f}/100")
print(f"Noise: {quality['noise_level']:.3f}")
print(f"Dynamic range: {quality['dynamic_range']:.3f}")
```

## GPU Acceleration

```python
# Use GPU
analyzer = AudioAnalyzer(device='cuda')

# Force CPU
analyzer = AudioAnalyzer(device='cpu')

# Auto-detect (default)
analyzer = AudioAnalyzer()
```

## Batch Processing

```python
analyzer = AudioAnalyzer()  # Initialize once

videos = ["video1.mp4", "video2.mp4", "video3.mp4"]
results = []

for video in videos:
    try:
        analysis = analyzer.analyze_video(video)
        results.append({
            'video': video,
            'transcript': analysis.transcript.text,
            'emotion': analysis.emotion,
            'quality': analysis.audio_quality_score
        })
    except Exception as e:
        print(f"Failed {video}: {e}")
```

## Integration Examples

### Video Ranking
```python
def score_video_audio(video_path: str) -> float:
    analyzer = AudioAnalyzer()
    analysis = analyzer.analyze_video(video_path)

    score = 0.0

    # Quality bonus
    score += analysis.audio_quality_score / 10

    # Early hook bonus
    if analysis.hook_timing < 5.0:
        score += 5.0

    # Emotion bonus (positive emotions)
    if analysis.emotion in ['happy', 'surprise']:
        score += 3.0

    # Speaking rate bonus (120-150 WPM is optimal)
    wpm = analysis.pacing.words_per_minute
    if 120 <= wpm <= 150:
        score += 2.0

    return score
```

### Content Search
```python
def search_by_keywords(videos: List[str], keywords: List[str]) -> List[str]:
    analyzer = AudioAnalyzer()
    matches = []

    for video in videos:
        transcript = analyzer.transcribe_video(video)
        text = transcript.text.lower()

        if any(kw.lower() in text for kw in keywords):
            matches.append(video)

    return matches
```

### Highlight Detection
```python
def find_highlight_moments(video_path: str) -> List[float]:
    analyzer = AudioAnalyzer()

    audio_path = analyzer.extract_audio(video_path)
    moments = analyzer.detect_attention_moments(audio_path)

    # Return timestamps of strong moments
    highlights = [m['time'] for m in moments if m['intensity'] > 0.8]

    return highlights
```

## Testing

```bash
# Run test suite
cd /home/user/geminivideo/services/drive-intel
python examples/test_audio_analyzer.py your_audio.wav

# Or use synthetic test audio
python examples/test_audio_analyzer.py
```

## Data Classes

### AudioAnalysis
```python
analysis.transcript          # Transcript object
analysis.pacing             # PacingMetrics object
analysis.emotion            # str
analysis.emotion_confidence # float
analysis.music_presence     # float (0-1)
analysis.speech_presence    # float (0-1)
analysis.loudness_lufs      # float
analysis.hook_timing        # float (seconds)
analysis.audio_quality_score # float (0-100)
```

### Transcript
```python
transcript.text             # str
transcript.words            # List[Dict]
transcript.duration         # float
transcript.language         # str
transcript.confidence       # float
```

### PacingMetrics
```python
pacing.words_per_minute     # float
pacing.avg_pause_duration   # float
pacing.pause_count          # int
pacing.speech_ratio         # float
pacing.energy_profile       # List[float]
```

## Troubleshooting

### FFmpeg not found
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

### CUDA out of memory
```python
analyzer = AudioAnalyzer(device='cpu')
```

### Slow first run
Models are downloaded on first use (~1.5GB). Subsequent runs are fast.

## Performance Tips

1. **Reuse analyzer instance** for batch processing
2. **Use GPU** for 5-10x speedup
3. **Cache models** to avoid re-downloading
4. **Process audio directly** when possible (skip video extraction)

## Common Patterns

### Get full metadata
```python
def get_audio_metadata(video_path: str) -> dict:
    analyzer = AudioAnalyzer()
    analysis = analyzer.analyze_video(video_path)

    return {
        'transcript': analysis.transcript.text,
        'duration': analysis.transcript.duration,
        'word_count': len(analysis.transcript.words),
        'emotion': analysis.emotion,
        'wpm': analysis.pacing.words_per_minute,
        'has_music': analysis.music_presence > 0.3,
        'quality': analysis.audio_quality_score,
        'hook_timing': analysis.hook_timing,
        'loudness': analysis.loudness_lufs
    }
```

### Filter by quality
```python
def filter_quality_videos(videos: List[str], min_quality: float = 70.0) -> List[str]:
    analyzer = AudioAnalyzer()
    good_videos = []

    for video in videos:
        quality = analyzer.assess_audio_quality(
            analyzer.extract_audio(video)
        )
        if quality['overall_score'] >= min_quality:
            good_videos.append(video)

    return good_videos
```

### Extract speaker insights
```python
def analyze_speaker(audio_path: str) -> dict:
    analyzer = AudioAnalyzer()

    transcript = analyzer.transcribe(audio_path)
    pacing = analyzer.analyze_pacing(audio_path, transcript)
    emotion, conf = analyzer.detect_speech_emotion(audio_path)

    return {
        'speaking_rate': pacing.words_per_minute,
        'pause_frequency': pacing.pause_count / transcript.duration,
        'energy_level': 'high' if pacing.speech_ratio > 0.8 else 'low',
        'emotion': emotion,
        'confidence': conf
    }
```

## Reference

- **Models**: facebook/wav2vec2-base-960h, ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition
- **Location**: `/home/user/geminivideo/services/drive-intel/services/audio_analyzer.py`
- **Docs**: `AUDIO_ANALYZER_README.md`
- **Tests**: `examples/test_audio_analyzer.py`
