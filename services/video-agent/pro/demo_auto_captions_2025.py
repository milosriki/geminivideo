"""
DEMO: Auto-Caption System 2025 Edition
Showcases all new features including Whisper V3 Turbo, Distil-Whisper, and advanced capabilities.

Run this script to see examples of:
- V3 Turbo (8x faster)
- Distil-Whisper preview mode (6x faster)
- Real-time transcription
- Batch processing
- Multi-language translation
- Speaker diarization
"""

import os
import asyncio
from pathlib import Path
from auto_captions import (
    AutoCaptionSystem,
    WhisperModelSize,
    WhisperBackend,
    CaptionStyle,
    TranscriptionMode,
    GPUMemoryManager,
    compare_model_speeds
)


def demo_1_basic_usage():
    """Demo 1: Basic usage with V3 Turbo (8x faster!)"""
    print("\n" + "="*80)
    print("DEMO 1: Basic Usage with Whisper V3 Turbo (8x faster!)")
    print("="*80)

    # Create system with V3 Turbo (default)
    system = AutoCaptionSystem()

    print("\n✓ System initialized with Whisper V3 Turbo")
    print("  This is 8x faster than Large V3 with same accuracy!")

    # Check GPU
    if os.path.exists("cuda"):
        print(f"✓ GPU available: {GPUMemoryManager.get_available_memory():.1f}GB")
    else:
        print("ℹ Running on CPU (slower but works)")

    # Process video (you'll need to provide a real video path)
    # result = system.process_video(
    #     video_path="sample_video.mp4",
    #     caption_style=CaptionStyle.HORMOZI
    # )


def demo_2_fast_preview():
    """Demo 2: Fast preview mode with Distil-Whisper (6x faster!)"""
    print("\n" + "="*80)
    print("DEMO 2: Fast Preview Mode with Distil-Whisper (6x faster!)")
    print("="*80)

    # Create system
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.LARGE_V3_TURBO
    )

    print("\n✓ System ready for fast preview mode")
    print("  Uses Distil-Whisper for ultra-fast transcription")
    print("  Perfect for client reviews and quick previews")

    # Fast preview
    # result = system.process_video_fast_preview(
    #     video_path="sample_video.mp4"
    # )
    # print(f"\n✓ Preview generated in seconds!")


def demo_3_model_comparison():
    """Demo 3: Compare different model speeds"""
    print("\n" + "="*80)
    print("DEMO 3: Model Speed Comparison")
    print("="*80)

    print(compare_model_speeds())


def demo_4_speaker_diarization():
    """Demo 4: Speaker diarization (who is speaking)"""
    print("\n" + "="*80)
    print("DEMO 4: Speaker Diarization (Who Is Speaking)")
    print("="*80)

    # Check if HF token is available
    hf_token = os.environ.get("HF_TOKEN")

    if not hf_token:
        print("\n⚠ HuggingFace token not found!")
        print("  To enable speaker diarization:")
        print("  1. Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("  2. Accept the license")
        print("  3. Get token: https://huggingface.co/settings/tokens")
        print("  4. Set: export HF_TOKEN='your_token_here'")
        return

    # Create system with diarization
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.LARGE_V3_TURBO,
        enable_diarization=True,
        hf_token=hf_token
    )

    print("\n✓ Speaker diarization enabled")
    print("  Will identify who is speaking and when")
    print("  Uses pyannote/speaker-diarization-3.1 (latest)")

    # Process with diarization
    # result = system.process_video(
    #     video_path="interview.mp4"
    # )

    # Print speaker segments
    # for caption in result['captions']:
    #     speaker = caption.get('speaker', 'Unknown')
    #     print(f"Speaker {speaker}: {caption['text']}")


def demo_5_multilanguage():
    """Demo 5: Multi-language translation"""
    print("\n" + "="*80)
    print("DEMO 5: Multi-Language Translation")
    print("="*80)

    system = AutoCaptionSystem()

    print("\n✓ Creating captions in multiple languages")
    print("  Transcribe once, translate to many languages")

    # Create captions in English, Spanish, French, German
    # srt_paths = system.create_translated_captions(
    #     video_path="video.mp4",
    #     source_language="en",
    #     target_languages=["es", "fr", "de", "pt"],
    #     output_dir="./multilang"
    # )

    # for lang, path in srt_paths.items():
    #     print(f"  {lang}: {path}")

    print("\nSupported languages:")
    languages = ["English", "Spanish", "French", "German", "Italian",
                "Portuguese", "Russian", "Japanese", "Korean", "Chinese"]
    for lang in languages:
        print(f"  • {lang}")


