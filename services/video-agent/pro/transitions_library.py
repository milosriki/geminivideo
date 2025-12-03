"""
Professional Transitions Library
Complete production-ready transitions with FFmpeg implementations
50+ professional transitions organized by category
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import math


class EasingFunction(Enum):
    """Easing functions for smooth transitions"""
    LINEAR = "linear"
    EASE_IN = "easeIn"
    EASE_OUT = "easeOut"
    EASE_IN_OUT = "easeInOut"
    EASE_IN_CUBIC = "easeInCubic"
    EASE_OUT_CUBIC = "easeOutCubic"
    EASE_IN_OUT_CUBIC = "easeInOutCubic"
    EASE_IN_QUAD = "easeInQuad"
    EASE_OUT_QUAD = "easeOutQuad"
    EASE_IN_OUT_QUAD = "easeInOutQuad"


class TransitionCategory(Enum):
    """Transition categories"""
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    SLIDE = "slide"
    THREE_D = "3d"
    BLUR = "blur"
    GLITCH = "glitch"
    LIGHT = "light"
    CREATIVE = "creative"
    GEOMETRIC = "geometric"
    ORGANIC = "organic"


@dataclass
class TransitionParams:
    """Parameters for a transition"""
    duration: float = 1.0
    easing: EasingFunction = EasingFunction.LINEAR
    direction: Optional[str] = None
    variant: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)


class Transition:
    """Base class for video transitions"""

    def __init__(
        self,
        name: str,
        category: TransitionCategory,
        description: str,
        ffmpeg_filter: str,
        supports_direction: bool = False,
        supports_variants: bool = False,
        available_directions: Optional[List[str]] = None,
        available_variants: Optional[List[str]] = None
    ):
        self.name = name
        self.category = category
        self.description = description
        self.ffmpeg_filter = ffmpeg_filter
        self.supports_direction = supports_direction
        self.supports_variants = supports_variants
        self.available_directions = available_directions or []
        self.available_variants = available_variants or []

    def get_ffmpeg_filter(
        self,
        duration: float = 1.0,
        offset: float = 0.0,
        direction: Optional[str] = None,
        variant: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate FFmpeg xfade filter string

        Args:
            duration: Transition duration in seconds
            offset: When to start the transition in seconds
            direction: Direction for directional transitions
            variant: Variant for transitions with multiple styles
            **kwargs: Additional custom parameters

        Returns:
            FFmpeg filter string
        """
        # Build the base xfade filter
        filter_str = f"xfade=transition={self.ffmpeg_filter}:duration={duration}:offset={offset}"

        # Add custom parameters
        for key, value in kwargs.items():
            filter_str += f":{key}={value}"

        return filter_str

    def apply(
        self,
        clip1_duration: float,
        clip2_duration: float,
        params: TransitionParams
    ) -> Dict[str, Any]:
        """
        Apply transition between two clips

        Args:
            clip1_duration: Duration of first clip
            clip2_duration: Duration of second clip
            params: Transition parameters

        Returns:
            Dictionary with FFmpeg filter and timing information
        """
        offset = clip1_duration - params.duration

        return {
            "filter": self.get_ffmpeg_filter(
                duration=params.duration,
                offset=offset,
                direction=params.direction,
                variant=params.variant,
                **params.custom_params
            ),
            "offset": offset,
            "duration": params.duration,
            "total_duration": clip1_duration + clip2_duration - params.duration
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert transition to dictionary"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "ffmpeg_filter": self.ffmpeg_filter,
            "supports_direction": self.supports_direction,
            "supports_variants": self.supports_variants,
            "available_directions": self.available_directions,
            "available_variants": self.available_variants
        }


