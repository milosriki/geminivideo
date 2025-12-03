"""
Smart Crop System - Example Usage and Demos

Real-world examples for converting videos to different formats
with intelligent face/object tracking

Author: Pro Video Agent
"""

import sys
from pathlib import Path
from smart_crop import (
    SmartCropTracker,
    AspectRatio,
    FaceDetector,
    ObjectDetector,
    KenBurnsEffect,
    create_smart_crop_pipeline,
    CropRegion
)
import cv2
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_youtube_to_tiktok(input_video: str, output_video: str):
    """
    Example 1: Convert 16:9 YouTube video to 9:16 TikTok format

    Features:
    - Face detection and tracking
    - Smooth pan following subjects
    - Safe zone awareness
    """
    logger.info("Example 1: YouTube to TikTok (16:9 -> 9:16)")
    logger.info(f"Input: {input_video}")
    logger.info(f"Output: {output_video}")

    ffmpeg_cmd = create_smart_crop_pipeline(
        video_path=input_video,
        output_path=output_video,
        target_aspect=AspectRatio.PORTRAIT_9_16,
        output_resolution=(1080, 1920),  # TikTok optimal resolution
        detect_faces=True,
        detect_objects=False,
        detect_motion=True,
        sample_interval=3  # Process every 3rd frame for performance
    )

    logger.info(f"FFmpeg command:\n{ffmpeg_cmd}")
    return ffmpeg_cmd


def example_2_youtube_to_instagram_square(input_video: str, output_video: str):
    """
    Example 2: Convert 16:9 YouTube video to 1:1 Instagram feed

    Features:
    - Face-centered cropping
    - Perfect for Instagram feed posts
    """
    logger.info("Example 2: YouTube to Instagram Square (16:9 -> 1:1)")
    logger.info(f"Input: {input_video}")
    logger.info(f"Output: {output_video}")

    ffmpeg_cmd = create_smart_crop_pipeline(
        video_path=input_video,
        output_path=output_video,
        target_aspect=AspectRatio.SQUARE_1_1,
        output_resolution=(1080, 1080),  # Instagram square
        detect_faces=True,
        detect_objects=False,
        detect_motion=True,
        sample_interval=5
    )

    logger.info(f"FFmpeg command:\n{ffmpeg_cmd}")
    return ffmpeg_cmd


def example_3_youtube_to_instagram_reels(input_video: str, output_video: str):
    """
    Example 3: Convert 16:9 YouTube video to 4:5 Instagram Reels

    Features:
    - Optimized for Instagram Reels
    - Face tracking with motion detection
    """
    logger.info("Example 3: YouTube to Instagram Reels (16:9 -> 4:5)")
    logger.info(f"Input: {input_video}")
    logger.info(f"Output: {output_video}")

    ffmpeg_cmd = create_smart_crop_pipeline(
        video_path=input_video,
        output_path=output_video,
        target_aspect=AspectRatio.PORTRAIT_4_5,
        output_resolution=(1080, 1350),  # Instagram Reels optimal
        detect_faces=True,
        detect_objects=False,
        detect_motion=True,
        sample_interval=3
    )

    logger.info(f"FFmpeg command:\n{ffmpeg_cmd}")
    return ffmpeg_cmd


def example_4_custom_face_tracking(input_video: str):
    """
    Example 4: Custom face tracking with detailed control

    Process video frame-by-frame with custom settings
    """
    logger.info("Example 4: Custom Face Tracking")

    # Initialize tracker with custom settings
    tracker = SmartCropTracker(
        target_aspect=AspectRatio.PORTRAIT_9_16,
        smoothing_window=20,  # More smoothing
        safe_zone_ratio=0.85   # Tighter safe zone
    )

    if not tracker.initialize():
        logger.error("Failed to initialize tracker")
        return

    # Open video
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {input_video}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    logger.info(f"Video: {frame_width}x{frame_height}, {fps} fps, {total_frames} frames")

    # Process frames
    crop_regions = []
    frame_number = 0

    while frame_number < min(total_frames, 300):  # Process first 300 frames
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        crop_region = tracker.process_frame(
            frame,
            frame_number,
            detect_faces=True,
            detect_objects=False,
            detect_motion=True
        )

        crop_regions.append(crop_region)
        frame_number += 1

        if frame_number % 30 == 0:
            logger.info(f"Processed {frame_number}/{total_frames} frames")

    cap.release()

    # Analyze results
    logger.info(f"\nProcessed {len(crop_regions)} frames")
    if crop_regions:
        avg_x = sum(cr.x for cr in crop_regions) / len(crop_regions)
        avg_y = sum(cr.y for cr in crop_regions) / len(crop_regions)
        logger.info(f"Average crop position: ({avg_x:.1f}, {avg_y:.1f})")
        logger.info(f"Crop dimensions: {crop_regions[0].width}x{crop_regions[0].height}")

    return crop_regions


