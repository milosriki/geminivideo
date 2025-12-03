"""
Production-Ready Keyframe Animation System for Video Editing

Supports multiple animatable properties with various interpolation types,
FFmpeg filter generation, and complete keyframe management.
"""

import json
import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Tuple, Optional, Union
from enum import Enum
from copy import deepcopy


class InterpolationType(Enum):
    """Supported interpolation types for keyframe animation."""
    LINEAR = "linear"
    BEZIER = "bezier"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    ELASTIC = "elastic"
    BOUNCE = "bounce"
    STEP = "step"


class PropertyType(Enum):
    """Animatable property types."""
    POSITION_X = "position_x"
    POSITION_Y = "position_y"
    SCALE_X = "scale_x"
    SCALE_Y = "scale_y"
    ROTATION = "rotation"
    OPACITY = "opacity"
    VOLUME = "volume"
    COLOR_RED = "color_red"
    COLOR_GREEN = "color_green"
    COLOR_BLUE = "color_blue"
    COLOR_ALPHA = "color_alpha"


@dataclass
class BezierControlPoints:
    """Control points for cubic Bezier curve interpolation."""
    cp1_x: float = 0.42  # First control point X
    cp1_y: float = 0.0   # First control point Y
    cp2_x: float = 0.58  # Second control point X
    cp2_y: float = 1.0   # Second control point Y

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            'cp1_x': self.cp1_x,
            'cp1_y': self.cp1_y,
            'cp2_x': self.cp2_x,
            'cp2_y': self.cp2_y
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'BezierControlPoints':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Keyframe:
    """
    Represents a single keyframe in an animation timeline.

    Attributes:
        time: Time in seconds where this keyframe occurs
        value: The value at this keyframe (can be float or list of floats)
        interpolation: Type of interpolation to next keyframe
        bezier_points: Control points for bezier interpolation
    """
    time: float
    value: Union[float, List[float]]
    interpolation: InterpolationType = InterpolationType.LINEAR
    bezier_points: Optional[BezierControlPoints] = None

    def __post_init__(self):
        """Ensure interpolation is an InterpolationType enum."""
        if isinstance(self.interpolation, str):
            self.interpolation = InterpolationType(self.interpolation)

        # Create default bezier points if using bezier interpolation
        if self.interpolation == InterpolationType.BEZIER and self.bezier_points is None:
            self.bezier_points = BezierControlPoints()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize keyframe to dictionary."""
        data = {
            'time': self.time,
            'value': self.value,
            'interpolation': self.interpolation.value
        }
        if self.bezier_points:
            data['bezier_points'] = self.bezier_points.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Keyframe':
        """Deserialize keyframe from dictionary."""
        bezier_points = None
        if 'bezier_points' in data:
            bezier_points = BezierControlPoints.from_dict(data['bezier_points'])

        return cls(
            time=data['time'],
            value=data['value'],
            interpolation=InterpolationType(data['interpolation']),
            bezier_points=bezier_points
        )


class InterpolationEngine:
    """
    Handles various interpolation algorithms for keyframe animation.
    """

    @staticmethod
    def cubic_bezier(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
        """
        Calculate cubic Bezier curve value at parameter t.

        Args:
            t: Parameter value (0-1)
            p0, p1, p2, p3: Control points

        Returns:
            Interpolated value
        """
        u = 1 - t
        return (u * u * u * p0 +
                3 * u * u * t * p1 +
                3 * u * t * t * p2 +
                t * t * t * p3)

    @staticmethod
    def solve_bezier_t(x: float, cp1_x: float, cp2_x: float, epsilon: float = 1e-6) -> float:
        """
        Solve for t given x in a cubic Bezier curve (for timing function).
        Uses Newton-Raphson method for accurate approximation.

        Args:
            x: Target x value (0-1)
            cp1_x, cp2_x: X coordinates of control points
            epsilon: Convergence threshold

        Returns:
            Parameter t that produces the given x
        """
        # Newton-Raphson iteration
        t = x
        for _ in range(8):  # Max 8 iterations
            # Calculate current x at t
            current_x = InterpolationEngine.cubic_bezier(t, 0, cp1_x, cp2_x, 1)

            # Check if close enough
            if abs(current_x - x) < epsilon:
                return t

            # Calculate derivative
            u = 1 - t
            derivative = (3 * u * u * (cp1_x - 0) +
                         6 * u * t * (cp2_x - cp1_x) +
                         3 * t * t * (1 - cp2_x))

            # Avoid division by zero
            if abs(derivative) < 1e-6:
                break

            # Newton-Raphson step
            t = t - (current_x - x) / derivative
            t = max(0, min(1, t))  # Clamp to [0, 1]

        return t

    @staticmethod
    def linear(t: float, start: float, end: float) -> float:
        """Linear interpolation."""
        return start + (end - start) * t

    @staticmethod
    def bezier_easing(t: float, start: float, end: float,
                     control_points: BezierControlPoints) -> float:
        """
        Bezier curve interpolation with custom control points.

        Args:
            t: Time progress (0-1)
            start: Start value
            end: End value
            control_points: Bezier control points

        Returns:
            Interpolated value
        """
        # Solve for curve parameter given time
        curve_t = InterpolationEngine.solve_bezier_t(
            t, control_points.cp1_x, control_points.cp2_x
        )

        # Calculate y value using bezier curve
        progress = InterpolationEngine.cubic_bezier(
            curve_t, 0, control_points.cp1_y, control_points.cp2_y, 1
        )

        return start + (end - start) * progress

    @staticmethod
    def ease_in(t: float, start: float, end: float) -> float:
        """Ease-in interpolation (slow start, fast end)."""
        # Cubic ease-in
        progress = t * t * t
        return start + (end - start) * progress

    @staticmethod
    def ease_out(t: float, start: float, end: float) -> float:
        """Ease-out interpolation (fast start, slow end)."""
        # Cubic ease-out
        progress = 1 - math.pow(1 - t, 3)
        return start + (end - start) * progress

    @staticmethod
    def ease_in_out(t: float, start: float, end: float) -> float:
        """Ease-in-out interpolation (slow start and end, fast middle)."""
        # Cubic ease-in-out
        if t < 0.5:
            progress = 4 * t * t * t
        else:
            progress = 1 - math.pow(-2 * t + 2, 3) / 2
        return start + (end - start) * progress

    @staticmethod
    def elastic(t: float, start: float, end: float) -> float:
        """
        Elastic interpolation (overshoots and oscillates).
        """
        if t == 0:
            return start
        if t == 1:
            return end

        c4 = (2 * math.pi) / 3
        progress = -math.pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)
        progress = 1 + progress

        return start + (end - start) * progress

    @staticmethod
    def bounce(t: float, start: float, end: float) -> float:
        """
        Bounce interpolation (bouncing effect at the end).
        """
        n1 = 7.5625
        d1 = 2.75

        if t < 1 / d1:
            progress = n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            progress = n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            progress = n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            progress = n1 * t * t + 0.984375

        return start + (end - start) * progress

    @staticmethod
    def step(t: float, start: float, end: float) -> float:
        """Step/Hold interpolation (no interpolation, holds start value until end)."""
        return start if t < 1.0 else end

    @staticmethod
    def interpolate(t: float, start: float, end: float,
                   interpolation: InterpolationType,
                   bezier_points: Optional[BezierControlPoints] = None) -> float:
        """
        Main interpolation dispatcher.

        Args:
            t: Time progress (0-1)
            start: Start value
            end: End value
            interpolation: Type of interpolation
            bezier_points: Control points for bezier (if applicable)

        Returns:
            Interpolated value
        """
        t = max(0, min(1, t))  # Clamp t to [0, 1]

        if interpolation == InterpolationType.LINEAR:
            return InterpolationEngine.linear(t, start, end)
        elif interpolation == InterpolationType.BEZIER:
            if bezier_points is None:
                bezier_points = BezierControlPoints()
            return InterpolationEngine.bezier_easing(t, start, end, bezier_points)
        elif interpolation == InterpolationType.EASE_IN:
            return InterpolationEngine.ease_in(t, start, end)
        elif interpolation == InterpolationType.EASE_OUT:
            return InterpolationEngine.ease_out(t, start, end)
        elif interpolation == InterpolationType.EASE_IN_OUT:
            return InterpolationEngine.ease_in_out(t, start, end)
        elif interpolation == InterpolationType.ELASTIC:
            return InterpolationEngine.elastic(t, start, end)
        elif interpolation == InterpolationType.BOUNCE:
            return InterpolationEngine.bounce(t, start, end)
        elif interpolation == InterpolationType.STEP:
            return InterpolationEngine.step(t, start, end)
        else:
            return InterpolationEngine.linear(t, start, end)


class KeyframeTrack:
    """
    Manages a collection of keyframes for a single property.
    """

    def __init__(self, property_type: PropertyType):
        """
        Initialize keyframe track.

        Args:
            property_type: Type of property being animated
        """
        self.property_type = property_type
        self.keyframes: List[Keyframe] = []

    def add_keyframe(self, time: float, value: Union[float, List[float]],
                    interpolation: InterpolationType = InterpolationType.LINEAR,
                    bezier_points: Optional[BezierControlPoints] = None) -> Keyframe:
        """
        Add a keyframe at specified time.

        Args:
            time: Time in seconds
            value: Value at this keyframe
            interpolation: Interpolation type to next keyframe
            bezier_points: Control points for bezier interpolation

        Returns:
            Created keyframe
        """
        # Remove existing keyframe at same time if exists
        self.remove_keyframe_at_time(time)

        keyframe = Keyframe(
            time=time,
            value=value,
            interpolation=interpolation,
            bezier_points=bezier_points
        )

        self.keyframes.append(keyframe)
        self._sort_keyframes()

        return keyframe

    def remove_keyframe_at_time(self, time: float, tolerance: float = 0.001) -> bool:
        """
        Remove keyframe at specified time.

        Args:
            time: Time in seconds
            tolerance: Time tolerance for matching

        Returns:
            True if keyframe was removed
        """
        for i, kf in enumerate(self.keyframes):
            if abs(kf.time - time) < tolerance:
                self.keyframes.pop(i)
                return True
        return False

    def move_keyframe(self, old_time: float, new_time: float,
                     tolerance: float = 0.001) -> bool:
        """
        Move a keyframe from one time to another.

        Args:
            old_time: Current time of keyframe
            new_time: New time for keyframe
            tolerance: Time tolerance for matching

        Returns:
            True if keyframe was moved
        """
        for kf in self.keyframes:
            if abs(kf.time - old_time) < tolerance:
                kf.time = new_time
                self._sort_keyframes()
                return True
        return False

    def get_keyframe_at_time(self, time: float,
                            tolerance: float = 0.001) -> Optional[Keyframe]:
        """
        Get keyframe at specified time.

        Args:
            time: Time in seconds
            tolerance: Time tolerance for matching

        Returns:
            Keyframe if found, None otherwise
        """
        for kf in self.keyframes:
            if abs(kf.time - time) < tolerance:
                return kf
        return None

    def copy_keyframe(self, time: float, tolerance: float = 0.001) -> Optional[Keyframe]:
        """
        Copy keyframe at specified time.

        Args:
            time: Time in seconds
            tolerance: Time tolerance for matching

        Returns:
            Copy of keyframe if found, None otherwise
        """
        kf = self.get_keyframe_at_time(time, tolerance)
        if kf:
            return deepcopy(kf)
        return None

    def paste_keyframe(self, keyframe: Keyframe, time: Optional[float] = None):
        """
        Paste a keyframe (possibly at a new time).

        Args:
            keyframe: Keyframe to paste
            time: New time (if None, uses keyframe's time)
        """
        new_kf = deepcopy(keyframe)
        if time is not None:
            new_kf.time = time

        self.remove_keyframe_at_time(new_kf.time)
        self.keyframes.append(new_kf)
        self._sort_keyframes()

    def get_value_at(self, time: float) -> Union[float, List[float]]:
        """
        Calculate value at specified time using interpolation.

        Args:
            time: Time in seconds

        Returns:
            Interpolated value
        """
        if not self.keyframes:
            return 0.0

        # Before first keyframe
        if time <= self.keyframes[0].time:
            return self.keyframes[0].value

        # After last keyframe
        if time >= self.keyframes[-1].time:
            return self.keyframes[-1].value

        # Find surrounding keyframes
        for i in range(len(self.keyframes) - 1):
            kf1 = self.keyframes[i]
            kf2 = self.keyframes[i + 1]

            if kf1.time <= time <= kf2.time:
                # Calculate normalized time between keyframes
                duration = kf2.time - kf1.time
                if duration == 0:
                    return kf1.value

                t = (time - kf1.time) / duration

                # Handle single value
                if isinstance(kf1.value, (int, float)) and isinstance(kf2.value, (int, float)):
                    return InterpolationEngine.interpolate(
                        t, float(kf1.value), float(kf2.value),
                        kf1.interpolation, kf1.bezier_points
                    )

                # Handle list of values (e.g., RGB)
                if isinstance(kf1.value, list) and isinstance(kf2.value, list):
                    return [
                        InterpolationEngine.interpolate(
                            t, float(v1), float(v2),
                            kf1.interpolation, kf1.bezier_points
                        )
                        for v1, v2 in zip(kf1.value, kf2.value)
                    ]

        return self.keyframes[-1].value

    def _sort_keyframes(self):
        """Sort keyframes by time."""
        self.keyframes.sort(key=lambda kf: kf.time)

    def get_time_range(self) -> Tuple[float, float]:
        """
        Get time range covered by keyframes.

        Returns:
            Tuple of (start_time, end_time)
        """
        if not self.keyframes:
            return (0.0, 0.0)
        return (self.keyframes[0].time, self.keyframes[-1].time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize track to dictionary."""
        return {
            'property_type': self.property_type.value,
            'keyframes': [kf.to_dict() for kf in self.keyframes]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyframeTrack':
        """Deserialize track from dictionary."""
        track = cls(PropertyType(data['property_type']))
        track.keyframes = [Keyframe.from_dict(kf_data) for kf_data in data['keyframes']]
        return track


class KeyframeAnimator:
    """
    Manages all keyframe tracks for a video clip.
    """

    def __init__(self, clip_id: str):
        """
        Initialize keyframe animator.

        Args:
            clip_id: Unique identifier for the clip
        """
        self.clip_id = clip_id
        self.tracks: Dict[PropertyType, KeyframeTrack] = {}

    def add_keyframe(self, property_type: PropertyType, time: float,
                    value: Union[float, List[float]],
                    interpolation: InterpolationType = InterpolationType.LINEAR,
                    bezier_points: Optional[BezierControlPoints] = None) -> Keyframe:
        """
        Add keyframe for a property.

        Args:
            property_type: Type of property to animate
            time: Time in seconds
            value: Value at this keyframe
            interpolation: Interpolation type
            bezier_points: Control points for bezier

        Returns:
            Created keyframe
        """
        if property_type not in self.tracks:
            self.tracks[property_type] = KeyframeTrack(property_type)

        return self.tracks[property_type].add_keyframe(
            time, value, interpolation, bezier_points
        )

    def remove_keyframe(self, property_type: PropertyType, time: float) -> bool:
        """Remove keyframe at specified time for a property."""
        if property_type in self.tracks:
            return self.tracks[property_type].remove_keyframe_at_time(time)
        return False

    def move_keyframe(self, property_type: PropertyType,
                     old_time: float, new_time: float) -> bool:
        """Move keyframe from one time to another."""
        if property_type in self.tracks:
            return self.tracks[property_type].move_keyframe(old_time, new_time)
        return False

    def copy_keyframe(self, property_type: PropertyType,
                     time: float) -> Optional[Keyframe]:
        """Copy keyframe at specified time."""
        if property_type in self.tracks:
            return self.tracks[property_type].copy_keyframe(time)
        return None

    def paste_keyframe(self, property_type: PropertyType,
                      keyframe: Keyframe, time: Optional[float] = None):
        """Paste keyframe to a property track."""
        if property_type not in self.tracks:
            self.tracks[property_type] = KeyframeTrack(property_type)

        self.tracks[property_type].paste_keyframe(keyframe, time)

    def get_value_at(self, property_type: PropertyType,
                    time: float) -> Union[float, List[float]]:
        """
        Get interpolated value for a property at specified time.

        Args:
            property_type: Property type
            time: Time in seconds

        Returns:
            Interpolated value
        """
        if property_type in self.tracks:
            return self.tracks[property_type].get_value_at(time)
        return 0.0

    def has_animation(self, property_type: PropertyType) -> bool:
        """Check if property has any keyframes."""
        return property_type in self.tracks and len(self.tracks[property_type].keyframes) > 0

    def get_animated_properties(self) -> List[PropertyType]:
        """Get list of all properties with keyframes."""
        return [pt for pt in self.tracks.keys() if len(self.tracks[pt].keyframes) > 0]

    def to_ffmpeg_expression(self, property_type: PropertyType,
                            fps: float = 30.0,
                            video_width: int = 1920,
                            video_height: int = 1080) -> Optional[str]:
        """
        Generate FFmpeg filter expression for animated property.

        Args:
            property_type: Property to generate expression for
            fps: Frame rate for sampling
            video_width: Video width (for position calculations)
            video_height: Video height (for position calculations)

        Returns:
            FFmpeg expression string or None if no animation
        """
        if not self.has_animation(property_type):
            return None

        track = self.tracks[property_type]
        start_time, end_time = track.get_time_range()

        # Sample keyframe values at regular intervals
        sample_times = []
        duration = end_time - start_time
        if duration <= 0:
            return None

        # Sample at frame rate
        num_samples = max(int(duration * fps) + 1, 2)
        for i in range(num_samples):
            t = start_time + (duration * i / (num_samples - 1))
            sample_times.append(t)

        # Generate expression based on property type
        if property_type == PropertyType.OPACITY:
            # Generate alpha expression
            values = [track.get_value_at(t) for t in sample_times]

            # Build FFmpeg expression with conditional time ranges
            expr_parts = []
            for i, (t, val) in enumerate(zip(sample_times[:-1], values[:-1])):
                next_t = sample_times[i + 1]
                next_val = values[i + 1]

                # Linear interpolation in FFmpeg
                expr = f"if(between(t,{t:.3f},{next_t:.3f}),lerp({val:.3f},{next_val:.3f},(t-{t:.3f})/({next_t-t:.3f})),0)"
                expr_parts.append(expr)

            # Combine with + operator (any matching condition returns value)
            full_expr = "+".join(expr_parts) if expr_parts else "1.0"
            return f"format=rgba,colorchannelmixer=aa={full_expr}"

        elif property_type == PropertyType.SCALE_X or property_type == PropertyType.SCALE_Y:
            # Generate scale expression
            values = [track.get_value_at(t) for t in sample_times]

            expr_parts = []
            for i, (t, val) in enumerate(zip(sample_times[:-1], values[:-1])):
                next_t = sample_times[i + 1]
                next_val = values[i + 1]

                expr = f"if(between(t,{t:.3f},{next_t:.3f}),lerp({val:.3f},{next_val:.3f},(t-{t:.3f})/({next_t-t:.3f})),1)"
                expr_parts.append(expr)

            scale_expr = "+".join(expr_parts) if expr_parts else "1.0"

            if property_type == PropertyType.SCALE_X:
                return f"scale=iw*({scale_expr}):ih"
            else:
                return f"scale=iw:ih*({scale_expr})"

        elif property_type == PropertyType.ROTATION:
            # Generate rotation expression
            values = [track.get_value_at(t) for t in sample_times]

            expr_parts = []
            for i, (t, val) in enumerate(zip(sample_times[:-1], values[:-1])):
                next_t = sample_times[i + 1]
                next_val = values[i + 1]

                # Convert degrees to radians
                val_rad = val * math.pi / 180
                next_val_rad = next_val * math.pi / 180

                expr = f"if(between(t,{t:.3f},{next_t:.3f}),lerp({val_rad:.6f},{next_val_rad:.6f},(t-{t:.3f})/({next_t-t:.3f})),0)"
                expr_parts.append(expr)

            rotate_expr = "+".join(expr_parts) if expr_parts else "0"
            return f"rotate={rotate_expr}:c=none:ow=rotw({rotate_expr}):oh=roth({rotate_expr})"

        elif property_type == PropertyType.VOLUME:
            # Generate volume expression
            values = [track.get_value_at(t) for t in sample_times]

            expr_parts = []
            for i, (t, val) in enumerate(zip(sample_times[:-1], values[:-1])):
                next_t = sample_times[i + 1]
                next_val = values[i + 1]

                expr = f"if(between(t,{t:.3f},{next_t:.3f}),lerp({val:.3f},{next_val:.3f},(t-{t:.3f})/({next_t-t:.3f})),1)"
                expr_parts.append(expr)

            volume_expr = "+".join(expr_parts) if expr_parts else "1.0"
            return f"volume={volume_expr}"

        # For position, we'd typically use overlay filter with expressions
        # which is handled at a higher level

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize animator to dictionary."""
        return {
            'clip_id': self.clip_id,
            'tracks': {
                prop_type.value: track.to_dict()
                for prop_type, track in self.tracks.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyframeAnimator':
        """Deserialize animator from dictionary."""
        animator = cls(data['clip_id'])
        for prop_type_str, track_data in data['tracks'].items():
            prop_type = PropertyType(prop_type_str)
            animator.tracks[prop_type] = KeyframeTrack.from_dict(track_data)
        return animator

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'KeyframeAnimator':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save_to_file(self, filepath: str):
        """Save animation data to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, filepath: str) -> 'KeyframeAnimator':
        """Load animation data from file."""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())

    def clear_all_keyframes(self):
        """Remove all keyframes from all tracks."""
        self.tracks.clear()

    def clear_property_keyframes(self, property_type: PropertyType):
        """Remove all keyframes for a specific property."""
        if property_type in self.tracks:
            del self.tracks[property_type]

    def get_all_keyframe_times(self) -> List[float]:
        """Get sorted list of all unique keyframe times across all properties."""
        times = set()
        for track in self.tracks.values():
            for kf in track.keyframes:
                times.add(kf.time)
        return sorted(times)

    def offset_all_keyframes(self, time_offset: float):
        """Shift all keyframes by a time offset."""
        for track in self.tracks.values():
            for kf in track.keyframes:
                kf.time += time_offset
            track._sort_keyframes()

    def scale_timeline(self, scale_factor: float):
        """Scale the timeline (speed up or slow down all animations)."""
        for track in self.tracks.values():
            for kf in track.keyframes:
                kf.time *= scale_factor
            track._sort_keyframes()