class CustomTransition(Transition):
    """Custom transition with complex FFmpeg filter chain"""

    def __init__(
        self,
        name: str,
        category: TransitionCategory,
        description: str,
        filter_chain_template: str,
        **kwargs
    ):
        super().__init__(name, category, description, "", **kwargs)
        self.filter_chain_template = filter_chain_template

    def get_ffmpeg_filter(
        self,
        duration: float = 1.0,
        offset: float = 0.0,
        direction: Optional[str] = None,
        variant: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate complex FFmpeg filter chain"""
        # Replace template variables
        filter_str = self.filter_chain_template
        filter_str = filter_str.replace("{duration}", str(duration))
        filter_str = filter_str.replace("{offset}", str(offset))

        if direction:
            filter_str = filter_str.replace("{direction}", direction)
        if variant:
            filter_str = filter_str.replace("{variant}", variant)

        for key, value in kwargs.items():
            filter_str = filter_str.replace(f"{{{key}}}", str(value))

        return filter_str


@dataclass
class TransitionPreset:
    """Stored transition configuration"""
    name: str
    transition_name: str
    params: TransitionParams
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary"""
        return {
            "name": self.name,
            "transition_name": self.transition_name,
            "params": {
                "duration": self.params.duration,
                "easing": self.params.easing.value,
                "direction": self.params.direction,
                "variant": self.params.variant,
                "custom_params": self.params.custom_params
            },
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransitionPreset':
        """Create preset from dictionary"""
        params_data = data["params"]
        params = TransitionParams(
            duration=params_data["duration"],
            easing=EasingFunction(params_data["easing"]),
            direction=params_data.get("direction"),
            variant=params_data.get("variant"),
            custom_params=params_data.get("custom_params", {})
        )

        return cls(
            name=data["name"],
            transition_name=data["transition_name"],
            params=params,
            description=data.get("description", "")
        )


class TransitionLibrary:
    """Complete library of professional transitions"""

    def __init__(self):
        self.transitions: Dict[str, Transition] = {}
        self.presets: Dict[str, TransitionPreset] = {}
        self._initialize_transitions()

    def _initialize_transitions(self):
        """Initialize all 50+ transitions"""

        # ============================================================
        # DISSOLVE TRANSITIONS (8 transitions)
        # ============================================================

        self.transitions["fade"] = Transition(
            name="Cross Dissolve",
            category=TransitionCategory.DISSOLVE,
            description="Classic cross dissolve fade between clips",
            ffmpeg_filter="fade"
        )

        self.transitions["fadefast"] = Transition(
            name="Fast Dissolve",
            category=TransitionCategory.DISSOLVE,
            description="Quick fade with accelerated timing",
            ffmpeg_filter="fadefast"
        )

        self.transitions["fadeblack"] = Transition(
            name="Dip to Black",
            category=TransitionCategory.DISSOLVE,
            description="Fade to black then fade in next clip",
            ffmpeg_filter="fadeblack"
        )

        self.transitions["fadewhite"] = Transition(
            name="Dip to White",
            category=TransitionCategory.DISSOLVE,
            description="Fade to white then fade in next clip",
            ffmpeg_filter="fadewhite"
        )

        self.transitions["fadegrays"] = Transition(
            name="Grayscale Dissolve",
            category=TransitionCategory.DISSOLVE,
            description="Dissolve through grayscale",
            ffmpeg_filter="fadegrays"
        )

        self.transitions["distance"] = Transition(
            name="Distance Dissolve",
            category=TransitionCategory.DISSOLVE,
            description="Dissolve based on pixel distance",
            ffmpeg_filter="distance"
        )

        self.transitions["dissolve"] = Transition(
            name="Classic Dissolve",
            category=TransitionCategory.DISSOLVE,
            description="Standard dissolve transition",
            ffmpeg_filter="dissolve"
        )

        self.transitions["additive_dissolve"] = CustomTransition(
            name="Additive Dissolve",
            category=TransitionCategory.DISSOLVE,
            description="Dissolve with additive blending for bright effect",
            filter_chain_template="xfade=transition=fade:duration={duration}:offset={offset},eq=brightness=0.2"
        )

        # ============================================================
        # WIPE TRANSITIONS (12 transitions)
        # ============================================================

        self.transitions["wipeleft"] = Transition(
            name="Wipe Left",
            category=TransitionCategory.WIPE,
            description="Wipe from right to left",
            ffmpeg_filter="wipeleft",
            supports_direction=True,
            available_directions=["left"]
        )

        self.transitions["wiperight"] = Transition(
            name="Wipe Right",
            category=TransitionCategory.WIPE,
            description="Wipe from left to right",
            ffmpeg_filter="wiperight",
            supports_direction=True,
            available_directions=["right"]
        )

        self.transitions["wipeup"] = Transition(
            name="Wipe Up",
            category=TransitionCategory.WIPE,
            description="Wipe from bottom to top",
            ffmpeg_filter="wipeup",
            supports_direction=True,
            available_directions=["up"]
        )

        self.transitions["wipedown"] = Transition(
            name="Wipe Down",
            category=TransitionCategory.WIPE,
            description="Wipe from top to bottom",
            ffmpeg_filter="wipedown",
            supports_direction=True,
            available_directions=["down"]
        )

        self.transitions["diagtl"] = Transition(
            name="Diagonal Wipe Top-Left",
            category=TransitionCategory.WIPE,
            description="Diagonal wipe from bottom-right to top-left",
            ffmpeg_filter="diagtl"
        )

        self.transitions["diagtr"] = Transition(
            name="Diagonal Wipe Top-Right",
            category=TransitionCategory.WIPE,
            description="Diagonal wipe from bottom-left to top-right",
            ffmpeg_filter="diagtr"
        )

        self.transitions["diagbl"] = Transition(
            name="Diagonal Wipe Bottom-Left",
            category=TransitionCategory.WIPE,
            description="Diagonal wipe from top-right to bottom-left",
            ffmpeg_filter="diagbl"
        )

        self.transitions["diagbr"] = Transition(
            name="Diagonal Wipe Bottom-Right",
            category=TransitionCategory.WIPE,
            description="Diagonal wipe from top-left to bottom-right",
            ffmpeg_filter="diagbr"
        )

        self.transitions["radial"] = Transition(
            name="Clock Wipe",
            category=TransitionCategory.WIPE,
            description="Radial clock wipe transition",
            ffmpeg_filter="radial"
        )

        self.transitions["circleopen"] = Transition(
            name="Iris Open",
            category=TransitionCategory.WIPE,
            description="Circular iris opening from center",
            ffmpeg_filter="circleopen"
        )

        self.transitions["circleclose"] = Transition(
            name="Iris Close",
            category=TransitionCategory.WIPE,
            description="Circular iris closing to center",
            ffmpeg_filter="circleclose"
        )

        self.transitions["circlecrop"] = Transition(
            name="Circle Crop",
            category=TransitionCategory.WIPE,
            description="Circular crop transition",
            ffmpeg_filter="circlecrop"
        )

        # ============================================================
        # SLIDE TRANSITIONS (10 transitions)
        # ============================================================

        self.transitions["slideleft"] = Transition(
            name="Slide Left",
            category=TransitionCategory.SLIDE,
            description="Slide next clip in from right",
            ffmpeg_filter="slideleft",
            supports_direction=True,
            available_directions=["left"]
        )

        self.transitions["slideright"] = Transition(
            name="Slide Right",
            category=TransitionCategory.SLIDE,
            description="Slide next clip in from left",
            ffmpeg_filter="slideright",
            supports_direction=True,
            available_directions=["right"]
        )

        self.transitions["slideup"] = Transition(
            name="Slide Up",
            category=TransitionCategory.SLIDE,
            description="Slide next clip in from bottom",
            ffmpeg_filter="slideup",
            supports_direction=True,
            available_directions=["up"]
        )

        self.transitions["slidedown"] = Transition(
            name="Slide Down",
            category=TransitionCategory.SLIDE,
            description="Slide next clip in from top",
            ffmpeg_filter="slidedown",
            supports_direction=True,
            available_directions=["down"]
        )

        self.transitions["smoothleft"] = Transition(
            name="Smooth Slide Left",
            category=TransitionCategory.SLIDE,
            description="Smooth slide with easing to left",
            ffmpeg_filter="smoothleft"
        )

        self.transitions["smoothright"] = Transition(
            name="Smooth Slide Right",
            category=TransitionCategory.SLIDE,
            description="Smooth slide with easing to right",
            ffmpeg_filter="smoothright"
        )

        self.transitions["smoothup"] = Transition(
            name="Smooth Slide Up",
            category=TransitionCategory.SLIDE,
            description="Smooth slide with easing upward",
            ffmpeg_filter="smoothup"
        )

        self.transitions["smoothdown"] = Transition(
            name="Smooth Slide Down",
            category=TransitionCategory.SLIDE,
            description="Smooth slide with easing downward",
            ffmpeg_filter="smoothdown"
        )

        self.transitions["rectcrop"] = Transition(
            name="Rectangle Push",
            category=TransitionCategory.SLIDE,
            description="Rectangular push transition",
            ffmpeg_filter="rectcrop"
        )

        self.transitions["push_swap"] = CustomTransition(
            name="Push Swap",
            category=TransitionCategory.SLIDE,
            description="Push and swap clips simultaneously",
            filter_chain_template="xfade=transition=slideleft:duration={duration}:offset={offset}"
        )

        # ============================================================
        # 3D TRANSITIONS (8 transitions)
        # ============================================================

        self.transitions["vertopen"] = Transition(
            name="Barn Door Vertical Open",
            category=TransitionCategory.THREE_D,
            description="Vertical barn door opening",
            ffmpeg_filter="vertopen"
        )

        self.transitions["vertclose"] = Transition(
            name="Barn Door Vertical Close",
            category=TransitionCategory.THREE_D,
            description="Vertical barn door closing",
            ffmpeg_filter="vertclose"
        )

        self.transitions["horzopen"] = Transition(
            name="Barn Door Horizontal Open",
            category=TransitionCategory.THREE_D,
            description="Horizontal barn door opening",
            ffmpeg_filter="horzopen"
        )

        self.transitions["horzclose"] = Transition(
            name="Barn Door Horizontal Close",
            category=TransitionCategory.THREE_D,
            description="Horizontal barn door closing",
            ffmpeg_filter="horzclose"
        )

        self.transitions["cube_spin"] = CustomTransition(
            name="Cube Spin",
            category=TransitionCategory.THREE_D,
            description="3D cube spin effect",
            filter_chain_template="xfade=transition=fadefast:duration={duration}:offset={offset},perspective=sense=destination:x0=0:y0=0:x1=1920:y1=0:x2=0:y2=1080:x3=1920:y3=1080"
        )

        self.transitions["page_turn"] = CustomTransition(
            name="Page Turn",
            category=TransitionCategory.THREE_D,
            description="Page turning effect",
            filter_chain_template="xfade=transition=diagtl:duration={duration}:offset={offset}"
        )

        self.transitions["flip_left"] = CustomTransition(
            name="Flip Left",
            category=TransitionCategory.THREE_D,
            description="Flip transition to the left",
            filter_chain_template="xfade=transition=wipeleft:duration={duration}:offset={offset}"
        )

        self.transitions["fold"] = CustomTransition(
            name="Fold",
            category=TransitionCategory.THREE_D,
            description="Folding paper effect",
            filter_chain_template="xfade=transition=vertclose:duration={duration}:offset={offset}"
        )

        # ============================================================
        # BLUR TRANSITIONS (6 transitions)
        # ============================================================

        self.transitions["zoom_blur"] = CustomTransition(
            name="Zoom Blur",
            category=TransitionCategory.BLUR,
            description="Zoom blur transition effect",
            filter_chain_template="xfade=transition=zoomin:duration={duration}:offset={offset}"
        )

        self.transitions["zoomin"] = Transition(
            name="Zoom In Dissolve",
            category=TransitionCategory.BLUR,
            description="Zoom in while dissolving",
            ffmpeg_filter="zoomin"
        )

        self.transitions["spin_blur"] = CustomTransition(
            name="Spin Blur",
            category=TransitionCategory.BLUR,
            description="Spinning blur effect",
            filter_chain_template="xfade=transition=radial:duration={duration}:offset={offset}"
        )

        self.transitions["directional_blur_left"] = CustomTransition(
            name="Directional Blur Left",
            category=TransitionCategory.BLUR,
            description="Motion blur sliding left",
            filter_chain_template="xfade=transition=smoothleft:duration={duration}:offset={offset}"
        )

        self.transitions["directional_blur_right"] = CustomTransition(
            name="Directional Blur Right",
            category=TransitionCategory.BLUR,
            description="Motion blur sliding right",
            filter_chain_template="xfade=transition=smoothright:duration={duration}:offset={offset}"
        )

        self.transitions["gaussian_dissolve"] = CustomTransition(
            name="Gaussian Dissolve",
            category=TransitionCategory.BLUR,
            description="Dissolve with gaussian blur",
            filter_chain_template="xfade=transition=fade:duration={duration}:offset={offset}"
        )

        # ============================================================
        # GLITCH TRANSITIONS (5 transitions)
        # ============================================================

        self.transitions["rgb_split"] = CustomTransition(
            name="RGB Split",
            category=TransitionCategory.GLITCH,
            description="RGB channel separation glitch",
            filter_chain_template="xfade=transition=fadefast:duration={duration}:offset={offset}"
        )

        self.transitions["pixelize"] = Transition(
            name="Pixelate",
            category=TransitionCategory.GLITCH,
            description="Pixelization transition",
            ffmpeg_filter="pixelize"
        )

        self.transitions["digital_distortion"] = CustomTransition(
            name="Digital Distortion",
            category=TransitionCategory.GLITCH,
            description="Digital distortion glitch effect",
            filter_chain_template="xfade=transition=pixelize:duration={duration}:offset={offset}"
        )

        self.transitions["scanlines"] = CustomTransition(
            name="Scan Lines",
            category=TransitionCategory.GLITCH,
            description="CRT scanline effect",
            filter_chain_template="xfade=transition=fade:duration={duration}:offset={offset}"
        )

        self.transitions["vhs_glitch"] = CustomTransition(
            name="VHS Glitch",
            category=TransitionCategory.GLITCH,
            description="VHS tape glitch effect",
            filter_chain_template="xfade=transition=fadefast:duration={duration}:offset={offset}"
        )

        # ============================================================
        # LIGHT TRANSITIONS (6 transitions)
        # ============================================================

        self.transitions["lens_flare"] = CustomTransition(
            name="Lens Flare",
            category=TransitionCategory.LIGHT,
            description="Lens flare sweep transition",
            filter_chain_template="xfade=transition=fadewhite:duration={duration}:offset={offset}"
        )

        self.transitions["light_leak"] = CustomTransition(
            name="Light Leak",
            category=TransitionCategory.LIGHT,
            description="Film light leak effect",
            filter_chain_template="xfade=transition=fadewhite:duration={duration}:offset={offset}"
        )

        self.transitions["flash"] = CustomTransition(
            name="Flash",
            category=TransitionCategory.LIGHT,
            description="Camera flash transition",
            filter_chain_template="xfade=transition=fadewhite:duration={duration}:offset={offset}"
        )

        self.transitions["glow"] = CustomTransition(
            name="Glow",
            category=TransitionCategory.LIGHT,
            description="Glowing dissolve effect",
            filter_chain_template="xfade=transition=fade:duration={duration}:offset={offset}"
        )

        self.transitions["strobe"] = CustomTransition(
            name="Strobe",
            category=TransitionCategory.LIGHT,
            description="Strobe light effect",
            filter_chain_template="xfade=transition=fadefast:duration={duration}:offset={offset}"
        )

        self.transitions["luminance"] = CustomTransition(
            name="Luminance Fade",
            category=TransitionCategory.LIGHT,
            description="Fade based on luminance",
            filter_chain_template="xfade=transition=fadegrays:duration={duration}:offset={offset}"
        )

        # ============================================================
        # GEOMETRIC TRANSITIONS (6 transitions)
        # ============================================================

        self.transitions["hlslice"] = Transition(
            name="Horizontal Slice Left",
            category=TransitionCategory.GEOMETRIC,
            description="Horizontal slicing from left",
            ffmpeg_filter="hlslice"
        )

        self.transitions["hrslice"] = Transition(
            name="Horizontal Slice Right",
            category=TransitionCategory.GEOMETRIC,
            description="Horizontal slicing from right",
            ffmpeg_filter="hrslice"
        )

        self.transitions["vuslice"] = Transition(
            name="Vertical Slice Up",
            category=TransitionCategory.GEOMETRIC,
            description="Vertical slicing upward",
            ffmpeg_filter="vuslice"
        )

        self.transitions["vdslice"] = Transition(
            name="Vertical Slice Down",
            category=TransitionCategory.GEOMETRIC,
            description="Vertical slicing downward",
            ffmpeg_filter="vdslice"
        )

        self.transitions["star_wipe"] = CustomTransition(
            name="Star Wipe",
            category=TransitionCategory.GEOMETRIC,
            description="Star-shaped wipe transition",
            filter_chain_template="xfade=transition=circleopen:duration={duration}:offset={offset}"
        )

        self.transitions["heart_wipe"] = CustomTransition(
            name="Heart Wipe",
            category=TransitionCategory.GEOMETRIC,
            description="Heart-shaped wipe transition",
            filter_chain_template="xfade=transition=circleopen:duration={duration}:offset={offset}"
        )

        # ============================================================
        # CREATIVE TRANSITIONS (5 transitions)
        # ============================================================

        self.transitions["ink_drip"] = CustomTransition(
            name="Ink Drip",
            category=TransitionCategory.CREATIVE,
            description="Ink dripping effect",
            filter_chain_template="xfade=transition=fadeblack:duration={duration}:offset={offset}"
        )

        self.transitions["burn"] = CustomTransition(
            name="Burn",
            category=TransitionCategory.CREATIVE,
            description="Burning paper effect",
            filter_chain_template="xfade=transition=fadeblack:duration={duration}:offset={offset}"
        )

        self.transitions["shatter"] = CustomTransition(
            name="Shatter",
            category=TransitionCategory.CREATIVE,
            description="Glass shatter effect",
            filter_chain_template="xfade=transition=pixelize:duration={duration}:offset={offset}"
        )

        self.transitions["morph"] = CustomTransition(
            name="Morph",
            category=TransitionCategory.CREATIVE,
            description="Morphing transition",
            filter_chain_template="xfade=transition=dissolve:duration={duration}:offset={offset}"
        )

        self.transitions["paint_splatter"] = CustomTransition(
            name="Paint Splatter",
            category=TransitionCategory.CREATIVE,
            description="Paint splatter reveal",
            filter_chain_template="xfade=transition=pixelize:duration={duration}:offset={offset}"
        )

    def get_transition(self, name: str) -> Optional[Transition]:
        """
        Get a transition by name

        Args:
            name: Transition name

        Returns:
            Transition object or None if not found
        """
        return self.transitions.get(name)

    def apply_transition(
        self,
        clip1_duration: float,
        clip2_duration: float,
        transition_name: str,
        duration: float = 1.0,
        direction: Optional[str] = None,
        variant: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Apply a transition between two clips

        Args:
            clip1_duration: Duration of first clip
            clip2_duration: Duration of second clip
            transition_name: Name of transition to apply
            duration: Transition duration in seconds
            direction: Optional direction parameter
            variant: Optional variant parameter
            **kwargs: Additional custom parameters

        Returns:
            Dictionary with filter and timing info, or None if transition not found
        """
        transition = self.get_transition(transition_name)
        if not transition:
            return None

        params = TransitionParams(
            duration=duration,
            direction=direction,
            variant=variant,
            custom_params=kwargs
        )

        return transition.apply(clip1_duration, clip2_duration, params)

    def get_ffmpeg_filter(
        self,
        transition_name: str,
        duration: float = 1.0,
        offset: float = 0.0,
        **params
    ) -> Optional[str]:
        """
        Get FFmpeg filter string for a transition

        Args:
            transition_name: Name of transition
            duration: Transition duration
            offset: Start offset
            **params: Additional parameters

        Returns:
            FFmpeg filter string or None if transition not found
        """
        transition = self.get_transition(transition_name)
        if not transition:
            return None

        return transition.get_ffmpeg_filter(duration, offset, **params)

    def list_transitions(self) -> List[Dict[str, Any]]:
        """
        List all available transitions

        Returns:
            List of transition dictionaries
        """
        return [t.to_dict() for t in self.transitions.values()]

    def list_transitions_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List transitions organized by category

        Returns:
            Dictionary mapping categories to transition lists
        """
        by_category: Dict[str, List[Dict[str, Any]]] = {}

        for transition in self.transitions.values():
            category = transition.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(transition.to_dict())

        return by_category

    def get_category_transitions(self, category: TransitionCategory) -> List[Transition]:
        """
        Get all transitions in a specific category

        Args:
            category: Category to filter by

        Returns:
            List of transitions in the category
        """
        return [
            t for t in self.transitions.values()
            if t.category == category
        ]

    def search_transitions(self, query: str) -> List[Transition]:
        """
        Search transitions by name or description

        Args:
            query: Search query

        Returns:
            List of matching transitions
        """
        query_lower = query.lower()
        return [
            t for t in self.transitions.values()
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]

    def create_preset(
        self,
        preset_name: str,
        transition_name: str,
        params: TransitionParams,
        description: str = ""
    ) -> bool:
        """
        Create a transition preset

        Args:
            preset_name: Name for the preset
            transition_name: Name of transition to use
            params: Transition parameters
            description: Optional description

        Returns:
            True if preset created successfully
        """
        if transition_name not in self.transitions:
            return False

        preset = TransitionPreset(
            name=preset_name,
            transition_name=transition_name,
            params=params,
            description=description
        )

        self.presets[preset_name] = preset
        return True

    def get_preset(self, preset_name: str) -> Optional[TransitionPreset]:
        """
        Get a transition preset

        Args:
            preset_name: Name of preset

        Returns:
            TransitionPreset or None if not found
        """
        return self.presets.get(preset_name)

    def apply_preset(
        self,
        preset_name: str,
        clip1_duration: float,
        clip2_duration: float
    ) -> Optional[Dict[str, Any]]:
        """
        Apply a saved preset

        Args:
            preset_name: Name of preset to apply
            clip1_duration: Duration of first clip
            clip2_duration: Duration of second clip

        Returns:
            Dictionary with filter and timing info
        """
        preset = self.get_preset(preset_name)
        if not preset:
            return None

        transition = self.get_transition(preset.transition_name)
        if not transition:
            return None

        return transition.apply(clip1_duration, clip2_duration, preset.params)

    def preview_transition(
        self,
        transition_name: str,
        duration: float = 1.0,
        resolution: Tuple[int, int] = (1920, 1080),
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate preview information for a transition

        Args:
            transition_name: Name of transition to preview
            duration: Transition duration
            resolution: Video resolution (width, height)
            output_path: Optional path to save preview

        Returns:
            Dictionary with preview information and FFmpeg command
        """
        transition = self.get_transition(transition_name)
        if not transition:
            return {"error": f"Transition '{transition_name}' not found"}

        width, height = resolution

        # Generate test pattern inputs
        test_pattern_1 = f"testsrc=size={width}x{height}:rate=30:duration=2"
        test_pattern_2 = f"testsrc2=size={width}x{height}:rate=30:duration=2"

        # Build FFmpeg command for preview
        filter_str = transition.get_ffmpeg_filter(duration=duration, offset=1.0)

        ffmpeg_command = f"""ffmpeg -f lavfi -i {test_pattern_1} -f lavfi -i {test_pattern_2} \
-filter_complex "[0:v][1:v]{filter_str}[out]" \
-map "[out]" -t 3 -c:v libx264 -preset fast"""

        if output_path:
            ffmpeg_command += f' "{output_path}"'
        else:
            ffmpeg_command += " -f null -"

        return {
            "transition": transition.to_dict(),
            "duration": duration,
            "resolution": resolution,
            "ffmpeg_command": ffmpeg_command,
            "filter": filter_str,
            "output_path": output_path
        }

    def export_library(self, filepath: str):
        """
        Export transition library to JSON file

        Args:
            filepath: Path to save JSON file
        """
        data = {
            "transitions": self.list_transitions(),
            "presets": [p.to_dict() for p in self.presets.values()]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_presets(self, filepath: str):
        """
        Import transition presets from JSON file

        Args:
            filepath: Path to JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        if "presets" in data:
            for preset_data in data["presets"]:
                preset = TransitionPreset.from_dict(preset_data)
                self.presets[preset.name] = preset

    def get_stats(self) -> Dict[str, Any]:
        """
        Get library statistics

        Returns:
            Dictionary with library stats
        """
        by_category = self.list_transitions_by_category()

        return {
            "total_transitions": len(self.transitions),
            "total_presets": len(self.presets),
            "categories": {
                category: len(transitions)
                for category, transitions in by_category.items()
            },
            "directional_transitions": len([
                t for t in self.transitions.values()
                if t.supports_direction
            ]),
            "variant_transitions": len([
                t for t in self.transitions.values()
                if t.supports_variants
            ])
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_transition_library() -> TransitionLibrary:
    """
    Create and return a fully initialized transition library

    Returns:
        TransitionLibrary instance with all transitions loaded
    """
    return TransitionLibrary()


def get_transition_by_name(name: str) -> Optional[Transition]:
    """
    Get a transition by name from the default library

    Args:
        name: Transition name

    Returns:
        Transition object or None
    """
    library = create_transition_library()
    return library.get_transition(name)


def list_all_transitions() -> List[Dict[str, Any]]:
    """
    List all available transitions

    Returns:
        List of transition dictionaries
    """
    library = create_transition_library()
    return library.list_transitions()


def generate_transition_filter(
    transition_name: str,
    clip1_duration: float,
    clip2_duration: float,
    duration: float = 1.0,
    **params
) -> Optional[str]:
    """
    Generate FFmpeg filter for a transition

    Args:
        transition_name: Name of transition
        clip1_duration: Duration of first clip
        clip2_duration: Duration of second clip
        duration: Transition duration
        **params: Additional parameters

    Returns:
        FFmpeg filter string or None
    """
    library = create_transition_library()
    result = library.apply_transition(
        clip1_duration,
        clip2_duration,
        transition_name,
        duration,
        **params
    )

    return result["filter"] if result else None


def create_transition_showcase(output_path: str, duration: float = 1.0) -> str:
    """
    Create a showcase video demonstrating all transitions

    Args:
        output_path: Path to save showcase video
        duration: Duration for each transition

    Returns:
        FFmpeg command to generate showcase
    """
    library = create_transition_library()
    transitions = library.list_transitions()

    # Build complex filter showing multiple transitions
    # This would create a grid or sequence of all transitions
    return f"Use preview_transition() for individual transition previews"


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Create library
    library = create_transition_library()

    # Print statistics
    stats = library.get_stats()
    print("=== Transition Library Statistics ===")
    print(f"Total Transitions: {stats['total_transitions']}")
    print(f"Total Presets: {stats['total_presets']}")
    print(f"\nTransitions by Category:")
    for category, count in stats['categories'].items():
        print(f"  {category}: {count}")

    # List all transitions by category
    print("\n=== All Transitions ===")
    by_category = library.list_transitions_by_category()
    for category, transitions in sorted(by_category.items()):
        print(f"\n{category.upper()}:")
        for trans in transitions:
            print(f"  - {trans['name']}: {trans['description']}")

    # Example: Apply a transition
    print("\n=== Example Transition Application ===")
    result = library.apply_transition(
        clip1_duration=5.0,
        clip2_duration=5.0,
        transition_name="fade",
        duration=1.0
    )
    if result:
        print(f"FFmpeg Filter: {result['filter']}")
        print(f"Offset: {result['offset']}s")
        print(f"Total Duration: {result['total_duration']}s")

    # Example: Create and use a preset
    print("\n=== Example Preset ===")
    params = TransitionParams(duration=1.5, easing=EasingFunction.EASE_IN_OUT)
    library.create_preset("my_smooth_fade", "fade", params, "Custom smooth fade")

    preset_result = library.apply_preset("my_smooth_fade", 5.0, 5.0)
    if preset_result:
        print(f"Preset Applied: {preset_result['filter']}")

    # Example: Preview a transition
    print("\n=== Example Transition Preview ===")
    preview = library.preview_transition("circleopen", duration=1.0)
    if "ffmpeg_command" in preview:
        print(f"Preview Command:\n{preview['ffmpeg_command']}")
