# Professional Transitions Library

Complete production-ready transitions library with 66+ professional video transitions and real FFmpeg implementations.

## Overview

This library provides a comprehensive collection of professional video transitions organized into 9 categories, each with real FFmpeg filter implementations. NO mock data - every transition generates working FFmpeg code.

## Features

- **66+ Professional Transitions** across 9 categories
- **Real FFmpeg Filter Implementations** - no mock/placeholder code
- **Transition Presets** - save and reuse custom configurations
- **Category Organization** - easily find the right transition
- **Search & Filter** - find transitions by keyword or category
- **Preview Generation** - test transitions before applying
- **Custom Transition API** - create your own complex transitions
- **Export/Import** - share presets and configurations

## Installation

```python
from transitions_library import TransitionLibrary, TransitionParams, EasingFunction

# Create library instance
library = TransitionLibrary()
```

## Quick Start

### Basic Usage

```python
# Apply a simple cross dissolve
result = library.apply_transition(
    clip1_duration=5.0,
    clip2_duration=7.0,
    transition_name="fade",
    duration=1.0
)

# Get FFmpeg filter
print(result["filter"])
# Output: xfade=transition=fade:duration=1.0:offset=4.0
```

### Using with FFmpeg

```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 \
  -filter_complex "xfade=transition=fade:duration=1.0:offset=4.0" \
  -y output.mp4
```

## Transition Categories

### 1. Dissolve (8 transitions)
Classic fade and dissolve effects:
- **Cross Dissolve** - Classic cross fade
- **Fast Dissolve** - Quick fade with accelerated timing
- **Dip to Black** - Fade to black then fade in
- **Dip to White** - Fade to white then fade in
- **Grayscale Dissolve** - Dissolve through grayscale
- **Distance Dissolve** - Pixel distance-based dissolve
- **Classic Dissolve** - Standard dissolve
- **Additive Dissolve** - Bright additive blending

### 2. Wipe (12 transitions)
Directional wipe transitions:
- **Wipe Left/Right/Up/Down** - Basic directional wipes
- **Diagonal Wipes** - 4 diagonal directions
- **Clock Wipe** - Radial clock-style wipe
- **Iris Open/Close** - Circular iris effects
- **Circle Crop** - Circular crop transition

### 3. Slide (10 transitions)
Sliding and pushing effects:
- **Slide Left/Right/Up/Down** - Push clips in/out
- **Smooth Slides** - Eased sliding transitions
- **Rectangle Push** - Rectangular push effect
- **Push Swap** - Simultaneous push and swap

### 4. 3D (8 transitions)
Three-dimensional effects:
- **Barn Door** - Vertical/horizontal barn doors
- **Cube Spin** - 3D cube rotation
- **Page Turn** - Page turning effect
- **Flip Left** - Flip transition
- **Fold** - Folding paper effect

### 5. Blur (6 transitions)
Motion blur and blur effects:
- **Zoom Blur** - Zoom blur transition
- **Zoom In Dissolve** - Zoom while dissolving
- **Spin Blur** - Spinning blur effect
- **Directional Blur** - Motion blur (left/right)
- **Gaussian Dissolve** - Blur-based dissolve

### 6. Glitch (5 transitions)
Digital glitch effects:
- **RGB Split** - Color channel separation
- **Pixelate** - Pixelization effect
- **Digital Distortion** - Glitch distortion
- **Scan Lines** - CRT scanline effect
- **VHS Glitch** - Vintage VHS glitch

### 7. Light (6 transitions)
Light and luminance effects:
- **Lens Flare** - Lens flare sweep
- **Light Leak** - Film light leak
- **Flash** - Camera flash
- **Glow** - Glowing dissolve
- **Strobe** - Strobe light effect
- **Luminance Fade** - Luminance-based fade

### 8. Geometric (6 transitions)
Geometric patterns and slices:
- **Horizontal Slice** - Left/right slicing
- **Vertical Slice** - Up/down slicing
- **Star Wipe** - Star-shaped wipe
- **Heart Wipe** - Heart-shaped wipe

### 9. Creative (5 transitions)
Artistic and creative effects:
- **Ink Drip** - Ink dripping effect
- **Burn** - Burning paper
- **Shatter** - Glass shatter
- **Morph** - Morphing transition
- **Paint Splatter** - Paint splatter reveal

## API Reference

### TransitionLibrary

Main class for managing transitions.

#### Methods

##### `get_transition(name: str) -> Transition`
Get a transition by name.

```python
transition = library.get_transition("fade")
```

##### `apply_transition(...) -> dict`
Apply a transition between two clips.

