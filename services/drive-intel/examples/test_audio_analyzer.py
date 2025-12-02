"""
Test script for AudioAnalyzer service.
Demonstrates real Wav2Vec2-based audio analysis.
"""
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.audio_analyzer import AudioAnalyzer, AudioAnalysis
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_transcription(analyzer: AudioAnalyzer, audio_path: str):
    """Test audio transcription."""
    print("\n" + "=" * 60)
    print("TRANSCRIPTION TEST")
    print("=" * 60)

    try:
        transcript = analyzer.transcribe(audio_path)

        print(f"Text: {transcript.text}")
        print(f"Duration: {transcript.duration:.2f}s")
        print(f"Language: {transcript.language}")
        print(f"Confidence: {transcript.confidence:.3f}")
        print(f"Word count: {len(transcript.words)}")

        if transcript.words:
            print("\nFirst 5 words with timestamps:")
            for word_data in transcript.words[:5]:
                print(f"  {word_data['word']:15} "
                      f"{word_data['start']:.2f}s - {word_data['end']:.2f}s "
                      f"(conf: {word_data['confidence']:.2f})")

        return transcript

    except Exception as e:
        logger.error(f"Transcription test failed: {e}")
        return None


def test_emotion_detection(analyzer: AudioAnalyzer, audio_path: str):
    """Test emotion detection."""
    print("\n" + "=" * 60)
    print("EMOTION DETECTION TEST")
    print("=" * 60)

    try:
        emotion, confidence = analyzer.detect_speech_emotion(audio_path)

        print(f"Detected Emotion: {emotion}")
        print(f"Confidence: {confidence:.3f}")

        return emotion, confidence

    except Exception as e:
        logger.error(f"Emotion detection test failed: {e}")
        return None, 0.0


def test_pacing_analysis(analyzer: AudioAnalyzer, audio_path: str):
    """Test pacing analysis."""
    print("\n" + "=" * 60)
    print("PACING ANALYSIS TEST")
    print("=" * 60)

    try:
        pacing = analyzer.analyze_pacing(audio_path)

        print(f"Words per minute: {pacing.words_per_minute:.1f}")
        print(f"Average pause duration: {pacing.avg_pause_duration:.2f}s")
        print(f"Pause count: {pacing.pause_count}")
        print(f"Speech ratio: {pacing.speech_ratio:.2%}")
        print(f"Energy profile length: {len(pacing.energy_profile)}")

        return pacing

    except Exception as e:
        logger.error(f"Pacing analysis test failed: {e}")
        return None


def test_music_vs_speech(analyzer: AudioAnalyzer, audio_path: str):
    """Test music vs speech detection."""
    print("\n" + "=" * 60)
    print("MUSIC VS SPEECH DETECTION TEST")
    print("=" * 60)

    try:
        music_ratio, speech_ratio = analyzer.detect_music_vs_speech(audio_path)

        print(f"Music presence: {music_ratio:.2%}")
        print(f"Speech presence: {speech_ratio:.2%}")

        segments = analyzer.segment_audio(audio_path)
        print(f"\nAudio segments: {len(segments)}")
        for i, seg in enumerate(segments[:10]):  # Show first 10
            print(f"  {i+1}. {seg['type']:10} "
                  f"{seg['start']:.2f}s - {seg['end']:.2f}s "
                  f"(duration: {seg['end'] - seg['start']:.2f}s)")

        return music_ratio, speech_ratio

    except Exception as e:
        logger.error(f"Music vs speech test failed: {e}")
        return 0.0, 0.0


def test_loudness_analysis(analyzer: AudioAnalyzer, audio_path: str):
    """Test loudness analysis."""
    print("\n" + "=" * 60)
    print("LOUDNESS ANALYSIS TEST")
    print("=" * 60)

    try:
        lufs = analyzer.calculate_loudness_lufs(audio_path)
        print(f"Integrated loudness: {lufs:.2f} LUFS")

        profile = analyzer.calculate_loudness_profile(audio_path)
        print(f"Loudness profile points: {len(profile)}")
        if profile:
            print(f"  Min: {min(profile):.2f} dB")
            print(f"  Max: {max(profile):.2f} dB")
            print(f"  Mean: {sum(profile)/len(profile):.2f} dB")

        peaks = analyzer.detect_loudness_peaks(audio_path)
        print(f"\nLoudness peaks detected: {len(peaks)}")
        for i, peak_time in enumerate(peaks[:5]):
            print(f"  Peak {i+1}: {peak_time:.2f}s")

        return lufs

    except Exception as e:
        logger.error(f"Loudness analysis test failed: {e}")
        return -70.0


