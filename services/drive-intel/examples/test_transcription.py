#!/usr/bin/env python3
"""
Example usage of the Whisper Transcription Service

This demonstrates how to use the TranscriptionService for:
1. Basic transcription with timestamps
2. Keyword extraction for hook detection
3. Integration with feature extraction pipeline
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transcription import TranscriptionService
from services.feature_extractor import FeatureExtractorService
import json


def example_1_basic_transcription():
    """Example 1: Basic transcription of a video segment"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Transcription")
    print("=" * 70)

    # Initialize service
    service = TranscriptionService(model_size='base')

    # Example video path (replace with actual video)
    video_path = "/path/to/your/video.mp4"
    start_time = 10.0  # Start at 10 seconds
    end_time = 30.0    # End at 30 seconds

    print(f"\nTranscribing segment: {start_time}s - {end_time}s")
    print(f"Duration: {end_time - start_time}s")

    # Extract transcript
    result = service.extract_transcript(video_path, start_time, end_time)

    if result['success']:
        print("\n✓ Transcription successful!")
        print(f"\nLanguage: {result['language']}")
        print(f"\nTranscript ({len(result['text'])} chars):")
        print("-" * 70)
        print(result['text'])
        print("-" * 70)

        # Show segments with timestamps
        print(f"\nSegments ({len(result['segments'])} total):")
        for i, seg in enumerate(result['segments'][:3], 1):  # Show first 3
            print(f"\n  [{i}] {seg['start']:.2f}s - {seg['end']:.2f}s")
            print(f"      \"{seg['text']}\"")
            print(f"      Confidence: {seg['confidence']:.3f}")

        if len(result['segments']) > 3:
            print(f"\n  ... and {len(result['segments']) - 3} more segments")

        # Show word-level timestamps
        print(f"\nWord-level timestamps ({len(result['words'])} words):")
        for i, word in enumerate(result['words'][:10], 1):  # Show first 10
            print(f"  {word['word']}: {word['start']:.2f}s - {word['end']:.2f}s "
                  f"(prob: {word['probability']:.3f})")

        if len(result['words']) > 10:
            print(f"  ... and {len(result['words']) - 10} more words")

        # Show extracted keywords
        print(f"\nKeywords ({len(result['keywords'])} total):")
        print(f"  {', '.join(result['keywords'][:20])}")

    else:
        print(f"\n✗ Transcription failed: {result['error']}")


def example_2_keyword_extraction():
    """Example 2: Standalone keyword extraction"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Keyword Extraction for Hook Detection")
    print("=" * 70)

    service = TranscriptionService()

    # Sample transcript
    sample_text = """
    This is an amazing discovery that will change everything you know about
    video editing. Today I'm revealing the secret technique that professional
    editors never talk about. You won't believe how simple this hack is, but
    it's absolutely critical for creating viral content. This is a game changer.
    """

    print(f"\nSample text:")
    print("-" * 70)
    print(sample_text.strip())
    print("-" * 70)

    # Extract keywords
    keywords = service.extract_keywords(sample_text, max_keywords=15)

    print(f"\nExtracted keywords ({len(keywords)} total):")
    print(f"  {', '.join(keywords)}")
    print("\nNote: Hook indicator words (amazing, secret, revealed, etc.) are boosted")


def example_3_feature_extraction_integration():
    """Example 3: Full feature extraction with transcription"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Integration with Feature Extraction Pipeline")
    print("=" * 70)

    # Initialize feature extractor (includes transcription service)
    extractor = FeatureExtractorService()

    # Example video
    video_path = "/path/to/your/video.mp4"
    start_time = 5.0
    end_time = 15.0

    print(f"\nExtracting all features for segment: {start_time}s - {end_time}s")
    print("This includes:")
    print("  - Motion score (frame differencing)")
    print("  - Object detection (YOLO)")
    print("  - Text detection (OCR)")
    print("  - Audio transcription (Whisper)")
    print("  - Semantic embeddings (sentence-transformers)")

    # Extract all features
    features = extractor.extract_features(video_path, start_time, end_time)

    print("\nExtracted features:")
    print(f"  Motion score: {features.motion_score:.3f}")
    print(f"  Objects detected: {len(features.objects)}")
    print(f"  Text detected: {len(features.text_detected)}")
    print(f"  Transcript length: {len(features.transcript)} chars")
    print(f"  Embedding dimensions: {len(features.embedding) if features.embedding else 0}")

    if features.transcript:
        print(f"\nTranscript preview:")
        print(f"  \"{features.transcript[:200]}...\"")


def example_4_search_transcript():
    """Example 4: Search within transcript"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Search Transcript for Keywords")
    print("=" * 70)

    service = TranscriptionService()

    # Assume we have a transcript result from previous extraction
    segments = [
        {'text': 'Welcome to this amazing video tutorial', 'start': 0.0, 'end': 2.5},
        {'text': 'Today we will learn about video editing', 'start': 2.5, 'end': 5.0},
        {'text': 'This technique is amazing and powerful', 'start': 5.0, 'end': 7.5},
    ]

    query = "amazing"

    print(f"\nSearching for: '{query}'")
    print(f"In {len(segments)} segments")

    # Search
    results = service.search_transcript(segments, query, case_sensitive=False)

    print(f"\nFound {len(results)} matches:")
    for seg, positions in results:
        print(f"\n  {seg['start']:.2f}s - {seg['end']:.2f}s")
        print(f"  \"{seg['text']}\"")
        print(f"  Match positions: {positions}")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("WHISPER TRANSCRIPTION SERVICE - USAGE EXAMPLES")
    print("=" * 70)
    print("\nNote: These examples require:")
    print("  1. FFmpeg installed (for audio extraction)")
    print("  2. openai-whisper package (pip install openai-whisper)")
    print("  3. A valid video file path")
    print("\n" + "=" * 70)

    try:
        # Run examples (commented out by default - uncomment to test with real video)
        # example_1_basic_transcription()
        example_2_keyword_extraction()
        # example_3_feature_extraction_integration()
        example_4_search_transcript()

        print("\n" + "=" * 70)
        print("EXAMPLES COMPLETED")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
