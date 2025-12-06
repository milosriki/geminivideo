"""
Production-Ready Timeline-Based Video Editing Engine

A comprehensive, frame-accurate timeline engine supporting:
- Multi-track video/audio/text/effect editing
- Advanced clip operations (trim, split, slip, slide, ripple)
- Track management (lock, mute, solo, reorder)
- Compound clips (nested timelines)
- Gap detection and magnetic timeline
- FFmpeg command generation
- JSON serialization

Author: Claude Code
Version: 1.0.0
"""

import uuid
import json
import copy
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class TrackType(Enum):
    """Track type enumeration"""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    EFFECT = "effect"


class TransitionType(Enum):
    """Transition type enumeration"""
    CUT = "cut"
    DISSOLVE = "dissolve"
    FADE = "fade"
    WIPE = "wipe"
    SLIDE = "slide"


class OverlapStrategy(Enum):
    """Strategy for handling overlapping clips"""
    REJECT = "reject"  # Reject the operation
    OVERWRITE = "overwrite"  # Overwrite existing clips
    INSERT = "insert"  # Insert and shift clips
    LAYER = "layer"  # Allow overlap (compositing)


@dataclass
class Effect:
    """Effect applied to clip or track"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""  # blur, brightness, saturation, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Effect':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Transition:
    """Transition between clips"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TransitionType = TransitionType.CUT
    duration: float = 0.0  # seconds
    from_clip_id: Optional[str] = None
    to_clip_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['type'] = self.type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transition':
        """Create from dictionary"""
        data = data.copy()
        data['type'] = TransitionType(data['type'])
        return cls(**data)


@dataclass
class Clip:
    """
    Media clip on timeline

    Timing model:
    - start_time: position on timeline (seconds)
    - duration: how long the clip plays (seconds)
    - in_point: where to start in source media (seconds)
    - out_point: where to end in source media (seconds)
    - source_duration: total duration of source media (seconds)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""  # Path to source media or compound timeline ID
    start_time: float = 0.0  # Position on timeline
    duration: float = 0.0  # Duration on timeline
    in_point: float = 0.0  # Trim in point in source
    out_point: Optional[float] = None  # Trim out point in source
    source_duration: Optional[float] = None  # Total source duration
    track_id: str = ""
    name: str = ""
    enabled: bool = True
    locked: bool = False
    volume: float = 1.0  # 0.0 to 2.0
    speed: float = 1.0  # Playback speed multiplier
    effects: List[Effect] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_compound: bool = False  # Is this a compound clip

    def __post_init__(self):
        """Validate and set defaults"""
        if self.out_point is None and self.source_duration is not None:
            self.out_point = self.source_duration
        if self.out_point is None:
            self.out_point = self.in_point + self.duration

    @property
    def end_time(self) -> float:
        """End position on timeline"""
        return self.start_time + self.duration

    @property
    def source_in_out_duration(self) -> float:
        """Duration based on in/out points"""
        return (self.out_point or 0) - self.in_point

    def overlaps_with(self, other: 'Clip') -> bool:
        """Check if this clip overlaps with another"""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)

    def contains_time(self, time: float) -> bool:
        """Check if this clip contains the given time"""
        return self.start_time <= time < self.end_time

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['effects'] = [e.to_dict() for e in self.effects]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Clip':
        """Create from dictionary"""
        data = data.copy()
        data['effects'] = [Effect.from_dict(e) for e in data.get('effects', [])]
        return cls(**data)


@dataclass
class Track:
    """Timeline track containing clips"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TrackType = TrackType.VIDEO
    name: str = ""
    clips: List[Clip] = field(default_factory=list)
    locked: bool = False
    muted: bool = False
    solo: bool = False
    visible: bool = True
    order: int = 0  # Layer order (higher = on top)
    effects: List[Effect] = field(default_factory=list)
    volume: float = 1.0  # Track-level volume

    def add_clip(self, clip: Clip, overlap_strategy: OverlapStrategy = OverlapStrategy.REJECT) -> bool:
        """
        Add clip to track

        Args:
            clip: Clip to add
            overlap_strategy: How to handle overlaps

        Returns:
            True if successful, False otherwise
        """
        clip.track_id = self.id

        # Check for overlaps
        overlapping = self.get_overlapping_clips(clip.start_time, clip.end_time)

        if overlapping:
            if overlap_strategy == OverlapStrategy.REJECT:
                return False
            elif overlap_strategy == OverlapStrategy.OVERWRITE:
                # Remove overlapping clips
                for oclip in overlapping:
                    self.clips.remove(oclip)
            elif overlap_strategy == OverlapStrategy.INSERT:
                # Shift clips to make room
                shift_amount = clip.duration
                for oclip in self.clips:
                    if oclip.start_time >= clip.start_time:
                        oclip.start_time += shift_amount
            elif overlap_strategy == OverlapStrategy.LAYER:
                # Allow overlap (for compositing)
                pass

        self.clips.append(clip)
        self._sort_clips()
        return True

    def remove_clip(self, clip_id: str) -> Optional[Clip]:
        """Remove clip by ID"""
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                return self.clips.pop(i)
        return None

    def get_clip(self, clip_id: str) -> Optional[Clip]:
        """Get clip by ID"""
        for clip in self.clips:
            if clip.id == clip_id:
                return clip
        return None

    def get_overlapping_clips(self, start: float, end: float) -> List[Clip]:
        """Get clips that overlap with the given time range"""
        overlapping = []
        for clip in self.clips:
            if not (clip.end_time <= start or clip.start_time >= end):
                overlapping.append(clip)
        return overlapping

    def get_clip_at_time(self, time: float) -> Optional[Clip]:
        """Get clip at specific time"""
        for clip in self.clips:
            if clip.contains_time(time):
                return clip
        return None

    def detect_gaps(self) -> List[Tuple[float, float]]:
        """
        Detect gaps between clips

        Returns:
            List of (gap_start, gap_end) tuples
        """
        if not self.clips:
            return []

        self._sort_clips()
        gaps = []

        for i in range(len(self.clips) - 1):
            current_end = self.clips[i].end_time
            next_start = self.clips[i + 1].start_time

            if next_start > current_end:
                gaps.append((current_end, next_start))

        return gaps

    def remove_gaps(self) -> int:
        """
        Remove all gaps by shifting clips

        Returns:
            Number of gaps removed
        """
        gaps = self.detect_gaps()
        if not gaps:
            return 0

        self._sort_clips()
        shift = 0.0

        for i, clip in enumerate(self.clips):
            if i > 0:
                # Calculate gap before this clip
                prev_end = self.clips[i - 1].end_time
                gap = clip.start_time - prev_end
                if gap > 0:
                    shift += gap

            if shift > 0:
                clip.start_time -= shift

        return len(gaps)

    def _sort_clips(self):
        """Sort clips by start time"""
        self.clips.sort(key=lambda c: c.start_time)

    def get_duration(self) -> float:
        """Get total duration of track"""
        if not self.clips:
            return 0.0
        return max(clip.end_time for clip in self.clips)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['type'] = self.type.value
        data['clips'] = [c.to_dict() for c in self.clips]
        data['effects'] = [e.to_dict() for e in self.effects]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Track':
        """Create from dictionary"""
        data = data.copy()
        data['type'] = TrackType(data['type'])
        data['clips'] = [Clip.from_dict(c) for c in data.get('clips', [])]
        data['effects'] = [Effect.from_dict(e) for e in data.get('effects', [])]
        return cls(**data)