# Utility functions for common animation patterns

def create_fade_in(animator: KeyframeAnimator, start_time: float,
                  duration: float, interpolation: InterpolationType = InterpolationType.LINEAR):
    """
    Create a fade-in animation.

    Args:
        animator: KeyframeAnimator instance
        start_time: Start time in seconds
        duration: Duration of fade in seconds
        interpolation: Interpolation type
    """
    animator.add_keyframe(PropertyType.OPACITY, start_time, 0.0, interpolation)
    animator.add_keyframe(PropertyType.OPACITY, start_time + duration, 1.0)


def create_fade_out(animator: KeyframeAnimator, start_time: float,
                   duration: float, interpolation: InterpolationType = InterpolationType.LINEAR):
    """
    Create a fade-out animation.

    Args:
        animator: KeyframeAnimator instance
        start_time: Start time in seconds
        duration: Duration of fade in seconds
        interpolation: Interpolation type
    """
    animator.add_keyframe(PropertyType.OPACITY, start_time, 1.0, interpolation)
    animator.add_keyframe(PropertyType.OPACITY, start_time + duration, 0.0)


def create_zoom_in(animator: KeyframeAnimator, start_time: float,
                  duration: float, start_scale: float = 1.0, end_scale: float = 1.5,
                  interpolation: InterpolationType = InterpolationType.EASE_OUT):
    """
    Create a zoom-in animation.

    Args:
        animator: KeyframeAnimator instance
        start_time: Start time in seconds
        duration: Duration of zoom in seconds
        start_scale: Starting scale value
        end_scale: Ending scale value
        interpolation: Interpolation type
    """
    animator.add_keyframe(PropertyType.SCALE_X, start_time, start_scale, interpolation)
    animator.add_keyframe(PropertyType.SCALE_X, start_time + duration, end_scale)
    animator.add_keyframe(PropertyType.SCALE_Y, start_time, start_scale, interpolation)
    animator.add_keyframe(PropertyType.SCALE_Y, start_time + duration, end_scale)


