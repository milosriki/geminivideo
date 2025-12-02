#!/usr/bin/env python3
"""
Practical examples of using the Professional Transitions Library
"""

from transitions_library import (
    TransitionLibrary,
    TransitionParams,
    EasingFunction,
    TransitionCategory,
    create_transition_library
)


def example_basic_usage():
    """Example 1: Basic transition usage"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Transition Usage")
    print("=" * 70)

    library = create_transition_library()

    # Apply a simple cross dissolve
    result = library.apply_transition(
        clip1_duration=5.0,
        clip2_duration=7.0,
        transition_name="fade",
        duration=1.0
    )

    print("\nFFmpeg command to apply cross dissolve:")
    print(f"ffmpeg -i clip1.mp4 -i clip2.mp4 \\")
    print(f'  -filter_complex "{result["filter"]}" \\')
    print(f"  -y output.mp4")
    print(f"\nTiming:")
    print(f"  Clip 1 duration: 5.0s")
    print(f"  Clip 2 duration: 7.0s")
    print(f"  Transition offset: {result['offset']}s")
    print(f"  Total output: {result['total_duration']}s")


def example_multiple_transitions():
    """Example 2: Multiple transitions in sequence"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Multiple Transitions in Sequence")
    print("=" * 70)

    library = create_transition_library()

    clips = [
        {"name": "intro.mp4", "duration": 5.0},
        {"name": "main.mp4", "duration": 10.0},
        {"name": "outro.mp4", "duration": 5.0}
    ]

    transitions = ["fade", "slideright"]

    print("\nCreating 3-clip sequence with 2 transitions:")
    print("-" * 70)

    for i, trans_name in enumerate(transitions):
        result = library.apply_transition(
            clip1_duration=clips[i]["duration"],
            clip2_duration=clips[i+1]["duration"],
            transition_name=trans_name,
            duration=1.0
        )
        print(f"\nTransition {i+1}: {library.get_transition(trans_name).name}")
        print(f"  Between: {clips[i]['name']} -> {clips[i+1]['name']}")
        print(f"  Filter: {result['filter']}")


def example_category_showcase():
    """Example 3: Showcase all transitions in a category"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Showcase All Wipe Transitions")
    print("=" * 70)

    library = create_transition_library()

    wipe_transitions = library.get_category_transitions(TransitionCategory.WIPE)

    print(f"\nFound {len(wipe_transitions)} wipe transitions:")
    print("-" * 70)

    for trans in wipe_transitions[:5]:  # Show first 5
        filter_str = trans.get_ffmpeg_filter(duration=1.0, offset=4.0)
        print(f"\n{trans.name}:")
        print(f"  Description: {trans.description}")
        print(f"  Filter: {filter_str}")


def example_custom_presets():
    """Example 4: Creating and using custom presets"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Custom Presets")
    print("=" * 70)

    library = create_transition_library()

    # Create custom presets
    presets = [
        {
            "name": "quick_cut",
            "transition": "fadefast",
            "duration": 0.3,
            "description": "Fast cut for energetic videos"
        },
        {
            "name": "cinematic_fade",
            "transition": "fade",
            "duration": 2.0,
            "description": "Slow, cinematic fade"
        },
        {
            "name": "dynamic_slide",
            "transition": "smoothright",
            "duration": 0.8,
            "description": "Dynamic slide transition"
        }
    ]

    print("\nCreating custom presets:")
    print("-" * 70)

    for preset in presets:
        params = TransitionParams(
            duration=preset["duration"],
            easing=EasingFunction.EASE_IN_OUT
        )

        library.create_preset(
            preset["name"],
            preset["transition"],
            params,
            preset["description"]
        )

        print(f"\n✓ {preset['name']}")
        print(f"  Transition: {preset['transition']}")
        print(f"  Duration: {preset['duration']}s")
        print(f"  Description: {preset['description']}")

    # Use a preset
    print("\n\nUsing preset 'cinematic_fade':")
    result = library.apply_preset("cinematic_fade", 10.0, 8.0)
    if result:
        print(f"  Filter: {result['filter']}")


