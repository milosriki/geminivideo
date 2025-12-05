"""
Voice Generation System - Example Usage
Complete examples for generating voiceovers and cloning voices.
"""

import asyncio
import os
from voice_generator import (
    VoiceGenerator,
    VoiceProvider,
    OpenAIVoice,
    VoiceSettings,
    VoiceCloneConfig,
    VoicePresets
)


async def example_1_basic_openai_tts():
    """Example 1: Basic OpenAI TTS generation"""
    print("\n" + "="*60)
    print("Example 1: Basic OpenAI TTS")
    print("="*60)

    generator = VoiceGenerator()

    # Generate voiceover with Nova (female, warm)
    audio_path = await generator.generate_voiceover(
        script="Transform your business with AI-powered video ads. Get 10x more engagement in just 30 days.",
        voice_id=OpenAIVoice.NOVA.value,
        provider=VoiceProvider.OPENAI,
        model="tts-1-hd"
    )

    print(f"✓ Generated voiceover: {audio_path}")
    duration = await generator._get_audio_duration(audio_path)
    print(f"  Duration: {duration:.2f} seconds")


async def example_2_all_openai_voices():
    """Example 2: Test all OpenAI voices"""
    print("\n" + "="*60)
    print("Example 2: All OpenAI Voices")
    print("="*60)

    generator = VoiceGenerator()

    script = "Welcome to our platform. We're excited to have you here."

    voices = {
        "alloy": "Neutral, balanced",
        "echo": "Male, clear",
        "fable": "British male, authoritative",
        "onyx": "Deep male, dramatic",
        "nova": "Female, warm",
        "shimmer": "Female, energetic"
    }

    for voice_id, description in voices.items():
        print(f"\n{voice_id.upper()} ({description}):")
        audio_path = await generator.generate_voiceover(
            script=script,
            voice_id=voice_id,
            provider=VoiceProvider.OPENAI,
            model="tts-1"  # Use standard for faster testing
        )
        print(f"  ✓ {audio_path}")


async def example_3_voice_presets():
    """Example 3: Using voice presets"""
    print("\n" + "="*60)
    print("Example 3: Voice Presets")
    print("="*60)

    generator = VoiceGenerator()

    # Professional male voice
    voice_id, settings = VoicePresets.professional_male()
    audio_path = await generator.generate_voiceover(
        script="Introducing our latest innovation in video marketing.",
        voice_id=voice_id,
        provider=VoiceProvider.OPENAI,
        settings=settings
    )
    print(f"✓ Professional male: {audio_path}")

    # Energetic female voice
    voice_id, settings = VoicePresets.energetic_female()
    audio_path = await generator.generate_voiceover(
        script="Don't miss out! Limited time offer ends today!",
        voice_id=voice_id,
        provider=VoiceProvider.OPENAI,
        settings=settings
    )
    print(f"✓ Energetic female: {audio_path}")


async def example_4_speed_control():
    """Example 4: Speed control for different effects"""
    print("\n" + "="*60)
    print("Example 4: Speed Control")
    print("="*60)

    generator = VoiceGenerator()

    script = "Transform your business in 30 days."

    speeds = {
        0.75: "Slow (storytelling)",
        1.0: "Normal",
        1.25: "Fast (energetic)",
        1.5: "Very fast (urgent)"
    }

    for speed, description in speeds.items():
        print(f"\nSpeed {speed}x ({description}):")
        settings = VoiceSettings(speed=speed)
        audio_path = await generator.generate_voiceover(
            script=script,
            voice_id=OpenAIVoice.NOVA.value,
            provider=VoiceProvider.OPENAI,
            settings=settings
        )
        duration = await generator._get_audio_duration(audio_path)
        print(f"  ✓ {audio_path}")
        print(f"  Duration: {duration:.2f}s")