def create_rotation_animation(animator: KeyframeAnimator, start_time: float,
                             duration: float, start_angle: float = 0.0,
                             end_angle: float = 360.0,
                             interpolation: InterpolationType = InterpolationType.LINEAR):
    """
    Create a rotation animation.

    Args:
        animator: KeyframeAnimator instance
        start_time: Start time in seconds
        duration: Duration of rotation in seconds
        start_angle: Starting angle in degrees
        end_angle: Ending angle in degrees
        interpolation: Interpolation type
    """
    animator.add_keyframe(PropertyType.ROTATION, start_time, start_angle, interpolation)
    animator.add_keyframe(PropertyType.ROTATION, start_time + duration, end_angle)


def create_slide_in(animator: KeyframeAnimator, start_time: float,
                   duration: float, direction: str = "left",
                   distance: float = 100.0,
                   interpolation: InterpolationType = InterpolationType.EASE_OUT):
    """
    Create a slide-in animation.

    Args:
        animator: KeyframeAnimator instance
        start_time: Start time in seconds
        duration: Duration of slide in seconds
        direction: Direction ("left", "right", "top", "bottom")
        distance: Distance to slide in pixels
        interpolation: Interpolation type
    """
    if direction == "left":
        animator.add_keyframe(PropertyType.POSITION_X, start_time, -distance, interpolation)
        animator.add_keyframe(PropertyType.POSITION_X, start_time + duration, 0.0)
    elif direction == "right":
        animator.add_keyframe(PropertyType.POSITION_X, start_time, distance, interpolation)
        animator.add_keyframe(PropertyType.POSITION_X, start_time + duration, 0.0)
    elif direction == "top":
        animator.add_keyframe(PropertyType.POSITION_Y, start_time, -distance, interpolation)
        animator.add_keyframe(PropertyType.POSITION_Y, start_time + duration, 0.0)
    elif direction == "bottom":
        animator.add_keyframe(PropertyType.POSITION_Y, start_time, distance, interpolation)
        animator.add_keyframe(PropertyType.POSITION_Y, start_time + duration, 0.0)
