#!/usr/bin/env python3
"""
Complete list of all transitions in the library
"""

import sys
sys.path.insert(0, '/home/user/geminivideo/services/video-agent/pro')

from transitions_library import TransitionLibrary, TransitionCategory

def main():
    library = TransitionLibrary()
    
    print("=" * 100)
    print(" " * 30 + "PROFESSIONAL TRANSITIONS LIBRARY")
    print(" " * 35 + "Complete Transition List")
    print("=" * 100)
    
    by_category = library.list_transitions_by_category()
    
    total = 0
    for category in sorted(by_category.keys()):
        transitions = by_category[category]
        
        print(f"\n{category.upper():=^100}")
        print(f"{'#':<4} {'Name':<35} {'FFmpeg Filter':<25} {'Description':<30}")
        print("-" * 100)
        
        for i, trans in enumerate(transitions, 1):
            name = trans['name'][:34]
            ffmpeg = trans['ffmpeg_filter'][:24] if trans['ffmpeg_filter'] else 'custom'
            desc = trans['description'][:29]
            print(f"{i:<4} {name:<35} {ffmpeg:<25} {desc:<30}")
            total += 1
        
        print(f"\nSubtotal: {len(transitions)} transitions")
    
    print("\n" + "=" * 100)
    print(f"TOTAL TRANSITIONS: {total}")
    print("=" * 100)
    
    # Statistics summary
    stats = library.get_stats()
    print(f"\nLibrary Statistics:")
    print(f"  - Total Transitions: {stats['total_transitions']}")
    print(f"  - Categories: {len(stats['categories'])}")
    print(f"  - Directional Transitions: {stats['directional_transitions']}")
    print(f"  - Average per Category: {stats['total_transitions'] / len(stats['categories']):.1f}")

if __name__ == "__main__":
    main()
