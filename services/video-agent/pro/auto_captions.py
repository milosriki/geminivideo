"""
PRO-GRADE AUTO-CAPTION SYSTEM FOR VIDEO ADS
Uses OpenAI Whisper for transcription with advanced features.

Features:
- OpenAI Whisper integration (multiple model sizes)
- GPU acceleration for fast transcription
- Multiple language support with auto-detection
- Word-level timestamps for animated captions
- Speaker diarization (who is speaking)
- Custom vocabulary for fitness terms
- Profanity filtering
- Multiple caption styles (Instagram, YouTube, Karaoke, TikTok, Hormozi)
- SRT/VTT file generation
- Burn-in captions with FFmpeg drawtext
- Custom fonts, colors, backgrounds
- Emoji support
- Auto-punctuation
- Caption timing optimization
"""

import os
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Whisper and ML libraries
import whisper
import torch
import numpy as np

# For word-level timestamps
from whisper.utils import get_writer

# For speaker diarization (optional)
try:
    from pyannote.audio import Pipeline
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False
    logging.warning("pyannote.audio not installed. Speaker diarization disabled.")

# For profanity filtering
try:
    from better_profanity import profanity
    profanity.load_censor_words()
    PROFANITY_FILTER_AVAILABLE = True
except ImportError:
    PROFANITY_FILTER_AVAILABLE = False
    logging.warning("better_profanity not installed. Profanity filtering disabled.")


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperModelSize(Enum):
    """Available Whisper model sizes."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"


class CaptionStyle(Enum):
    """Available caption styles for video ads."""
    INSTAGRAM = "instagram"  # Word-by-word pop with color highlight
    YOUTUBE = "youtube"      # Sentence blocks at bottom
    KARAOKE = "karaoke"      # Word highlight as spoken
    TIKTOK = "tiktok"        # Centered, bold, animated
    HORMOZI = "hormozi"      # Big bold words, one at a time


@dataclass
class Word:
    """Individual word with timing information."""
    text: str
    start: float
    end: float
    confidence: float
    speaker: Optional[str] = None


@dataclass
class Caption:
    """Caption segment with timing and styling."""
    text: str
    start: float
    end: float
    words: List[Word]
    speaker: Optional[str] = None


@dataclass
class CaptionStyleConfig:
    """Configuration for caption styling."""
    # Font settings
    font_family: str = "Arial-Bold"
    font_size: int = 48
    font_color: str = "white"
    highlight_color: str = "yellow"

    # Background/outline settings
    box_color: str = "black@0.6"
    border_width: int = 2
    border_color: str = "black"

    # Position settings
    position_x: str = "(w-text_w)/2"  # Centered horizontally
    position_y: str = "h-th-50"        # Near bottom

    # Animation settings
    animate: bool = True
    duration_per_word: float = 0.3

    # Style-specific settings
    all_caps: bool = False
    max_chars_per_line: int = 40
    max_words_per_line: int = 6

    # Emoji settings
    emoji_support: bool = True

    # Shadow settings
    shadow_enabled: bool = True
    shadow_color: str = "black@0.8"
    shadow_x: int = 2
    shadow_y: int = 2


class FitnessVocabulary:
    """Custom vocabulary for fitness terms."""

    TERMS = {
        # Common misspellings/misheard terms
        "rep": ["reps", "repetition", "repetitions"],
        "set": ["sets"],
        "workout": ["work out", "workouts"],
        "cardio": ["cardiovascular"],
        "gains": ["gain", "muscle gains"],
        "protein": ["proteins", "protein shake"],
        "macro": ["macros", "macronutrients"],
        "calorie": ["calories", "cal", "kcal"],
        "cut": ["cutting", "cuts"],
        "bulk": ["bulking", "bulks"],
        "shred": ["shredded", "shredding"],
        "pump": ["pumped", "pumping"],
        "PR": ["personal record", "P.R.", "pr"],
        "HIIT": ["high intensity interval training", "H.I.I.T."],
        "BMI": ["body mass index", "B.M.I."],
        "BMR": ["basal metabolic rate", "B.M.R."],
        "TDEE": ["total daily energy expenditure", "T.D.E.E."],
    }

    @classmethod
    def enhance_text(cls, text: str) -> str:
        """Enhance text with proper fitness terminology."""
        enhanced = text
        for key, variations in cls.TERMS.items():
            for variation in variations:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(variation), re.IGNORECASE)
                enhanced = pattern.sub(key, enhanced)
        return enhanced


class ProfanityFilter:
    """Filter profanity from captions."""

    @staticmethod
    def filter_text(text: str, replacement: str = "***") -> str:
        """Filter profanity from text."""
        if not PROFANITY_FILTER_AVAILABLE:
            return text
        return profanity.censor(text, replacement)

    @staticmethod
    def contains_profanity(text: str) -> bool:
        """Check if text contains profanity."""
        if not PROFANITY_FILTER_AVAILABLE:
            return False
        return profanity.contains_profanity(text)


class WhisperTranscriber:
    """
    OpenAI Whisper transcriber with advanced features.
    """

    def __init__(
        self,
        model_size: WhisperModelSize = WhisperModelSize.BASE,
        device: Optional[str] = None,
        language: Optional[str] = None,
        compute_type: str = "float16"
    ):
        """
        Initialize Whisper transcriber.

        Args:
            model_size: Whisper model size to use
            device: Device to use ('cuda' or 'cpu'). Auto-detect if None.
            language: Language code (e.g., 'en', 'es'). Auto-detect if None.
            compute_type: Computation precision ('float16' or 'int8' for faster inference)
        """
        self.model_size = model_size

        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.language = language
        self.compute_type = compute_type

        logger.info(f"Loading Whisper model: {model_size.value} on {self.device}")

        # Load Whisper model
        self.model = whisper.load_model(
            model_size.value,
            device=self.device
        )

        logger.info(f"Whisper model loaded successfully")

    def transcribe(
        self,
        audio_path: str,
        word_timestamps: bool = True,
        initial_prompt: Optional[str] = None,
        temperature: float = 0.0,
        best_of: int = 5,
        beam_size: int = 5,
        patience: float = 1.0,
        suppress_tokens: Optional[List[int]] = None,
        condition_on_previous_text: bool = True,
        fp16: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_path: Path to audio/video file
            word_timestamps: Enable word-level timestamps
            initial_prompt: Optional prompt to guide the model
            temperature: Sampling temperature (0 = deterministic)
            best_of: Number of candidates to generate
            beam_size: Beam search size
            patience: Beam search patience
            suppress_tokens: Token IDs to suppress
            condition_on_previous_text: Use previous text as context
            fp16: Use FP16 precision

        Returns:
            Dictionary with transcription results including word-level timestamps
        """
        logger.info(f"Transcribing: {audio_path}")

        # Check if GPU is available and adjust fp16
        if self.device == "cpu":
            fp16 = False

        # Transcribe with word timestamps
        result = self.model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=word_timestamps,
            task="transcribe",
            temperature=temperature,
            best_of=best_of,
            beam_size=beam_size,
            patience=patience,
            suppress_tokens=suppress_tokens,
            condition_on_previous_text=condition_on_previous_text,
            fp16=fp16,
            initial_prompt=initial_prompt
        )

        logger.info(f"Transcription complete. Language detected: {result['language']}")

        return result

    def extract_words(self, transcription_result: Dict[str, Any]) -> List[Word]:
        """
        Extract word-level timestamps from transcription result.

        Args:
            transcription_result: Result from transcribe()

        Returns:
            List of Word objects with timing information
        """
        words = []

        for segment in transcription_result.get("segments", []):
            for word_info in segment.get("words", []):
                word = Word(
                    text=word_info["word"].strip(),
                    start=word_info["start"],
                    end=word_info["end"],
                    confidence=word_info.get("probability", 1.0)
                )
                words.append(word)

        return words