async def example_5_voice_cloning():
    """Example 5: Voice cloning (requires ElevenLabs API key)"""
    print("\n" + "="*60)
    print("Example 5: Voice Cloning (ElevenLabs)")
    print("="*60)

    if not os.getenv("ELEVENLABS_API_KEY"):
        print("⚠ Skipped: ELEVENLABS_API_KEY not set")
        return

    generator = VoiceGenerator()

    # Example audio samples (you need to provide real files)
    audio_samples = [
        "/path/to/sample1.mp3",
        "/path/to/sample2.mp3",
        "/path/to/sample3.mp3"
    ]

    # Check if samples exist
    if not all(os.path.exists(s) for s in audio_samples):
        print("⚠ Skipped: Audio samples not found")
        print("  Provide 3-10 audio samples of 30-90 seconds each")
        return

    config = VoiceCloneConfig(
        name="Brand Voice",
        description="Professional brand spokesperson voice",
        audio_samples=audio_samples,
        labels={
            "gender": "female",
            "age": "young",
            "accent": "american",
            "tone": "professional"
        }
    )

    print("Cloning voice (this may take 2-5 minutes)...")
    voice_id = await generator.clone_voice(config)
    print(f"✓ Voice cloned successfully!")
    print(f"  Voice ID: {voice_id}")
    print(f"  Name: {config.name}")

    # Use cloned voice
    audio_path = await generator.generate_voiceover(
        script="Welcome to our brand. We're thrilled to have you.",
        voice_id=voice_id,
        provider=VoiceProvider.ELEVENLABS
    )
    print(f"✓ Generated with cloned voice: {audio_path}")


async def example_6_multilingual():
    """Example 6: Multi-language voiceovers (requires ElevenLabs API key)"""
    print("\n" + "="*60)
    print("Example 6: Multi-Language Voiceovers")
    print("="*60)

    if not os.getenv("ELEVENLABS_API_KEY"):
        print("⚠ Skipped: ELEVENLABS_API_KEY not set")
        return

    generator = VoiceGenerator()

    # Get available ElevenLabs voices
    voices = await generator.get_available_voices(VoiceProvider.ELEVENLABS)
    if not voices:
        print("⚠ No ElevenLabs voices available")
        return

    voice_id = voices[0]["voice_id"]  # Use first available voice

    script = "Welcome to our platform!"
    languages = ["en", "es", "fr", "de"]

    print(f"Generating voiceovers in {len(languages)} languages...")
    for lang in languages:
        print(f"\n{lang.upper()}:")
        audio_path = await generator.generate_voiceover(
            script=script,
            voice_id=voice_id,
            provider=VoiceProvider.ELEVENLABS,
            language=lang
        )
        print(f"  ✓ {audio_path}")


async def example_7_sync_to_video():
    """Example 7: Sync voiceover to video"""
    print("\n" + "="*60)
    print("Example 7: Sync Voiceover to Video")
    print("="*60)

    generator = VoiceGenerator()

    # Generate voiceover
    audio_path = await generator.generate_voiceover(
        script="This is a professional video ad with AI-generated voiceover.",
        voice_id=OpenAIVoice.NOVA.value,
        provider=VoiceProvider.OPENAI
    )
    print(f"✓ Generated voiceover: {audio_path}")

    # Example video path (provide a real video file)
    video_path = "/path/to/video.mp4"

    if not os.path.exists(video_path):
        print("⚠ Skipped: Video file not found")
        print(f"  Provide a video file at: {video_path}")
        return

    # Sync to video with effects
    output_path = await generator.sync_to_video(
        audio_path=audio_path,
        video_path=video_path,
        volume=1.2,       # Boost voiceover volume by 20%
        fade_in=0.5,      # 0.5s fade in
        fade_out=1.0      # 1.0s fade out
    )
    print(f"✓ Video with voiceover: {output_path}")