def demo_6_batch_processing():
    """Demo 6: Batch process multiple videos"""
    print("\n" + "="*80)
    print("DEMO 6: Batch Processing (Multiple Videos)")
    print("="*80)

    system = AutoCaptionSystem(
        model_size=WhisperModelSize.LARGE_V3_TURBO
    )

    print("\n✓ Batch processing setup")
    print("  Process multiple videos efficiently")
    print("  Optimized GPU memory management")
    print("  Queue system for large jobs")

    # Example video list
    video_paths = [
        "video1.mp4",
        "video2.mp4",
        "video3.mp4"
    ]

    print(f"\nExample: Processing {len(video_paths)} videos")
    print("  Each video processes with optimal GPU usage")
    print("  Results returned as dictionary")

    # Process batch
    # results = system.process_batch(
    #     video_paths=video_paths,
    #     output_dir="./batch_output"
    # )

    # for video_path, result in results.items():
    #     print(f"\n{video_path}:")
    #     print(f"  Status: {result['status']}")
    #     if result['status'] == 'success':
    #         print(f"  Words: {len(result['words'])}")
    #         print(f"  Captions: {len(result['captions'])}")


async def demo_7_realtime():
    """Demo 7: Real-time transcription"""
    print("\n" + "="*80)
    print("DEMO 7: Real-Time Transcription (Streaming)")
    print("="*80)

    system = AutoCaptionSystem(
        model_size=WhisperModelSize.LARGE_V3_TURBO
    )

    print("\n✓ Real-time transcription setup")
    print("  Stream results as they become available")
    print("  Perfect for live editing and preview")

    # Progress callback
    async def progress_callback(data):
        print(f"  Progress: {data['progress']} words processed...")

    # Real-time processing
    # result = await system.process_video_realtime(
    #     video_path="video.mp4",
    #     callback=progress_callback
    # )

    print("\nReal-time mode processes audio in chunks")
    print("Results available immediately for each chunk")


def demo_8_backend_comparison():
    """Demo 8: Compare different backends"""
    print("\n" + "="*80)
    print("DEMO 8: Backend Comparison")
    print("="*80)

    print("\nAvailable backends:")

    # Transformers (for V3 Turbo)
    print("\n1. TRANSFORMERS (Recommended for V3 Turbo)")
    print("   • Best for: V3 Turbo, Distil-Whisper")
    print("   • Speed: Optimized for new models")
    print("   • Features: Full word-level timestamps")

    # Faster-Whisper
    print("\n2. FASTER-WHISPER (Fastest for standard models)")
    print("   • Best for: Standard Whisper models")
    print("   • Speed: 2x faster with CTranslate2")
    print("   • Features: VAD filtering, memory optimized")

    # OpenAI API
    print("\n3. OPENAI API (No GPU needed)")
    print("   • Best for: Cloud processing")
    print("   • Speed: Fast, network dependent")
    print("   • Features: No GPU required")

    # Original Whisper
    print("\n4. OPENAI (Original Whisper)")
    print("   • Best for: Compatibility")
    print("   • Speed: Baseline")
    print("   • Features: Full compatibility")


def demo_9_caption_styles():
    """Demo 9: Different caption styles"""
    print("\n" + "="*80)
    print("DEMO 9: Caption Styles for Video Ads")
    print("="*80)

    styles = {
        "HORMOZI": "Big bold words, one at a time - Perfect for sales videos",
        "INSTAGRAM": "Word-by-word pop with color highlight - Perfect for reels",
        "TIKTOK": "Bold, centered, uppercase - Perfect for short-form",
        "YOUTUBE": "Sentence blocks at bottom - Perfect for long-form",
        "KARAOKE": "Word highlight as spoken - Perfect for music videos"
    }

    print("\nAvailable caption styles:")
    for style, description in styles.items():
        print(f"\n{style}:")
        print(f"  {description}")

    print("\nExample usage:")
    print("""
    system = AutoCaptionSystem()
    result = system.process_video(
        video_path="ad_video.mp4",
        caption_style=CaptionStyle.HORMOZI  # Big bold words!
    )
    """)


