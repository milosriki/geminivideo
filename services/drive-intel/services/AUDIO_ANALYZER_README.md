# Audio Analyzer Service

Production-grade audio analysis using pretrained Wav2Vec2 models from HuggingFace.

## Overview

The `AudioAnalyzer` service provides comprehensive audio analysis for video content, including:

- **Transcription**: Word-level speech-to-text using Wav2Vec2
- **Emotion Detection**: Speech emotion recognition
- **Pacing Analysis**: Speech rhythm, pauses, and energy
- **Music vs Speech**: Content type classification
- **Loudness Analysis**: LUFS calculation and peak detection
- **Hook Detection**: Attention-grabbing moment identification
- **Audio Quality**: SNR, dynamic range, and quality scoring

## Key Features

### Real Pretrained Models

- **Transcription**: `facebook/wav2vec2-base-960h`
- **Emotion**: `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition`
- GPU support with automatic CPU fallback
- Model caching for faster subsequent loads

### Comprehensive Analysis

All analysis components work together to provide a complete audio profile suitable for:
- Video ranking and recommendation
- Content quality assessment
- Hook detection for short-form content
- Automated video editing decisions

## Installation

### Dependencies

```bash
pip install torch transformers librosa soundfile scipy
```

Already included in `requirements.txt`:
```
transformers==4.46.3
librosa==0.10.2.post1
soundfile==0.12.1
scipy==1.14.1
```

### System Requirements

- **FFmpeg**: Required for video audio extraction
- **GPU (optional)**: CUDA-capable GPU for faster inference
- **RAM**: 4GB+ recommended (models are ~1GB combined)

## Usage

### Basic Usage

```python
from services.audio_analyzer import AudioAnalyzer

# Initialize analyzer
analyzer = AudioAnalyzer()

# Analyze audio file
analysis = analyzer.analyze("path/to/audio.wav")

print(f"Transcript: {analysis.transcript.text}")
print(f"Emotion: {analysis.emotion} ({analysis.emotion_confidence:.2%})")
print(f"WPM: {analysis.pacing.words_per_minute:.1f}")
print(f"Quality: {analysis.audio_quality_score:.1f}/100")
```

### Video Analysis

```python
# Extract audio and analyze video
analysis = analyzer.analyze_video("path/to/video.mp4")
```

### Individual Components

```python
# Transcription only
transcript = analyzer.transcribe("audio.wav")
print(f"Text: {transcript.text}")
print(f"Words: {len(transcript.words)}")

# Emotion detection
emotion, confidence = analyzer.detect_speech_emotion("audio.wav")
print(f"Emotion: {emotion} ({confidence:.2%})")

# Pacing analysis
pacing = analyzer.analyze_pacing("audio.wav")
print(f"WPM: {pacing.words_per_minute}")
print(f"Pauses: {pacing.pause_count}")

# Music vs speech
music_ratio, speech_ratio = analyzer.detect_music_vs_speech("audio.wav")
print(f"Music: {music_ratio:.2%}, Speech: {speech_ratio:.2%}")

# Loudness
lufs = analyzer.calculate_loudness_lufs("audio.wav")
peaks = analyzer.detect_loudness_peaks("audio.wav")
print(f"Loudness: {lufs:.2f} LUFS")
print(f"Peaks at: {peaks}")

# Hook detection
hook_time = analyzer.detect_hook_timing("audio.wav")
moments = analyzer.detect_attention_moments("audio.wav")
print(f"First hook at: {hook_time:.2f}s")

# Quality assessment
quality = analyzer.assess_audio_quality("audio.wav")
print(f"Quality score: {quality['overall_score']:.1f}/100")
```

## API Reference

### AudioAnalyzer Class

#### Initialization

```python
analyzer = AudioAnalyzer(
    device: str = None,      # 'cuda', 'cpu', or None (auto-detect)
    cache_dir: str = None    # Model cache directory
)
```

#### Main Methods

##### `analyze(audio_path: str) -> AudioAnalysis`

Performs complete audio analysis.

