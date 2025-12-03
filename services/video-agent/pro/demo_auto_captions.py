"""
DEMO: Complete Auto-Caption System for Pro-Grade Video Ads

This demo shows all features of the auto-caption system:
- Multiple Whisper models
- GPU acceleration
- Multiple caption styles
- Speaker diarization
- Custom styling
- SRT/VTT export
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auto_captions import (
    AutoCaptionSystem,
    WhisperModelSize,
    CaptionStyle,
    CaptionStyleConfig,
    FFmpegCaptionBurner,
    WhisperTranscriber,
    CaptionGenerator,
    SubtitleExporter,
    FitnessVocabulary,
    ProfanityFilter
)


def demo_basic_transcription():
    """Demo 1: Basic transcription with word timestamps."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Transcription")
    print("="*60)

    video_path = "sample_video.mp4"  # Replace with your video

    # Initialize transcriber
    transcriber = WhisperTranscriber(
        model_size=WhisperModelSize.BASE,
        device="cuda"  # Use "cpu" if no GPU
    )

    # Transcribe
    result = transcriber.transcribe(video_path, word_timestamps=True)

    print(f"Language detected: {result['language']}")
    print(f"Full text: {result['text'][:200]}...")

    # Extract words
    words = transcriber.extract_words(result)
    print(f"\nTotal words: {len(words)}")
    print("\nFirst 5 words with timestamps:")
    for word in words[:5]:
        print(f"  {word.start:.2f}s - {word.end:.2f}s: '{word.text}'")


def demo_all_caption_styles():
    """Demo 2: Generate all caption styles."""
    print("\n" + "="*60)
    print("DEMO 2: All Caption Styles")
    print("="*60)

    video_path = "sample_video.mp4"
    output_dir = "caption_outputs"

    # Initialize system
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.BASE,
        enable_profanity_filter=True,
        enable_fitness_vocab=True
    )

    # Generate each style
    styles = [
        CaptionStyle.INSTAGRAM,
        CaptionStyle.YOUTUBE,
        CaptionStyle.KARAOKE,
        CaptionStyle.TIKTOK,
        CaptionStyle.HORMOZI
    ]

    for style in styles:
        print(f"\nGenerating {style.value} style...")

        result = system.process_video(
            video_path=video_path,
            output_dir=f"{output_dir}/{style.value}",
            caption_style=style,
            burn_captions=True
        )

        print(f"  Saved to: {result.get('captioned_video_path')}")


def demo_custom_styling():
    """Demo 3: Custom caption styling."""
    print("\n" + "="*60)
    print("DEMO 3: Custom Styling")
    print("="*60)

    video_path = "sample_video.mp4"

    # Create custom style config
    custom_style = CaptionStyleConfig(
        font_family="Arial-Bold",
        font_size=60,
        font_color="cyan",
        highlight_color="magenta",
        border_width=3,
        border_color="black",
        box_color="black@0.8",
        shadow_enabled=True,
        shadow_color="black@0.9",
        all_caps=True
    )

    # Initialize system
    system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)

    # Process with custom style
    result = system.process_video(
        video_path=video_path,
        output_dir="custom_style_output",
        caption_style=CaptionStyle.HORMOZI,
        style_config=custom_style,
        burn_captions=True
    )

    print(f"Custom styled video: {result.get('captioned_video_path')}")


def demo_speaker_diarization():
    """Demo 4: Speaker diarization (who is speaking)."""
    print("\n" + "="*60)
    print("DEMO 4: Speaker Diarization")
    print("="*60)

    video_path = "interview_video.mp4"

    # Initialize system with diarization
    # Note: Requires HuggingFace token
    hf_token = os.environ.get("HF_TOKEN")

    system = AutoCaptionSystem(
        model_size=WhisperModelSize.SMALL,
        enable_diarization=True,
        hf_token=hf_token
    )

    # Process with speaker detection
    result = system.process_video(
        video_path=video_path,
        output_dir="diarization_output",
        caption_style=CaptionStyle.YOUTUBE,
        num_speakers=2  # Expected number of speakers
    )

    # Check speaker assignments
    words_with_speakers = [w for w in result['words'] if w.get('speaker')]
    print(f"\nWords with speaker labels: {len(words_with_speakers)}")

    # Show speaker changes
    print("\nSpeaker timeline:")
    current_speaker = None
    for word in result['words']:
        if word.get('speaker') != current_speaker:
            current_speaker = word['speaker']
            print(f"  {word['start']:.2f}s: {current_speaker} speaks")


