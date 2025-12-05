"""
Test Beat-Sync Rendering - €5M Investment Grade
==============================================

This script demonstrates the beat-sync functionality that automatically
cuts video clips on music beats using librosa beat detection.

PRODUCTION FEATURES:
- Automatic beat detection using librosa.beat.beat_track()
- Video cuts synchronized to music beats
- Multi-clip stitching with beat-aligned transitions
- Platform-optimized output (Instagram, TikTok, YouTube)
- GPU-accelerated rendering with ProRenderer

USAGE:
    python test_beat_sync.py --video-clips clip1.mp4 clip2.mp4 --audio music.mp3
"""

import requests
import json
import time
import sys
import argparse
from pathlib import Path


def test_beat_sync_endpoint(
    video_clips: list,
    audio_path: str,
    platform: str = "instagram",
    quality: str = "high",
    api_url: str = "http://localhost:8002"
):
    """
    Test the /api/video/beat-sync-render endpoint

    Args:
        video_clips: List of video clip paths
        audio_path: Path to audio/music file
        platform: Target platform (instagram/tiktok/youtube)
        quality: Quality preset (draft/standard/high/master)
        api_url: Video agent API URL
    """

    print("=" * 70)
    print("BEAT-SYNC RENDERING TEST - €5M Investment Platform")
    print("=" * 70)
    print()

    # Prepare request
    request_data = {
        "video_clips": video_clips,
        "audio_path": audio_path,
        "platform": platform,
        "quality": quality,
        "aspect_ratio": "9:16",
        "async_mode": True
    }

    print("📋 Request Configuration:")
    print(f"   Video Clips: {len(video_clips)}")
    for i, clip in enumerate(video_clips):
        print(f"      {i+1}. {Path(clip).name}")
    print(f"   Audio: {Path(audio_path).name}")
    print(f"   Platform: {platform}")
    print(f"   Quality: {quality}")
    print()

    # Submit request
    print("🚀 Submitting beat-sync render request...")
    try:
        response = requests.post(
            f"{api_url}/api/video/beat-sync-render",
            json=request_data,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        job_id = result.get("job_id")

        print(f"✅ Request accepted!")
        print(f"   Job ID: {job_id}")
        print(f"   Status URL: {api_url}{result.get('status_url')}")
        print()

        # Poll for status
        print("⏳ Polling for completion...")
        print()

        max_polls = 120  # 10 minutes max
        poll_interval = 5  # seconds

        for i in range(max_polls):
            status_response = requests.get(
                f"{api_url}/api/pro/job/{job_id}",
                timeout=10
            )
            status_response.raise_for_status()

            status_data = status_response.json()
            job_status = status_data.get("status")
            job_data = status_data.get("data", {})

            progress = job_data.get("progress", 0)
            message = job_data.get("message", "Processing...")

            # Progress bar
            bar_length = 40
            filled = int(bar_length * progress / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(f"\r   [{bar}] {progress:.0f}% - {message}", end="", flush=True)

            if job_status == "completed":
                print()
                print()
                print("=" * 70)
                print("✅ BEAT-SYNC RENDER COMPLETED!")
                print("=" * 70)
                print()

                # Print results
                output_path = job_data.get("output_path")
                beat_info = job_data.get("beat_info", {})
                config = job_data.get("config", {})

                print("📊 Beat Detection Results:")
                print(f"   Tempo: {beat_info.get('tempo_bpm', 0):.1f} BPM")
                print(f"   Beats Detected: {beat_info.get('num_beats', 0)}")
                print(f"   Audio Duration: {beat_info.get('audio_duration', 0):.2f}s")
                print()

                print("🎬 Render Configuration:")
                print(f"   Clips Used: {config.get('num_clips', 0)}")
                print(f"   Platform: {config.get('platform', 'unknown')}")
                print(f"   Quality: {config.get('quality', 'unknown')}")
                print(f"   Aspect Ratio: {config.get('aspect_ratio', 'unknown')}")
                print()

                print("📁 Output:")
                print(f"   Path: {output_path}")
                print()

                # Show beat times (first 10)
                beat_times = beat_info.get("beat_times", [])[:10]
                if beat_times:
                    print("🎵 First 10 Beat Timestamps:")
                    for i, beat_time in enumerate(beat_times):
                        print(f"   Beat {i+1}: {beat_time:.3f}s")
                    print()

                return True

            elif job_status == "failed":
                print()
                print()
                print("❌ Render failed!")
                error = job_data.get("error", "Unknown error")
                print(f"   Error: {error}")
                return False

            time.sleep(poll_interval)

        print()
        print("⏱️ Timeout waiting for render completion")
        return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_beat_sync_in_campaign(
    campaign_id: str,
    audio_path: str,
    api_url: str = "http://localhost:8000"
):
    """
    Test beat-sync integration in campaign rendering

    Args:
        campaign_id: Campaign ID from generate-campaign
        audio_path: Path to music file
        api_url: Titan Core API URL
    """

    print("=" * 70)
    print("BEAT-SYNC IN CAMPAIGN TEST - €5M Investment Platform")
    print("=" * 70)
    print()

    # Prepare render request with beat-sync enabled
    render_request = {
        "campaign_id": campaign_id,
        "blueprint_ids": [],  # Empty = render all approved
        "platform": "instagram_reels",
        "quality": "HIGH",
        "add_captions": True,
        "caption_style": "hormozi",
        "smart_crop": True,
        "use_beat_sync": True,
        "audio_path": audio_path
    }

    print("📋 Render Configuration:")
    print(f"   Campaign ID: {campaign_id}")
    print(f"   Audio: {Path(audio_path).name}")
    print(f"   Beat-Sync: ENABLED")
    print(f"   Captions: ENABLED (Hormozi style)")
    print(f"   Smart Crop: ENABLED")
    print()

    # Submit render request
    print("🚀 Submitting campaign render with beat-sync...")
    try:
        response = requests.post(
            f"{api_url}/pipeline/render-winners",
            json=render_request,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()

        print(f"✅ Render jobs queued!")
        print(f"   Total Jobs: {result.get('total_jobs', 0)}")
        print(f"   Estimated Time: {result.get('estimated_time_seconds', 0)}s")
        print(f"   Status URL: {api_url}{result.get('status_url')}")
        print()

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test Beat-Sync Rendering for €5M Investment Platform"
    )
    parser.add_argument(
        "--video-clips",
        nargs="+",
        help="Paths to video clips (space-separated)"
    )
    parser.add_argument(
        "--audio",
        help="Path to audio/music file"
    )
    parser.add_argument(
        "--platform",
        choices=["instagram", "tiktok", "youtube", "facebook"],
        default="instagram",
        help="Target platform"
    )
    parser.add_argument(
        "--quality",
        choices=["draft", "standard", "high", "master"],
        default="high",
        help="Render quality"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8002",
        help="Video agent API URL"
    )
    parser.add_argument(
        "--campaign-mode",
        action="store_true",
        help="Test beat-sync in campaign rendering"
    )
    parser.add_argument(
        "--campaign-id",
        help="Campaign ID for campaign mode"
    )

    args = parser.parse_args()

    if args.campaign_mode:
        if not args.campaign_id or not args.audio:
            print("❌ Campaign mode requires --campaign-id and --audio")
            sys.exit(1)

        success = test_beat_sync_in_campaign(
            campaign_id=args.campaign_id,
            audio_path=args.audio,
            api_url=args.api_url.replace(":8002", ":8000")  # Use titan-core port
        )
    else:
        if not args.video_clips or not args.audio:
            print("❌ Direct mode requires --video-clips and --audio")
            print()
            print("Example:")
            print("  python test_beat_sync.py \\")
            print("    --video-clips clip1.mp4 clip2.mp4 clip3.mp4 \\")
            print("    --audio music.mp3 \\")
            print("    --platform instagram \\")
            print("    --quality high")
            sys.exit(1)

        success = test_beat_sync_endpoint(
            video_clips=args.video_clips,
            audio_path=args.audio,
            platform=args.platform,
            quality=args.quality,
            api_url=args.api_url
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