def example_5_object_tracking_product(input_video: str, output_video: str):
    """
    Example 5: Track specific objects (e.g., products in ads)

    Features:
    - YOLO object detection
    - Track specific product categories
    - Perfect for product showcase videos
    """
    logger.info("Example 5: Object Tracking for Product Videos")

    # Target objects for product videos
    target_objects = [
        "bottle", "cup", "laptop", "cell phone", "book",
        "clock", "vase", "scissors", "teddy bear", "handbag"
    ]

    tracker = SmartCropTracker(
        target_aspect=AspectRatio.PORTRAIT_9_16,
        smoothing_window=15
    )

    if not tracker.initialize():
        logger.error("Failed to initialize tracker")
        return

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {input_video}")
        return

    frame_number = 0
    crop_regions = []

    while frame_number < 150:  # Process sample
        ret, frame = cap.read()
        if not ret:
            break

        crop_region = tracker.process_frame(
            frame,
            frame_number,
            detect_faces=False,
            detect_objects=True,  # Enable object detection
            detect_motion=False,
            target_objects=target_objects
        )

        crop_regions.append(crop_region)
        frame_number += 1

    cap.release()

    logger.info(f"Processed {len(crop_regions)} frames with object tracking")
    return crop_regions


def example_6_ken_burns_image(input_image: str, output_video: str):
    """
    Example 6: Create Ken Burns effect on static image

    Features:
    - Cinematic pan and zoom
    - Perfect for image slideshows
    """
    logger.info("Example 6: Ken Burns Effect on Image")

    # Load image
    img = cv2.imread(input_image)
    if img is None:
        logger.error(f"Cannot load image: {input_image}")
        return

    h, w = img.shape[:2]
    logger.info(f"Image dimensions: {w}x{h}")

    # Create Ken Burns effect
    kb = KenBurnsEffect(duration=5.0, fps=30.0)

    # Generate filter with zoom and pan
    kb_filter = kb.generate_effect(
        image_width=w,
        image_height=h,
        target_width=1080,
        target_height=1920,
        zoom_start=1.0,
        zoom_end=1.3,
        pan_start=(0.3, 0.3),  # Start from top-left
        pan_end=(0.7, 0.7)     # Pan to bottom-right
    )

    # FFmpeg command
    ffmpeg_cmd = (
        f"ffmpeg -loop 1 -i {input_image} "
        f"-vf \"{kb_filter}\" "
        f"-c:v libx264 -preset medium -crf 23 "
        f"-t 5 "
        f"{output_video}"
    )

    logger.info(f"FFmpeg command:\n{ffmpeg_cmd}")
    return ffmpeg_cmd


def example_7_multi_format_batch(input_video: str, output_dir: str):
    """
    Example 7: Batch convert to multiple formats

    Convert one video to all major social media formats
    """
    logger.info("Example 7: Multi-Format Batch Conversion")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    formats = {
        "tiktok": {
            "aspect": AspectRatio.PORTRAIT_9_16,
            "resolution": (1080, 1920),
            "suffix": "_tiktok"
        },
        "reels": {
            "aspect": AspectRatio.PORTRAIT_4_5,
            "resolution": (1080, 1350),
            "suffix": "_reels"
        },
        "instagram_feed": {
            "aspect": AspectRatio.SQUARE_1_1,
            "resolution": (1080, 1080),
            "suffix": "_instagram"
        },
        "youtube": {
            "aspect": AspectRatio.LANDSCAPE_16_9,
            "resolution": (1920, 1080),
            "suffix": "_youtube"
        }
    }

    input_path = Path(input_video)
    base_name = input_path.stem

    commands = {}

    for platform, config in formats.items():
        output_file = output_path / f"{base_name}{config['suffix']}.mp4"

        ffmpeg_cmd = create_smart_crop_pipeline(
            video_path=input_video,
            output_path=str(output_file),
            target_aspect=config["aspect"],
            output_resolution=config["resolution"],
            detect_faces=True,
            detect_motion=True,
            sample_interval=5
        )

        commands[platform] = ffmpeg_cmd
        logger.info(f"\n{platform.upper()}: {output_file}")

    return commands