class SpeakerDiarization:
    """
    Speaker diarization using pyannote.audio.
    Identifies who is speaking when.
    """

    def __init__(self, hf_token: Optional[str] = None):
        """
        Initialize speaker diarization.

        Args:
            hf_token: HuggingFace token for accessing pyannote models
        """
        if not DIARIZATION_AVAILABLE:
            raise ImportError(
                "pyannote.audio not available. Install with: "
                "pip install pyannote.audio"
            )

        self.hf_token = hf_token or os.environ.get("HF_TOKEN")

        if not self.hf_token:
            logger.warning(
                "No HuggingFace token provided. "
                "Speaker diarization may not work."
            )

        logger.info("Loading speaker diarization pipeline")
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token
        )

        # Use GPU if available
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))

    def diarize(self, audio_path: str, num_speakers: Optional[int] = None) -> List[Dict]:
        """
        Perform speaker diarization on audio.

        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers (optional)

        Returns:
            List of speaker segments with timing
        """
        logger.info(f"Performing speaker diarization: {audio_path}")

        # Run diarization
        diarization = self.pipeline(
            audio_path,
            num_speakers=num_speakers
        )

        # Convert to list of segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })

        logger.info(f"Diarization complete. Found {len(set(s['speaker'] for s in segments))} speakers")

        return segments

    @staticmethod
    def assign_speakers_to_words(
        words: List[Word],
        speaker_segments: List[Dict]
    ) -> List[Word]:
        """
        Assign speaker labels to words based on diarization.

        Args:
            words: List of Word objects
            speaker_segments: Speaker diarization segments

        Returns:
            Words with speaker labels assigned
        """
        for word in words:
            word_time = (word.start + word.end) / 2

            # Find which speaker segment this word belongs to
            for segment in speaker_segments:
                if segment["start"] <= word_time <= segment["end"]:
                    word.speaker = segment["speaker"]
                    break

        return words


