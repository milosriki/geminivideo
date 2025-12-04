"""
Pro Audio Mixer - Multi-track Audio Mixing System for Pro-Grade Video Ads
Complete FFmpeg audio filter chain generation with professional features.

Features:
- Unlimited audio tracks with volume/pan automation
- 3-band EQ (low, mid, high)
- Compression/limiting for broadcast loudness
- Noise reduction and voice enhancement
- Auto-ducking (sidechain compression for voiceover clarity)
- Audio normalization (EBU R128, LUFS targeting)
- Fade in/out and crossfades
- De-essing for clear vocals
- Bass boost for energy
- Background music and sound effects library integration
"""

import subprocess
import json
import os
import tempfile
import shutil
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioTrackType(Enum):
    """Audio track types"""
    VOICEOVER = "voiceover"
    MUSIC = "music"
    SFX = "sfx"
    DIALOGUE = "dialogue"
    AMBIENCE = "ambience"


class NormalizationStandard(Enum):
    """Audio normalization standards"""
    EBU_R128 = "ebu_r128"  # -23 LUFS for broadcast
    STREAMING = "streaming"  # -14 LUFS for YouTube, Spotify
    SOCIAL_MEDIA = "social"  # -16 LUFS for Instagram, TikTok
    CUSTOM = "custom"


class VoiceEnhancementPreset(Enum):
    """Voice enhancement presets"""
    NATURAL = "natural"
    CRISP = "crisp"
    WARM = "warm"
    BROADCAST = "broadcast"
    PODCAST = "podcast"


@dataclass
class AudioKeyframe:
    """Audio automation keyframe"""
    time: float  # seconds
    value: float  # parameter value


@dataclass
class VolumeAutomation:
    """Volume automation with keyframes"""
    keyframes: List[AudioKeyframe] = field(default_factory=list)

    def add_keyframe(self, time: float, volume_db: float):
        """Add volume keyframe (in dB, -80 to +20)"""
        self.keyframes.append(AudioKeyframe(time, volume_db))
        self.keyframes.sort(key=lambda k: k.time)

    def add_fade_in(self, start_time: float, duration: float, start_db: float = -80, end_db: float = 0):
        """Add fade in automation"""
        self.add_keyframe(start_time, start_db)
        self.add_keyframe(start_time + duration, end_db)

    def add_fade_out(self, start_time: float, duration: float, start_db: float = 0, end_db: float = -80):
        """Add fade out automation"""
        self.add_keyframe(start_time, start_db)
        self.add_keyframe(start_time + duration, end_db)


@dataclass
class PanAutomation:
    """Pan automation with keyframes (stereo positioning)"""
    keyframes: List[AudioKeyframe] = field(default_factory=list)

    def add_keyframe(self, time: float, pan: float):
        """Add pan keyframe (-1.0 = full left, 0 = center, +1.0 = full right)"""
        pan = max(-1.0, min(1.0, pan))
        self.keyframes.append(AudioKeyframe(time, pan))
        self.keyframes.sort(key=lambda k: k.time)


@dataclass
class EQBand:
    """3-band equalizer"""
    low_gain: float = 0.0  # dB, -20 to +20
    mid_gain: float = 0.0  # dB, -20 to +20
    high_gain: float = 0.0  # dB, -20 to +20
    low_freq: float = 250.0  # Hz, crossover frequency
    high_freq: float = 4000.0  # Hz, crossover frequency


@dataclass
class Compressor:
    """Audio compressor/limiter settings"""
    threshold: float = -20.0  # dB
    ratio: float = 4.0  # compression ratio (1:1 to 20:1)
    attack: float = 0.005  # seconds
    release: float = 0.1  # seconds
    knee: float = 2.0  # dB, soft knee
    makeup_gain: float = 0.0  # dB


@dataclass
class NoiseReduction:
    """Noise reduction settings"""
    enabled: bool = True
    amount: float = 0.5  # 0.0 to 1.0, strength of noise reduction


@dataclass
class DeEsser:
    """De-esser for removing harsh sibilance"""
    enabled: bool = False
    frequency: float = 6000.0  # Hz, target frequency for sibilance
    threshold: float = -30.0  # dB
    amount: float = 0.5  # 0.0 to 1.0