def demo_multilingual():
    """Demo 5: Multi-language support."""
    print("\n" + "="*60)
    print("DEMO 5: Multi-Language Support")
    print("="*60)

    videos = {
        "english": "video_en.mp4",
        "spanish": "video_es.mp4",
        "french": "video_fr.mp4"
    }

    for lang_name, video_path in videos.items():
        print(f"\nProcessing {lang_name} video...")

        # Auto-detect language (language=None)
        system = AutoCaptionSystem(
            model_size=WhisperModelSize.BASE,
            language=None  # Auto-detect
        )

        result = system.process_video(
            video_path=video_path,
            output_dir=f"multilingual/{lang_name}",
            caption_style=CaptionStyle.TIKTOK
        )

        print(f"  Detected language: {result['language']}")


def demo_fitness_vocabulary():
    """Demo 6: Custom fitness vocabulary."""
    print("\n" + "="*60)
    print("DEMO 6: Fitness Vocabulary Enhancement")
    print("="*60)

    # Test vocabulary enhancement
    test_texts = [
        "I did 10 repetitions and 3 sets",
        "My body mass index is 22",
        "I'm doing high intensity interval training",
        "Time to start bulking for gains",
        "Track your macronutrients and total daily energy expenditure"
    ]

    print("Original → Enhanced:")
    for text in test_texts:
        enhanced = FitnessVocabulary.enhance_text(text)
        print(f"  {text}")
        print(f"  → {enhanced}\n")


def demo_profanity_filter():
    """Demo 7: Profanity filtering."""
    print("\n" + "="*60)
    print("DEMO 7: Profanity Filtering")
    print("="*60)

    test_texts = [
        "This is a clean sentence",
        "This has a bad word in it",  # Would contain profanity in real use
    ]

    for text in test_texts:
        filtered = ProfanityFilter.filter_text(text)
        has_profanity = ProfanityFilter.contains_profanity(text)
        print(f"Original: {text}")
        print(f"Filtered: {filtered}")
        print(f"Contains profanity: {has_profanity}\n")


def demo_srt_vtt_export():
    """Demo 8: Export SRT and VTT files."""
    print("\n" + "="*60)
    print("DEMO 8: SRT/VTT Export")
    print("="*60)

    video_path = "sample_video.mp4"

    # Process video
    system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)

    result = system.process_video(
        video_path=video_path,
        output_dir="subtitle_exports",
        generate_srt=True,
        generate_vtt=True,
        burn_captions=False  # Only export subtitle files
    )

    print(f"SRT file: {result.get('srt_path')}")
    print(f"VTT file: {result.get('vtt_path')}")

    # Read and display first few lines of SRT
    if result.get('srt_path'):
        with open(result['srt_path'], 'r') as f:
            lines = f.readlines()[:15]
            print("\nFirst caption in SRT format:")
            print("".join(lines))


def demo_model_comparison():
    """Demo 9: Compare different Whisper models."""
    print("\n" + "="*60)
    print("DEMO 9: Model Size Comparison")
    print("="*60)

    video_path = "sample_video.mp4"

    models = [
        WhisperModelSize.TINY,
        WhisperModelSize.BASE,
        WhisperModelSize.SMALL
    ]

    import time

    for model_size in models:
        print(f"\nTesting {model_size.value} model...")

        transcriber = WhisperTranscriber(model_size=model_size)

        start_time = time.time()
        result = transcriber.transcribe(video_path, word_timestamps=True)
        end_time = time.time()

        print(f"  Time: {end_time - start_time:.2f}s")
        print(f"  Language: {result['language']}")
        print(f"  Text preview: {result['text'][:100]}...")


