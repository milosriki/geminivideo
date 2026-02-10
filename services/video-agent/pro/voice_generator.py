"""
AI Voice Generation & Cloning System - ElevenLabs + OpenAI TTS
Professional voiceover generation for video ads with voice cloning capabilities.

Features:
- ElevenLabs: High-quality voice cloning and TTS (30+ languages)
- OpenAI TTS: Fast, affordable voiceover generation (6 premium voices)
- Voice library management
- Multi-language support
- Video-voiceover synchronization
- Script timing and pacing control
"""

import os
import json
import logging
import tempfile
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import asyncio
import aiohttp
import aiofiles
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceProvider(Enum):
    """Voice generation providers"""
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"


class OpenAIVoice(Enum):
    """OpenAI TTS voice options"""
    ALLOY = "alloy"  # Neutral, balanced
    ECHO = "echo"  # Male, clear
    FABLE = "fable"  # British male, authoritative
    ONYX = "onyx"  # Deep male, dramatic
    NOVA = "nova"  # Female, warm
    SHIMMER = "shimmer"  # Female, energetic


class OpenAIModel(Enum):
    """OpenAI TTS models"""
    TTS_1 = "tts-1"  # Standard quality, fast
    TTS_1_HD = "tts-1-hd"  # High definition, slower


class VoiceStability(Enum):
    """Voice stability settings (ElevenLabs)"""
    VERY_STABLE = 0.75  # More consistent, less expressive
    STABLE = 0.50  # Balanced
    EXPRESSIVE = 0.25  # More variable, more expressive


class SimilarityBoost(Enum):
    """Similarity boost for voice cloning (ElevenLabs)"""
    LOW = 0.25  # More general voice
    MEDIUM = 0.50  # Balanced
    HIGH = 0.75  # Very close to original
    MAX = 1.0  # Maximum similarity


@dataclass
class VoiceSettings:
    """Voice generation settings"""
    # ElevenLabs specific
    stability: float = 0.50  # 0-1, voice consistency
    similarity_boost: float = 0.75  # 0-1, voice cloning similarity
    style: float = 0.0  # 0-1, style exaggeration (v2 models only)
    use_speaker_boost: bool = True  # Enhance speaker similarity

    # OpenAI specific
    speed: float = 1.0  # 0.25-4.0, playback speed

    # Common settings
    optimize_streaming_latency: int = 0  # 0-4, lower latency (ElevenLabs)


@dataclass
class VoiceCloneConfig:
    """Voice cloning configuration"""
    name: str  # Voice name
    description: str = ""  # Voice description
    audio_samples: List[str] = field(default_factory=list)  # Paths to audio samples
    labels: Dict[str, str] = field(default_factory=dict)  # Voice metadata (age, gender, accent, etc.)


@dataclass
class Script:
    """Voiceover script with timing"""
    text: str
    start_time: Optional[float] = None  # seconds
    duration: Optional[float] = None  # seconds
    pause_after: float = 0.0  # seconds to pause after this segment
    emphasis: Optional[List[str]] = None  # Words to emphasize