```python
result = library.apply_transition(
    clip1_duration=5.0,
    clip2_duration=5.0,
    transition_name="fade",
    duration=1.0,
    direction=None,  # Optional direction
    variant=None     # Optional variant
)
```

Returns:
```python
{
    "filter": "xfade=transition=fade:duration=1.0:offset=4.0",
    "offset": 4.0,
    "duration": 1.0,
    "total_duration": 9.0
}
```

##### `get_ffmpeg_filter(...) -> str`
Get FFmpeg filter string directly.

```python
filter_str = library.get_ffmpeg_filter(
    transition_name="fade",
    duration=1.0,
    offset=4.0
)
```

##### `list_transitions() -> list`
List all available transitions.

```python
all_transitions = library.list_transitions()
```

##### `list_transitions_by_category() -> dict`
Get transitions organized by category.

```python
by_category = library.list_transitions_by_category()
for category, transitions in by_category.items():
    print(f"{category}: {len(transitions)} transitions")
```

##### `get_category_transitions(category: TransitionCategory) -> list`
Get all transitions in a specific category.

```python
from transitions_library import TransitionCategory

dissolves = library.get_category_transitions(TransitionCategory.DISSOLVE)
```

##### `search_transitions(query: str) -> list`
Search transitions by keyword.

```python
blur_transitions = library.search_transitions("blur")
slide_transitions = library.search_transitions("slide")
```

##### `create_preset(...) -> bool`
Create a transition preset.

```python
params = TransitionParams(
    duration=1.5,
    easing=EasingFunction.EASE_IN_OUT
)

library.create_preset(
    preset_name="cinematic_fade",
    transition_name="fade",
    params=params,
    description="Slow cinematic fade"
)
```

##### `apply_preset(...) -> dict`
Apply a saved preset.

```python
result = library.apply_preset(
    preset_name="cinematic_fade",
    clip1_duration=10.0,
    clip2_duration=8.0
)
```

##### `preview_transition(...) -> dict`
Generate preview information for a transition.

```python
preview = library.preview_transition(
    transition_name="circleopen",
    duration=1.0,
    resolution=(1920, 1080),
    output_path="/tmp/preview.mp4"
)

print(preview["ffmpeg_command"])
```

##### `get_stats() -> dict`
Get library statistics.

```python
stats = library.get_stats()
print(f"Total transitions: {stats['total_transitions']}")
print(f"Categories: {stats['categories']}")
```

### TransitionParams

Parameters for configuring a transition.

```python
@dataclass
class TransitionParams:
    duration: float = 1.0
    easing: EasingFunction = EasingFunction.LINEAR
    direction: Optional[str] = None
    variant: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)
```

### EasingFunction

Easing functions for smooth transitions:

```python
class EasingFunction(Enum):
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
```

## Examples

### Example 1: Basic Transition

```python
from transitions_library import TransitionLibrary

library = TransitionLibrary()

# Apply cross dissolve
result = library.apply_transition(
    clip1_duration=5.0,
    clip2_duration=7.0,
    transition_name="fade",
    duration=1.0
)

print(f"Filter: {result['filter']}")
print(f"Total duration: {result['total_duration']}s")
```

### Example 2: Multiple Transitions

```python
clips = [
    {"file": "intro.mp4", "duration": 5.0},
    {"file": "main.mp4", "duration": 10.0},
    {"file": "outro.mp4", "duration": 5.0}
]

transitions = ["fade", "slideright"]

for i, trans_name in enumerate(transitions):
    result = library.apply_transition(
        clip1_duration=clips[i]["duration"],
        clip2_duration=clips[i+1]["duration"],
        transition_name=trans_name,
        duration=1.0
    )
    print(f"Transition {i+1}: {result['filter']}")
```

### Example 3: Category Browse

```python
from transitions_library import TransitionCategory

# Get all wipe transitions
wipes = library.get_category_transitions(TransitionCategory.WIPE)

for wipe in wipes:
    print(f"{wipe.name}: {wipe.description}")
```

### Example 4: Custom Presets

```python
from transitions_library import TransitionParams, EasingFunction

# Create preset
params = TransitionParams(
    duration=2.0,
    easing=EasingFunction.EASE_IN_OUT
)

library.create_preset(
    "slow_fade",
    "fade",
    params,
    "Slow cinematic fade"
)

# Use preset
result = library.apply_preset("slow_fade", 10.0, 8.0)
```

### Example 5: Search Transitions

```python
# Search by keyword
blur_effects = library.search_transitions("blur")
print(f"Found {len(blur_effects)} blur transitions")

slide_effects = library.search_transitions("slide")
print(f"Found {len(slide_effects)} slide transitions")
```