**Returns**: `AudioAnalysis` object containing:
- `transcript`: Transcript with word-level timestamps
- `pacing`: PacingMetrics (WPM, pauses, speech ratio)
- `emotion`: Detected emotion label
- `emotion_confidence`: Emotion confidence score
- `music_presence`: Music ratio (0-1)
- `speech_presence`: Speech ratio (0-1)
- `loudness_lufs`: Integrated loudness in LUFS
- `hook_timing`: Time to first attention moment (seconds)
- `audio_quality_score`: Overall quality (0-100)

##### `analyze_video(video_path: str) -> AudioAnalysis`

Extracts audio from video and analyzes it.

##### `transcribe(audio_path: str, return_timestamps: bool = True) -> Transcript`

Transcribes audio to text.

**Returns**: `Transcript` object:
- `text`: Full transcription
- `words`: List of word dictionaries (word, start, end, confidence)
- `duration`: Audio duration in seconds
- `language`: Detected language code
- `confidence`: Overall confidence score

##### `detect_speech_emotion(audio_path: str) -> Tuple[str, float]`

Detects primary emotion in speech.

**Returns**: `(emotion_label, confidence)`

**Emotions**: angry, calm, disgust, fear, happy, neutral, sad, surprise

##### `analyze_pacing(audio_path: str, transcript: Transcript = None) -> PacingMetrics`

Analyzes speech pacing and rhythm.

**Returns**: `PacingMetrics` object:
- `words_per_minute`: Speaking rate
- `avg_pause_duration`: Average pause length
- `pause_count`: Number of pauses detected
- `speech_ratio`: Speech time / total time
- `energy_profile`: Energy levels over time

##### `detect_music_vs_speech(audio_path: str) -> Tuple[float, float]`

Classifies content as music or speech.

**Returns**: `(music_ratio, speech_ratio)`

##### `calculate_loudness_lufs(audio_path: str) -> float`

Calculates integrated loudness in LUFS.

**Returns**: Loudness value in LUFS

##### `detect_hook_timing(audio_path: str) -> float`

Detects time to first attention-grabbing moment.

**Returns**: Time in seconds

##### `assess_audio_quality(audio_path: str) -> Dict[str, Any]`

Assesses overall audio quality.

**Returns**: Dictionary with:
- `overall_score`: Quality score (0-100)
- `noise_level`: Background noise (0-1)
- `dynamic_range`: Dynamic range
- `clipping_ratio`: Clipping ratio
- `spectral_flatness`: Spectral flatness

### Data Classes

#### Transcript

```python
@dataclass
class Transcript:
    text: str                           # Full transcription
    words: List[Dict[str, Any]]         # Word-level data
    duration: float                     # Duration in seconds
    language: str                       # Language code
    confidence: float                   # Overall confidence
```

#### PacingMetrics

```python
@dataclass
class PacingMetrics:
    words_per_minute: float             # Speaking rate
    avg_pause_duration: float           # Average pause length
    pause_count: int                    # Number of pauses
    speech_ratio: float                 # Speech time ratio
    energy_profile: List[float]         # Energy over time
```

#### AudioAnalysis

```python
@dataclass
class AudioAnalysis:
    transcript: Transcript              # Transcription results
    pacing: PacingMetrics               # Pacing analysis
    emotion: str                        # Primary emotion
    emotion_confidence: float           # Emotion confidence
    music_presence: float               # Music ratio
    speech_presence: float              # Speech ratio
    loudness_lufs: float                # Loudness in LUFS
    hook_timing: float                  # Hook timing (seconds)
    audio_quality_score: float          # Quality score (0-100)
```

## Performance

### Benchmarks

Approximate processing times (on CPU):

- **Transcription**: ~1-2x realtime (5s audio = 5-10s processing)
- **Emotion Detection**: ~0.5x realtime
- **Pacing Analysis**: <1s for 60s audio
- **Full Analysis**: ~2-3x realtime

GPU acceleration provides 5-10x speedup for transcription and emotion detection.

### Memory Usage

- **Model Loading**: ~1.5GB RAM
- **Audio Processing**: ~100MB per minute of audio
- **Total**: 2-3GB recommended for smooth operation

## Integration Examples

### Video Ranking Integration

