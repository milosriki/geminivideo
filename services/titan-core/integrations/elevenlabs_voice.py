"""
ElevenLabs Voice Integration

Professional voiceovers and voice cloning for video ads.
This enables:
- Generate voiceovers from scripts
- Clone voices for brand consistency
- Multilingual voiceovers
- Different voice personalities
"""

import os
import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time
import base64

logger = logging.getLogger(__name__)

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

class VoiceModel(Enum):
    ELEVEN_TURBO_V2 = "eleven_turbo_v2"  # Fast, good quality
    ELEVEN_MULTILINGUAL_V2 = "eleven_multilingual_v2"  # Best for languages
    ELEVEN_MONOLINGUAL_V1 = "eleven_monolingual_v1"  # English optimized

class VoiceStyle(Enum):
    CONVERSATIONAL = "conversational"
    NARRATIVE = "narrative"
    NEWS = "news"
    PROMOTIONAL = "promotional"
    EXCITED = "excited"
    CALM = "calm"

@dataclass
class VoiceSettings:
    """Voice generation settings"""
    stability: float = 0.5  # 0-1, higher = more consistent
    similarity_boost: float = 0.75  # 0-1, higher = more similar to original
    style: float = 0.5  # 0-1, style exaggeration
    use_speaker_boost: bool = True

@dataclass
class VoiceOverRequest:
    """Request for voiceover generation"""
    text: str
    voice_id: str  # ElevenLabs voice ID
    model: VoiceModel = VoiceModel.ELEVEN_TURBO_V2
    settings: VoiceSettings = None
    output_format: str = "mp3_44100_128"

@dataclass
class VoiceOverResult:
    """Result of voiceover generation"""
    audio_data: bytes
    audio_url: Optional[str]
    duration_seconds: float
    characters_used: int
    generation_time: float
    error: Optional[str] = None

# Popular pre-built voices
VOICE_PRESETS = {
    "adam": "pNInz6obpgDQGcFmaJgB",  # Deep male voice
    "rachel": "21m00Tcm4TlvDq8ikWAM",  # Calm female voice
    "domi": "AZnzlk1XvdvUeBnXmlld",  # Young female, energetic
    "bella": "EXAVITQu4vr4xnSDxMaL",  # Soft female voice
    "elli": "MF3mGyEYCl7XYWbV9V6O",  # Young female, American
    "josh": "TxGEqnHWrfWFTfGW9XjX",  # Deep male, American
    "arnold": "VR6AewLTigWG4xSOukaG",  # Strong male voice
    "sam": "yoZ06aMxZJJ28mfd3POQ",  # Young male, American
}