async def example_8_get_voice_library():
    """Example 8: Get available voices"""
    print("\n" + "="*60)
    print("Example 8: Voice Library")
    print("="*60)

    generator = VoiceGenerator()

    # Get OpenAI voices
    print("\nOpenAI Voices:")
    openai_voices = await generator.get_available_voices(VoiceProvider.OPENAI)
    for voice in openai_voices:
        print(f"  - {voice['name']}: {voice['description']}")

    # Get ElevenLabs voices (if API key available)
    if os.getenv("ELEVENLABS_API_KEY"):
        print("\nElevenLabs Voices:")
        try:
            el_voices = await generator.get_available_voices(VoiceProvider.ELEVENLABS)
            for voice in el_voices[:5]:  # Show first 5
                print(f"  - {voice['name']}: {voice.get('description', 'N/A')}")
            if len(el_voices) > 5:
                print(f"  ... and {len(el_voices) - 5} more")
        except Exception as e:
            print(f"  ⚠ Error: {e}")
    else:
        print("\nElevenLabs: API key not set")

    # Get custom cloned voices
    print("\nCustom Cloned Voices:")
    custom_voices = generator.get_voice_library()
    if custom_voices:
        for voice_id, voice_data in custom_voices.items():
            print(f"  - {voice_data['name']} (ID: {voice_id})")
    else:
        print("  No custom voices yet")


async def example_9_batch_generation():
    """Example 9: Batch voiceover generation"""
    print("\n" + "="*60)
    print("Example 9: Batch Generation")
    print("="*60)

    generator = VoiceGenerator()

    # Generate voiceovers for multiple ads
    ads = [
        {
            "name": "Ad 1 - Problem",
            "script": "Struggling with low engagement rates?",
            "voice": "onyx"
        },
        {
            "name": "Ad 2 - Solution",
            "script": "Our AI-powered platform can help.",
            "voice": "nova"
        },
        {
            "name": "Ad 3 - CTA",
            "script": "Get started today for free!",
            "voice": "shimmer"
        }
    ]

    print("Generating voiceovers for 3 ads...\n")
    for ad in ads:
        print(f"{ad['name']}:")
        audio_path = await generator.generate_voiceover(
            script=ad["script"],
            voice_id=ad["voice"],
            provider=VoiceProvider.OPENAI
        )
        print(f"  ✓ {audio_path}\n")


async def example_10_ab_testing():
    """Example 10: A/B testing different voices"""
    print("\n" + "="*60)
    print("Example 10: A/B Testing Voices")
    print("="*60)

    generator = VoiceGenerator()

    script = "Transform your business with AI. Get started now!"

    # Test 3 different voices for the same ad
    voices_to_test = [
        ("nova", "Female, warm"),
        ("shimmer", "Female, energetic"),
        ("onyx", "Male, dramatic")
    ]

    print("Generating 3 variants for A/B testing...\n")
    for voice_id, description in voices_to_test:
        print(f"Variant: {voice_id.upper()} ({description})")
        audio_path = await generator.generate_voiceover(
            script=script,
            voice_id=voice_id,
            provider=VoiceProvider.OPENAI
        )
        print(f"  ✓ {audio_path}\n")

    print("Use these variants for A/B testing to find best performer!")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Voice Generation System - Example Usage")
    print("="*60)

    examples = [
        ("Basic OpenAI TTS", example_1_basic_openai_tts),
        ("All OpenAI Voices", example_2_all_openai_voices),
        ("Voice Presets", example_3_voice_presets),
        ("Speed Control", example_4_speed_control),
        ("Voice Cloning", example_5_voice_cloning),
        ("Multi-Language", example_6_multilingual),
        ("Sync to Video", example_7_sync_to_video),
        ("Voice Library", example_8_get_voice_library),
        ("Batch Generation", example_9_batch_generation),
        ("A/B Testing", example_10_ab_testing)
    ]

    # Run selected examples (comment out to skip)
    selected = [
        0,  # Basic OpenAI TTS
        # 1,  # All OpenAI Voices
        # 2,  # Voice Presets
        # 3,  # Speed Control
        # 4,  # Voice Cloning
        # 5,  # Multi-Language
        # 6,  # Sync to Video
        7,  # Voice Library
        # 8,  # Batch Generation
        # 9,  # A/B Testing
    ]

    for idx in selected:
        if idx < len(examples):
            name, func = examples[idx]
            try:
                await func()
            except Exception as e:
                print(f"\n⚠ Error in {name}: {e}")

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