```python
from services.audio_analyzer import AudioAnalyzer

def analyze_video_for_ranking(video_path: str) -> dict:
    """Analyze video audio for ranking system."""
    analyzer = AudioAnalyzer()
    analysis = analyzer.analyze_video(video_path)

    return {
        'transcript': analysis.transcript.text,
        'keywords': extract_keywords(analysis.transcript.text),
        'emotion': analysis.emotion,
        'speaking_rate': analysis.pacing.words_per_minute,
        'hook_time': analysis.hook_timing,
        'quality_score': analysis.audio_quality_score,
        'has_music': analysis.music_presence > 0.3,
        'is_speech': analysis.speech_presence > 0.5,
    }
```

### Batch Processing

```python
def batch_analyze_videos(video_paths: List[str]) -> List[AudioAnalysis]:
    """Analyze multiple videos efficiently."""
    analyzer = AudioAnalyzer()  # Initialize once

    results = []
    for video_path in video_paths:
        try:
            analysis = analyzer.analyze_video(video_path)
            results.append(analysis)
        except Exception as e:
            logger.error(f"Failed to analyze {video_path}: {e}")
            results.append(None)

    return results
```

### Hook Detection for Shorts

```python
def find_best_hook_for_short(video_path: str) -> float:
    """Find best hook timing for short-form content."""
    analyzer = AudioAnalyzer()

    # Detect attention moments
    audio_path = analyzer.extract_audio(video_path)
    moments = analyzer.detect_attention_moments(audio_path)

    # Find first strong moment in first 10 seconds
    for moment in moments:
        if moment['time'] < 10.0 and moment['intensity'] > 0.7:
            return moment['time']

    return 0.0  # No strong hook found
```

## Testing

Run the test suite:

```bash
# Test with your own audio
python examples/test_audio_analyzer.py path/to/audio.wav

# Test with synthetic audio
python examples/test_audio_analyzer.py
```

## Troubleshooting

### FFmpeg Not Found

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### CUDA Out of Memory

If you get CUDA OOM errors:

```python
# Force CPU usage
analyzer = AudioAnalyzer(device='cpu')
```

### Model Download Issues

Models are downloaded from HuggingFace on first use. If downloads fail:

```python
# Specify cache directory
analyzer = AudioAnalyzer(cache_dir='/path/to/cache')

# Or pre-download models
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
processor = Wav2Vec2Processor.from_pretrained('facebook/wav2vec2-base-960h')
model = Wav2Vec2ForCTC.from_pretrained('facebook/wav2vec2-base-960h')
```

### Poor Transcription Quality

- Ensure audio is clear and in English (model is English-only)
- Check audio quality (SNR, background noise)
- Verify sample rate is 16kHz (handled automatically)
- Try different audio extraction settings

## Technical Details

### Transcription Algorithm

1. Load audio at 16kHz sample rate
2. Process with Wav2Vec2 feature extractor
3. Forward pass through CTC model
4. Decode logits to text
5. Extract word timestamps using energy-based segmentation

### Emotion Detection

Uses pretrained XLSR-based emotion classifier trained on emotional speech datasets. Recognizes 8 emotion categories based on acoustic features.

### Loudness (LUFS)

Simplified BS.1770 algorithm:
- Calculates mean square energy
- Converts to LUFS using standard formula
- Note: Full BS.1770 requires K-weighting filter

### Hook Detection

Identifies attention moments based on:
- Sudden loudness increases
- Energy spikes
- Spectral changes
- Combines multiple acoustic features

## Limitations

- **Transcription**: English-only (Wav2Vec2-base-960h limitation)
- **Emotion**: Works best with clear speech, single speaker
- **LUFS**: Simplified calculation (not broadcast-compliant)
- **Music Detection**: Heuristic-based (not as accurate as specialized classifiers)

## Future Enhancements

- [ ] Multi-language transcription support
- [ ] Speaker diarization (multiple speakers)
- [ ] Full BS.1770 loudness compliance
- [ ] Advanced music detection (genre classification)
- [ ] Real-time streaming support
- [ ] Batch processing optimization

## References

- **Wav2Vec2**: [facebook/wav2vec2-base-960h](https://huggingface.co/facebook/wav2vec2-base-960h)
- **Emotion Model**: [ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition](https://huggingface.co/ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition)
- **Librosa**: [librosa.org](https://librosa.org/)
- **BS.1770**: ITU-R BS.1770 loudness standard

## License

Part of the GeminiVideo project. See main project LICENSE.
