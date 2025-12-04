"""
Whisper-based transcription service for video clips
Provides word-level timestamps, keyword extraction, and hook detection
"""
import os
import subprocess
import tempfile
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Whisper-based transcription service with audio extraction and keyword detection.

    Features:
    - Lazy loading of Whisper model (base size for speed/accuracy balance)
    - Audio extraction from video segments using FFmpeg
    - Word-level timestamps for precise editing
    - Keyword extraction for hook detection
    - Robust error handling with fallbacks
    """

    def __init__(self, model_size: str = "base"):
        """
        Initialize transcription service.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
                       base is recommended for production (good balance)
        """
        self.model = None
        self.model_size = model_size
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """Verify FFmpeg is installed"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("FFmpeg not found. Audio extraction will fail.")

    def _load_model(self):
        """Lazy load Whisper model on first use"""
        if self.model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self.model_size}")
                self.model = whisper.load_model(self.model_size)
                logger.info(f"Whisper model {self.model_size} loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise RuntimeError(f"Could not load Whisper model: {e}")

    def extract_audio(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract audio segment from video using FFmpeg.

        Args:
            video_path: Path to source video file
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Optional output path for audio file

        Returns:
            Path to extracted audio file, or None on failure
        """
        try:
            # Create temporary file if no output path specified
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.wav',
                    delete=False
                )
                output_path = temp_file.name
                temp_file.close()

            duration = end_time - start_time

            # FFmpeg command to extract audio segment
            # -ss: start time, -t: duration, -ac 1: mono, -ar 16000: 16kHz sample rate
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM audio codec
                '-ar', '16000',  # 16kHz sample rate (Whisper optimal)
                '-ac', '1',  # Mono channel
                '-y',  # Overwrite output file
                output_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60  # 60 second timeout
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr.decode()}")
                return None

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.error(f"Audio extraction failed: empty or missing file")
                return None

            logger.info(f"Audio extracted: {output_path} ({duration:.2f}s)")
            return output_path

        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout extracting audio from {video_path}")
            return None
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None

    def extract_transcript(
        self,
        video_path: str,
        start_time: float,
        end_time: float
    ) -> Dict:
        """
        Extract transcript from video segment with word-level timestamps.

        Args:
            video_path: Path to source video file
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            Dictionary containing:
            {
                'text': str,              # Full transcript text
                'segments': List[Dict],   # Segment-level data with timestamps
                'words': List[Dict],      # Word-level data with timestamps
                'language': str,          # Detected language code
                'keywords': List[str],    # Extracted keywords for hook detection
                'success': bool,          # Whether transcription succeeded
                'error': Optional[str]    # Error message if failed
            }
        """
        result = {
            'text': '',
            'segments': [],
            'words': [],
            'language': 'unknown',
            'keywords': [],
            'success': False,
            'error': None
        }

        audio_path = None
        try:
            # Load Whisper model
            self._load_model()

            # Extract audio segment
            audio_path = self.extract_audio(video_path, start_time, end_time)
            if audio_path is None:
                result['error'] = "Failed to extract audio from video"
                return result

            # Check audio file size (skip if too small)
            if os.path.getsize(audio_path) < 1000:  # Less than 1KB
                result['error'] = "Audio segment too short or empty"
                return result

            # Transcribe with Whisper
            logger.info(f"Transcribing audio: {audio_path}")
            transcription = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False
            )

            # Extract text
            result['text'] = transcription.get('text', '').strip()
            result['language'] = transcription.get('language', 'unknown')

            # Extract segments (sentence/phrase level)
            segments = transcription.get('segments', [])
            result['segments'] = [
                {
                    'text': seg.get('text', '').strip(),
                    'start': seg.get('start', 0.0),
                    'end': seg.get('end', 0.0),
                    'confidence': seg.get('avg_logprob', 0.0)
                }
                for seg in segments
            ]

            # Extract word-level timestamps
            words = []
            for seg in segments:
                if 'words' in seg:
                    for word in seg['words']:
                        words.append({
                            'word': word.get('word', '').strip(),
                            'start': word.get('start', 0.0),
                            'end': word.get('end', 0.0),
                            'probability': word.get('probability', 0.0)
                        })
            result['words'] = words

            # Extract keywords
            if result['text']:
                result['keywords'] = self.extract_keywords(result['text'])

            result['success'] = True
            logger.info(f"Transcription successful: {len(result['text'])} chars, "
                       f"{len(result['segments'])} segments, {len(words)} words")

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            result['error'] = str(e)

        finally:
            # Clean up temporary audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp audio file: {e}")

        return result

    def extract_keywords(
        self,
        text: str,
        min_word_length: int = 4,
        max_keywords: int = 20
    ) -> List[str]:
        """
        Extract keywords from transcript for hook detection.

        Identifies important words that might indicate hooks, catchphrases,
        or memorable moments in the content.

        Args:
            text: Transcript text
            min_word_length: Minimum word length to consider
            max_keywords: Maximum number of keywords to return

        Returns:
            List of keyword strings
        """
        if not text:
            return []

        try:
            # Normalize text
            text = text.lower()

            # Remove punctuation except apostrophes
            text = re.sub(r"[^\w\s']", ' ', text)

            # Split into words
            words = text.split()

            # Common stop words to exclude
            stop_words = {
                'the', 'and', 'for', 'that', 'this', 'with', 'from',
                'have', 'has', 'had', 'were', 'was', 'are', 'been',
                'will', 'would', 'could', 'should', 'can', 'may',
                'their', 'there', 'these', 'those', 'what', 'when',
                'where', 'which', 'who', 'why', 'how', 'about',
                'into', 'through', 'during', 'before', 'after',
                'above', 'below', 'between', 'under', 'over',
                'just', 'only', 'also', 'very', 'really', 'even',
                'because', 'while', 'although', 'though', 'unless'
            }

            # Hook indicator words (might indicate interesting moments)
            hook_indicators = {
                'amazing', 'incredible', 'shocking', 'secret', 'revealed',
                'discover', 'learn', 'trick', 'hack', 'tip', 'mistake',
                'never', 'always', 'believe', 'truth', 'fact', 'crazy',
                'insane', 'epic', 'massive', 'huge', 'important', 'critical',
                'warning', 'alert', 'breaking', 'announcement', 'reveal'
            }

            # Count word frequencies
            word_freq = {}
            for word in words:
                # Filter by length and stop words
                if len(word) >= min_word_length and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Boost hook indicators
            for word in word_freq:
                if word in hook_indicators:
                    word_freq[word] *= 3  # Triple the weight

            # Sort by frequency (descending)
            sorted_words = sorted(
                word_freq.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Return top keywords
            keywords = [word for word, freq in sorted_words[:max_keywords]]

            logger.debug(f"Extracted {len(keywords)} keywords from text")
            return keywords

        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []

    def get_transcript_segments_by_time(
        self,
        segments: List[Dict],
        start_time: float,
        end_time: float
    ) -> List[Dict]:
        """
        Filter transcript segments by time range.

        Args:
            segments: List of segment dictionaries with start/end times
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            Filtered list of segments within time range
        """
        filtered = []
        for seg in segments:
            seg_start = seg.get('start', 0.0)
            seg_end = seg.get('end', 0.0)

            # Include if segment overlaps with time range
            if seg_start < end_time and seg_end > start_time:
                filtered.append(seg)

        return filtered

    def search_transcript(
        self,
        segments: List[Dict],
        query: str,
        case_sensitive: bool = False
    ) -> List[Tuple[Dict, List[int]]]:
        """
        Search for query text in transcript segments.

        Args:
            segments: List of segment dictionaries
            query: Search query string
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of tuples: (segment, [match_positions])
        """
        results = []

        if not case_sensitive:
            query = query.lower()

        for seg in segments:
            text = seg.get('text', '')
            if not case_sensitive:
                text = text.lower()

            # Find all occurrences
            positions = []
            start = 0
            while True:
                pos = text.find(query, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1

            if positions:
                results.append((seg, positions))

        return results
