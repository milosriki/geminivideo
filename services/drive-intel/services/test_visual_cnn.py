"""
Test Visual CNN Pattern Analyzer
Agent 18: Verification tests for production-grade visual analysis
"""
import numpy as np
import cv2
import logging
from visual_cnn import VisualPatternAnalyzer, VisualPattern, PatternResult, FrameFeatures

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """Create a synthetic test frame"""
    frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    # Add some structure (circle in center)
    cv2.circle(frame, (width//2, height//2), 100, (255, 0, 0), -1)
    return frame


def test_feature_extraction():
    """Test CNN feature extraction"""
    logger.info("Testing feature extraction...")

    analyzer = VisualPatternAnalyzer()
    frame = create_test_frame()

    # Single frame extraction
    features = analyzer.extract_features(frame)
    assert features.shape == (2048,), f"Expected (2048,) got {features.shape}"
    assert features.dtype == np.float32
    logger.info(f"✓ Feature extraction: shape={features.shape}, mean={np.mean(features):.4f}")

    # Batch extraction
    frames = [create_test_frame() for _ in range(5)]
    batch_features = analyzer.extract_features_batch(frames)
    assert batch_features.shape == (5, 2048), f"Expected (5, 2048) got {batch_features.shape}"
    logger.info(f"✓ Batch feature extraction: shape={batch_features.shape}")


def test_pattern_classification():
    """Test visual pattern classification"""
    logger.info("Testing pattern classification...")

    analyzer = VisualPatternAnalyzer()
    frame = create_test_frame()

    # Classify single frame
    scores = analyzer.classify_frame(frame)
    assert len(scores) == 12, f"Expected 12 patterns, got {len(scores)}"
    assert all(0 <= score <= 1 for score in scores.values())
    assert abs(sum(scores.values()) - 1.0) < 0.01, "Scores should sum to ~1.0"

    logger.info(f"✓ Frame classification: {len(scores)} patterns")
    logger.info(f"  Top pattern: {max(scores.items(), key=lambda x: x[1])}")


def test_face_detection():
    """Test face detection"""
    logger.info("Testing face detection...")

    analyzer = VisualPatternAnalyzer()
    frame = create_test_frame()

    faces = analyzer.detect_faces(frame)
    logger.info(f"✓ Face detection: {len(faces)} faces detected")

    # Test emotion analysis (placeholder)
    emotions = analyzer.analyze_face_emotions(frame)
    logger.info(f"✓ Emotion analysis: {len(emotions)} faces analyzed")


def test_text_detection():
    """Test text region detection"""
    logger.info("Testing text detection...")

    analyzer = VisualPatternAnalyzer()
    frame = create_test_frame()

    text_regions = analyzer.detect_text_regions(frame)
    logger.info(f"✓ Text detection: {len(text_regions)} regions found")

    text_density = analyzer.calculate_text_density(frame)
    assert 0 <= text_density <= 1.0
    logger.info(f"✓ Text density: {text_density:.4f}")


def test_color_analysis():
    """Test color extraction"""
    logger.info("Testing color analysis...")

    analyzer = VisualPatternAnalyzer()
    frame = create_test_frame()

    colors = analyzer.extract_dominant_colors(frame, n_colors=5)
    assert len(colors) == 5, f"Expected 5 colors, got {len(colors)}"

    for color, percentage in colors:
        assert color.startswith('#'), f"Invalid hex color: {color}"
        assert 0 <= percentage <= 1.0

    logger.info(f"✓ Color extraction: {len(colors)} dominant colors")
    for i, (color, pct) in enumerate(colors[:3], 1):
        logger.info(f"  {i}. {color} ({pct*100:.1f}%)")


def test_composition_analysis():
    """Test frame composition analysis"""
    logger.info("Testing composition analysis...")

    analyzer = VisualPatternAnalyzer()
    frame = create_test_frame()

    composition = analyzer.analyze_frame_composition(frame)

    required_keys = ['complexity', 'edge_density', 'brightness', 'contrast', 'saturation']
    for key in required_keys:
        assert key in composition, f"Missing key: {key}"
        assert 0 <= composition[key] <= 1.0, f"Invalid range for {key}: {composition[key]}"

    logger.info(f"✓ Composition analysis:")
    logger.info(f"  Complexity: {composition['complexity']:.3f}")
    logger.info(f"  Brightness: {composition['brightness']:.3f}")
    logger.info(f"  Contrast: {composition['contrast']:.3f}")
    logger.info(f"  Saturation: {composition['saturation']:.3f}")


def test_visual_patterns_enum():
    """Test visual pattern enumeration"""
    logger.info("Testing visual pattern enumeration...")

    patterns = [p for p in VisualPattern]
    assert len(patterns) == 12, f"Expected 12 patterns, got {len(patterns)}"

    logger.info(f"✓ Visual patterns ({len(patterns)}):")
    for pattern in patterns:
        logger.info(f"  - {pattern.value}")


def test_device_detection():
    """Test device auto-detection"""
    logger.info("Testing device detection...")

    # Test auto-detection
    analyzer = VisualPatternAnalyzer()
    logger.info(f"✓ Auto-detected device: {analyzer.device}")

    # Test explicit CPU
    analyzer_cpu = VisualPatternAnalyzer(device='cpu')
    assert str(analyzer_cpu.device) == 'cpu'
    logger.info(f"✓ Explicit CPU device: {analyzer_cpu.device}")


def test_pattern_result_dataclass():
    """Test PatternResult dataclass"""
    logger.info("Testing PatternResult dataclass...")

    result = PatternResult(
        primary_pattern=VisualPattern.TALKING_HEAD,
        pattern_confidences={'talking_head': 0.85},
        visual_complexity=0.6,
        text_density=0.2,
        face_count=1,
        dominant_colors=['#ff0000', '#00ff00'],
        motion_score=0.4,
        scene_count=3,
        avg_scene_duration=2.5
    )

    # Test to_dict conversion
    result_dict = result.to_dict()
    assert result_dict['primary_pattern'] == 'talking_head'
    assert isinstance(result_dict, dict)

    logger.info(f"✓ PatternResult dataclass:")
    logger.info(f"  Primary pattern: {result.primary_pattern.value}")
    logger.info(f"  Face count: {result.face_count}")
    logger.info(f"  Scene count: {result.scene_count}")


def test_frame_features_dataclass():
    """Test FrameFeatures dataclass"""
    logger.info("Testing FrameFeatures dataclass...")

    features = FrameFeatures(
        embedding=np.random.randn(2048),
        faces_detected=2,
        text_regions=3,
        brightness=0.6,
        contrast=0.5,
        saturation=0.4,
        edge_density=0.3,
        dominant_color='#ff0000'
    )

    # Test to_dict conversion
    features_dict = features.to_dict()
    assert 'embedding_shape' in features_dict
    assert features_dict['faces_detected'] == 2

    logger.info(f"✓ FrameFeatures dataclass:")
    logger.info(f"  Faces: {features.faces_detected}")
    logger.info(f"  Text regions: {features.text_regions}")
    logger.info(f"  Dominant color: {features.dominant_color}")


def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("VISUAL CNN PATTERN ANALYZER - TEST SUITE")
    logger.info("Agent 18: Production-grade visual analysis")
    logger.info("=" * 60)

    tests = [
        test_visual_patterns_enum,
        test_device_detection,
        test_pattern_result_dataclass,
        test_frame_features_dataclass,
        test_feature_extraction,
        test_pattern_classification,
        test_face_detection,
        test_text_detection,
        test_color_analysis,
        test_composition_analysis,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            logger.info("")
            test()
            passed += 1
        except Exception as e:
            logger.error(f"✗ Test failed: {test.__name__}")
            logger.error(f"  Error: {e}")
            failed += 1

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"TEST RESULTS: {passed} passed, {failed} failed")
    logger.info("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