def demo_hormozi_style_detailed():
    """Demo 10: Detailed Hormozi style (most popular for ads)."""
    print("\n" + "="*60)
    print("DEMO 10: Hormozi Style - Detailed")
    print("="*60)

    video_path = "fitness_ad.mp4"

    # Hormozi-specific styling
    hormozi_config = CaptionStyleConfig(
        font_size=80,  # Very large
        font_color="yellow",
        highlight_color="yellow",
        border_width=4,
        border_color="black",
        box_color="black@0.85",
        shadow_enabled=True,
        shadow_x=4,
        shadow_y=4,
        all_caps=True,
        max_words_per_line=3  # Very few words at once
    )

    system = AutoCaptionSystem(
        model_size=WhisperModelSize.SMALL,  # Good balance
        enable_profanity_filter=True,
        enable_fitness_vocab=True
    )

    result = system.process_video(
        video_path=video_path,
        output_dir="hormozi_style",
        caption_style=CaptionStyle.HORMOZI,
        style_config=hormozi_config,
        burn_captions=True
    )

    print(f"Hormozi-style video: {result.get('captioned_video_path')}")
    print("\nCaption timing examples:")
    for caption in result['captions'][:5]:
        print(f"  {caption['start']:.2f}s - {caption['end']:.2f}s: {caption['text']}")


def demo_instagram_reels():
    """Demo 11: Instagram Reels optimized captions."""
    print("\n" + "="*60)
    print("DEMO 11: Instagram Reels Style")
    print("="*60)

    video_path = "reel_video.mp4"

    # Instagram-specific styling (vertical video optimized)
    instagram_config = CaptionStyleConfig(
        font_size=56,
        font_color="white",
        highlight_color="#FF0080",  # Instagram pink
        border_width=3,
        border_color="black",
        position_y="h-th-100",  # Higher up for Instagram
        all_caps=False,
        max_words_per_line=4,
        animate=True
    )

    system = AutoCaptionSystem(model_size=WhisperModelSize.BASE)

    result = system.process_video(
        video_path=video_path,
        output_dir="instagram_reels",
        caption_style=CaptionStyle.INSTAGRAM,
        style_config=instagram_config
    )

    print(f"Instagram-ready video: {result.get('captioned_video_path')}")


def demo_batch_processing():
    """Demo 12: Batch process multiple videos."""
    print("\n" + "="*60)
    print("DEMO 12: Batch Processing")
    print("="*60)

    video_directory = "videos_to_caption"
    videos = [
        "ad1.mp4",
        "ad2.mp4",
        "ad3.mp4"
    ]

    # Initialize system once
    system = AutoCaptionSystem(
        model_size=WhisperModelSize.BASE,
        enable_profanity_filter=True
    )

    for video_file in videos:
        video_path = os.path.join(video_directory, video_file)
        print(f"\nProcessing {video_file}...")

        try:
            result = system.process_video(
                video_path=video_path,
                output_dir=f"batch_output/{Path(video_file).stem}",
                caption_style=CaptionStyle.HORMOZI,
                generate_srt=True,
                burn_captions=True
            )

            print(f"  ✓ Success: {result.get('captioned_video_path')}")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")


def demo_advanced_timing_optimization():
    """Demo 13: Advanced caption timing optimization."""
    print("\n" + "="*60)
    print("DEMO 13: Advanced Timing Optimization")
    print("="*60)

    from auto_captions import Word, CaptionGenerator

    # Create sample words
    words = [
        Word("Hello", 0.0, 0.5, 0.98),
        Word("world", 0.5, 1.0, 0.95),
        Word("this", 1.0, 1.2, 0.97),
        Word("is", 1.2, 1.4, 0.99),
        Word("a", 1.4, 1.5, 0.96),
        Word("test", 1.5, 2.0, 0.98),
    ]

    # Generate captions with different settings
    configs = [
        {"max_words_per_caption": 2, "min_duration": 1.0},
        {"max_words_per_caption": 4, "min_duration": 1.5},
        {"max_words_per_caption": 6, "min_duration": 2.0},
    ]

    for config in configs:
        captions = CaptionGenerator.create_captions(words, **config)
        print(f"\nConfig: {config}")
        print(f"Generated {len(captions)} captions:")
        for cap in captions:
            print(f"  {cap.start:.2f}-{cap.end:.2f}s: '{cap.text}'")


