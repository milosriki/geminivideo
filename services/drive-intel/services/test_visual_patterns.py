"""
Test and example usage of Visual Pattern Extractor
Agent 3: CNN-based visual pattern extraction

This demonstrates the capabilities of the VisualPatternExtractor
"""
import cv2
import numpy as np
import logging
from visual_patterns import VisualPatternExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_single_frame_analysis():
    """Test visual pattern extraction on a single frame"""
    print("\n" + "="*80)
    print("TEST 1: Single Frame Analysis")
    print("="*80)

    # Initialize extractor
    extractor = VisualPatternExtractor()

    # Create a test frame (random noise for demonstration)
    test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

    # Extract features
    print("\nExtracting 2048-dim feature vector...")
    features = extractor.extract_features(test_frame)
    print(f"Feature vector shape: {features.shape}")
    print(f"Feature vector stats - mean: {features.mean():.4f}, std: {features.std():.4f}")

    # Classify visual pattern
    print("\nClassifying visual pattern...")
    result = extractor.classify_visual_pattern(test_frame)
    print(f"Primary pattern: {result.primary_pattern}")
    print(f"Confidence: {result.confidence:.4f}")
    print(f"Visual energy: {result.visual_energy:.4f}")
    print("\nTop 5 pattern scores:")
    sorted_scores = sorted(result.all_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    for pattern, score in sorted_scores:
        print(f"  {pattern}: {score:.4f}")

    # Detailed analysis
    print("\nDetailed analysis...")
    detailed = extractor.analyze_single_frame_detailed(test_frame)
    print(f"\nPrimary pattern: {detailed['primary_pattern']}")
    print(f"Description: {detailed['primary_description']}")
    print(f"\nTop 3 patterns:")
    for p in detailed['top_3_patterns']:
        print(f"  {p['pattern']}: {p['score']:.4f} - {p['description']}")


def test_batch_processing():
    """Test batch processing of multiple frames"""
    print("\n" + "="*80)
    print("TEST 2: Batch Processing")
    print("="*80)

    extractor = VisualPatternExtractor()

    # Create batch of test frames
    num_frames = 10
    frames = [
        np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        for _ in range(num_frames)
    ]

    print(f"\nProcessing batch of {num_frames} frames...")
    features_batch = extractor.extract_features_batch(frames)
    print(f"Batch features shape: {features_batch.shape}")
    print(f"Batch features stats - mean: {features_batch.mean():.4f}, std: {features_batch.std():.4f}")


def test_sequence_analysis():
    """Test video sequence analysis"""
    print("\n" + "="*80)
    print("TEST 3: Video Sequence Analysis")
    print("="*80)

    extractor = VisualPatternExtractor()

    # Create sequence of frames (simulating different patterns)
    num_frames = 30
    frames = []

    print(f"\nGenerating sequence of {num_frames} frames...")
    for i in range(num_frames):
        # Vary the content to simulate pattern changes
        if i < 10:
            # First third - darker frames
            frame = np.random.randint(0, 128, (720, 1280, 3), dtype=np.uint8)
        elif i < 20:
            # Middle third - brighter frames
            frame = np.random.randint(128, 255, (720, 1280, 3), dtype=np.uint8)
        else:
            # Last third - medium brightness
            frame = np.random.randint(64, 192, (720, 1280, 3), dtype=np.uint8)
        frames.append(frame)

    # Analyze sequence
    print("\nAnalyzing video sequence...")
    analysis = extractor.analyze_video_sequence(frames, sample_rate=1)

    print(f"\nSequence Analysis Results:")
    print(f"Frame count: {analysis.frame_count}")
    print(f"Dominant pattern: {analysis.dominant_pattern}")
    print(f"Average confidence: {analysis.average_confidence:.4f}")
    print(f"Average visual energy: {analysis.average_visual_energy:.4f}")
    print(f"Temporal consistency: {analysis.temporal_consistency:.4f}")
    print(f"Number of transitions: {len(analysis.pattern_transitions)}")

    print("\nPattern distribution:")
    for pattern, percentage in sorted(
        analysis.pattern_distribution.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        print(f"  {pattern}: {percentage*100:.1f}%")

    if analysis.pattern_transitions:
        print("\nPattern transitions:")
        for i, transition in enumerate(analysis.pattern_transitions[:5], 1):
            print(f"  {i}. Frame {transition['frame_index']}: "
                  f"{transition['from_pattern']} -> {transition['to_pattern']} "
                  f"(confidence: {transition['to_confidence']:.4f})")


def test_visual_patterns_descriptions():
    """Test pattern descriptions"""
    print("\n" + "="*80)
    print("TEST 4: Visual Pattern Descriptions")
    print("="*80)

    extractor = VisualPatternExtractor()

    print("\nAll 10 Visual Patterns:")
    for i, pattern in enumerate(extractor.VISUAL_PATTERNS, 1):
        description = extractor.get_pattern_description(pattern)
        print(f"{i}. {pattern}")
        print(f"   {description}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("Visual Pattern Extractor - Test Suite")
    print("Agent 3: CNN-based visual pattern extraction using ResNet-50")
    print("="*80)

    try:
        test_visual_patterns_descriptions()
        test_single_frame_analysis()
        test_batch_processing()
        test_sequence_analysis()

        print("\n" + "="*80)
        print("All tests completed successfully!")
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print("\n" + "="*80)
        print(f"Tests failed with error: {e}")
        print("="*80 + "\n")


if __name__ == "__main__":
    main()
