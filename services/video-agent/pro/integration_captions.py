"""
INTEGRATION: Auto-Captions with Pro Video Renderer

Shows how to integrate the auto-caption system with existing
pro video rendering pipeline.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import pro renderer components
try:
    from pro_renderer import ProRenderer, RenderConfig
    from timeline_engine import TimelineEngine
    RENDERER_AVAILABLE = True
except ImportError:
    RENDERER_AVAILABLE = False
    print("Warning: pro_renderer not available")

# Import auto-caption components
from auto_captions import (
    AutoCaptionSystem,
    WhisperModelSize,
    CaptionStyle,
    CaptionStyleConfig
)


class CaptionedVideoRenderer:
    """
    Integrated renderer that combines pro video rendering with auto-captions.
    """

    def __init__(
        self,
        whisper_model: WhisperModelSize = WhisperModelSize.BASE,
        enable_gpu: bool = True,
        enable_diarization: bool = False,
        hf_token: Optional[str] = None
    ):
        """
        Initialize integrated renderer.

        Args:
            whisper_model: Whisper model size to use
            enable_gpu: Enable GPU acceleration
            enable_diarization: Enable speaker diarization
            hf_token: HuggingFace token for diarization
        """
        # Initialize caption system
        self.caption_system = AutoCaptionSystem(
            model_size=whisper_model,
            device="cuda" if enable_gpu else "cpu",
            enable_diarization=enable_diarization,
            hf_token=hf_token,
            enable_profanity_filter=True,
            enable_fitness_vocab=True
        )

        # Initialize pro renderer if available
        if RENDERER_AVAILABLE:
            self.renderer = ProRenderer()
        else:
            self.renderer = None

    def render_with_captions(
        self,
        video_path: str,
        output_path: str,
        caption_style: CaptionStyle = CaptionStyle.HORMOZI,
        style_config: Optional[CaptionStyleConfig] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Render video with auto-generated captions.

        Args:
            video_path: Input video path
            output_path: Output video path
            caption_style: Caption style to use
            style_config: Custom style configuration
            language: Language code (auto-detect if None)

        Returns:
            Dictionary with render results
        """
        print(f"Rendering video with {caption_style.value} captions...")

        # Process video with captions
        result = self.caption_system.process_video(
            video_path=video_path,
            output_dir=str(Path(output_path).parent),
            caption_style=caption_style,
            style_config=style_config,
            burn_captions=True,
            generate_srt=True,
            generate_vtt=True
        )

        # Move final video to desired output path
        if result.get("captioned_video_path"):
            import shutil
            shutil.move(result["captioned_video_path"], output_path)
            result["final_output_path"] = output_path

        return result

    def create_ad_from_script(
        self,
        script: str,
        video_clips: list,
        output_path: str,
        caption_style: CaptionStyle = CaptionStyle.HORMOZI,
        style_config: Optional[CaptionStyleConfig] = None
    ) -> Dict[str, Any]:
        """
        Create a complete video ad from script and clips with auto-captions.

        Args:
            script: Video script text
            video_clips: List of video clip paths
            output_path: Output video path
            caption_style: Caption style
            style_config: Custom style configuration

        Returns:
            Dictionary with creation results
        """
        if not RENDERER_AVAILABLE:
            raise RuntimeError("Pro renderer not available")

        print("Creating video ad from script...")

        # Step 1: Render base video (without captions)
        # This would use your existing pro_renderer workflow
        # For now, we'll assume video_clips are already assembled

        # Step 2: Add captions to assembled video
        result = self.render_with_captions(
            video_path=video_clips[0],  # Or assembled video
            output_path=output_path,
            caption_style=caption_style,
            style_config=style_config
        )

        return result