def test_hook_detection(analyzer: AudioAnalyzer, audio_path: str):
    """Test hook detection."""
    print("\n" + "=" * 60)
    print("HOOK DETECTION TEST")
    print("=" * 60)

    try:
        hook_time = analyzer.detect_hook_timing(audio_path)
        print(f"First hook at: {hook_time:.2f}s")

        moments = analyzer.detect_attention_moments(audio_path)
        print(f"\nAttention moments detected: {len(moments)}")
        for i, moment in enumerate(moments[:5]):
            print(f"  {i+1}. {moment['type']:20} at {moment['time']:.2f}s "
                  f"(intensity: {moment['intensity']:.3f})")

        return hook_time

    except Exception as e:
        logger.error(f"Hook detection test failed: {e}")
        return 0.0


def test_audio_quality(analyzer: AudioAnalyzer, audio_path: str):
    """Test audio quality assessment."""
    print("\n" + "=" * 60)
    print("AUDIO QUALITY ASSESSMENT TEST")
    print("=" * 60)

    try:
        quality = analyzer.assess_audio_quality(audio_path)

        print(f"Overall quality score: {quality['overall_score']:.1f}/100")
        print(f"Noise level: {quality['noise_level']:.3f}")
        print(f"Dynamic range: {quality['dynamic_range']:.3f}")
        print(f"Clipping ratio: {quality['clipping_ratio']:.3f}")
        print(f"Spectral flatness: {quality['spectral_flatness']:.3f}")

        noise = analyzer.detect_background_noise(audio_path)
        print(f"\nBackground noise: {noise:.3f}")

        return quality

    except Exception as e:
        logger.error(f"Audio quality test failed: {e}")
        return {}


def test_full_analysis(analyzer: AudioAnalyzer, audio_path: str):
    """Test full audio analysis."""
    print("\n" + "=" * 60)
    print("FULL AUDIO ANALYSIS TEST")
    print("=" * 60)

    try:
        analysis = analyzer.analyze(audio_path)

        print("\nTRANSCRIPT:")
        print(f"  Text: {analysis.transcript.text[:100]}...")
        print(f"  Duration: {analysis.transcript.duration:.2f}s")
        print(f"  Confidence: {analysis.transcript.confidence:.3f}")

        print("\nPACING:")
        print(f"  WPM: {analysis.pacing.words_per_minute:.1f}")
        print(f"  Speech ratio: {analysis.pacing.speech_ratio:.2%}")
        print(f"  Pause count: {analysis.pacing.pause_count}")

        print("\nEMOTION:")
        print(f"  {analysis.emotion} ({analysis.emotion_confidence:.3f})")

        print("\nCONTENT:")
        print(f"  Music presence: {analysis.music_presence:.2%}")
        print(f"  Speech presence: {analysis.speech_presence:.2%}")

        print("\nAUDIO QUALITY:")
        print(f"  Loudness: {analysis.loudness_lufs:.2f} LUFS")
        print(f"  Quality score: {analysis.audio_quality_score:.1f}/100")
        print(f"  Hook timing: {analysis.hook_timing:.2f}s")

        return analysis

    except Exception as e:
        logger.error(f"Full analysis test failed: {e}")
        return None


def main():
    """Run audio analyzer tests."""
    print("=" * 60)
    print("AUDIO ANALYZER TEST SUITE")
    print("=" * 60)

    # Check for test audio file
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
    else:
        print("\nUsage: python test_audio_analyzer.py <audio_file>")
        print("\nNo audio file provided. Using synthetic test...")

        # Create a synthetic audio file for testing
        import numpy as np
        import tempfile
        import scipy.io.wavfile as wavfile

        print("\nGenerating synthetic test audio (5 seconds)...")
        sample_rate = 16000
        duration = 5.0
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Generate speech-like signal (mix of frequencies)
        signal = np.sin(2 * np.pi * 200 * t)  # Fundamental
        signal += 0.5 * np.sin(2 * np.pi * 400 * t)  # Harmonic
        signal += 0.3 * np.sin(2 * np.pi * 600 * t)  # Harmonic

        # Add some noise
        signal += 0.1 * np.random.randn(len(signal))

        # Normalize
        signal = signal / np.max(np.abs(signal)) * 0.8

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_path = temp_file.name
        temp_file.close()

        wavfile.write(audio_path, sample_rate, (signal * 32767).astype(np.int16))
        print(f"Created test audio: {audio_path}")

    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        return

    print(f"\nAnalyzing audio file: {audio_path}")

    # Initialize analyzer
    print("\nInitializing AudioAnalyzer...")
    analyzer = AudioAnalyzer()

    # Run tests
    try:
        # Individual component tests
        test_transcription(analyzer, audio_path)
        test_emotion_detection(analyzer, audio_path)
        test_pacing_analysis(analyzer, audio_path)
        test_music_vs_speech(analyzer, audio_path)
        test_loudness_analysis(analyzer, audio_path)
        test_hook_detection(analyzer, audio_path)
        test_audio_quality(analyzer, audio_path)

        # Full analysis test
        test_full_analysis(analyzer, audio_path)

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)

    # Clean up synthetic audio if created
    if len(sys.argv) <= 1 and os.path.exists(audio_path):
        try:
            os.unlink(audio_path)
            print(f"\nCleaned up test audio: {audio_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up test audio: {e}")


if __name__ == "__main__":
    main()