class Timeline:
    """
    Main timeline container for multi-track editing
    """

    def __init__(
        self,
        name: str = "Untitled Timeline",
        frame_rate: float = 30.0,
        resolution: Tuple[int, int] = (1920, 1080),
        sample_rate: int = 48000,
        snap_distance: float = 0.1
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.frame_rate = frame_rate
        self.resolution = resolution
        self.sample_rate = sample_rate
        self.snap_distance = snap_distance  # Seconds for magnetic timeline
        self.tracks: List[Track] = []
        self.transitions: List[Transition] = []
        self.compound_timelines: Dict[str, 'Timeline'] = {}  # Nested timelines
        self.metadata: Dict[str, Any] = {}

    # ==================== Track Operations ====================

    def add_track(
        self,
        track_type: TrackType,
        name: str = "",
        order: Optional[int] = None
    ) -> Track:
        """
        Add a new track

        Args:
            track_type: Type of track
            name: Track name
            order: Layer order (auto-assigned if None)

        Returns:
            Created track
        """
        if not name:
            name = f"{track_type.value.capitalize()} {len(self.tracks) + 1}"

        if order is None:
            order = len(self.tracks)

        track = Track(type=track_type, name=name, order=order)
        self.tracks.append(track)
        self._sort_tracks()
        return track

    def remove_track(self, track_id: str) -> Optional[Track]:
        """Remove track by ID"""
        for i, track in enumerate(self.tracks):
            if track.id == track_id:
                return self.tracks.pop(i)
        return None

    def get_track(self, track_id: str) -> Optional[Track]:
        """Get track by ID"""
        for track in self.tracks:
            if track.id == track_id:
                return track
        return None

    def reorder_track(self, track_id: str, new_order: int) -> bool:
        """
        Change track order

        Args:
            track_id: Track to reorder
            new_order: New order value

        Returns:
            True if successful
        """
        track = self.get_track(track_id)
        if not track:
            return False

        track.order = new_order
        self._sort_tracks()
        return True

    def lock_track(self, track_id: str, locked: bool = True) -> bool:
        """Lock/unlock track"""
        track = self.get_track(track_id)
        if track:
            track.locked = locked
            return True
        return False

    def mute_track(self, track_id: str, muted: bool = True) -> bool:
        """Mute/unmute track"""
        track = self.get_track(track_id)
        if track:
            track.muted = muted
            return True
        return False

    def solo_track(self, track_id: str, solo: bool = True) -> bool:
        """Solo/unsolo track"""
        track = self.get_track(track_id)
        if track:
            track.solo = solo
            return True
        return False

    def apply_track_effect(self, track_id: str, effect: Effect) -> bool:
        """Apply effect to entire track"""
        track = self.get_track(track_id)
        if track:
            track.effects.append(effect)
            return True
        return False

    def _sort_tracks(self):
        """Sort tracks by order"""
        self.tracks.sort(key=lambda t: t.order)

    # ==================== Clip Operations ====================

    def add_clip(
        self,
        track_id: str,
        source: str,
        start_time: float,
        duration: float,
        in_point: float = 0.0,
        out_point: Optional[float] = None,
        source_duration: Optional[float] = None,
        name: str = "",
        overlap_strategy: OverlapStrategy = OverlapStrategy.REJECT
    ) -> Optional[Clip]:
        """
        Add clip to track

        Args:
            track_id: Target track ID
            source: Path to source media
            start_time: Position on timeline
            duration: Clip duration
            in_point: Trim in point
            out_point: Trim out point
            source_duration: Total source duration
            name: Clip name
            overlap_strategy: How to handle overlaps

        Returns:
            Created clip or None if failed
        """
        track = self.get_track(track_id)
        if not track or track.locked:
            return None

        if not name:
            name = Path(source).stem

        # Snap to nearby points if enabled
        start_time = self.find_snap_position(start_time, track_id)

        clip = Clip(
            source=source,
            start_time=start_time,
            duration=duration,
            in_point=in_point,
            out_point=out_point,
            source_duration=source_duration,
            name=name
        )

        if track.add_clip(clip, overlap_strategy):
            return clip
        return None

    def remove_clip(self, clip_id: str) -> Optional[Clip]:
        """Remove clip from timeline"""
        for track in self.tracks:
            clip = track.remove_clip(clip_id)
            if clip:
                return clip
        return None

    def get_clip(self, clip_id: str) -> Optional[Clip]:
        """Get clip by ID"""
        for track in self.tracks:
            clip = track.get_clip(clip_id)
            if clip:
                return clip
        return None

    def move_clip(
        self,
        clip_id: str,
        new_start: float,
        snap: bool = True,
        overlap_strategy: OverlapStrategy = OverlapStrategy.REJECT
    ) -> bool:
        """
        Move clip to new position

        Args:
            clip_id: Clip to move
            new_start: New start time
            snap: Enable magnetic snapping
            overlap_strategy: How to handle overlaps

        Returns:
            True if successful
        """
        clip = self.get_clip(clip_id)
        if not clip or clip.locked:
            return False

        track = self.get_track(clip.track_id)
        if not track or track.locked:
            return False

        # Snap if enabled
        if snap:
            new_start = self.find_snap_position(new_start, clip.track_id, exclude_clip_id=clip_id)

        # Check for overlaps at new position
        old_start = clip.start_time
        clip.start_time = new_start

        overlapping = track.get_overlapping_clips(clip.start_time, clip.end_time)
        overlapping = [c for c in overlapping if c.id != clip_id]

        if overlapping:
            if overlap_strategy == OverlapStrategy.REJECT:
                clip.start_time = old_start  # Revert
                return False
            elif overlap_strategy == OverlapStrategy.OVERWRITE:
                for oclip in overlapping:
                    track.remove_clip(oclip.id)

        track._sort_clips()
        return True

    def trim_clip(
        self,
        clip_id: str,
        new_in: Optional[float] = None,
        new_out: Optional[float] = None,
        update_duration: bool = True
    ) -> bool:
        """
        Trim clip in/out points

        Args:
            clip_id: Clip to trim
            new_in: New in point (None to keep current)
            new_out: New out point (None to keep current)
            update_duration: Update clip duration based on new in/out

        Returns:
            True if successful
        """
        clip = self.get_clip(clip_id)
        if not clip or clip.locked:
            return False

        if new_in is not None:
            clip.in_point = new_in

        if new_out is not None:
            clip.out_point = new_out

        if update_duration:
            clip.duration = clip.source_in_out_duration / clip.speed

        return True

    def split_clip(self, clip_id: str, position: float) -> Optional[Tuple[Clip, Clip]]:
        """
        Split clip at position

        Args:
            clip_id: Clip to split
            position: Timeline position to split at

        Returns:
            Tuple of (left_clip, right_clip) or None if failed
        """
        clip = self.get_clip(clip_id)
        if not clip or clip.locked:
            return None

        if not clip.contains_time(position):
            return None

        track = self.get_track(clip.track_id)
        if not track or track.locked:
            return None

        # Calculate split point in source media
        time_in_clip = position - clip.start_time
        source_split = clip.in_point + (time_in_clip * clip.speed)

        # Create right clip
        right_clip = Clip(
            source=clip.source,
            start_time=position,
            duration=clip.end_time - position,
            in_point=source_split,
            out_point=clip.out_point,
            source_duration=clip.source_duration,
            name=f"{clip.name} (2)",
            volume=clip.volume,
            speed=clip.speed,
            effects=copy.deepcopy(clip.effects),
            is_compound=clip.is_compound
        )

        # Update left clip
        clip.duration = position - clip.start_time
        clip.out_point = source_split

        # Add right clip to track
        track.add_clip(right_clip, OverlapStrategy.LAYER)

        return (clip, right_clip)

    def slip_clip(self, clip_id: str, offset: float) -> bool:
        """
        Slip edit: move in/out points without changing timeline position

        Args:
            clip_id: Clip to slip
            offset: Offset amount (seconds)

        Returns:
            True if successful
        """
        clip = self.get_clip(clip_id)
        if not clip or clip.locked:
            return False

        new_in = clip.in_point + offset
        new_out = (clip.out_point or 0) + offset

        # Validate bounds
        if new_in < 0:
            return False
        if clip.source_duration and new_out > clip.source_duration:
            return False

        clip.in_point = new_in
        clip.out_point = new_out

        return True

    def slide_clip(self, clip_id: str, offset: float) -> bool:
        """
        Slide edit: move on timeline without changing in/out points

        Args:
            clip_id: Clip to slide
            offset: Offset amount (seconds)

        Returns:
            True if successful
        """
        return self.move_clip(clip_id, self.get_clip(clip_id).start_time + offset, snap=False)

    def ripple_edit(self, clip_id: str, delta: float, edge: str = "end") -> bool:
        """
        Ripple edit: adjust clip duration and shift following clips

        Args:
            clip_id: Clip to edit
            delta: Duration change (seconds)
            edge: Which edge to edit ("start" or "end")

        Returns:
            True if successful
        """
        clip = self.get_clip(clip_id)
        if not clip or clip.locked:
            return False

        track = self.get_track(clip.track_id)
        if not track or track.locked:
            return False

        if edge == "end":
            # Adjust out point and duration
            new_out = (clip.out_point or 0) + delta * clip.speed
            if clip.source_duration and new_out > clip.source_duration:
                return False
            if new_out <= clip.in_point:
                return False

            clip.out_point = new_out
            clip.duration += delta

            # Shift following clips
            for other in track.clips:
                if other.start_time >= clip.end_time - delta:
                    other.start_time += delta

        elif edge == "start":
            # Adjust in point, start time, and duration
            new_in = clip.in_point - delta * clip.speed
            if new_in < 0:
                return False
            if new_in >= (clip.out_point or 0):
                return False

            clip.in_point = new_in
            clip.start_time -= delta
            clip.duration += delta

            # Shift previous clips
            for other in track.clips:
                if other.end_time <= clip.start_time + delta:
                    other.start_time -= delta

        return True

    def apply_clip_effect(self, clip_id: str, effect: Effect) -> bool:
        """Apply effect to clip"""
        clip = self.get_clip(clip_id)
        if clip:
            clip.effects.append(effect)
            return True
        return False

    # ==================== Compound Clips ====================

    def create_compound_clip(
        self,
        clip_ids: List[str],
        name: str = "Compound Clip",
        track_id: Optional[str] = None
    ) -> Optional[Clip]:
        """
        Create compound clip from multiple clips

        Args:
            clip_ids: Clips to combine
            name: Compound clip name
            track_id: Target track (uses first clip's track if None)

        Returns:
            Compound clip or None if failed
        """
        if not clip_ids:
            return None

        clips = [self.get_clip(cid) for cid in clip_ids]
        clips = [c for c in clips if c is not None]

        if not clips:
            return None

        # Create nested timeline
        nested_timeline = Timeline(
            name=name,
            frame_rate=self.frame_rate,
            resolution=self.resolution,
            sample_rate=self.sample_rate
        )

        # Calculate bounds
        min_start = min(c.start_time for c in clips)
        max_end = max(c.end_time for c in clips)

        # Group clips by track and recreate in nested timeline
        track_map = {}
        for clip in clips:
            if clip.track_id not in track_map:
                orig_track = self.get_track(clip.track_id)
                if orig_track:
                    new_track = nested_timeline.add_track(orig_track.type, orig_track.name)
                    track_map[clip.track_id] = new_track.id

        # Add clips to nested timeline (offset to start at 0)
        for clip in clips:
            new_clip = copy.deepcopy(clip)
            new_clip.start_time -= min_start
            new_clip.track_id = track_map.get(clip.track_id, "")
            new_track = nested_timeline.get_track(new_clip.track_id)
            if new_track:
                new_track.add_clip(new_clip, OverlapStrategy.LAYER)

        # Store nested timeline
        self.compound_timelines[nested_timeline.id] = nested_timeline

        # Create compound clip
        target_track_id = track_id or clips[0].track_id
        compound_clip = self.add_clip(
            track_id=target_track_id,
            source=nested_timeline.id,
            start_time=min_start,
            duration=max_end - min_start,
            name=name,
            overlap_strategy=OverlapStrategy.OVERWRITE
        )

        if compound_clip:
            compound_clip.is_compound = True

            # Remove original clips
            for clip in clips:
                self.remove_clip(clip.id)

        return compound_clip

    def expand_compound_clip(self, clip_id: str) -> bool:
        """
        Expand compound clip back to individual clips

        Args:
            clip_id: Compound clip to expand

        Returns:
            True if successful
        """
        clip = self.get_clip(clip_id)
        if not clip or not clip.is_compound:
            return False

        nested_timeline = self.compound_timelines.get(clip.source)
        if not nested_timeline:
            return False

        # Recreate original clips
        offset = clip.start_time

        for track in nested_timeline.tracks:
            # Find or create matching track
            target_track = None
            for t in self.tracks:
                if t.type == track.type and t.name == track.name:
                    target_track = t
                    break

            if not target_track:
                target_track = self.add_track(track.type, track.name)

            # Add clips
            for nested_clip in track.clips:
                new_clip = copy.deepcopy(nested_clip)
                new_clip.start_time += offset
                new_clip.track_id = target_track.id
                target_track.add_clip(new_clip, OverlapStrategy.LAYER)

        # Remove compound clip
        self.remove_clip(clip_id)

        return True

    # ==================== Gap Operations ====================

    def detect_gaps(self, track_id: str) -> List[Tuple[float, float]]:
        """Detect gaps in track"""
        track = self.get_track(track_id)
        if track:
            return track.detect_gaps()
        return []

    def remove_gaps(self, track_id: str) -> int:
        """Remove gaps in track"""
        track = self.get_track(track_id)
        if track and not track.locked:
            return track.remove_gaps()
        return 0

    def remove_all_gaps(self) -> int:
        """Remove gaps in all unlocked tracks"""
        total = 0
        for track in self.tracks:
            if not track.locked:
                total += track.remove_gaps()
        return total

    # ==================== Overlap Detection ====================

    def detect_overlaps(self, track_id: str) -> List[Tuple[Clip, Clip]]:
        """
        Detect overlapping clips in track

        Returns:
            List of (clip1, clip2) tuples
        """
        track = self.get_track(track_id)
        if not track:
            return []

        overlaps = []
        clips = sorted(track.clips, key=lambda c: c.start_time)

        for i in range(len(clips) - 1):
            for j in range(i + 1, len(clips)):
                if clips[i].overlaps_with(clips[j]):
                    overlaps.append((clips[i], clips[j]))

        return overlaps

    def resolve_overlaps(
        self,
        track_id: str,
        strategy: OverlapStrategy = OverlapStrategy.REJECT
    ) -> int:
        """
        Resolve overlapping clips

        Args:
            track_id: Track to process
            strategy: How to resolve overlaps

        Returns:
            Number of overlaps resolved
        """
        overlaps = self.detect_overlaps(track_id)
        if not overlaps:
            return 0

        track = self.get_track(track_id)
        if not track or track.locked:
            return 0

        resolved = 0

        for clip1, clip2 in overlaps:
            if strategy == OverlapStrategy.OVERWRITE:
                # Keep earlier clip, trim or remove later
                if clip1.start_time < clip2.start_time:
                    if clip2.start_time < clip1.end_time:
                        # Trim clip2 or remove if fully overlapped
                        if clip2.end_time <= clip1.end_time:
                            track.remove_clip(clip2.id)
                        else:
                            clip2.start_time = clip1.end_time
                            clip2.duration = clip2.end_time - clip2.start_time
                        resolved += 1

            elif strategy == OverlapStrategy.INSERT:
                # Shift later clip
                if clip1.start_time < clip2.start_time:
                    overlap = clip1.end_time - clip2.start_time
                    if overlap > 0:
                        clip2.start_time += overlap
                        resolved += 1

        return resolved

    # ==================== Magnetic Timeline ====================

    def find_snap_position(
        self,
        time: float,
        track_id: Optional[str] = None,
        exclude_clip_id: Optional[str] = None
    ) -> float:
        """
        Find nearest snap position for magnetic timeline

        Args:
            time: Requested time
            track_id: Track to check (all tracks if None)
            exclude_clip_id: Clip to exclude from snapping

        Returns:
            Snapped time or original time if no snap point
        """
        snap_points = [0.0]  # Always snap to start

        # Collect snap points from clips
        tracks = [self.get_track(track_id)] if track_id else self.tracks

        for track in tracks:
            if not track:
                continue
            for clip in track.clips:
                if clip.id != exclude_clip_id:
                    snap_points.append(clip.start_time)
                    snap_points.append(clip.end_time)

        # Find closest snap point within snap distance
        closest = time
        min_distance = self.snap_distance

        for point in snap_points:
            distance = abs(time - point)
            if distance < min_distance:
                min_distance = distance
                closest = point

        return closest

    # ==================== Timeline Info ====================

    def get_duration(self) -> float:
        """Get total timeline duration"""
        if not self.tracks:
            return 0.0
        return max((track.get_duration() for track in self.tracks), default=0.0)

    def get_frame_count(self) -> int:
        """Get total frame count"""
        return int(self.get_duration() * self.frame_rate)

    def time_to_frame(self, time: float) -> int:
        """Convert time to frame number"""
        return int(time * self.frame_rate)

    def frame_to_time(self, frame: int) -> float:
        """Convert frame number to time"""
        return frame / self.frame_rate

    # ==================== Beat Sync Integration ====================

    def apply_beat_sync(
        self,
        sync_points: List,
        track_id: str,
        snap_tolerance: float = 0.05,
        add_transitions: bool = True,
        transition_duration: float = 0.5
    ) -> Dict[str, Any]:
        """
        Align cuts/transitions to beat positions

        Takes sync points from precision_av_sync and adjusts clip positions
        to align with audio beats for beat-matched editing.

        Args:
            sync_points: List of SyncPoint objects from precision_av_sync
            track_id: Track to apply beat sync to
            snap_tolerance: How close clips need to be to snap to beat (seconds)
            add_transitions: Whether to add transitions at beat points
            transition_duration: Duration of transitions in seconds

        Returns:
            Dict with:
                - adjusted_clips: Number of clips adjusted
                - snapped_to_beats: Number of beats used for snapping
                - transitions_added: Number of transitions added
                - sync_quality: Overall sync quality score
        """
        track = self.get_track(track_id)
        if not track or track.locked:
            return {
                "status": "failed",
                "error": "Track not found or locked"
            }

        # Extract beat timestamps from sync points
        beat_times = []
        for sp in sync_points:
            # Use audio peaks that are beats
            if hasattr(sp, 'audio_peak') and sp.audio_peak.peak_type == 'beat':
                beat_times.append(sp.audio_peak.timestamp)

        if not beat_times:
            # Fallback: use all audio timestamps
            for sp in sync_points:
                if hasattr(sp, 'audio_peak'):
                    beat_times.append(sp.audio_peak.timestamp)

        beat_times.sort()

        if not beat_times:
            return {
                "status": "failed",
                "error": "No beat times found in sync points"
            }

        adjusted_count = 0
        snapped_count = 0
        transitions_added = 0

        # Adjust clip positions to align with beats
        for clip in track.clips:
            if clip.locked:
                continue

            # Find nearest beat to clip start
            nearest_beat = min(beat_times, key=lambda t: abs(t - clip.start_time))
            distance = abs(nearest_beat - clip.start_time)

            # Snap to beat if within tolerance
            if distance <= snap_tolerance:
                clip.start_time = nearest_beat
                adjusted_count += 1
                snapped_count += 1

            # Also check clip end
            nearest_end_beat = min(beat_times, key=lambda t: abs(t - clip.end_time))
            end_distance = abs(nearest_end_beat - clip.end_time)

            if end_distance <= snap_tolerance:
                # Adjust duration to snap end to beat
                new_duration = nearest_end_beat - clip.start_time
                if new_duration > 0:
                    clip.duration = new_duration
                    adjusted_count += 1

        # Add transitions at beat points if requested
        if add_transitions:
            # Sort clips by start time
            track._sort_clips()

            for i in range(len(track.clips) - 1):
                current_clip = track.clips[i]
                next_clip = track.clips[i + 1]

                # Check if there's a beat near the transition point
                transition_point = current_clip.end_time
                nearest_beat = min(beat_times, key=lambda t: abs(t - transition_point))

                if abs(nearest_beat - transition_point) <= snap_tolerance:
                    # Add transition
                    transition = Transition(
                        type=TransitionType.DISSOLVE,
                        duration=min(transition_duration, current_clip.duration / 2, next_clip.duration / 2),
                        from_clip_id=current_clip.id,
                        to_clip_id=next_clip.id
                    )
                    self.transitions.append(transition)
                    transitions_added += 1

        # Calculate sync quality
        total_clips = len([c for c in track.clips if not c.locked])
        sync_quality = adjusted_count / total_clips if total_clips > 0 else 0

        return {
            "status": "success",
            "adjusted_clips": adjusted_count,
            "snapped_to_beats": snapped_count,
            "transitions_added": transitions_added,
            "sync_quality": sync_quality,
            "total_beats_available": len(beat_times),
            "track_id": track_id
        }

    def align_clips_to_beats(
        self,
        beat_times: List[float],
        track_id: str,
        strategy: str = "nearest"
    ) -> int:
        """
        Align all clips in track to beat positions

        Args:
            beat_times: List of beat timestamps in seconds
            track_id: Track to align
            strategy: Alignment strategy ("nearest", "earlier", "later")

        Returns:
            Number of clips aligned
        """
        track = self.get_track(track_id)
        if not track or track.locked:
            return 0

        aligned_count = 0

        for clip in track.clips:
            if clip.locked:
                continue

            if strategy == "nearest":
                # Find nearest beat
                nearest_beat = min(beat_times, key=lambda t: abs(t - clip.start_time))
                clip.start_time = nearest_beat
                aligned_count += 1

            elif strategy == "earlier":
                # Find nearest earlier beat
                earlier_beats = [t for t in beat_times if t <= clip.start_time]
                if earlier_beats:
                    clip.start_time = max(earlier_beats)
                    aligned_count += 1

            elif strategy == "later":
                # Find nearest later beat
                later_beats = [t for t in beat_times if t >= clip.start_time]
                if later_beats:
                    clip.start_time = min(later_beats)
                    aligned_count += 1

        track._sort_clips()
        return aligned_count

    # ==================== Serialization ====================

    def serialize(self) -> str:
        """
        Serialize timeline to JSON

        Returns:
            JSON string
        """
        data = {
            'id': self.id,
            'name': self.name,
            'frame_rate': self.frame_rate,
            'resolution': self.resolution,
            'sample_rate': self.sample_rate,
            'snap_distance': self.snap_distance,
            'tracks': [t.to_dict() for t in self.tracks],
            'transitions': [t.to_dict() for t in self.transitions],
            'compound_timelines': {
                tid: tl.serialize() for tid, tl in self.compound_timelines.items()
            },
            'metadata': self.metadata
        }
        return json.dumps(data, indent=2)

    @classmethod
    def deserialize(cls, json_str: str) -> 'Timeline':
        """
        Deserialize timeline from JSON

        Args:
            json_str: JSON string

        Returns:
            Timeline instance
        """
        data = json.loads(json_str)

        timeline = cls(
            name=data.get('name', 'Untitled Timeline'),
            frame_rate=data.get('frame_rate', 30.0),
            resolution=tuple(data.get('resolution', [1920, 1080])),
            sample_rate=data.get('sample_rate', 48000),
            snap_distance=data.get('snap_distance', 0.1)
        )

        timeline.id = data.get('id', timeline.id)
        timeline.metadata = data.get('metadata', {})

        # Restore tracks
        for track_data in data.get('tracks', []):
            track = Track.from_dict(track_data)
            timeline.tracks.append(track)

        # Restore transitions
        for trans_data in data.get('transitions', []):
            trans = Transition.from_dict(trans_data)
            timeline.transitions.append(trans)

        # Restore compound timelines
        for tid, tl_json in data.get('compound_timelines', {}).items():
            timeline.compound_timelines[tid] = cls.deserialize(tl_json)

        return timeline

    # ==================== FFmpeg Generation ====================

    def to_ffmpeg_command(self, output_path: str) -> str:
        """
        Generate FFmpeg command from timeline

        Args:
            output_path: Output file path

        Returns:
            FFmpeg command string
        """
        inputs = []
        filter_complex = []
        input_map = {}
        input_counter = 0

        # Collect all unique sources
        sources = set()
        for track in self.tracks:
            for clip in track.clips:
                if not clip.enabled or clip.is_compound:
                    continue
                sources.add(clip.source)

        # Create input map
        for source in sources:
            input_map[source] = input_counter
            inputs.append(f"-i {source}")
            input_counter += 1

        # Generate filter complex
        filter_parts = []

        # Process video tracks
        video_tracks = [t for t in self.tracks if t.type == TrackType.VIDEO]
        video_streams = []

        for track_idx, track in enumerate(video_tracks):
            if track.muted or not track.visible:
                continue

            # Check if any track is soloed
            has_solo = any(t.solo for t in video_tracks)
            if has_solo and not track.solo:
                continue

            for clip_idx, clip in enumerate(track.clips):
                if not clip.enabled:
                    continue

                input_idx = input_map.get(clip.source)
                if input_idx is None:
                    continue

                stream_label = f"v{track_idx}_{clip_idx}"

                # Trim and set timing
                trim_filter = (
                    f"[{input_idx}:v]trim=start={clip.in_point}:end={clip.out_point or clip.in_point + clip.duration},"
                    f"setpts=PTS-STARTPTS"
                )

                # Apply speed if needed
                if clip.speed != 1.0:
                    trim_filter += f",setpts=PTS/{clip.speed}"

                # Apply clip effects
                for effect in clip.effects:
                    if not effect.enabled:
                        continue
                    trim_filter += self._effect_to_filter(effect)

                # Apply track effects
                for effect in track.effects:
                    if not effect.enabled:
                        continue
                    trim_filter += self._effect_to_filter(effect)

                # Scale to timeline resolution
                trim_filter += f",scale={self.resolution[0]}:{self.resolution[1]}"

                trim_filter += f"[{stream_label}]"
                filter_parts.append(trim_filter)

                video_streams.append((stream_label, clip.start_time, clip.duration))

        # Process audio tracks
        audio_tracks = [t for t in self.tracks if t.type == TrackType.AUDIO]
        audio_streams = []

        for track_idx, track in enumerate(audio_tracks):
            if track.muted:
                continue

            # Check if any track is soloed
            has_solo = any(t.solo for t in audio_tracks)
            if has_solo and not track.solo:
                continue

            for clip_idx, clip in enumerate(track.clips):
                if not clip.enabled:
                    continue

                input_idx = input_map.get(clip.source)
                if input_idx is None:
                    continue

                stream_label = f"a{track_idx}_{clip_idx}"

                # Trim audio
                trim_filter = (
                    f"[{input_idx}:a]atrim=start={clip.in_point}:end={clip.out_point or clip.in_point + clip.duration},"
                    f"asetpts=PTS-STARTPTS"
                )

                # Apply speed if needed
                if clip.speed != 1.0:
                    trim_filter += f",atempo={clip.speed}"

                # Apply volume
                volume = clip.volume * track.volume
                if volume != 1.0:
                    trim_filter += f",volume={volume}"

                trim_filter += f"[{stream_label}]"
                filter_parts.append(trim_filter)

                audio_streams.append((stream_label, clip.start_time, clip.duration))

        # Composite video streams with timing
        if video_streams:
            # Sort by time
            video_streams.sort(key=lambda x: x[1])

            # Create timeline composition
            if len(video_streams) == 1:
                final_video = video_streams[0][0]
            else:
                # Use concat filter for sequential clips or overlay for layers
                concat_inputs = ";".join([f"[{s[0]}]" for s in video_streams])
                filter_parts.append(f"{concat_inputs}concat=n={len(video_streams)}:v=1:a=0[vout]")
                final_video = "vout"
        else:
            final_video = None

        # Mix audio streams
        if audio_streams:
            audio_streams.sort(key=lambda x: x[1])

            if len(audio_streams) == 1:
                final_audio = audio_streams[0][0]
            else:
                # Mix all audio
                mix_inputs = "".join([f"[{s[0]}]" for s in audio_streams])
                filter_parts.append(f"{mix_inputs}amix=inputs={len(audio_streams)}:duration=longest[aout]")
                final_audio = "aout"
        else:
            final_audio = None

        # Build command
        cmd_parts = ["ffmpeg"]
        cmd_parts.extend(inputs)

        if filter_parts:
            filter_complex = ";".join(filter_parts)
            cmd_parts.append(f'-filter_complex "{filter_complex}"')

        # Map outputs
        if final_video:
            cmd_parts.append(f"-map [{final_video}]")
        if final_audio:
            cmd_parts.append(f"-map [{final_audio}]")

        # Output settings
        cmd_parts.extend([
            f"-r {self.frame_rate}",
            f"-s {self.resolution[0]}x{self.resolution[1]}",
            f"-ar {self.sample_rate}",
            "-c:v libx264",
            "-c:a aac",
            "-b:a 192k",
            "-movflags +faststart",
            output_path
        ])

        return " ".join(cmd_parts)

    def _effect_to_filter(self, effect: Effect) -> str:
        """
        Convert effect to FFmpeg filter

        Args:
            effect: Effect to convert

        Returns:
            Filter string
        """
        filters = {
            'blur': lambda p: f",boxblur={p.get('radius', 5)}",
            'brightness': lambda p: f",eq=brightness={p.get('value', 0)}",
            'contrast': lambda p: f",eq=contrast={p.get('value', 1)}",
            'saturation': lambda p: f",eq=saturation={p.get('value', 1)}",
            'fade_in': lambda p: f",fade=in:st={p.get('start', 0)}:d={p.get('duration', 1)}",
            'fade_out': lambda p: f",fade=out:st={p.get('start', 0)}:d={p.get('duration', 1)}",
        }

        filter_fn = filters.get(effect.type)
        if filter_fn:
            return filter_fn(effect.parameters)
        return ""


# ==================== Utility Functions ====================

def create_sample_timeline() -> Timeline:
    """Create a sample timeline for testing"""
    timeline = Timeline(
        name="Sample Project",
        frame_rate=30.0,
        resolution=(1920, 1080)
    )

    # Add tracks
    video_track = timeline.add_track(TrackType.VIDEO, "Video 1")
    audio_track = timeline.add_track(TrackType.AUDIO, "Audio 1")

    return timeline


if __name__ == "__main__":
    # Example usage
    print("Timeline Engine v1.0.0")
    print("=" * 50)

    # Create timeline
    timeline = create_sample_timeline()

    # Add some clips
    clip1 = timeline.add_clip(
        track_id=timeline.tracks[0].id,
        source="/path/to/video1.mp4",
        start_time=0.0,
        duration=5.0,
        name="Opening Scene"
    )

    clip2 = timeline.add_clip(
        track_id=timeline.tracks[0].id,
        source="/path/to/video2.mp4",
        start_time=5.0,
        duration=3.0,
        name="Scene 2"
    )

    # Split a clip
    if clip1:
        split_result = timeline.split_clip(clip1.id, 2.5)
        if split_result:
            print(f"Split clip into: {split_result[0].name} and {split_result[1].name}")

    # Show timeline info
    print(f"\nTimeline: {timeline.name}")
    print(f"Duration: {timeline.get_duration():.2f}s")
    print(f"Frames: {timeline.get_frame_count()}")
    print(f"Tracks: {len(timeline.tracks)}")

    # Serialize
    json_data = timeline.serialize()
    print(f"\nSerialized size: {len(json_data)} bytes")

    # Generate FFmpeg command
    ffmpeg_cmd = timeline.to_ffmpeg_command("output.mp4")
    print(f"\nFFmpeg command:\n{ffmpeg_cmd[:200]}...")

    print("\nTimeline engine ready for production use!")