@dataclass
class VoiceoverJob:
    """Voiceover generation job"""
    job_id: str
    script: str
    voice_id: str
    provider: VoiceProvider
    status: str = "pending"  # pending, processing, completed, failed
    output_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VoiceGenerator:
    """
    Professional AI voice generation system.
    Supports ElevenLabs (voice cloning) and OpenAI TTS (fast, affordable).
    """

    # API endpoints
    ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
    OPENAI_API_BASE = "https://api.openai.com/v1"

    def __init__(
        self,
        elevenlabs_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        output_dir: str = "/tmp/voiceovers"
    ):
        """
        Initialize voice generator.

        Args:
            elevenlabs_api_key: ElevenLabs API key (optional)
            openai_api_key: OpenAI API key (optional)
            output_dir: Output directory for generated audio
        """
        self.elevenlabs_api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Voice library
        self.voice_library: Dict[str, Dict[str, Any]] = {}
        self._load_voice_library()

        # Job tracking
        self.jobs: Dict[str, VoiceoverJob] = {}

    def _load_voice_library(self):
        """Load voice library from disk"""
        library_file = self.output_dir / "voice_library.json"
        if library_file.exists():
            try:
                with open(library_file, 'r') as f:
                    self.voice_library = json.load(f)
                logger.info(f"Loaded {len(self.voice_library)} voices from library")
            except Exception as e:
                logger.error(f"Failed to load voice library: {e}")

    def _save_voice_library(self):
        """Save voice library to disk"""
        library_file = self.output_dir / "voice_library.json"
        try:
            with open(library_file, 'w') as f:
                json.dump(self.voice_library, f, indent=2, default=str)
            logger.info(f"Saved {len(self.voice_library)} voices to library")
        except Exception as e:
            logger.error(f"Failed to save voice library: {e}")

    async def generate_voiceover(
        self,
        script: str,
        voice_id: str,
        provider: VoiceProvider = VoiceProvider.OPENAI,
        model: Optional[str] = None,
        settings: Optional[VoiceSettings] = None,
        output_format: str = "mp3",
        language: str = "en"
    ) -> str:
        """
        Generate voiceover from script.

        Args:
            script: Text to convert to speech
            voice_id: Voice ID (OpenAI voice name or ElevenLabs voice ID)
            provider: Voice provider (OPENAI or ELEVENLABS)
            model: Model to use (OpenAI: tts-1/tts-1-hd, ElevenLabs: auto-detect)
            settings: Voice generation settings
            output_format: Output audio format (mp3, wav, pcm)
            language: Language code (e.g., 'en', 'es', 'fr')

        Returns:
            Path to generated audio file
        """
        if settings is None:
            settings = VoiceSettings()

        logger.info(f"Generating voiceover with {provider.value}, voice: {voice_id}")

        if provider == VoiceProvider.OPENAI:
            return await self._generate_openai_tts(
                script, voice_id, model or OpenAIModel.TTS_1.value,
                settings, output_format
            )
        elif provider == VoiceProvider.ELEVENLABS:
            return await self._generate_elevenlabs_tts(
                script, voice_id, settings, output_format, language
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _generate_openai_tts(
        self,
        text: str,
        voice: str,
        model: str,
        settings: VoiceSettings,
        output_format: str
    ) -> str:
        """Generate speech using OpenAI TTS"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        # Output file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"openai_{voice}_{timestamp}.{output_format}"

        # OpenAI TTS API call
        url = f"{self.OPENAI_API_BASE}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        # Map format names (OpenAI uses different names)
        format_map = {
            "mp3": "mp3",
            "wav": "wav",
            "pcm": "pcm",
            "aac": "aac",
            "opus": "opus",
            "flac": "flac"
        }

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": format_map.get(output_format, "mp3"),
            "speed": settings.speed
        }

        logger.info(f"OpenAI TTS request: model={model}, voice={voice}, speed={settings.speed}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI TTS failed: {error_text}")

                # Save audio file
                async with aiofiles.open(output_file, 'wb') as f:
                    await f.write(await response.read())

        logger.info(f"Generated OpenAI voiceover: {output_file}")
        return str(output_file)

    async def _generate_elevenlabs_tts(
        self,
        text: str,
        voice_id: str,
        settings: VoiceSettings,
        output_format: str,
        language: str
    ) -> str:
        """Generate speech using ElevenLabs TTS"""
        if not self.elevenlabs_api_key:
            raise ValueError("ElevenLabs API key not configured")

        # Output file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"elevenlabs_{voice_id}_{timestamp}.{output_format}"

        # ElevenLabs TTS API call
        url = f"{self.ELEVENLABS_API_BASE}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json"
        }

        # Map output formats
        format_map = {
            "mp3": "mp3_44100_128",
            "wav": "pcm_44100",
            "pcm": "pcm_22050"
        }

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Supports 30+ languages
            "voice_settings": {
                "stability": settings.stability,
                "similarity_boost": settings.similarity_boost,
                "style": settings.style,
                "use_speaker_boost": settings.use_speaker_boost
            }
        }

        # Add language code for non-English
        if language != "en":
            payload["language_code"] = language

        logger.info(f"ElevenLabs TTS request: voice={voice_id}, language={language}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ElevenLabs TTS failed: {error_text}")

                # Save audio file
                async with aiofiles.open(output_file, 'wb') as f:
                    await f.write(await response.read())

        # Convert to desired format if needed
        if output_format != "mp3":
            output_file = await self._convert_audio_format(str(output_file), output_format)

        logger.info(f"Generated ElevenLabs voiceover: {output_file}")
        return str(output_file)

    async def clone_voice(
        self,
        config: VoiceCloneConfig
    ) -> str:
        """
        Clone a voice from audio samples (ElevenLabs only).

        Args:
            config: Voice cloning configuration

        Returns:
            Voice ID of cloned voice
        """
        if not self.elevenlabs_api_key:
            raise ValueError("ElevenLabs API key not configured")

        if not config.audio_samples:
            raise ValueError("At least one audio sample required for voice cloning")

        logger.info(f"Cloning voice: {config.name} ({len(config.audio_samples)} samples)")

        url = f"{self.ELEVENLABS_API_BASE}/voices/add"
        headers = {
            "xi-api-key": self.elevenlabs_api_key
        }

        # Prepare multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field("name", config.name)

        if config.description:
            form_data.add_field("description", config.description)

        # Add audio samples
        for i, sample_path in enumerate(config.audio_samples):
            if not os.path.exists(sample_path):
                raise ValueError(f"Audio sample not found: {sample_path}")

            async with aiofiles.open(sample_path, 'rb') as f:
                file_data = await f.read()
                form_data.add_field(
                    f"files",
                    file_data,
                    filename=os.path.basename(sample_path),
                    content_type="audio/mpeg"
                )

        # Add labels (metadata)
        if config.labels:
            form_data.add_field("labels", json.dumps(config.labels))

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=form_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Voice cloning failed: {error_text}")

                result = await response.json()
                voice_id = result.get("voice_id")

        # Add to voice library
        self.voice_library[voice_id] = {
            "voice_id": voice_id,
            "name": config.name,
            "description": config.description,
            "provider": "elevenlabs",
            "cloned": True,
            "created_at": datetime.utcnow().isoformat(),
            "labels": config.labels,
            "sample_count": len(config.audio_samples)
        }
        self._save_voice_library()

        logger.info(f"Voice cloned successfully: {config.name} (ID: {voice_id})")
        return voice_id

    async def get_available_voices(
        self,
        provider: VoiceProvider = VoiceProvider.OPENAI
    ) -> List[Dict[str, Any]]:
        """
        Get list of available voices.

        Args:
            provider: Voice provider

        Returns:
            List of voice metadata
        """
        if provider == VoiceProvider.OPENAI:
            # OpenAI voices are predefined
            return [
                {
                    "voice_id": "alloy",
                    "name": "Alloy",
                    "description": "Neutral, balanced voice",
                    "provider": "openai",
                    "gender": "neutral"
                },
                {
                    "voice_id": "echo",
                    "name": "Echo",
                    "description": "Male, clear voice",
                    "provider": "openai",
                    "gender": "male"
                },
                {
                    "voice_id": "fable",
                    "name": "Fable",
                    "description": "British male, authoritative voice",
                    "provider": "openai",
                    "gender": "male"
                },
                {
                    "voice_id": "onyx",
                    "name": "Onyx",
                    "description": "Deep male, dramatic voice",
                    "provider": "openai",
                    "gender": "male"
                },
                {
                    "voice_id": "nova",
                    "name": "Nova",
                    "description": "Female, warm voice",
                    "provider": "openai",
                    "gender": "female"
                },
                {
                    "voice_id": "shimmer",
                    "name": "Shimmer",
                    "description": "Female, energetic voice",
                    "provider": "openai",
                    "gender": "female"
                }
            ]

        elif provider == VoiceProvider.ELEVENLABS:
            if not self.elevenlabs_api_key:
                raise ValueError("ElevenLabs API key not configured")

            # Fetch voices from ElevenLabs API
            url = f"{self.ELEVENLABS_API_BASE}/voices"
            headers = {
                "xi-api-key": self.elevenlabs_api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Failed to fetch ElevenLabs voices: {error_text}")

                    result = await response.json()
                    voices = result.get("voices", [])

            # Format voice data
            formatted_voices = []
            for voice in voices:
                formatted_voices.append({
                    "voice_id": voice.get("voice_id"),
                    "name": voice.get("name"),
                    "description": voice.get("description", ""),
                    "provider": "elevenlabs",
                    "category": voice.get("category", ""),
                    "labels": voice.get("labels", {}),
                    "preview_url": voice.get("preview_url")
                })

            return formatted_voices

        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def sync_to_video(
        self,
        audio_path: str,
        video_path: str,
        output_path: Optional[str] = None,
        volume: float = 1.0,
        fade_in: float = 0.0,
        fade_out: float = 0.0
    ) -> str:
        """
        Add voiceover audio to video with proper synchronization.

        Args:
            audio_path: Path to voiceover audio file
            video_path: Path to source video file
            output_path: Output video path (optional)
            volume: Audio volume multiplier (0.0-2.0)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds

        Returns:
            Path to output video with voiceover
        """
        if not os.path.exists(audio_path):
            raise ValueError(f"Audio file not found: {audio_path}")

        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")

        if output_path is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"video_with_voiceover_{timestamp}.mp4")

        logger.info(f"Syncing voiceover to video: {video_path}")

        # Build FFmpeg filter chain
        audio_filters = []

        # Volume adjustment
        if volume != 1.0:
            audio_filters.append(f"volume={volume}")

        # Fade in
        if fade_in > 0:
            audio_filters.append(f"afade=t=in:st=0:d={fade_in}")

        # Fade out
        if fade_out > 0:
            # Get audio duration first
            duration = await self._get_audio_duration(audio_path)
            fade_start = duration - fade_out
            if fade_start > 0:
                audio_filters.append(f"afade=t=out:st={fade_start}:d={fade_out}")

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Input files
        cmd.extend(["-i", video_path])
        cmd.extend(["-i", audio_path])

        # Map video from first input
        cmd.extend(["-map", "0:v"])

        # Mix audio: original video audio + voiceover
        if audio_filters:
            filter_str = ",".join(audio_filters)
            cmd.extend([
                "-filter_complex",
                f"[1:a]{filter_str}[vo];[0:a][vo]amix=inputs=2:duration=first[aout]"
            ])
            cmd.extend(["-map", "[aout]"])
        else:
            cmd.extend([
                "-filter_complex",
                "[0:a][1:a]amix=inputs=2:duration=first[aout]"
            ])
            cmd.extend(["-map", "[aout]"])

        # Output codec settings
        cmd.extend([
            "-c:v", "copy",  # Copy video without re-encoding
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-shortest"  # Trim to shortest stream
        ])

        cmd.append(output_path)

        logger.info(f"FFmpeg command: {' '.join(cmd)}")

        # Execute FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"FFmpeg failed: {error_msg}")

        logger.info(f"Video with voiceover created: {output_path}")
        return output_path

    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration using ffprobe"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            audio_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Failed to get audio duration: {stderr.decode()}")

        data = json.loads(stdout.decode())
        return float(data["format"]["duration"])

    async def _convert_audio_format(
        self,
        input_path: str,
        output_format: str
    ) -> str:
        """Convert audio to different format using FFmpeg"""
        output_path = str(Path(input_path).with_suffix(f".{output_format}"))

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-acodec", "pcm_s16le" if output_format == "wav" else "copy",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Audio conversion failed: {stderr.decode()}")

        # Remove original file
        try:
            os.remove(input_path)
        except OSError:
            pass

        return output_path

    def get_voice_library(self) -> Dict[str, Dict[str, Any]]:
        """Get all voices in library"""
        return self.voice_library

    async def delete_voice(self, voice_id: str) -> bool:
        """
        Delete a cloned voice (ElevenLabs only).

        Args:
            voice_id: Voice ID to delete

        Returns:
            True if successful
        """
        if not self.elevenlabs_api_key:
            raise ValueError("ElevenLabs API key not configured")

        url = f"{self.ELEVENLABS_API_BASE}/voices/{voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to delete voice: {error_text}")

        # Remove from library
        if voice_id in self.voice_library:
            del self.voice_library[voice_id]
            self._save_voice_library()

        logger.info(f"Voice deleted: {voice_id}")
        return True


# ============================================================================
# HELPER FUNCTIONS & PRESETS
# ============================================================================

class VoicePresets:
    """Pre-configured voice presets for common use cases"""

    @staticmethod
    def professional_male() -> Tuple[str, VoiceSettings]:
        """Professional male voice (OpenAI Onyx)"""
        return (
            OpenAIVoice.ONYX.value,
            VoiceSettings(speed=1.0)
        )

    @staticmethod
    def professional_female() -> Tuple[str, VoiceSettings]:
        """Professional female voice (OpenAI Nova)"""
        return (
            OpenAIVoice.NOVA.value,
            VoiceSettings(speed=1.0)
        )

    @staticmethod
    def energetic_female() -> Tuple[str, VoiceSettings]:
        """Energetic female voice (OpenAI Shimmer)"""
        return (
            OpenAIVoice.SHIMMER.value,
            VoiceSettings(speed=1.05)
        )

    @staticmethod
    def authoritative_male() -> Tuple[str, VoiceSettings]:
        """Authoritative male voice (OpenAI Fable)"""
        return (
            OpenAIVoice.FABLE.value,
            VoiceSettings(speed=0.95)
        )

    @staticmethod
    def neutral_balanced() -> Tuple[str, VoiceSettings]:
        """Neutral balanced voice (OpenAI Alloy)"""
        return (
            OpenAIVoice.ALLOY.value,
            VoiceSettings(speed=1.0)
        )

    @staticmethod
    def clear_male() -> Tuple[str, VoiceSettings]:
        """Clear male voice (OpenAI Echo)"""
        return (
            OpenAIVoice.ECHO.value,
            VoiceSettings(speed=1.0)
        )


async def generate_multi_language_voiceover(
    generator: VoiceGenerator,
    script: str,
    languages: List[str],
    voice_id: str,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate voiceovers in multiple languages.

    Args:
        generator: VoiceGenerator instance
        script: Script text
        languages: List of language codes
        voice_id: ElevenLabs voice ID
        output_dir: Output directory

    Returns:
        Dict mapping language codes to audio file paths
    """
    results = {}

    for lang in languages:
        try:
            audio_path = await generator.generate_voiceover(
                script=script,
                voice_id=voice_id,
                provider=VoiceProvider.ELEVENLABS,
                language=lang
            )
            results[lang] = audio_path
            logger.info(f"Generated {lang} voiceover: {audio_path}")
        except Exception as e:
            logger.error(f"Failed to generate {lang} voiceover: {e}")

    return results


if __name__ == "__main__":
    # Example usage
    print("AI Voice Generator - ElevenLabs + OpenAI TTS")
    print("=" * 60)

    async def demo():
        # Initialize generator
        generator = VoiceGenerator()

        # Example 1: Generate OpenAI voiceover
        print("\n1. Generating OpenAI TTS voiceover...")
        try:
            audio_path = await generator.generate_voiceover(
                script="Transform your business with AI-powered video ads. Get 10x more engagement in just 30 days.",
                voice_id=OpenAIVoice.NOVA.value,
                provider=VoiceProvider.OPENAI,
                model=OpenAIModel.TTS_1_HD.value
            )
            print(f"✓ Generated: {audio_path}")
        except Exception as e:
            print(f"✗ Error: {e}")

        # Example 2: List available voices
        print("\n2. Listing available OpenAI voices...")
        try:
            voices = await generator.get_available_voices(VoiceProvider.OPENAI)
            for voice in voices:
                print(f"  - {voice['name']}: {voice['description']}")
        except Exception as e:
            print(f"✗ Error: {e}")

        # Example 3: Voice cloning (requires ElevenLabs API key)
        print("\n3. Voice cloning example (requires audio samples)...")
        print("  See VoiceCloneConfig for configuration options")

        print("\n" + "=" * 60)
        print("Voice generation system ready!")

    # Run demo
    asyncio.run(demo())