class CaptionAgent:
    """
    Agent that specializes in caption generation for video ads.
    Can be integrated into multi-agent system.
    """

    def __init__(self, model_size: WhisperModelSize = WhisperModelSize.BASE):
        """Initialize caption agent."""
        self.caption_system = AutoCaptionSystem(
            model_size=model_size,
            enable_profanity_filter=True,
            enable_fitness_vocab=True
        )

    def generate_captions(
        self,
        video_path: str,
        style: str = "hormozi"
    ) -> Dict[str, Any]:
        """
        Generate captions for video (agent interface).

        Args:
            video_path: Path to video
            style: Caption style name

        Returns:
            Caption generation results
        """
        # Map style name to enum
        style_map = {
            "hormozi": CaptionStyle.HORMOZI,
            "instagram": CaptionStyle.INSTAGRAM,
            "tiktok": CaptionStyle.TIKTOK,
            "youtube": CaptionStyle.YOUTUBE,
            "karaoke": CaptionStyle.KARAOKE
        }

        caption_style = style_map.get(style.lower(), CaptionStyle.HORMOZI)

        # Process video
        result = self.caption_system.process_video(
            video_path=video_path,
            caption_style=caption_style,
            burn_captions=False,  # Agent only generates, doesn't burn
            generate_srt=True,
            generate_vtt=True
        )

        return {
            "success": True,
            "transcription": result["transcription"]["text"],
            "language": result["language"],
            "word_count": len(result["words"]),
            "caption_count": len(result["captions"]),
            "srt_path": result.get("srt_path"),
            "vtt_path": result.get("vtt_path"),
            "words": result["words"],
            "captions": result["captions"]
        }

    def get_caption_suggestions(
        self,
        transcription_text: str,
        video_duration: float
    ) -> Dict[str, Any]:
        """
        Suggest optimal caption style based on content and duration.

        Args:
            transcription_text: Transcribed text
            video_duration: Video duration in seconds

        Returns:
            Style suggestions
        """
        word_count = len(transcription_text.split())
        words_per_second = word_count / video_duration

        # Determine best style based on content
        suggestions = []

        # Fast-paced content (>2 words/sec) -> Hormozi
        if words_per_second > 2:
            suggestions.append({
                "style": "hormozi",
                "reason": "Fast-paced content works best with one word at a time",
                "confidence": 0.9
            })

        # Short content (<30 sec) -> TikTok or Instagram
        if video_duration < 30:
            suggestions.append({
                "style": "tiktok",
                "reason": "Short-form content optimized for TikTok style",
                "confidence": 0.85
            })

        # Long content (>60 sec) -> YouTube
        if video_duration > 60:
            suggestions.append({
                "style": "youtube",
                "reason": "Long-form content works well with traditional subtitles",
                "confidence": 0.8
            })

        # Check for fitness keywords
        fitness_keywords = ["workout", "training", "gains", "muscle", "fitness"]
        if any(keyword in transcription_text.lower() for keyword in fitness_keywords):
            suggestions.append({
                "style": "hormozi",
                "reason": "Fitness content benefits from high-impact Hormozi style",
                "confidence": 0.95
            })

        return {
            "primary_suggestion": suggestions[0] if suggestions else {"style": "hormozi"},
            "all_suggestions": suggestions,
            "video_stats": {
                "duration": video_duration,
                "word_count": word_count,
                "words_per_second": words_per_second
            }
        }


def example_integrated_workflow():
    """
    Example: Complete workflow integrating captions with video rendering.
    """
    print("\n" + "="*60)
    print("INTEGRATED WORKFLOW EXAMPLE")
    print("="*60)

    # Step 1: Initialize renderer with captions
    renderer = CaptionedVideoRenderer(
        whisper_model=WhisperModelSize.BASE,
        enable_gpu=True
    )

    # Step 2: Define Hormozi-style config for fitness ad
    hormozi_config = CaptionStyleConfig(
        font_size=80,
        font_color="yellow",
        highlight_color="yellow",
        border_width=4,
        border_color="black",
        box_color="black@0.85",
        all_caps=True,
        max_words_per_line=2
    )

    # Step 3: Render video with captions
    result = renderer.render_with_captions(
        video_path="raw_fitness_ad.mp4",
        output_path="final_fitness_ad_captioned.mp4",
        caption_style=CaptionStyle.HORMOZI,
        style_config=hormozi_config
    )

    print(f"\nRendering complete!")
    print(f"Output: {result['final_output_path']}")
    print(f"Language: {result['language']}")
    print(f"Captions: {len(result['captions'])}")


def example_agent_workflow():
    """
    Example: Using caption agent in multi-agent system.
    """
    print("\n" + "="*60)
    print("CAPTION AGENT WORKFLOW")
    print("="*60)

    # Initialize caption agent
    agent = CaptionAgent(model_size=WhisperModelSize.BASE)

    # Step 1: Generate captions
    video_path = "fitness_ad.mp4"

    print(f"\nAgent: Generating captions for {video_path}")
    result = agent.generate_captions(video_path, style="hormozi")

    print(f"\nAgent: Caption generation complete")
    print(f"  Language: {result['language']}")
    print(f"  Words: {result['word_count']}")
    print(f"  Captions: {result['caption_count']}")
    print(f"  SRT: {result['srt_path']}")

    # Step 2: Get style suggestions
    suggestions = agent.get_caption_suggestions(
        transcription_text=result['transcription'],
        video_duration=30.0
    )

    print(f"\nAgent: Style suggestions")
    print(f"  Primary: {suggestions['primary_suggestion']['style']}")
    print(f"  Reason: {suggestions['primary_suggestion']['reason']}")


def example_batch_captioning():
    """
    Example: Batch caption multiple videos for ad campaign.
    """
    print("\n" + "="*60)
    print("BATCH CAPTIONING WORKFLOW")
    print("="*60)

    videos = [
        {"path": "ad_1.mp4", "style": "hormozi"},
        {"path": "ad_2.mp4", "style": "tiktok"},
        {"path": "ad_3.mp4", "style": "instagram"},
    ]

    # Initialize renderer
    renderer = CaptionedVideoRenderer(whisper_model=WhisperModelSize.BASE)

    # Process each video
    results = []
    for video in videos:
        print(f"\nProcessing {video['path']} with {video['style']} style...")

        result = renderer.render_with_captions(
            video_path=video['path'],
            output_path=f"captioned_{video['path']}",
            caption_style=CaptionStyle(video['style'])
        )

        results.append(result)
        print(f"  ✓ Complete: {result.get('final_output_path')}")

    print(f"\n✓ All {len(results)} videos processed!")