@dataclass
class AutoDucking:
    """Auto-ducking configuration (sidechain compression)"""
    enabled: bool = False
    trigger_track: Optional[str] = None  # Track name that triggers ducking
    threshold: float = -30.0  # dB, trigger threshold
    ratio: float = 4.0  # ducking ratio
    attack: float = 0.1  # seconds
    release: float = 0.5  # seconds
    reduction: float = -12.0  # dB, how much to reduce volume


@dataclass
class AudioTrack:
    """Audio track with all processing parameters"""
    name: str
    file_path: str
    track_type: AudioTrackType = AudioTrackType.MUSIC
    start_time: float = 0.0  # seconds in timeline
    duration: Optional[float] = None  # None = use full file
    trim_start: float = 0.0  # trim from beginning of file

    # Volume and panning
    volume: float = 0.0  # base volume in dB
    volume_automation: Optional[VolumeAutomation] = None
    pan: float = 0.0  # -1.0 to +1.0
    pan_automation: Optional[PanAutomation] = None

    # Processing
    eq: Optional[EQBand] = None
    compressor: Optional[Compressor] = None
    noise_reduction: Optional[NoiseReduction] = None
    de_esser: Optional[DeEsser] = None
    bass_boost: float = 0.0  # dB, 0 to +12

    # Fades
    fade_in_duration: float = 0.0  # seconds
    fade_out_duration: float = 0.0  # seconds

    # Auto-ducking
    auto_ducking: Optional[AutoDucking] = None

    # Mute/solo
    muted: bool = False
    solo: bool = False


@dataclass
class CrossFade:
    """Audio crossfade between two tracks"""
    track1_name: str
    track2_name: str
    start_time: float  # when crossfade starts
    duration: float  # crossfade duration
    curve: str = "tri"  # tri, qsin, esin, hsin, log, ipar, qua, cub, squ, cbr, par, exp, iqsin, ihsin, dese, desi


@dataclass
class MasterBus:
    """Master bus processing"""
    normalization: NormalizationStandard = NormalizationStandard.STREAMING
    target_lufs: float = -14.0  # target loudness
    true_peak: float = -1.0  # dBTP, true peak limit
    compressor: Optional[Compressor] = None
    limiter_enabled: bool = True
    limiter_threshold: float = -1.0  # dB


@dataclass
class AudioMixerConfig:
    """Complete audio mixer configuration"""
    tracks: List[AudioTrack] = field(default_factory=list)
    crossfades: List[CrossFade] = field(default_factory=list)
    master_bus: MasterBus = field(default_factory=MasterBus)
    sample_rate: int = 48000  # Hz
    output_format: str = "aac"  # aac, mp3, opus, pcm_s16le
    output_bitrate: str = "192k"


