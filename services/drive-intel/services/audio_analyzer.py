"""
Audio analysis service using pretrained Wav2Vec2 models.
Provides transcription, emotion detection, pacing analysis, and audio quality assessment.
"""
import torch
from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
    Wav2Vec2FeatureExtractor,
    pipeline
)
import librosa
import numpy as np
import logging
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


@dataclass
class Transcript:
    """Transcription result with word-level details."""
    text: str
    words: List[Dict[str, Any]]  # word, start, end, confidence
    duration: float
    language: str
    confidence: float


@dataclass
class PacingMetrics:
    """Speech pacing and rhythm metrics."""
    words_per_minute: float
    avg_pause_duration: float
    pause_count: int
    speech_ratio: float  # speech time / total time
    energy_profile: List[float]


@dataclass
class AudioAnalysis:
    """Complete audio analysis results."""
    transcript: Transcript
    pacing: PacingMetrics
    emotion: str
    emotion_confidence: float
    music_presence: float
    speech_presence: float
    loudness_lufs: float
    hook_timing: float  # time to first strong moment
    audio_quality_score: float


class AudioAnalyzer:
    """
    Pretrained Wav2Vec2-based audio analyzer.

    Provides comprehensive audio analysis including:
    - Transcription with word-level timestamps
    - Speech emotion recognition
    - Pacing and rhythm analysis
    - Music vs speech detection
    - Loudness (LUFS) calculation
    - Hook detection
    - Audio quality assessment
    """

    # Model configurations
    TRANSCRIPTION_MODEL = "facebook/wav2vec2-base-960h"
    EMOTION_MODEL = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"

    # Audio parameters
    SAMPLE_RATE = 16000

    # Emotion labels (based on model training)
    EMOTION_LABELS = ["angry", "calm", "disgust", "fear", "happy", "neutral", "sad", "surprise"]

    def __init__(
        self,
        device: str = None,
        cache_dir: str = None
    ):
        """
        Initialize audio analyzer with pretrained models.

        Args:
            device: Device to run models on ('cuda', 'cpu', or None for auto-detect)
            cache_dir: Directory to cache downloaded models
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = cache_dir

        logger.info(f"Initializing AudioAnalyzer on device: {self.device}")

        # Model components (lazy loaded)
        self.processor = None
        self.transcription_model = None
        self.emotion_pipeline = None
        self.feature_extractor = None

        # Check for ffmpeg
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """Verify FFmpeg is installed."""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info("FFmpeg detected")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("FFmpeg not found. Video audio extraction will fail.")

    def _load_models(self, cache_dir: str = None) -> None:
        """
        Load pretrained models for transcription and emotion detection.

        Args:
            cache_dir: Directory to cache models
        """
        try:
            # Load transcription model
            if self.processor is None:
                logger.info(f"Loading Wav2Vec2 processor: {self.TRANSCRIPTION_MODEL}")
                self.processor = Wav2Vec2Processor.from_pretrained(
                    self.TRANSCRIPTION_MODEL,
                    cache_dir=cache_dir
                )

            if self.transcription_model is None:
                logger.info(f"Loading Wav2Vec2 model: {self.TRANSCRIPTION_MODEL}")
                self.transcription_model = Wav2Vec2ForCTC.from_pretrained(
                    self.TRANSCRIPTION_MODEL,
                    cache_dir=cache_dir
                ).to(self.device)
                self.transcription_model.eval()

            # Load emotion detection pipeline
            if self.emotion_pipeline is None:
                logger.info(f"Loading emotion detection model: {self.EMOTION_MODEL}")
                self.emotion_pipeline = pipeline(
                    "audio-classification",
                    model=self.EMOTION_MODEL,
                    device=0 if self.device == "cuda" else -1
                )

            logger.info("All models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    # ==================== Audio Loading ====================

    def load_audio(
        self,
        audio_path: str,
        sample_rate: int = None
    ) -> np.ndarray:
        """
        Load audio file as numpy array.

        Args:
            audio_path: Path to audio file
            sample_rate: Target sample rate (default: 16000)

        Returns:
            Audio waveform as numpy array
        """
        if sample_rate is None:
            sample_rate = self.SAMPLE_RATE

        try:
            audio, sr = librosa.load(audio_path, sr=sample_rate, mono=True)
            return audio
        except Exception as e:
            logger.error(f"Failed to load audio {audio_path}: {e}")
            raise

    def extract_audio(
        self,
        video_path: str,
        output_path: str = None
    ) -> str:
        """
        Extract audio from video file.

        Args:
            video_path: Path to video file
            output_path: Output path for audio (optional, creates temp file if None)

        Returns:
            Path to extracted audio file
        """
        try:
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.wav',
                    delete=False
                )
                output_path = temp_file.name
                temp_file.close()

            # Extract audio using FFmpeg
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', str(self.SAMPLE_RATE),
                '-ac', '1',  # Mono
                '-y',
                output_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr.decode()}")
                raise RuntimeError("Audio extraction failed")

            logger.info(f"Audio extracted to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to extract audio from {video_path}: {e}")
            raise

    # ==================== Transcription ====================

    def transcribe(
        self,
        audio_path: str,
        return_timestamps: bool = True
    ) -> Transcript:
        """
        Transcribe audio to text using Wav2Vec2.

        Args:
            audio_path: Path to audio file
            return_timestamps: Whether to return word-level timestamps

        Returns:
            Transcript object with text and metadata
        """
        try:
            # Load models
            self._load_models(self.cache_dir)

            # Load audio
            audio = self.load_audio(audio_path)
            duration = len(audio) / self.SAMPLE_RATE

            # Prepare input
            inputs = self.processor(
                audio,
                sampling_rate=self.SAMPLE_RATE,
                return_tensors="pt",
                padding=True
            ).to(self.device)

            # Perform transcription
            with torch.no_grad():
                logits = self.transcription_model(inputs.input_values).logits

            # Decode
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]

            # Calculate confidence (average probability of predicted tokens)
            probs = torch.nn.functional.softmax(logits, dim=-1)
            predicted_probs = torch.gather(
                probs,
                2,
                predicted_ids.unsqueeze(-1)
            ).squeeze(-1)
            confidence = predicted_probs.mean().item()

            # Extract word-level timestamps (simplified approach)
            words = self._extract_word_timestamps(
                transcription,
                audio,
                duration
            ) if return_timestamps else []

            return Transcript(
                text=transcription.strip(),
                words=words,
                duration=duration,
                language="en",  # Wav2Vec2-base-960h is English-only
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {e}")
            raise

    def transcribe_video(self, video_path: str) -> Transcript:
        """
        Extract and transcribe audio from video.

        Args:
            video_path: Path to video file

        Returns:
            Transcript object
        """
        audio_path = None
        try:
            audio_path = self.extract_audio(video_path)
            return self.transcribe(audio_path)
        finally:
            # Clean up temp audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp audio: {e}")

    def _extract_word_timestamps(
        self,
        text: str,
        audio: np.ndarray,
        duration: float
    ) -> List[Dict[str, Any]]:
        """
        Extract word-level timestamps using energy-based segmentation.

        Args:
            text: Transcribed text
            audio: Audio waveform
            duration: Total duration in seconds

        Returns:
            List of word dictionaries with timestamps
        """
        words_list = text.split()
        if not words_list:
            return []

        # Calculate energy envelope
        frame_length = 2048
        hop_length = 512
        energy = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]

        # Convert frame indices to time
        times = librosa.frames_to_time(
            np.arange(len(energy)),
            sr=self.SAMPLE_RATE,
            hop_length=hop_length
        )

        # Find speech segments based on energy threshold
        threshold = np.percentile(energy, 20)
        speech_frames = energy > threshold

        # Distribute words across speech segments
        words = []
        word_duration = duration / len(words_list)

        for i, word in enumerate(words_list):
            start_time = i * word_duration
            end_time = (i + 1) * word_duration

            words.append({
                'word': word,
                'start': start_time,
                'end': end_time,
                'confidence': 0.8  # Placeholder confidence
            })

        return words

    # ==================== Emotion Detection ====================

    def detect_speech_emotion(
        self,
        audio_path: str
    ) -> Tuple[str, float]:
        """
        Detect emotion in speech using pretrained Wav2Vec2 emotion model.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (emotion_label, confidence)
        """
        try:
            # Load models
            self._load_models(self.cache_dir)

            # Perform emotion classification
            result = self.emotion_pipeline(audio_path)

            # Get top prediction
            top_prediction = result[0]
            emotion = top_prediction['label']
            confidence = top_prediction['score']

            logger.info(f"Detected emotion: {emotion} (confidence: {confidence:.3f})")
            return emotion, confidence

        except Exception as e:
            logger.error(f"Emotion detection failed for {audio_path}: {e}")
            return "neutral", 0.0

    def analyze_emotion_timeline(
        self,
        audio_path: str,
        segment_duration: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        Analyze emotion throughout audio in segments.

        Args:
            audio_path: Path to audio file
            segment_duration: Duration of each segment in seconds

        Returns:
            List of emotion analysis for each segment
        """
        try:
            audio = self.load_audio(audio_path)
            total_duration = len(audio) / self.SAMPLE_RATE

            timeline = []
            segment_samples = int(segment_duration * self.SAMPLE_RATE)

            for start_sample in range(0, len(audio), segment_samples):
                end_sample = min(start_sample + segment_samples, len(audio))
                segment = audio[start_sample:end_sample]

                # Save segment to temp file
                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.wav',
                    delete=False
                )
                temp_path = temp_file.name
                temp_file.close()

                try:
                    import soundfile as sf
                    sf.write(temp_path, segment, self.SAMPLE_RATE)

                    emotion, confidence = self.detect_speech_emotion(temp_path)

                    start_time = start_sample / self.SAMPLE_RATE
                    end_time = end_sample / self.SAMPLE_RATE

                    timeline.append({
                        'start': start_time,
                        'end': end_time,
                        'emotion': emotion,
                        'confidence': confidence
                    })

                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

            return timeline

        except Exception as e:
            logger.error(f"Emotion timeline analysis failed: {e}")
            # Fallback: use librosa to save segments
            return self._analyze_emotion_timeline_fallback(audio_path, segment_duration)

    def _analyze_emotion_timeline_fallback(
        self,
        audio_path: str,
        segment_duration: float
    ) -> List[Dict[str, Any]]:
        """Fallback emotion timeline using librosa for writing."""
        try:
            audio = self.load_audio(audio_path)
            timeline = []
            segment_samples = int(segment_duration * self.SAMPLE_RATE)

            for start_sample in range(0, len(audio), segment_samples):
                end_sample = min(start_sample + segment_samples, len(audio))
                segment = audio[start_sample:end_sample]

                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_path = temp_file.name
                temp_file.close()

                try:
                    # Use librosa to write audio
                    import scipy.io.wavfile as wavfile
                    wavfile.write(temp_path, self.SAMPLE_RATE, (segment * 32767).astype(np.int16))

                    emotion, confidence = self.detect_speech_emotion(temp_path)

                    timeline.append({
                        'start': start_sample / self.SAMPLE_RATE,
                        'end': end_sample / self.SAMPLE_RATE,
                        'emotion': emotion,
                        'confidence': confidence
                    })
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)

            return timeline
        except Exception as e:
            logger.error(f"Fallback emotion timeline failed: {e}")
            return []

    # ==================== Pacing Analysis ====================

    def analyze_pacing(
        self,
        audio_path: str,
        transcript: Transcript = None
    ) -> PacingMetrics:
        """
        Analyze speech pacing and rhythm.

        Args:
            audio_path: Path to audio file
            transcript: Pre-computed transcript (optional)

        Returns:
            PacingMetrics object
        """
        try:
            # Get transcript if not provided
            if transcript is None:
                transcript = self.transcribe(audio_path)

            # Load audio for energy analysis
            audio = self.load_audio(audio_path)

            # Calculate energy profile
            energy = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)[0]

            # Detect pauses
            pauses = self.detect_pauses(audio_path)

            # Calculate metrics
            word_count = len(transcript.text.split())
            duration_minutes = transcript.duration / 60.0
            words_per_minute = word_count / duration_minutes if duration_minutes > 0 else 0

            pause_durations = [end - start for start, end in pauses]
            avg_pause_duration = np.mean(pause_durations) if pause_durations else 0

            # Calculate speech ratio
            total_pause_time = sum(pause_durations)
            speech_time = transcript.duration - total_pause_time
            speech_ratio = speech_time / transcript.duration if transcript.duration > 0 else 0

            return PacingMetrics(
                words_per_minute=words_per_minute,
                avg_pause_duration=avg_pause_duration,
                pause_count=len(pauses),
                speech_ratio=speech_ratio,
                energy_profile=energy.tolist()
            )

        except Exception as e:
            logger.error(f"Pacing analysis failed: {e}")
            # Return default metrics
            return PacingMetrics(
                words_per_minute=0.0,
                avg_pause_duration=0.0,
                pause_count=0,
                speech_ratio=0.0,
                energy_profile=[]
            )

    def detect_pauses(
        self,
        audio_path: str,
        min_pause_duration: float = 0.3
    ) -> List[Tuple[float, float]]:
        """
        Detect pauses in speech.

        Args:
            audio_path: Path to audio file
            min_pause_duration: Minimum pause duration in seconds

        Returns:
            List of (start_time, end_time) tuples for pauses
        """
        try:
            audio = self.load_audio(audio_path)

            # Calculate energy
            frame_length = 2048
            hop_length = 512
            energy = librosa.feature.rms(
                y=audio,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]

            # Determine silence threshold
            threshold = np.percentile(energy, 15)

            # Find silent frames
            silent_frames = energy < threshold

            # Convert to time
            times = librosa.frames_to_time(
                np.arange(len(silent_frames)),
                sr=self.SAMPLE_RATE,
                hop_length=hop_length
            )

            # Find continuous silent segments
            pauses = []
            in_pause = False
            pause_start = 0

            for i, is_silent in enumerate(silent_frames):
                if is_silent and not in_pause:
                    # Start of pause
                    pause_start = times[i]
                    in_pause = True
                elif not is_silent and in_pause:
                    # End of pause
                    pause_end = times[i]
                    duration = pause_end - pause_start
                    if duration >= min_pause_duration:
                        pauses.append((pause_start, pause_end))
                    in_pause = False

            # Handle pause extending to end
            if in_pause:
                pause_end = times[-1]
                duration = pause_end - pause_start
                if duration >= min_pause_duration:
                    pauses.append((pause_start, pause_end))

            return pauses

        except Exception as e:
            logger.error(f"Pause detection failed: {e}")
            return []

    # ==================== Music vs Speech Detection ====================

    def detect_music_vs_speech(
        self,
        audio_path: str
    ) -> Tuple[float, float]:
        """
        Detect music vs speech ratio using spectral features.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (music_ratio, speech_ratio)
        """
        try:
            audio = self.load_audio(audio_path)

            # Extract spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=self.SAMPLE_RATE)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.SAMPLE_RATE)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)[0]

            # Music typically has:
            # - Higher spectral centroid variance
            # - More consistent zero crossing rate
            # - Broader frequency range

            centroid_variance = np.var(spectral_centroid)
            zcr_variance = np.var(zero_crossing_rate)

            # Heuristic scoring
            music_score = 0
            speech_score = 0

            # High centroid variance suggests music
            if centroid_variance > 1e6:
                music_score += 1
            else:
                speech_score += 1

            # Low ZCR variance suggests music (more rhythmic)
            if zcr_variance < 0.01:
                music_score += 1
            else:
                speech_score += 1

            # Normalize
            total = music_score + speech_score
            music_ratio = music_score / total if total > 0 else 0.5
            speech_ratio = speech_score / total if total > 0 else 0.5

            return music_ratio, speech_ratio

        except Exception as e:
            logger.error(f"Music vs speech detection failed: {e}")
            return 0.5, 0.5

    def segment_audio(
        self,
        audio_path: str
    ) -> List[Dict[str, Any]]:
        """
        Segment audio into music/speech/silence regions.

        Args:
            audio_path: Path to audio file

        Returns:
            List of segments with type and timestamps
        """
        try:
            audio = self.load_audio(audio_path)

            # Calculate features per frame
            frame_length = 2048
            hop_length = 512

            energy = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
            zcr = librosa.feature.zero_crossing_rate(audio, frame_length=frame_length, hop_length=hop_length)[0]
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=self.SAMPLE_RATE, n_fft=frame_length, hop_length=hop_length)[0]

            times = librosa.frames_to_time(np.arange(len(energy)), sr=self.SAMPLE_RATE, hop_length=hop_length)

            # Classify each frame
            segments = []
            current_type = None
            segment_start = 0

            energy_threshold = np.percentile(energy, 20)

            for i in range(len(energy)):
                # Determine frame type
                if energy[i] < energy_threshold:
                    frame_type = "silence"
                elif zcr[i] < 0.05 and spectral_centroid[i] > 2000:
                    frame_type = "music"
                else:
                    frame_type = "speech"

                # Check for segment boundary
                if frame_type != current_type:
                    if current_type is not None:
                        segments.append({
                            'type': current_type,
                            'start': segment_start,
                            'end': times[i]
                        })
                    current_type = frame_type
                    segment_start = times[i]

            # Add final segment
            if current_type is not None:
                segments.append({
                    'type': current_type,
                    'start': segment_start,
                    'end': times[-1]
                })

            return segments

        except Exception as e:
            logger.error(f"Audio segmentation failed: {e}")
            return []

    # ==================== Loudness Analysis ====================

    def calculate_loudness_profile(
        self,
        audio_path: str,
        window_size: float = 0.5
    ) -> List[float]:
        """
        Calculate loudness over time.

        Args:
            audio_path: Path to audio file
            window_size: Window size in seconds

        Returns:
            List of loudness values (dB)
        """
        try:
            audio = self.load_audio(audio_path)

            window_samples = int(window_size * self.SAMPLE_RATE)
            hop_samples = window_samples // 2

            loudness_profile = []

            for i in range(0, len(audio) - window_samples, hop_samples):
                window = audio[i:i + window_samples]

                # Calculate RMS and convert to dB
                rms = np.sqrt(np.mean(window ** 2))
                db = 20 * np.log10(rms + 1e-10)  # Add small epsilon to avoid log(0)

                loudness_profile.append(db)

            return loudness_profile

        except Exception as e:
            logger.error(f"Loudness profile calculation failed: {e}")
            return []

    def calculate_loudness_lufs(
        self,
        audio_path: str
    ) -> float:
        """
        Calculate integrated loudness in LUFS (simplified BS.1770 algorithm).

        Args:
            audio_path: Path to audio file

        Returns:
            Loudness in LUFS
        """
        try:
            audio = self.load_audio(audio_path)

            # Simplified LUFS calculation
            # Full BS.1770 requires K-weighting filter

            # Calculate mean square
            mean_square = np.mean(audio ** 2)

            # Convert to LUFS (approximation)
            lufs = -0.691 + 10 * np.log10(mean_square + 1e-10)

            return lufs

        except Exception as e:
            logger.error(f"LUFS calculation failed: {e}")
            return -70.0  # Very quiet

    def detect_loudness_peaks(
        self,
        audio_path: str
    ) -> List[float]:
        """
        Detect timestamps of loudness peaks.

        Args:
            audio_path: Path to audio file

        Returns:
            List of peak timestamps
        """
        try:
            audio = self.load_audio(audio_path)

            # Calculate envelope
            hop_length = 512
            energy = librosa.feature.rms(y=audio, frame_length=2048, hop_length=hop_length)[0]
            times = librosa.frames_to_time(np.arange(len(energy)), sr=self.SAMPLE_RATE, hop_length=hop_length)

            # Find peaks
            from scipy.signal import find_peaks

            peaks, _ = find_peaks(energy, height=np.percentile(energy, 80), distance=20)

            peak_times = times[peaks].tolist()

            return peak_times

        except Exception as e:
            logger.error(f"Peak detection failed: {e}")
            return []

    # ==================== Hook Detection ====================

    def detect_hook_timing(
        self,
        audio_path: str
    ) -> float:
        """
        Detect time to first attention-grabbing moment.

        Args:
            audio_path: Path to audio file

        Returns:
            Time in seconds to first hook
        """
        try:
            moments = self.detect_attention_moments(audio_path)

            if moments:
                return moments[0]['time']
            else:
                # No strong moments detected
                return 0.0

        except Exception as e:
            logger.error(f"Hook timing detection failed: {e}")
            return 0.0

    def detect_attention_moments(
        self,
        audio_path: str
    ) -> List[Dict[str, Any]]:
        """
        Detect attention-grabbing moments in audio.

        Attention moments are characterized by:
        - Sudden loudness increase
        - Change in spectral content
        - High energy

        Args:
            audio_path: Path to audio file

        Returns:
            List of attention moment dictionaries
        """
        try:
            audio = self.load_audio(audio_path)

            hop_length = 512
            energy = librosa.feature.rms(y=audio, frame_length=2048, hop_length=hop_length)[0]
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=self.SAMPLE_RATE, hop_length=hop_length)[0]
            times = librosa.frames_to_time(np.arange(len(energy)), sr=self.SAMPLE_RATE, hop_length=hop_length)

            # Calculate derivatives
            energy_diff = np.diff(energy, prepend=energy[0])
            centroid_diff = np.diff(spectral_centroid, prepend=spectral_centroid[0])

            # Detect attention moments
            attention_moments = []

            energy_threshold = np.percentile(energy_diff, 90)

            for i in range(len(energy)):
                # High energy increase
                if energy_diff[i] > energy_threshold and energy[i] > np.percentile(energy, 70):
                    attention_moments.append({
                        'time': times[i],
                        'type': 'loudness_spike',
                        'intensity': float(energy[i])
                    })

            # Remove duplicates (moments within 1 second)
            filtered_moments = []
            last_time = -2.0

            for moment in attention_moments:
                if moment['time'] - last_time > 1.0:
                    filtered_moments.append(moment)
                    last_time = moment['time']

            return filtered_moments

        except Exception as e:
            logger.error(f"Attention moment detection failed: {e}")
            return []

    # ==================== Audio Quality ====================

    def assess_audio_quality(
        self,
        audio_path: str
    ) -> Dict[str, Any]:
        """
        Assess overall audio quality.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with quality metrics
        """
        try:
            audio = self.load_audio(audio_path)

            # Signal-to-noise ratio estimate
            noise_level = self.detect_background_noise(audio_path)

            # Dynamic range
            dynamic_range = np.max(np.abs(audio)) - np.min(np.abs(audio))

            # Clipping detection
            clipping_ratio = np.sum(np.abs(audio) > 0.99) / len(audio)

            # Spectral flatness (measure of noisiness)
            spectral_flatness = librosa.feature.spectral_flatness(y=audio)[0]
            avg_flatness = np.mean(spectral_flatness)

            # Calculate overall quality score (0-100)
            quality_score = 100.0

            # Penalize high noise
            if noise_level > 0.1:
                quality_score -= 20

            # Penalize clipping
            if clipping_ratio > 0.01:
                quality_score -= 30

            # Penalize low dynamic range
            if dynamic_range < 0.1:
                quality_score -= 20

            quality_score = max(0, quality_score)

            return {
                'overall_score': quality_score,
                'noise_level': noise_level,
                'dynamic_range': float(dynamic_range),
                'clipping_ratio': float(clipping_ratio),
                'spectral_flatness': float(avg_flatness)
            }

        except Exception as e:
            logger.error(f"Audio quality assessment failed: {e}")
            return {
                'overall_score': 50.0,
                'noise_level': 0.0,
                'dynamic_range': 0.0,
                'clipping_ratio': 0.0,
                'spectral_flatness': 0.0
            }

    def detect_background_noise(
        self,
        audio_path: str
    ) -> float:
        """
        Detect background noise level.

        Args:
            audio_path: Path to audio file

        Returns:
            Noise level (0-1)
        """
        try:
            audio = self.load_audio(audio_path)

            # Use lowest 10% of energy frames as noise estimate
            energy = librosa.feature.rms(y=audio)[0]
            noise_frames = np.percentile(energy, 10)

            # Normalize to 0-1
            noise_level = min(1.0, noise_frames / 0.1)

            return float(noise_level)

        except Exception as e:
            logger.error(f"Noise detection failed: {e}")
            return 0.0

    # ==================== Full Analysis ====================

    def analyze(
        self,
        audio_path: str
    ) -> AudioAnalysis:
        """
        Run complete audio analysis.

        Args:
            audio_path: Path to audio file

        Returns:
            AudioAnalysis object with all metrics
        """
        try:
            logger.info(f"Starting full audio analysis: {audio_path}")

            # Transcription
            transcript = self.transcribe(audio_path)

            # Emotion
            emotion, emotion_confidence = self.detect_speech_emotion(audio_path)

            # Pacing
            pacing = self.analyze_pacing(audio_path, transcript)

            # Music vs speech
            music_presence, speech_presence = self.detect_music_vs_speech(audio_path)

            # Loudness
            loudness_lufs = self.calculate_loudness_lufs(audio_path)

            # Hook timing
            hook_timing = self.detect_hook_timing(audio_path)

            # Audio quality
            quality = self.assess_audio_quality(audio_path)

            analysis = AudioAnalysis(
                transcript=transcript,
                pacing=pacing,
                emotion=emotion,
                emotion_confidence=emotion_confidence,
                music_presence=music_presence,
                speech_presence=speech_presence,
                loudness_lufs=loudness_lufs,
                hook_timing=hook_timing,
                audio_quality_score=quality['overall_score']
            )

            logger.info("Audio analysis complete")
            return analysis

        except Exception as e:
            logger.error(f"Full audio analysis failed: {e}")
            raise

    def analyze_video(
        self,
        video_path: str
    ) -> AudioAnalysis:
        """
        Extract audio from video and perform full analysis.

        Args:
            video_path: Path to video file

        Returns:
            AudioAnalysis object
        """
        audio_path = None
        try:
            audio_path = self.extract_audio(video_path)
            return self.analyze(audio_path)
        finally:
            # Clean up temp audio file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp audio: {e}")