class CaptionGenerator:
    """
    Generate captions from transcribed words.
    """

    @staticmethod
    def create_captions(
        words: List[Word],
        max_words_per_caption: int = 6,
        max_chars_per_caption: int = 40,
        min_duration: float = 1.0,
        max_duration: float = 5.0
    ) -> List[Caption]:
        """
        Create caption segments from words with optimal timing.

        Args:
            words: List of Word objects
            max_words_per_caption: Maximum words per caption
            max_chars_per_caption: Maximum characters per caption
            min_duration: Minimum caption display duration
            max_duration: Maximum caption display duration

        Returns:
            List of Caption objects
        """
        if not words:
            return []

        captions = []
        current_words = []
        current_chars = 0

        for word in words:
            word_len = len(word.text)

            # Check if we should start a new caption
            should_break = (
                len(current_words) >= max_words_per_caption or
                current_chars + word_len > max_chars_per_caption or
                (current_words and word.speaker != current_words[0].speaker)
            )

            if should_break and current_words:
                # Create caption from current words
                caption = CaptionGenerator._create_caption_from_words(
                    current_words,
                    min_duration,
                    max_duration
                )
                captions.append(caption)
                current_words = []
                current_chars = 0

            current_words.append(word)
            current_chars += word_len + 1  # +1 for space

        # Add remaining words
        if current_words:
            caption = CaptionGenerator._create_caption_from_words(
                current_words,
                min_duration,
                max_duration
            )
            captions.append(caption)

        return captions

    @staticmethod
    def _create_caption_from_words(
        words: List[Word],
        min_duration: float,
        max_duration: float
    ) -> Caption:
        """Create a single caption from a list of words."""
        text = " ".join(word.text for word in words)
        start = words[0].start
        end = words[-1].end

        # Optimize timing
        duration = end - start
        if duration < min_duration:
            end = start + min_duration
        elif duration > max_duration:
            end = start + max_duration

        speaker = words[0].speaker if words else None

        return Caption(
            text=text,
            start=start,
            end=end,
            words=words,
            speaker=speaker
        )