def demo_10_gpu_optimization():
    """Demo 10: GPU memory optimization"""
    print("\n" + "="*80)
    print("DEMO 10: GPU Memory Optimization")
    print("="*80)

    print("\n✓ Automatic GPU memory management")
    print("  Prevents out-of-memory errors")
    print("  Optimizes batch sizes")
    print("  Clears cache automatically")

    # Check GPU memory
    if os.path.exists("/proc/driver/nvidia/version"):
        available = GPUMemoryManager.get_available_memory()
        print(f"\n  Current available memory: {available:.1f}GB")

        # Optimize batch size
        batch_size = GPUMemoryManager.optimize_batch_size(
            video_duration=60.0,
            model_size="large-v3-turbo"
        )
        print(f"  Optimal batch size: {batch_size}")
    else:
        print("\n  No GPU detected - will use CPU")

    print("\nMemory requirements:")
    models = {
        "Large V3 Turbo": "6GB",
        "Distil-Large-V2": "4GB",
        "Distil-Medium-EN": "2GB",
        "Base": "1GB"
    }

    for model, memory in models.items():
        print(f"  {model}: {memory} VRAM")


def demo_11_production_setup():
    """Demo 11: Production setup recommendations"""
    print("\n" + "="*80)
    print("DEMO 11: Production Setup Recommendations")
    print("="*80)

    print("\n1. MAXIMUM ACCURACY SETUP:")
    print("""
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.LARGE_V3_TURBO,
        backend=WhisperBackend.TRANSFORMERS,
        enable_diarization=True,
        hf_token=os.environ.get("HF_TOKEN"),
        enable_profanity_filter=True
    )
    """)

    print("\n2. MAXIMUM SPEED SETUP:")
    print("""
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.DISTIL_MEDIUM_EN,
        backend=WhisperBackend.TRANSFORMERS
    )
    """)

    print("\n3. NO GPU / CLOUD SETUP:")
    print("""
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.BASE,
        backend=WhisperBackend.OPENAI_API,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )
    """)

    print("\n4. BATCH PROCESSING SETUP:")
    print("""
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.LARGE_V3_TURBO,
        backend=WhisperBackend.FASTER_WHISPER
    )

    results = system.process_batch(video_paths, output_dir="./output")
    """)


def main():
    """Run all demos"""
    print("\n" + "="*80)
    print("AUTO-CAPTION SYSTEM 2025 EDITION - DEMO")
    print("Whisper Large V3 Turbo + Advanced Features")
    print("="*80)

    demos = [
        ("Basic Usage (V3 Turbo)", demo_1_basic_usage),
        ("Fast Preview Mode", demo_2_fast_preview),
        ("Model Speed Comparison", demo_3_model_comparison),
        ("Speaker Diarization", demo_4_speaker_diarization),
        ("Multi-Language Translation", demo_5_multilanguage),
        ("Batch Processing", demo_6_batch_processing),
        ("Real-Time Transcription", demo_7_realtime),
        ("Backend Comparison", demo_8_backend_comparison),
        ("Caption Styles", demo_9_caption_styles),
        ("GPU Optimization", demo_10_gpu_optimization),
        ("Production Setup", demo_11_production_setup),
    ]

    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")

    print("\nRunning all demos...\n")

    for name, demo_func in demos:
        try:
            if asyncio.iscoroutinefunction(demo_func):
                asyncio.run(demo_func())
            else:
                demo_func()
        except Exception as e:
            print(f"\n⚠ Demo '{name}' error: {str(e)}")

        input("\nPress Enter to continue to next demo...")

    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nFor full documentation, see: AUTO_CAPTIONS_2025_GUIDE.md")
    print("For installation, see: requirements_auto_captions.txt")
    print("\nGet started:")
    print("  1. Install: pip install -r requirements_auto_captions.txt")
    print("  2. Run: python auto_captions.py your_video.mp4 --model large-v3-turbo")
    print("  3. Enjoy 8x faster transcription! ⚡")
    print()


if __name__ == "__main__":
    main()