def demo_gpu_vs_cpu():
    """Demo 14: GPU vs CPU performance comparison."""
    print("\n" + "="*60)
    print("DEMO 14: GPU vs CPU Performance")
    print("="*60)

    import torch
    import time

    if not torch.cuda.is_available():
        print("GPU not available, skipping GPU test")
        return

    video_path = "sample_video.mp4"

    # Test CPU
    print("\nTesting CPU...")
    cpu_transcriber = WhisperTranscriber(
        model_size=WhisperModelSize.BASE,
        device="cpu"
    )
    start = time.time()
    cpu_result = cpu_transcriber.transcribe(video_path)
    cpu_time = time.time() - start

    # Test GPU
    print("\nTesting GPU...")
    gpu_transcriber = WhisperTranscriber(
        model_size=WhisperModelSize.BASE,
        device="cuda"
    )
    start = time.time()
    gpu_result = gpu_transcriber.transcribe(video_path)
    gpu_time = time.time() - start

    print(f"\nResults:")
    print(f"  CPU time: {cpu_time:.2f}s")
    print(f"  GPU time: {gpu_time:.2f}s")
    print(f"  Speedup: {cpu_time/gpu_time:.2f}x")


def run_all_demos():
    """Run all demos."""
    print("\n" + "="*60)
    print("RUNNING ALL AUTO-CAPTION DEMOS")
    print("="*60)

    demos = [
        ("Basic Transcription", demo_basic_transcription),
        ("All Caption Styles", demo_all_caption_styles),
        ("Custom Styling", demo_custom_styling),
        ("Speaker Diarization", demo_speaker_diarization),
        ("Multi-Language", demo_multilingual),
        ("Fitness Vocabulary", demo_fitness_vocabulary),
        ("Profanity Filter", demo_profanity_filter),
        ("SRT/VTT Export", demo_srt_vtt_export),
        ("Model Comparison", demo_model_comparison),
        ("Hormozi Style", demo_hormozi_style_detailed),
        ("Instagram Reels", demo_instagram_reels),
        ("Batch Processing", demo_batch_processing),
        ("Timing Optimization", demo_advanced_timing_optimization),
        ("GPU vs CPU", demo_gpu_vs_cpu),
    ]

    for name, demo_func in demos:
        try:
            print(f"\n\nRunning: {name}")
            demo_func()
        except Exception as e:
            print(f"Error in {name}: {str(e)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-Caption System Demos")
    parser.add_argument(
        "--demo",
        type=int,
        help="Run specific demo number (1-14), or omit to see menu"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all demos"
    )

    args = parser.parse_args()

    demos = {
        1: ("Basic Transcription", demo_basic_transcription),
        2: ("All Caption Styles", demo_all_caption_styles),
        3: ("Custom Styling", demo_custom_styling),
        4: ("Speaker Diarization", demo_speaker_diarization),
        5: ("Multi-Language", demo_multilingual),
        6: ("Fitness Vocabulary", demo_fitness_vocabulary),
        7: ("Profanity Filter", demo_profanity_filter),
        8: ("SRT/VTT Export", demo_srt_vtt_export),
        9: ("Model Comparison", demo_model_comparison),
        10: ("Hormozi Style", demo_hormozi_style_detailed),
        11: ("Instagram Reels", demo_instagram_reels),
        12: ("Batch Processing", demo_batch_processing),
        13: ("Timing Optimization", demo_advanced_timing_optimization),
        14: ("GPU vs CPU", demo_gpu_vs_cpu),
    }

    if args.all:
        run_all_demos()
    elif args.demo:
        if args.demo in demos:
            name, func = demos[args.demo]
            print(f"\nRunning Demo {args.demo}: {name}")
            func()
        else:
            print(f"Invalid demo number: {args.demo}")
    else:
        # Show menu
        print("\n" + "="*60)
        print("AUTO-CAPTION SYSTEM DEMOS")
        print("="*60)
        print("\nAvailable demos:")
        for num, (name, _) in demos.items():
            print(f"  {num:2d}. {name}")
        print("\nUsage:")
        print("  python demo_auto_captions.py --demo <number>")
        print("  python demo_auto_captions.py --all")