class ElevenLabsClient:
    """
    Client for ElevenLabs Text-to-Speech API.

    Features:
    - High-quality AI voiceovers
    - Voice cloning
    - Multiple languages
    - Voice customization
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.base_url = ELEVENLABS_API_URL

        if not self.api_key:
            logger.warning("ElevenLabs API key not set. Set ELEVENLABS_API_KEY.")

    async def generate_voiceover(self, request: VoiceOverRequest) -> VoiceOverResult:
        """
        Generate voiceover from text.

        Args:
            request: VoiceOverRequest with text, voice, settings

        Returns:
            VoiceOverResult with audio data or error
        """
        if not self.api_key:
            return VoiceOverResult(
                audio_data=b"",
                audio_url=None,
                duration_seconds=0,
                characters_used=0,
                generation_time=0,
                error="API key not configured"
            )

        start_time = time.time()

        settings = request.settings or VoiceSettings()

        payload = {
            "text": request.text,
            "model_id": request.model.value,
            "voice_settings": {
                "stability": settings.stability,
                "similarity_boost": settings.similarity_boost,
                "style": settings.style,
                "use_speaker_boost": settings.use_speaker_boost
            }
        }

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{request.voice_id}",
                    json=payload,
                    headers=headers
                )

                if response.status_code != 200:
                    return VoiceOverResult(
                        audio_data=b"",
                        audio_url=None,
                        duration_seconds=0,
                        characters_used=len(request.text),
                        generation_time=time.time() - start_time,
                        error=f"API error: {response.status_code}"
                    )

                audio_data = response.content

                # Estimate duration (rough: ~150 words per minute)
                word_count = len(request.text.split())
                estimated_duration = (word_count / 150) * 60

                return VoiceOverResult(
                    audio_data=audio_data,
                    audio_url=None,  # Would need to upload somewhere
                    duration_seconds=estimated_duration,
                    characters_used=len(request.text),
                    generation_time=time.time() - start_time
                )

        except Exception as e:
            logger.error(f"ElevenLabs generation failed: {e}")
            return VoiceOverResult(
                audio_data=b"",
                audio_url=None,
                duration_seconds=0,
                characters_used=0,
                generation_time=time.time() - start_time,
                error=str(e)
            )

    async def get_available_voices(self) -> List[Dict]:
        """Get list of available voices"""
        if not self.api_key:
            return []

        headers = {"xi-api-key": self.api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")

        return []

    async def clone_voice(self, name: str, audio_files: List[bytes],
                           description: str = "") -> Optional[str]:
        """
        Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice
            audio_files: List of audio file bytes (min 1, max 25)
            description: Optional description

        Returns:
            Voice ID if successful, None if failed
        """
        if not self.api_key:
            return None

        headers = {"xi-api-key": self.api_key}

        files = []
        for i, audio_data in enumerate(audio_files):
            files.append(("files", (f"sample_{i}.mp3", audio_data, "audio/mpeg")))

        data = {
            "name": name,
            "description": description
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/voices/add",
                    headers=headers,
                    data=data,
                    files=files
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("voice_id")
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")

        return None

    async def generate_ad_voiceover(self, script: str,
                                     voice_type: str = "energetic_male") -> VoiceOverResult:
        """Generate voiceover optimized for ads"""

        # Map voice types to presets
        voice_map = {
            "energetic_male": VOICE_PRESETS["josh"],
            "energetic_female": VOICE_PRESETS["domi"],
            "calm_male": VOICE_PRESETS["adam"],
            "calm_female": VOICE_PRESETS["rachel"],
            "young_female": VOICE_PRESETS["elli"],
            "young_male": VOICE_PRESETS["sam"],
            "authoritative": VOICE_PRESETS["arnold"]
        }

        voice_id = voice_map.get(voice_type, VOICE_PRESETS["josh"])

        # Optimized settings for ads
        settings = VoiceSettings(
            stability=0.6,  # Slightly more stable for clarity
            similarity_boost=0.8,
            style=0.7,  # More expressive for ads
            use_speaker_boost=True
        )

        return await self.generate_voiceover(VoiceOverRequest(
            text=script,
            voice_id=voice_id,
            model=VoiceModel.ELEVEN_TURBO_V2,
            settings=settings
        ))

    async def generate_multilingual(self, text: str, voice_id: str,
                                     language: str = "en") -> VoiceOverResult:
        """Generate voiceover in multiple languages"""
        return await self.generate_voiceover(VoiceOverRequest(
            text=text,
            voice_id=voice_id,
            model=VoiceModel.ELEVEN_MULTILINGUAL_V2
        ))

    def estimate_cost(self, text: str) -> Dict:
        """Estimate cost for text generation"""
        char_count = len(text)
        # ElevenLabs pricing is per character
        cost_per_char = 0.00003  # Approximate, check actual pricing

        return {
            "characters": char_count,
            "estimated_cost_usd": char_count * cost_per_char,
            "estimated_duration_seconds": (len(text.split()) / 150) * 60
        }


class MockElevenLabsClient:
    """Mock client for testing"""

    async def generate_voiceover(self, request: VoiceOverRequest) -> VoiceOverResult:
        await asyncio.sleep(1)
        return VoiceOverResult(
            audio_data=b"mock_audio_data",
            audio_url=None,
            duration_seconds=5.0,
            characters_used=len(request.text),
            generation_time=1.0
        )

    async def get_available_voices(self) -> List[Dict]:
        return [
            {"voice_id": "mock_voice_1", "name": "Mock Voice 1"},
            {"voice_id": "mock_voice_2", "name": "Mock Voice 2"}
        ]


def get_elevenlabs_client() -> ElevenLabsClient:
    """Get ElevenLabs client"""
    if ELEVENLABS_API_KEY:
        return ElevenLabsClient()
    else:
        logger.warning("Using mock ElevenLabs client - set ELEVENLABS_API_KEY for real audio")
        return MockElevenLabsClient()