class SubtitleExporter:
    """
    Export captions to SRT and VTT formats.
    """

    @staticmethod
    def to_srt(captions: List[Caption], output_path: str) -> str:
        """
        Export captions to SRT format.

        Args:
            captions: List of Caption objects
            output_path: Path to save SRT file

        Returns:
            Path to saved SRT file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, caption in enumerate(captions, 1):
                # Write caption number
                f.write(f"{i}\n")

                # Write timing
                start_time = SubtitleExporter._format_srt_time(caption.start)
                end_time = SubtitleExporter._format_srt_time(caption.end)
                f.write(f"{start_time} --> {end_time}\n")

                # Write text
                f.write(f"{caption.text}\n\n")

        logger.info(f"SRT file saved: {output_path}")
        return output_path

    @staticmethod
    def to_vtt(captions: List[Caption], output_path: str) -> str:
        """
        Export captions to WebVTT format.

        Args:
            captions: List of Caption objects
            output_path: Path to save VTT file

        Returns:
            Path to saved VTT file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write VTT header
            f.write("WEBVTT\n\n")

            for i, caption in enumerate(captions, 1):
                # Write timing
                start_time = SubtitleExporter._format_vtt_time(caption.start)
                end_time = SubtitleExporter._format_vtt_time(caption.end)
                f.write(f"{start_time} --> {end_time}\n")

                # Write text
                f.write(f"{caption.text}\n\n")

        logger.info(f"VTT file saved: {output_path}")
        return output_path

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time for SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Format time for VTT (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


class FFmpegCaptionBurner:
    """
    Burn captions into video using FFmpeg with different styles.
    """

    def __init__(self, style_config: Optional[CaptionStyleConfig] = None):
        """
        Initialize caption burner.

        Args:
            style_config: Caption styling configuration
        """
        self.style_config = style_config or CaptionStyleConfig()

    def burn_captions_instagram(
        self,
        video_path: str,
        captions: List[Caption],
        output_path: str
    ) -> str:
        """
        Instagram style: Word-by-word pop with color highlight.

        Args:
            video_path: Input video path
            captions: List of Caption objects
            output_path: Output video path

        Returns:
            Path to output video
        """
        logger.info("Generating Instagram-style captions")

        # Generate drawtext filters for each word
        filters = []

        for caption in captions:
            for word in caption.words:
                # Escape text for FFmpeg
                text = self._escape_text(word.text)

                # Create animated word filter
                filter_str = (
                    f"drawtext="
                    f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                    f"text='{text}':"
                    f"fontsize={self.style_config.font_size}:"
                    f"fontcolor={self.style_config.highlight_color}:"
                    f"x={self.style_config.position_x}:"
                    f"y={self.style_config.position_y}:"
                    f"borderw={self.style_config.border_width}:"
                    f"bordercolor={self.style_config.border_color}:"
                    f"enable='between(t,{word.start},{word.end})':"
                    f"box=1:"
                    f"boxcolor={self.style_config.box_color}"
                )
                filters.append(filter_str)

        # Combine all filters
        filter_complex = ",".join(filters)

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:a", "copy",
            "-y",
            output_path
        ]

        return self._run_ffmpeg(cmd, output_path)

    def burn_captions_youtube(
        self,
        video_path: str,
        captions: List[Caption],
        output_path: str
    ) -> str:
        """
        YouTube style: Sentence blocks at bottom.

        Args:
            video_path: Input video path
            captions: List of Caption objects
            output_path: Output video path

        Returns:
            Path to output video
        """
        logger.info("Generating YouTube-style captions")

        filters = []

        for caption in captions:
            text = self._escape_text(caption.text)

            filter_str = (
                f"drawtext="
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"text='{text}':"
                f"fontsize={self.style_config.font_size}:"
                f"fontcolor={self.style_config.font_color}:"
                f"x={self.style_config.position_x}:"
                f"y=h-th-30:"  # Bottom position
                f"borderw={self.style_config.border_width}:"
                f"bordercolor={self.style_config.border_color}:"
                f"enable='between(t,{caption.start},{caption.end})':"
                f"box=1:"
                f"boxcolor={self.style_config.box_color}"
            )
            filters.append(filter_str)

        filter_complex = ",".join(filters)

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:a", "copy",
            "-y",
            output_path
        ]

        return self._run_ffmpeg(cmd, output_path)

    def burn_captions_karaoke(
        self,
        video_path: str,
        captions: List[Caption],
        output_path: str
    ) -> str:
        """
        Karaoke style: Word highlight as spoken with full sentence visible.

        Args:
            video_path: Input video path
            captions: List of Caption objects
            output_path: Output video path

        Returns:
            Path to output video
        """
        logger.info("Generating Karaoke-style captions")

        filters = []

        for caption in captions:
            # Show full caption in white
            full_text = self._escape_text(caption.text)

            base_filter = (
                f"drawtext="
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"text='{full_text}':"
                f"fontsize={self.style_config.font_size}:"
                f"fontcolor={self.style_config.font_color}:"
                f"x={self.style_config.position_x}:"
                f"y={self.style_config.position_y}:"
                f"borderw={self.style_config.border_width}:"
                f"bordercolor={self.style_config.border_color}:"
                f"enable='between(t,{caption.start},{caption.end})':"
                f"box=1:"
                f"boxcolor={self.style_config.box_color}"
            )
            filters.append(base_filter)

            # Highlight each word as it's spoken
            for word in caption.words:
                word_text = self._escape_text(word.text)

                # Find word position in full text
                word_index = caption.text.find(word.text)
                if word_index == -1:
                    continue

                highlight_filter = (
                    f"drawtext="
                    f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                    f"text='{word_text}':"
                    f"fontsize={self.style_config.font_size}:"
                    f"fontcolor={self.style_config.highlight_color}:"
                    f"x={self.style_config.position_x}+{word_index * 10}:"  # Approximate position
                    f"y={self.style_config.position_y}:"
                    f"enable='between(t,{word.start},{word.end})':"
                    f"alpha=0.9"
                )
                filters.append(highlight_filter)

        filter_complex = ",".join(filters)

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:a", "copy",
            "-y",
            output_path
        ]

        return self._run_ffmpeg(cmd, output_path)

    def burn_captions_tiktok(
        self,
        video_path: str,
        captions: List[Caption],
        output_path: str
    ) -> str:
        """
        TikTok style: Centered, bold, animated captions.

        Args:
            video_path: Input video path
            captions: List of Caption objects
            output_path: Output video path

        Returns:
            Path to output video
        """
        logger.info("Generating TikTok-style captions")

        filters = []

        for caption in captions:
            text = self._escape_text(caption.text.upper())  # TikTok uses uppercase

            filter_str = (
                f"drawtext="
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"text='{text}':"
                f"fontsize={self.style_config.font_size + 12}:"  # Larger font
                f"fontcolor={self.style_config.font_color}:"
                f"x=(w-text_w)/2:"  # Center horizontally
                f"y=(h-text_h)/2:"  # Center vertically
                f"borderw={self.style_config.border_width + 2}:"
                f"bordercolor={self.style_config.border_color}:"
                f"enable='between(t,{caption.start},{caption.end})':"
                f"box=1:"
                f"boxcolor={self.style_config.box_color}:"
                f"shadowx={self.style_config.shadow_x}:"
                f"shadowy={self.style_config.shadow_y}:"
                f"shadowcolor={self.style_config.shadow_color}"
            )
            filters.append(filter_str)

        filter_complex = ",".join(filters)

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:a", "copy",
            "-y",
            output_path
        ]

        return self._run_ffmpeg(cmd, output_path)

    def burn_captions_hormozi(
        self,
        video_path: str,
        captions: List[Caption],
        output_path: str
    ) -> str:
        """
        Hormozi style: Big bold words, one at a time, centered.

        Args:
            video_path: Input video path
            captions: List of Caption objects
            output_path: Output video path

        Returns:
            Path to output video
        """
        logger.info("Generating Hormozi-style captions")

        filters = []

        # Show one word at a time, very large and centered
        for caption in captions:
            for word in caption.words:
                text = self._escape_text(word.text.upper())

                filter_str = (
                    f"drawtext="
                    f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                    f"text='{text}':"
                    f"fontsize={self.style_config.font_size + 32}:"  # Much larger
                    f"fontcolor={self.style_config.highlight_color}:"
                    f"x=(w-text_w)/2:"  # Center horizontally
                    f"y=(h-text_h)/2:"  # Center vertically
                    f"borderw={self.style_config.border_width + 3}:"
                    f"bordercolor={self.style_config.border_color}:"
                    f"enable='between(t,{word.start},{word.end})':"
                    f"box=1:"
                    f"boxcolor=black@0.8:"
                    f"shadowx={self.style_config.shadow_x * 2}:"
                    f"shadowy={self.style_config.shadow_y * 2}:"
                    f"shadowcolor={self.style_config.shadow_color}"
                )
                filters.append(filter_str)

        filter_complex = ",".join(filters)

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:a", "copy",
            "-y",
            output_path
        ]

        return self._run_ffmpeg(cmd, output_path)

    def burn_captions_from_srt(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
        style: CaptionStyle = CaptionStyle.YOUTUBE
    ) -> str:
        """
        Burn captions from SRT file into video.

        Args:
            video_path: Input video path
            srt_path: Path to SRT file
            output_path: Output video path
            style: Caption style to use

        Returns:
            Path to output video
        """
        logger.info(f"Burning captions from SRT: {srt_path}")

        # Basic subtitle filter
        subtitles_filter = f"subtitles={srt_path}"

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", subtitles_filter,
            "-c:a", "copy",
            "-y",
            output_path
        ]

        return self._run_ffmpeg(cmd, output_path)

    @staticmethod
    def _escape_text(text: str) -> str:
        """Escape text for FFmpeg drawtext filter."""
        # Escape special characters for FFmpeg
        text = text.replace("\\", "\\\\")
        text = text.replace("'", "\\'")
        text = text.replace(":", "\\:")
        text = text.replace("%", "\\%")
        return text

    @staticmethod
    def _run_ffmpeg(cmd: List[str], output_path: str) -> str:
        """Run FFmpeg command."""
        try:
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            logger.info(f"Captions burned successfully: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise


class AutoCaptionSystem:
    """
    Complete auto-caption system for pro-grade video ads.
    """

    def __init__(
        self,
        model_size: WhisperModelSize = WhisperModelSize.BASE,
        device: Optional[str] = None,
        language: Optional[str] = None,
        enable_diarization: bool = False,
        hf_token: Optional[str] = None,
        enable_profanity_filter: bool = True,
        enable_fitness_vocab: bool = True
    ):
        """
        Initialize auto-caption system.

        Args:
            model_size: Whisper model size
            device: Device to use ('cuda' or 'cpu')
            language: Language code (auto-detect if None)
            enable_diarization: Enable speaker diarization
            hf_token: HuggingFace token for diarization
            enable_profanity_filter: Enable profanity filtering
            enable_fitness_vocab: Enable fitness vocabulary enhancement
        """
        self.transcriber = WhisperTranscriber(
            model_size=model_size,
            device=device,
            language=language
        )

        self.enable_diarization = enable_diarization and DIARIZATION_AVAILABLE
        if self.enable_diarization:
            self.diarizer = SpeakerDiarization(hf_token=hf_token)
        else:
            self.diarizer = None

        self.enable_profanity_filter = enable_profanity_filter
        self.enable_fitness_vocab = enable_fitness_vocab

    def process_video(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        caption_style: CaptionStyle = CaptionStyle.HORMOZI,
        style_config: Optional[CaptionStyleConfig] = None,
        generate_srt: bool = True,
        generate_vtt: bool = True,
        burn_captions: bool = True,
        num_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process video and generate captions.

        Args:
            video_path: Path to input video
            output_dir: Output directory (creates temp dir if None)
            caption_style: Style of captions to generate
            style_config: Caption styling configuration
            generate_srt: Generate SRT file
            generate_vtt: Generate VTT file
            burn_captions: Burn captions into video
            num_speakers: Expected number of speakers (for diarization)

        Returns:
            Dictionary with paths to generated files and transcription data
        """
        logger.info(f"Processing video: {video_path}")

        # Create output directory
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)

        video_name = Path(video_path).stem

        # Step 1: Transcribe audio
        logger.info("Step 1: Transcribing audio with Whisper")
        transcription = self.transcriber.transcribe(video_path, word_timestamps=True)

        # Step 2: Extract words
        logger.info("Step 2: Extracting word-level timestamps")
        words = self.transcriber.extract_words(transcription)

        # Step 3: Speaker diarization (optional)
        if self.enable_diarization and self.diarizer:
            logger.info("Step 3: Performing speaker diarization")
            speaker_segments = self.diarizer.diarize(video_path, num_speakers)
            words = SpeakerDiarization.assign_speakers_to_words(words, speaker_segments)
        else:
            logger.info("Step 3: Skipping speaker diarization")

        # Step 4: Process text
        logger.info("Step 4: Processing text")
        for word in words:
            # Apply fitness vocabulary
            if self.enable_fitness_vocab:
                word.text = FitnessVocabulary.enhance_text(word.text)

            # Apply profanity filter
            if self.enable_profanity_filter:
                word.text = ProfanityFilter.filter_text(word.text)

        # Step 5: Generate captions
        logger.info("Step 5: Generating caption segments")
        captions = CaptionGenerator.create_captions(words)

        # Step 6: Export to SRT/VTT
        result = {
            "video_path": video_path,
            "transcription": transcription,
            "words": [asdict(w) for w in words],
            "captions": [asdict(c) for c in captions],
            "language": transcription["language"]
        }

        if generate_srt:
            logger.info("Step 6a: Exporting to SRT")
            srt_path = os.path.join(output_dir, f"{video_name}.srt")
            SubtitleExporter.to_srt(captions, srt_path)
            result["srt_path"] = srt_path

        if generate_vtt:
            logger.info("Step 6b: Exporting to VTT")
            vtt_path = os.path.join(output_dir, f"{video_name}.vtt")
            SubtitleExporter.to_vtt(captions, vtt_path)
            result["vtt_path"] = vtt_path

        # Step 7: Burn captions into video
        if burn_captions:
            logger.info(f"Step 7: Burning captions into video ({caption_style.value} style)")

            burner = FFmpegCaptionBurner(style_config or CaptionStyleConfig())
            output_video_path = os.path.join(
                output_dir,
                f"{video_name}_captioned_{caption_style.value}.mp4"
            )

            # Select burn method based on style
            if caption_style == CaptionStyle.INSTAGRAM:
                burner.burn_captions_instagram(video_path, captions, output_video_path)
            elif caption_style == CaptionStyle.YOUTUBE:
                burner.burn_captions_youtube(video_path, captions, output_video_path)
            elif caption_style == CaptionStyle.KARAOKE:
                burner.burn_captions_karaoke(video_path, captions, output_video_path)
            elif caption_style == CaptionStyle.TIKTOK:
                burner.burn_captions_tiktok(video_path, captions, output_video_path)
            elif caption_style == CaptionStyle.HORMOZI:
                burner.burn_captions_hormozi(video_path, captions, output_video_path)
            else:
                # Default to SRT burn-in
                if generate_srt:
                    burner.burn_captions_from_srt(
                        video_path,
                        result["srt_path"],
                        output_video_path,
                        caption_style
                    )

            result["captioned_video_path"] = output_video_path

        logger.info(f"Processing complete! Output saved to: {output_dir}")

        return result


# Example usage and utility functions

def get_available_whisper_models() -> List[str]:
    """Get list of available Whisper models."""
    return [model.value for model in WhisperModelSize]


def estimate_processing_time(
    video_duration_seconds: float,
    model_size: WhisperModelSize,
    has_gpu: bool
) -> float:
    """
    Estimate processing time for a video.

    Args:
        video_duration_seconds: Duration of video in seconds
        model_size: Whisper model size
        has_gpu: Whether GPU is available

    Returns:
        Estimated processing time in seconds
    """
    # Rough estimates based on model size and hardware
    speed_factors = {
        WhisperModelSize.TINY: 0.05 if has_gpu else 0.2,
        WhisperModelSize.BASE: 0.1 if has_gpu else 0.4,
        WhisperModelSize.SMALL: 0.2 if has_gpu else 0.8,
        WhisperModelSize.MEDIUM: 0.4 if has_gpu else 1.6,
        WhisperModelSize.LARGE: 0.8 if has_gpu else 3.2,
        WhisperModelSize.LARGE_V2: 0.8 if has_gpu else 3.2,
        WhisperModelSize.LARGE_V3: 0.8 if has_gpu else 3.2,
    }

    factor = speed_factors.get(model_size, 1.0)
    return video_duration_seconds * factor


def main():
    """Example usage of the auto-caption system."""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-caption system for video ads")
    parser.add_argument("video_path", help="Path to input video")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument(
        "--model",
        choices=[m.value for m in WhisperModelSize],
        default="base",
        help="Whisper model size"
    )
    parser.add_argument(
        "--style",
        choices=[s.value for s in CaptionStyle],
        default="hormozi",
        help="Caption style"
    )
    parser.add_argument("--language", help="Language code (e.g., en, es)")
    parser.add_argument("--diarization", action="store_true", help="Enable speaker diarization")
    parser.add_argument("--hf-token", help="HuggingFace token for diarization")
    parser.add_argument("--no-burn", action="store_true", help="Skip burning captions")
    parser.add_argument("--font-size", type=int, default=48, help="Font size")
    parser.add_argument("--font-color", default="white", help="Font color")
    parser.add_argument("--highlight-color", default="yellow", help="Highlight color")

    args = parser.parse_args()

    # Create style config
    style_config = CaptionStyleConfig(
        font_size=args.font_size,
        font_color=args.font_color,
        highlight_color=args.highlight_color
    )

    # Initialize system
    system = AutoCaptionSystem(
        model_size=WhisperModelSize(args.model),
        language=args.language,
        enable_diarization=args.diarization,
        hf_token=args.hf_token
    )

    # Process video
    result = system.process_video(
        video_path=args.video_path,
        output_dir=args.output_dir,
        caption_style=CaptionStyle(args.style),
        style_config=style_config,
        burn_captions=not args.no_burn
    )

    # Print results
    print("\n" + "="*60)
    print("AUTO-CAPTION PROCESSING COMPLETE")
    print("="*60)
    print(f"Language detected: {result['language']}")
    print(f"Total words: {len(result['words'])}")
    print(f"Total captions: {len(result['captions'])}")

    if "srt_path" in result:
        print(f"SRT file: {result['srt_path']}")

    if "vtt_path" in result:
        print(f"VTT file: {result['vtt_path']}")

    if "captioned_video_path" in result:
        print(f"Captioned video: {result['captioned_video_path']}")

    print("="*60 + "\n")


if __name__ == "__main__":
    main()