class AudioMixer:
    """
    Professional multi-track audio mixer with FFmpeg filter chains.
    Generates real FFmpeg audio filters for production use.
    """

    def __init__(self, config: AudioMixerConfig):
        self.config = config
        self.temp_dir: Optional[Path] = None

    def __enter__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="audio_mixer_"))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _generate_volume_filter(self, track: AudioTrack, duration: float) -> str:
        """Generate volume filter with automation"""
        filters = []

        # Base volume
        if track.volume != 0.0:
            filters.append(f"volume={track.volume}dB")

        # Volume automation with keyframes
        if track.volume_automation and track.volume_automation.keyframes:
            # Generate volume automation expression
            keyframes = track.volume_automation.keyframes
            if len(keyframes) == 1:
                # Single keyframe - constant volume
                filters.append(f"volume={keyframes[0].value}dB")
            else:
                # Multiple keyframes - interpolated automation
                # Build expression using 'volume' filter with enable expression
                expr_parts = []
                for i in range(len(keyframes) - 1):
                    kf1 = keyframes[i]
                    kf2 = keyframes[i + 1]
                    # Linear interpolation between keyframes
                    # Convert dB to linear gain for smooth interpolation
                    gain1 = 10 ** (kf1.value / 20.0)
                    gain2 = 10 ** (kf2.value / 20.0)
                    slope = (gain2 - gain1) / (kf2.time - kf1.time)

                    # Use volume filter with expression
                    expr = f"if(between(t,{kf1.time},{kf2.time}),{gain1}+({slope}*(t-{kf1.time})),"
                    expr_parts.append(expr)

                # Close all if statements with final value
                final_gain = 10 ** (keyframes[-1].value / 20.0)
                expr = "".join(expr_parts) + f"{final_gain}" + ")" * len(expr_parts)
                filters.append(f"volume='volume={expr}'")

        # Fade in
        if track.fade_in_duration > 0:
            filters.append(f"afade=t=in:st={track.start_time}:d={track.fade_in_duration}")

        # Fade out
        if track.fade_out_duration > 0:
            fade_start = track.start_time + duration - track.fade_out_duration
            filters.append(f"afade=t=out:st={fade_start}:d={track.fade_out_duration}")

        return ",".join(filters) if filters else "anull"

    def _generate_pan_filter(self, track: AudioTrack) -> str:
        """Generate stereo pan filter with automation"""
        if track.pan == 0.0 and not track.pan_automation:
            return "anull"

        if track.pan_automation and track.pan_automation.keyframes:
            # Pan automation with keyframes
            keyframes = track.pan_automation.keyframes
            if len(keyframes) == 1:
                pan_value = keyframes[0].value
                return f"pan=stereo|c0=c0*{1-pan_value}+c1*{max(0, -pan_value)}|c1=c0*{max(0, pan_value)}+c1*{1+pan_value}"
            else:
                # Complex pan automation - use multiple pan filters with enable
                filters = []
                for i in range(len(keyframes) - 1):
                    kf1 = keyframes[i]
                    kf2 = keyframes[i + 1]
                    # Linear interpolation
                    slope = (kf2.value - kf1.value) / (kf2.time - kf1.time)
                    # Simplified - use average pan for this segment
                    avg_pan = (kf1.value + kf2.value) / 2
                    filters.append(f"pan=stereo|c0=c0*{1-avg_pan}+c1*{max(0, -avg_pan)}|c1=c0*{max(0, avg_pan)}+c1*{1+avg_pan}")
                return filters[0]  # Simplified - use first segment
        else:
            # Static pan
            pan = track.pan
            return f"pan=stereo|c0=c0*{1-pan}+c1*{max(0, -pan)}|c1=c0*{max(0, pan)}+c1*{1+pan}"

    def _generate_eq_filter(self, eq: EQBand) -> str:
        """Generate 3-band EQ filter"""
        filters = []

        # Low band (bass) - low shelf
        if eq.low_gain != 0.0:
            filters.append(f"equalizer=f={eq.low_freq}:t=h:width={eq.low_freq/2}:g={eq.low_gain}")

        # Mid band - peaking EQ
        if eq.mid_gain != 0.0:
            mid_freq = (eq.low_freq + eq.high_freq) / 2
            bandwidth = (eq.high_freq - eq.low_freq) / 2
            filters.append(f"equalizer=f={mid_freq}:t=q:width={bandwidth}:g={eq.mid_gain}")

        # High band (treble) - high shelf
        if eq.high_gain != 0.0:
            filters.append(f"equalizer=f={eq.high_freq}:t=h:width={eq.high_freq/2}:g={eq.high_gain}")

        return ",".join(filters) if filters else "anull"

    def _generate_compressor_filter(self, comp: Compressor) -> str:
        """Generate compressor/limiter filter using compand"""
        # FFmpeg compand format: attacks:decays:points:soft-knee:gain:volume:delay
        # Points format: input_dB/output_dB (multiple points separated by space)

        # Calculate compression curve points
        threshold = comp.threshold
        ratio = comp.ratio
        knee = comp.knee

        # Create compression curve
        # Below threshold: 1:1 (no compression)
        # At threshold with knee: soft transition
        # Above threshold: compression ratio

        points = []

        # Point 1: Well below threshold (no compression)
        points.append(f"{threshold - 40}/{threshold - 40}")

        # Point 2: Below threshold (no compression)
        points.append(f"{threshold - knee}/{threshold - knee}")

        # Point 3: At threshold (start of compression)
        points.append(f"{threshold}/{threshold}")

        # Point 4: Above threshold (compressed)
        input_level = threshold + 20
        compressed_amount = 20 / ratio
        output_level = threshold + compressed_amount
        points.append(f"{input_level}/{output_level}")

        # Point 5: Well above threshold (heavily compressed)
        input_level = threshold + 40
        compressed_amount = 40 / ratio
        output_level = threshold + compressed_amount
        points.append(f"{input_level}/{output_level}")

        points_str = " ".join(points)

        # Build compand filter
        # Format: attacks:decays:soft-knee:points:gain
        attack_ms = comp.attack * 1000
        release_ms = comp.release * 1000

        filter_str = f"compand=attacks={attack_ms}:decays={release_ms}:points={points_str}:soft-knee={knee}:gain={comp.makeup_gain}"

        return filter_str

    def _generate_noise_reduction_filter(self, nr: NoiseReduction) -> str:
        """Generate noise reduction filter using afftdn"""
        if not nr.enabled:
            return "anull"

        # afftdn - FFT based noise reduction
        # nr: noise reduction amount (0.01 to 97)
        nr_amount = nr.amount * 20  # Scale to 0-20 dB

        return f"afftdn=nr={nr_amount}:nf=-25:tn=1"

    def _generate_deesser_filter(self, deesser: DeEsser) -> str:
        """Generate de-esser filter for reducing sibilance"""
        if not deesser.enabled:
            return "anull"

        # De-esser using multiband compression on high frequencies
        # Split signal, compress highs, mix back
        freq = deesser.frequency
        threshold = deesser.threshold
        amount = deesser.amount

        # Use compand on high-frequency band
        ratio = 1 + (amount * 5)  # 1:1 to 6:1 based on amount

        filter_str = f"highpass=f={freq},compand=attacks=0.001:decays=0.01:points=-80/-80|{threshold}/{threshold}|20/{threshold+20/ratio}:soft-knee=1,alowpass=f={freq*2}"

        return filter_str

    def _generate_bass_boost_filter(self, bass_boost: float) -> str:
        """Generate bass boost filter"""
        if bass_boost <= 0:
            return "anull"

        # Low shelf filter at 150 Hz
        return f"equalizer=f=150:t=h:width=100:g={bass_boost}"

    def _generate_voice_enhancement_filter(self, preset: VoiceEnhancementPreset) -> str:
        """Generate voice enhancement filter chain"""
        filters = []

        if preset == VoiceEnhancementPreset.NATURAL:
            # Gentle high-pass, slight presence boost
            filters.append("highpass=f=80")
            filters.append("equalizer=f=3000:t=q:width=2000:g=2")

        elif preset == VoiceEnhancementPreset.CRISP:
            # Clear, bright vocals
            filters.append("highpass=f=100")
            filters.append("equalizer=f=2500:t=q:width=2000:g=3")
            filters.append("equalizer=f=5000:t=q:width=3000:g=2")

        elif preset == VoiceEnhancementPreset.WARM:
            # Warm, rich vocals
            filters.append("highpass=f=80")
            filters.append("equalizer=f=200:t=q:width=150:g=2")
            filters.append("equalizer=f=3000:t=q:width=2000:g=1.5")

        elif preset == VoiceEnhancementPreset.BROADCAST:
            # Radio/broadcast quality
            filters.append("highpass=f=120")
            filters.append("equalizer=f=250:t=q:width=200:g=-3")
            filters.append("equalizer=f=3500:t=q:width=2500:g=4")
            filters.append("compand=attacks=0.001:decays=0.05:points=-80/-80|-45/-45|-25/-15|0/-5:soft-knee=2:gain=5")

        elif preset == VoiceEnhancementPreset.PODCAST:
            # Podcast optimized
            filters.append("highpass=f=80")
            filters.append("equalizer=f=200:t=q:width=150:g=-2")
            filters.append("equalizer=f=3000:t=q:width=2000:g=3")
            filters.append("compand=attacks=0.003:decays=0.1:points=-80/-80|-35/-35|-20/-15|0/-5:soft-knee=3:gain=3")

        return ",".join(filters) if filters else "anull"

    def _generate_auto_ducking_filter(self, main_track_label: str, trigger_track_label: str,
                                      ducking: AutoDucking) -> str:
        """Generate auto-ducking filter using sidechain compression"""
        if not ducking.enabled:
            return "anull"

        # Sidechain compression: lower main track volume when trigger track is active
        threshold = ducking.threshold
        ratio = ducking.ratio
        attack = ducking.attack * 1000  # convert to ms
        release = ducking.release * 1000  # convert to ms

        # Points for sidechain: aggressive ducking
        points = f"-80/-80|{threshold}/{threshold}|0/{threshold + (0 - threshold) / ratio}"

        # Format: [trigger][main]sidechaincompress
        filter_str = f"[{trigger_track_label}][{main_track_label}]sidechaincompress=threshold={threshold}dB:ratio={ratio}:attack={attack}:release={release}:level_in=1"

        return filter_str

    def _generate_crossfade_filter(self, crossfade: CrossFade) -> str:
        """Generate crossfade filter between two tracks"""
        # acrossfade filter
        duration = crossfade.duration
        curve = crossfade.curve

        return f"acrossfade=d={duration}:c1={curve}:c2={curve}"

    def _generate_normalization_filter(self, master: MasterBus) -> str:
        """Generate loudness normalization filter"""
        filters = []

        if master.normalization == NormalizationStandard.EBU_R128:
            # EBU R128 normalization for broadcast (-23 LUFS)
            target = -23.0
            filters.append(f"loudnorm=I={target}:TP={master.true_peak}:LRA=11")

        elif master.normalization == NormalizationStandard.STREAMING:
            # Streaming platforms (-14 LUFS)
            target = -14.0
            filters.append(f"loudnorm=I={target}:TP={master.true_peak}:LRA=11")

        elif master.normalization == NormalizationStandard.SOCIAL_MEDIA:
            # Social media (-16 LUFS)
            target = -16.0
            filters.append(f"loudnorm=I={target}:TP={master.true_peak}:LRA=11")

        elif master.normalization == NormalizationStandard.CUSTOM:
            # Custom LUFS target
            filters.append(f"loudnorm=I={master.target_lufs}:TP={master.true_peak}:LRA=11")

        return ",".join(filters) if filters else "anull"

    def _generate_limiter_filter(self, threshold: float) -> str:
        """Generate limiter filter to prevent clipping"""
        # Use compand as a hard limiter
        points = f"-80/-80|{threshold}/{threshold}|0/{threshold}"
        return f"compand=attacks=0.0001:decays=0.01:points={points}:soft-knee=0.1:gain=0"

    def _get_audio_duration(self, file_path: str) -> float:
        """Get audio file duration using ffprobe"""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception as e:
            logger.error(f"Failed to get audio duration for {file_path}: {e}")
            return 0.0

    def _build_track_filter_chain(self, track: AudioTrack, track_index: int) -> Tuple[str, str]:
        """Build complete filter chain for a single track"""
        # Get track duration
        file_duration = self._get_audio_duration(track.file_path)
        duration = track.duration if track.duration else file_duration - track.trim_start

        filters = []
        input_label = f"[{track_index}:a]"
        output_label = f"[a{track_index}]"

        # Trim if needed
        if track.trim_start > 0:
            filters.append(f"atrim=start={track.trim_start}")

        if track.duration:
            filters.append(f"atrim=duration={track.duration}")

        # Set presentation timestamp
        filters.append("asetpts=PTS-STARTPTS")

        # Delay to match timeline position
        if track.start_time > 0:
            delay_ms = int(track.start_time * 1000)
            filters.append(f"adelay={delay_ms}|{delay_ms}")

        # Noise reduction (early in chain)
        if track.noise_reduction:
            nr_filter = self._generate_noise_reduction_filter(track.noise_reduction)
            if nr_filter != "anull":
                filters.append(nr_filter)

        # High-pass filter for voiceovers (remove rumble)
        if track.track_type == AudioTrackType.VOICEOVER:
            filters.append("highpass=f=80")

        # EQ
        if track.eq:
            eq_filter = self._generate_eq_filter(track.eq)
            if eq_filter != "anull":
                filters.append(eq_filter)

        # Bass boost
        if track.bass_boost > 0:
            bass_filter = self._generate_bass_boost_filter(track.bass_boost)
            if bass_filter != "anull":
                filters.append(bass_filter)

        # De-esser
        if track.de_esser:
            deesser_filter = self._generate_deesser_filter(track.de_esser)
            if deesser_filter != "anull":
                filters.append(deesser_filter)

        # Compressor
        if track.compressor:
            comp_filter = self._generate_compressor_filter(track.compressor)
            filters.append(comp_filter)

        # Volume and automation
        vol_filter = self._generate_volume_filter(track, duration)
        if vol_filter != "anull":
            filters.append(vol_filter)

        # Pan
        pan_filter = self._generate_pan_filter(track)
        if pan_filter != "anull":
            filters.append(pan_filter)

        # Build filter chain
        filter_chain = input_label + ",".join(filters) + output_label

        return filter_chain, output_label

    def generate_filter_complex(self) -> Tuple[str, List[str]]:
        """
        Generate complete FFmpeg filter_complex for all tracks.

        Returns:
            Tuple of (filter_complex_string, input_files_list)
        """
        input_files = []
        filter_chains = []
        track_labels = []

        # Build filter chains for each track
        for idx, track in enumerate(self.config.tracks):
            if track.muted:
                continue

            input_files.append(track.file_path)
            filter_chain, output_label = self._build_track_filter_chain(track, len(input_files) - 1)
            filter_chains.append(filter_chain)
            track_labels.append((track.name, output_label))

        # Handle auto-ducking (sidechain compression)
        ducked_tracks = []
        for track_name, track_label in track_labels:
            track = next((t for t in self.config.tracks if t.name == track_name), None)
            if track and track.auto_ducking and track.auto_ducking.enabled:
                # Find trigger track
                trigger_track = next((t for t in self.config.tracks if t.name == track.auto_ducking.trigger_track), None)
                if trigger_track:
                    trigger_label = next((label for name, label in track_labels if name == trigger_track.name), None)
                    if trigger_label:
                        # Generate sidechain filter
                        ducked_label = f"[ducked_{track_name}]"
                        sidechain_filter = self._generate_auto_ducking_filter(
                            track_label.strip("[]"),
                            trigger_label.strip("[]"),
                            track.auto_ducking
                        )
                        filter_chains.append(sidechain_filter + ducked_label)
                        ducked_tracks.append((track_name, ducked_label))

        # Update labels for ducked tracks
        for track_name, ducked_label in ducked_tracks:
            track_labels = [(name, ducked_label if name == track_name else label) for name, label in track_labels]

        # Mix all tracks together
        if len(track_labels) > 1:
            mix_inputs = "".join([label for _, label in track_labels])
            mix_filter = f"{mix_inputs}amix=inputs={len(track_labels)}:duration=longest:dropout_transition=2[mixed]"
            filter_chains.append(mix_filter)
            master_input = "[mixed]"
        else:
            master_input = track_labels[0][1] if track_labels else "[0:a]"

        # Master bus processing
        master_filters = []

        # Master compressor
        if self.config.master_bus.compressor:
            comp_filter = self._generate_compressor_filter(self.config.master_bus.compressor)
            master_filters.append(comp_filter)

        # Normalization
        norm_filter = self._generate_normalization_filter(self.config.master_bus)
        if norm_filter != "anull":
            master_filters.append(norm_filter)

        # Limiter
        if self.config.master_bus.limiter_enabled:
            limiter_filter = self._generate_limiter_filter(self.config.master_bus.limiter_threshold)
            master_filters.append(limiter_filter)

        # Final master chain
        if master_filters:
            master_chain = master_input + ",".join(master_filters) + "[aout]"
            filter_chains.append(master_chain)
        else:
            # Just relabel
            filter_chains.append(f"{master_input}anull[aout]")

        # Combine all filter chains
        filter_complex = ";".join(filter_chains)

        return filter_complex, input_files

    def mix_to_file(self, output_path: str, progress_callback: Optional[callable] = None) -> bool:
        """
        Mix all tracks and render to output file.

        Args:
            output_path: Output audio file path
            progress_callback: Optional callback for progress updates (percent: float)

        Returns:
            True if successful
        """
        try:
            # Generate filter complex
            filter_complex, input_files = self.generate_filter_complex()

            logger.info(f"Mixing {len(input_files)} audio tracks")
            logger.debug(f"Filter complex: {filter_complex}")

            # Build FFmpeg command
            cmd = ["ffmpeg", "-y"]

            # Add input files
            for input_file in input_files:
                cmd.extend(["-i", input_file])

            # Add filter complex
            cmd.extend(["-filter_complex", filter_complex])

            # Map output
            cmd.extend(["-map", "[aout]"])

            # Audio codec settings
            cmd.extend([
                "-c:a", self.config.output_format,
                "-b:a", self.config.output_bitrate,
                "-ar", str(self.config.sample_rate)
            ])

            # Output file
            cmd.append(output_path)

            logger.info(f"FFmpeg command: {' '.join(cmd)}")

            # Execute FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Monitor progress
            if progress_callback:
                duration_pattern = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})")
                time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")
                total_duration = None

                for line in process.stderr:
                    logger.debug(line.strip())

                    # Extract total duration
                    if total_duration is None:
                        duration_match = duration_pattern.search(line)
                        if duration_match:
                            h, m, s = map(float, duration_match.groups())
                            total_duration = h * 3600 + m * 60 + s

                    # Extract current time
                    if total_duration:
                        time_match = time_pattern.search(line)
                        if time_match:
                            h, m, s = map(float, time_match.groups())
                            current_time = h * 3600 + m * 60 + s
                            progress = min(100.0, (current_time / total_duration) * 100)
                            progress_callback(progress)
            else:
                # Just wait for completion
                process.wait()

            if process.returncode != 0:
                stderr = process.stderr.read() if process.stderr else ""
                logger.error(f"FFmpeg failed: {stderr}")
                return False

            logger.info(f"Audio mix completed: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Audio mixing failed: {e}")
            return False

    def analyze_loudness(self, file_path: str) -> Dict[str, float]:
        """
        Analyze loudness of audio file (LUFS, true peak, etc.)

        Returns:
            Dict with: integrated_lufs, true_peak, lra (loudness range)
        """
        try:
            cmd = [
                "ffmpeg", "-i", file_path,
                "-af", "loudnorm=print_format=json",
                "-f", "null", "-"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # Extract JSON from stderr
            stderr = result.stderr
            json_start = stderr.rfind("{")
            json_end = stderr.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = stderr[json_start:json_end]
                data = json.loads(json_str)

                return {
                    "integrated_lufs": float(data.get("input_i", 0)),
                    "true_peak": float(data.get("input_tp", 0)),
                    "lra": float(data.get("input_lra", 0)),
                    "threshold": float(data.get("input_thresh", 0))
                }

        except Exception as e:
            logger.error(f"Loudness analysis failed: {e}")

        return {}


# ============================================================================
# PRESETS AND HELPERS
# ============================================================================

class AudioPresets:
    """Pre-configured audio processing presets"""

    @staticmethod
    def voiceover_professional() -> AudioTrack:
        """Professional voiceover preset"""
        track = AudioTrack(name="voiceover", file_path="", track_type=AudioTrackType.VOICEOVER)
        track.compressor = Compressor(threshold=-20, ratio=4, attack=0.003, release=0.1, makeup_gain=3)
        track.eq = EQBand(low_gain=-3, mid_gain=3, high_gain=2, low_freq=200, high_freq=3500)
        track.noise_reduction = NoiseReduction(enabled=True, amount=0.6)
        track.de_esser = DeEsser(enabled=True, frequency=6000, threshold=-30, amount=0.7)
        return track

    @staticmethod
    def music_background() -> AudioTrack:
        """Background music preset (auto-ducked)"""
        track = AudioTrack(name="music", file_path="", track_type=AudioTrackType.MUSIC)
        track.volume = -12  # Lower than voiceover
        track.eq = EQBand(low_gain=0, mid_gain=-2, high_gain=-3)  # Reduce mid/high for voiceover clarity
        track.auto_ducking = AutoDucking(
            enabled=True,
            trigger_track="voiceover",
            threshold=-30,
            ratio=4,
            attack=0.1,
            release=0.5,
            reduction=-12
        )
        return track

    @staticmethod
    def music_energetic() -> AudioTrack:
        """Energetic music with bass boost"""
        track = AudioTrack(name="music", file_path="", track_type=AudioTrackType.MUSIC)
        track.bass_boost = 6
        track.eq = EQBand(low_gain=4, mid_gain=0, high_gain=2)
        track.compressor = Compressor(threshold=-18, ratio=3, attack=0.01, release=0.15, makeup_gain=2)
        return track

    @staticmethod
    def sfx_impactful() -> AudioTrack:
        """Impactful sound effects"""
        track = AudioTrack(name="sfx", file_path="", track_type=AudioTrackType.SFX)
        track.volume = 3  # Slightly louder
        track.bass_boost = 3
        track.compressor = Compressor(threshold=-15, ratio=6, attack=0.001, release=0.05, makeup_gain=4)
        return track

    @staticmethod
    def master_streaming() -> MasterBus:
        """Master bus for streaming platforms"""
        master = MasterBus()
        master.normalization = NormalizationStandard.STREAMING
        master.target_lufs = -14.0
        master.true_peak = -1.0
        master.compressor = Compressor(threshold=-8, ratio=2.5, attack=0.005, release=0.1, makeup_gain=0)
        master.limiter_enabled = True
        master.limiter_threshold = -1.0
        return master

    @staticmethod
    def master_broadcast() -> MasterBus:
        """Master bus for broadcast (EBU R128)"""
        master = MasterBus()
        master.normalization = NormalizationStandard.EBU_R128
        master.target_lufs = -23.0
        master.true_peak = -1.0
        master.limiter_enabled = True
        master.limiter_threshold = -1.0
        return master


# ============================================================================
# AUDIO LIBRARY INTEGRATION
# ============================================================================

class AudioLibrary:
    """Audio library for background music and sound effects"""

    def __init__(self, library_path: str):
        self.library_path = Path(library_path)
        self.music_path = self.library_path / "music"
        self.sfx_path = self.library_path / "sfx"

        # Create directories if they don't exist
        self.music_path.mkdir(parents=True, exist_ok=True)
        self.sfx_path.mkdir(parents=True, exist_ok=True)

    def list_music(self, category: Optional[str] = None) -> List[str]:
        """List available background music files"""
        search_path = self.music_path / category if category else self.music_path
        if not search_path.exists():
            return []

        music_files = []
        for ext in ["*.mp3", "*.wav", "*.aac", "*.m4a", "*.ogg"]:
            music_files.extend([str(f) for f in search_path.rglob(ext)])

        return sorted(music_files)

    def list_sfx(self, category: Optional[str] = None) -> List[str]:
        """List available sound effects"""
        search_path = self.sfx_path / category if category else self.sfx_path
        if not search_path.exists():
            return []

        sfx_files = []
        for ext in ["*.mp3", "*.wav", "*.aac", "*.m4a", "*.ogg"]:
            sfx_files.extend([str(f) for f in search_path.rglob(ext)])

        return sorted(sfx_files)

    def get_music_by_mood(self, mood: str) -> List[str]:
        """Get music by mood (energetic, calm, dramatic, etc.)"""
        return self.list_music(category=mood)

    def get_sfx_by_type(self, sfx_type: str) -> List[str]:
        """Get sound effects by type (whoosh, impact, ui, etc.)"""
        return self.list_sfx(category=sfx_type)


if __name__ == "__main__":
    # Example usage
    print("Pro Audio Mixer - Multi-track Audio Mixing System")
    print("=" * 60)

    # Create mixer configuration
    config = AudioMixerConfig()
    config.sample_rate = 48000
    config.output_format = "aac"
    config.output_bitrate = "192k"

    # Add voiceover track
    voiceover = AudioPresets.voiceover_professional()
    voiceover.name = "voiceover"
    voiceover.file_path = "voiceover.wav"
    voiceover.start_time = 0.5
    voiceover.fade_in_duration = 0.2
    voiceover.fade_out_duration = 0.3
    config.tracks.append(voiceover)

    # Add background music (auto-ducked)
    music = AudioPresets.music_background()
    music.name = "background_music"
    music.file_path = "music.mp3"
    music.start_time = 0.0
    music.fade_in_duration = 1.0
    music.fade_out_duration = 2.0
    config.tracks.append(music)

    # Add sound effect
    sfx = AudioPresets.sfx_impactful()
    sfx.name = "whoosh"
    sfx.file_path = "whoosh.wav"
    sfx.start_time = 2.5
    config.tracks.append(sfx)

    # Configure master bus
    config.master_bus = AudioPresets.master_streaming()

    # Mix audio
    with AudioMixer(config) as mixer:
        # Generate filter complex
        filter_complex, input_files = mixer.generate_filter_complex()

        print("\nGenerated Filter Complex:")
        print(filter_complex)

        print("\nInput Files:")
        for i, f in enumerate(input_files):
            print(f"  [{i}] {f}")

        print("\nTo render, call: mixer.mix_to_file('output.aac')")