def example_8_action_sports_tracking(input_video: str, output_video: str):
    """
    Example 8: Track action/motion for sports videos

    Features:
    - Motion detection prioritized
    - Fast-moving subject tracking
    - Perfect for sports highlights
    """
    logger.info("Example 8: Action/Sports Tracking")

    tracker = SmartCropTracker(
        target_aspect=AspectRatio.PORTRAIT_9_16,
        smoothing_window=8,  # Less smoothing for faster response
        safe_zone_ratio=0.7   # Wider area for motion
    )

    if not tracker.initialize():
        logger.error("Failed to initialize tracker")
        return

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {input_video}")
        return

    frame_number = 0
    crop_regions = []

    # Prioritize motion detection
    while frame_number < 200:
        ret, frame = cap.read()
        if not ret:
            break

        crop_region = tracker.process_frame(
            frame,
            frame_number,
            detect_faces=False,  # Disable face detection
            detect_objects=False,
            detect_motion=True   # Focus on motion
        )

        crop_regions.append(crop_region)
        frame_number += 1

    cap.release()

    logger.info(f"Tracked {len(crop_regions)} frames of action")
    return crop_regions


def example_9_visualize_tracking(input_video: str, output_video: str):
    """
    Example 9: Visualize crop regions (debug/preview)

    Draw crop region overlay on video to preview tracking
    """
    logger.info("Example 9: Visualize Tracking")

    tracker = SmartCropTracker(
        target_aspect=AspectRatio.PORTRAIT_9_16,
        smoothing_window=15
    )

    if not tracker.initialize():
        logger.error("Failed to initialize tracker")
        return

    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {input_video}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))

    frame_number = 0

    while frame_number < 300:  # Process sample
        ret, frame = cap.read()
        if not ret:
            break

        # Process frame
        crop_region = tracker.process_frame(
            frame,
            frame_number,
            detect_faces=True,
            detect_motion=True
        )

        # Draw crop region
        cv2.rectangle(
            frame,
            (crop_region.x, crop_region.y),
            (crop_region.x + crop_region.width, crop_region.y + crop_region.height),
            (0, 255, 0),  # Green
            3
        )

        # Draw center point
        center_x = crop_region.x + crop_region.width // 2
        center_y = crop_region.y + crop_region.height // 2
        cv2.circle(frame, (center_x, center_y), 10, (0, 0, 255), -1)  # Red

        # Add text
        cv2.putText(
            frame,
            f"Frame: {frame_number}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )

        out.write(frame)
        frame_number += 1

    cap.release()
    out.release()

    logger.info(f"Visualization saved: {output_video}")


def example_10_performance_benchmark():
    """
    Example 10: Performance benchmark

    Test detection and tracking performance
    """
    logger.info("Example 10: Performance Benchmark")

    import time

    # Test face detection
    face_detector = FaceDetector()
    face_detector.load_model()

    # Create test frame
    test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

    # Benchmark face detection
    iterations = 100
    start_time = time.time()

    for i in range(iterations):
        faces = face_detector.detect(test_frame)

    elapsed = time.time() - start_time
    fps_face = iterations / elapsed

    logger.info(f"\nFace Detection Performance:")
    logger.info(f"  Iterations: {iterations}")
    logger.info(f"  Time: {elapsed:.2f} seconds")
    logger.info(f"  FPS: {fps_face:.1f}")

    # Test full pipeline
    tracker = SmartCropTracker(target_aspect=AspectRatio.PORTRAIT_9_16)
    tracker.initialize()

    iterations = 50
    start_time = time.time()

    for i in range(iterations):
        crop_region = tracker.process_frame(
            test_frame,
            i,
            detect_faces=True,
            detect_motion=True
        )

    elapsed = time.time() - start_time
    fps_pipeline = iterations / elapsed

    logger.info(f"\nFull Pipeline Performance:")
    logger.info(f"  Iterations: {iterations}")
    logger.info(f"  Time: {elapsed:.2f} seconds")
    logger.info(f"  FPS: {fps_pipeline:.1f}")

    return {
        "face_detection_fps": fps_face,
        "pipeline_fps": fps_pipeline
    }


def main():
    """Main menu for examples"""
    print("\n" + "="*60)
    print("Smart Crop System - Examples")
    print("="*60)
    print("\nAvailable Examples:")
    print("  1. YouTube to TikTok (16:9 -> 9:16)")
    print("  2. YouTube to Instagram Square (16:9 -> 1:1)")
    print("  3. YouTube to Instagram Reels (16:9 -> 4:5)")
    print("  4. Custom Face Tracking")
    print("  5. Object Tracking for Products")
    print("  6. Ken Burns Effect on Image")
    print("  7. Multi-Format Batch Conversion")
    print("  8. Action/Sports Tracking")
    print("  9. Visualize Tracking (Debug)")
    print(" 10. Performance Benchmark")
    print("\nUsage:")
    print("  python smart_crop_examples.py <example_number> <input_file> [output_file]")
    print("\nExample:")
    print("  python smart_crop_examples.py 1 input.mp4 output_tiktok.mp4")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        main()
    elif sys.argv[1] == "benchmark":
        example_10_performance_benchmark()
    else:
        main()