def example_advanced_filters():
    """Example 5: Advanced FFmpeg filter generation"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Advanced Filter Combinations")
    print("=" * 70)

    library = create_transition_library()

    # Complex transition scenarios
    scenarios = [
        {
            "name": "Glitch Effect Transition",
            "transition": "pixelize",
            "duration": 0.5,
            "description": "Fast pixelation for glitch effect"
        },
        {
            "name": "3D Cube Spin",
            "transition": "cube_spin",
            "duration": 1.5,
            "description": "3D cube rotation between clips"
        },
        {
            "name": "Light Leak Effect",
            "transition": "light_leak",
            "duration": 1.2,
            "description": "Vintage film light leak"
        }
    ]

    print("\nAdvanced transition examples:")
    print("-" * 70)

    for scenario in scenarios:
        result = library.apply_transition(
            clip1_duration=5.0,
            clip2_duration=5.0,
            transition_name=scenario["transition"],
            duration=scenario["duration"]
        )

        if result:
            print(f"\n{scenario['name']}:")
            print(f"  {scenario['description']}")
            print(f"  Filter: {result['filter']}")


def example_preview_generation():
    """Example 6: Generate transition previews"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Transition Preview Generation")
    print("=" * 70)

    library = create_transition_library()

    # Generate previews for different transitions
    transitions_to_preview = [
        ("circleopen", 1.0, "Iris open preview"),
        ("slideright", 0.8, "Slide right preview"),
        ("zoomin", 1.5, "Zoom in preview")
    ]

    print("\nGenerating transition previews:")
    print("-" * 70)

    for trans_name, duration, description in transitions_to_preview:
        preview = library.preview_transition(
            trans_name,
            duration=duration,
            output_path=f"/tmp/{trans_name}_preview.mp4"
        )

        if "ffmpeg_command" in preview:
            print(f"\n{description}:")
            print(f"  Output: {preview['output_path']}")
            print(f"  Command: {preview['ffmpeg_command'][:100]}...")


def example_search_and_filter():
    """Example 7: Search and filter transitions"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Search and Filter Transitions")
    print("=" * 70)

    library = create_transition_library()

    # Search by keyword
    search_terms = ["blur", "slide", "dissolve"]

    print("\nSearching transitions by keyword:")
    print("-" * 70)

    for term in search_terms:
        results = library.search_transitions(term)
        print(f"\n'{term}' - {len(results)} results:")
        for trans in results[:3]:
            print(f"  - {trans.name}")


def example_complete_video_workflow():
    """Example 8: Complete video editing workflow"""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Complete Video Editing Workflow")
    print("=" * 70)

    library = create_transition_library()

    # Simulate a complete video project
    video_project = {
        "clips": [
            {"file": "intro.mp4", "duration": 5.0},
            {"file": "scene1.mp4", "duration": 10.0},
            {"file": "scene2.mp4", "duration": 8.0},
            {"file": "scene3.mp4", "duration": 12.0},
            {"file": "outro.mp4", "duration": 5.0}
        ],
        "transitions": [
            {"type": "fade", "duration": 1.0},
            {"type": "slideright", "duration": 0.8},
            {"type": "circleopen", "duration": 1.2},
            {"type": "fade", "duration": 1.5}
        ]
    }

    print("\nVideo Project Structure:")
    print("-" * 70)
    print(f"Total clips: {len(video_project['clips'])}")
    print(f"Total transitions: {len(video_project['transitions'])}")

    total_duration = sum(clip["duration"] for clip in video_project["clips"])
    transition_duration = sum(t["duration"] for t in video_project["transitions"])
    final_duration = total_duration - transition_duration

    print(f"\nTiming:")
    print(f"  Raw clips total: {total_duration}s")
    print(f"  Transition overlaps: -{transition_duration}s")
    print(f"  Final video length: {final_duration}s")

    print("\n\nTransition Timeline:")
    print("-" * 70)

    current_time = 0
    for i, trans_spec in enumerate(video_project["transitions"]):
        clip1 = video_project["clips"][i]
        clip2 = video_project["clips"][i + 1]

        result = library.apply_transition(
            clip1_duration=clip1["duration"],
            clip2_duration=clip2["duration"],
            transition_name=trans_spec["type"],
            duration=trans_spec["duration"]
        )

        trans_obj = library.get_transition(trans_spec["type"])

        print(f"\n{i+1}. {clip1['file']} -> {clip2['file']}")
        print(f"   Transition: {trans_obj.name}")
        print(f"   Starts at: {current_time + result['offset']:.1f}s")
        print(f"   Duration: {result['duration']}s")
        print(f"   Filter: {result['filter']}")

        current_time += clip1["duration"] - trans_spec["duration"]


def example_export_import():
    """Example 9: Export and import library data"""
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Export/Import Library Data")
    print("=" * 70)

    library = create_transition_library()

    # Create some presets
    presets_to_create = [
        ("fast_cut", "fadefast", 0.3),
        ("smooth_dissolve", "fade", 1.5),
        ("dynamic_wipe", "wiperight", 0.8)
    ]

    for name, transition, duration in presets_to_create:
        params = TransitionParams(duration=duration)
        library.create_preset(name, transition, params)

    # Get statistics
    stats = library.get_stats()

    print("\nLibrary Statistics:")
    print("-" * 70)
    print(f"Total Transitions: {stats['total_transitions']}")
    print(f"Total Presets: {stats['total_presets']}")
    print(f"Categories: {len(stats['categories'])}")

    print("\n\nExport location: /tmp/transitions_library.json")
    print("Import presets from: /tmp/custom_presets.json")


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    example_multiple_transitions()
    example_category_showcase()
    example_custom_presets()
    example_advanced_filters()
    example_preview_generation()
    example_search_and_filter()
    example_complete_video_workflow()
    example_export_import()

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)