### Example 6: Preview Generation

```python
preview = library.preview_transition(
    transition_name="circleopen",
    duration=1.0,
    output_path="/tmp/preview.mp4"
)

# Run the generated FFmpeg command
import subprocess
subprocess.run(preview["ffmpeg_command"], shell=True)
```

### Example 7: Complete Workflow

```python
# Video project with multiple clips and transitions
project = {
    "clips": [
        {"file": "intro.mp4", "duration": 5.0},
        {"file": "scene1.mp4", "duration": 10.0},
        {"file": "scene2.mp4", "duration": 8.0},
        {"file": "outro.mp4", "duration": 5.0}
    ],
    "transitions": [
        {"type": "fade", "duration": 1.0},
        {"type": "slideright", "duration": 0.8},
        {"type": "circleopen", "duration": 1.2}
    ]
}

# Calculate timing
filters = []
for i, trans_spec in enumerate(project["transitions"]):
    result = library.apply_transition(
        clip1_duration=project["clips"][i]["duration"],
        clip2_duration=project["clips"][i+1]["duration"],
        transition_name=trans_spec["type"],
        duration=trans_spec["duration"]
    )
    filters.append(result["filter"])

# Build FFmpeg command with all transitions
# [Complex filter chain construction here]
```

## FFmpeg Integration

All transitions generate real FFmpeg xfade filters that can be used directly:

```bash
# Single transition
ffmpeg -i clip1.mp4 -i clip2.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=1.0:offset=4.0[out]" \
  -map "[out]" output.mp4

# Multiple transitions (3 clips)
ffmpeg -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 \
  -filter_complex "\
    [0:v][1:v]xfade=transition=fade:duration=1.0:offset=4.0[v01];\
    [v01][2:v]xfade=transition=slideright:duration=1.0:offset=13.0[out]" \
  -map "[out]" output.mp4
```

## Performance Notes

- All transitions use FFmpeg's native xfade filter for optimal performance
- Complex transitions may require additional GPU/CPU resources
- Preview generation uses test patterns for quick rendering
- Custom transitions can combine multiple filter chains

## Transition Timing

Transitions work by overlapping the end of clip1 with the start of clip2:

```
Clip 1: [==========]
              [====] <- Transition duration
Clip 2:       [==========]

Timeline: [======]###[======]
           Clip1  Tr  Clip2
```

The offset is calculated as: `offset = clip1_duration - transition_duration`

## Best Practices

1. **Choose appropriate durations**: 0.5-2.0s for most transitions
2. **Match transition style to content**: Fast cuts for action, slow fades for drama
3. **Use presets for consistency**: Create presets for your project style
4. **Preview before rendering**: Test transitions with preview_transition()
5. **Consider performance**: Complex 3D transitions may require more processing

## Advanced Features

### Custom Transitions

Create your own complex transitions:

```python
from transitions_library import CustomTransition, TransitionCategory

custom = CustomTransition(
    name="My Custom Effect",
    category=TransitionCategory.CREATIVE,
    description="Custom multi-filter effect",
    filter_chain_template="xfade=transition=fade:duration={duration}:offset={offset},eq=brightness=0.2"
)
```

### Directional Transitions

Some transitions support direction parameters:

```python
# Wipes support direction
result = library.apply_transition(
    clip1_duration=5.0,
    clip2_duration=5.0,
    transition_name="wipeleft",
    duration=1.0,
    direction="left"
)
```

### Export/Import Presets

```python
# Export library
library.export_library("/tmp/transitions.json")

# Import presets
library.import_presets("/tmp/my_presets.json")
```

## Statistics

Run the library to see current statistics:

```python
stats = library.get_stats()
print(stats)
```

Output:
```
{
    'total_transitions': 66,
    'total_presets': 0,
    'categories': {
        'dissolve': 8,
        'wipe': 12,
        'slide': 10,
        '3d': 8,
        'blur': 6,
        'glitch': 5,
        'light': 6,
        'geometric': 6,
        'creative': 5
    },
    'directional_transitions': 8,
    'variant_transitions': 0
}
```

## Troubleshooting

### Transition not found
```python
transition = library.get_transition("invalid_name")
if not transition:
    print("Transition not found")
```

### Invalid duration
Ensure transition duration is less than the shorter clip duration.

### FFmpeg filter errors
Verify FFmpeg version supports xfade filter (FFmpeg 4.3+).

## License

This library is part of the GeminiVideo professional video editing suite.

## Support

For issues, questions, or feature requests, please refer to the main GeminiVideo documentation.