def example_celery_task_integration():
    """
    Example: Integrate caption generation as Celery task.
    """
    print("\n" + "="*60)
    print("CELERY TASK INTEGRATION EXAMPLE")
    print("="*60)

    # This would be in your celery_app.py

    code_example = '''
from celery import shared_task
from auto_captions import AutoCaptionSystem, CaptionStyle

@shared_task(bind=True, name="caption.generate")
def generate_captions_task(self, video_path: str, style: str = "hormozi"):
    """
    Celery task for caption generation.
    """
    # Initialize system
    system = AutoCaptionSystem()

    # Update progress
    self.update_state(state='PROCESSING', meta={'progress': 0})

    # Process video
    result = system.process_video(
        video_path=video_path,
        caption_style=CaptionStyle(style)
    )

    self.update_state(state='PROCESSING', meta={'progress': 100})

    return {
        "captioned_video": result["captioned_video_path"],
        "srt_file": result["srt_path"],
        "language": result["language"]
    }

# Usage:
# task = generate_captions_task.delay("video.mp4", "hormozi")
# result = task.get()
'''

    print(code_example)


def example_api_endpoint():
    """
    Example: REST API endpoint for caption generation.
    """
    print("\n" + "="*60)
    print("API ENDPOINT EXAMPLE")
    print("="*60)

    code_example = '''
from fastapi import FastAPI, File, UploadFile, Form
from auto_captions import AutoCaptionSystem, CaptionStyle

app = FastAPI()

# Initialize caption system
caption_system = AutoCaptionSystem()

@app.post("/api/captions/generate")
async def generate_captions(
    video: UploadFile = File(...),
    style: str = Form("hormozi"),
    language: str = Form(None)
):
    """
    Generate captions for uploaded video.
    """
    # Save uploaded file
    video_path = f"temp/{video.filename}"
    with open(video_path, "wb") as f:
        f.write(await video.read())

    # Generate captions
    result = caption_system.process_video(
        video_path=video_path,
        caption_style=CaptionStyle(style),
        language=language
    )

    return {
        "success": True,
        "language": result["language"],
        "caption_count": len(result["captions"]),
        "srt_url": f"/downloads/{result['srt_path']}",
        "video_url": f"/downloads/{result['captioned_video_path']}"
    }

# Run with: uvicorn integration_captions:app --reload
'''

    print(code_example)


def example_with_pro_renderer():
    """
    Example: Full integration with ProRenderer.
    """
    print("\n" + "="*60)
    print("PRO RENDERER INTEGRATION")
    print("="*60)

    if not RENDERER_AVAILABLE:
        print("Pro renderer not available, showing code example:")

    code_example = '''
from pro_renderer import ProRenderer, RenderConfig
from auto_captions import AutoCaptionSystem, CaptionStyle

# Create fitness ad with captions
def create_fitness_ad_with_captions(
    script: str,
    video_clips: list,
    output_path: str
):
    """
    Complete workflow: Render video + Add captions.
    """
    # Step 1: Render base video with pro renderer
    renderer = ProRenderer()

    base_config = RenderConfig(
        output_path="temp_base_video.mp4",
        resolution=(1080, 1920),  # Vertical
        fps=30
    )

    # Add video clips, transitions, effects
    timeline = renderer.create_timeline()
    for clip in video_clips:
        timeline.add_clip(clip)

    # Render base video
    base_video = renderer.render(base_config)

    # Step 2: Add captions using auto-caption system
    caption_system = AutoCaptionSystem()

    result = caption_system.process_video(
        video_path=base_video,
        output_dir="output",
        caption_style=CaptionStyle.HORMOZI,
        burn_captions=True
    )

    # Move to final output
    import shutil
    shutil.move(result["captioned_video_path"], output_path)

    return {
        "video_path": output_path,
        "srt_path": result["srt_path"],
        "language": result["language"]
    }

# Usage
result = create_fitness_ad_with_captions(
    script="Get ripped in 30 days!",
    video_clips=["workout1.mp4", "workout2.mp4"],
    output_path="final_ad.mp4"
)
'''

    print(code_example)


def main():
    """Run all integration examples."""
    import argparse

    parser = argparse.ArgumentParser(description="Caption Integration Examples")
    parser.add_argument(
        "--example",
        choices=[
            "integrated",
            "agent",
            "batch",
            "celery",
            "api",
            "renderer",
            "all"
        ],
        default="all",
        help="Which example to run"
    )

    args = parser.parse_args()

    examples = {
        "integrated": example_integrated_workflow,
        "agent": example_agent_workflow,
        "batch": example_batch_captioning,
        "celery": example_celery_task_integration,
        "api": example_api_endpoint,
        "renderer": example_with_pro_renderer
    }

    if args.example == "all":
        for name, func in examples.items():
            try:
                func()
            except Exception as e:
                print(f"\nError in {name}: {e}")
    else:
        examples[args.example]()


if __name__ == "__main__":
    main()
