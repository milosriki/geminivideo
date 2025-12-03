#!/usr/bin/env python3
"""
Practical Example: Audio Mixing for Real Video Ads

This example shows how to create audio mixes for different types of video ads:
1. Product launch ad (15 seconds)
2. Social media ad (30 seconds)
3. YouTube pre-roll ad (6 seconds)
4. Podcast sponsorship (60 seconds)
"""

from audio_mixer import (
    AudioMixer, AudioMixerConfig, AudioTrack, AudioTrackType,
    VolumeAutomation, EQBand, Compressor, NoiseReduction, DeEsser,
    AutoDucking, MasterBus, NormalizationStandard, AudioPresets
)


def create_product_launch_ad():
    """
    Example 1: Product Launch Ad (15 seconds)
    - High energy music
    - Clear voiceover
    - Impact sound effects
    - Optimized for Instagram/TikTok
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Product Launch Ad (15 seconds)")
    print("Platform: Instagram Reels, TikTok")
    print("="*70)

    config = AudioMixerConfig()
    config.sample_rate = 48000
    config.output_format = "aac"
    config.output_bitrate = "192k"

    # Track 1: Energetic background music
    music = AudioTrack(
        name="bg_music",
        file_path="assets/energetic_music.mp3",
        track_type=AudioTrackType.MUSIC,
        start_time=0.0
    )
    music.volume = -12  # Quieter than voiceover
    music.bass_boost = 6  # Extra punch
    music.eq = EQBand(
        low_gain=4,   # Boost bass
        mid_gain=-2,  # Reduce mids for voiceover clarity
        high_gain=2   # Boost highs for sparkle
    )
    music.fade_in_duration = 0.5
    music.fade_out_duration = 1.5

    # Auto-duck when voiceover plays
    music.auto_ducking = AutoDucking(
        enabled=True,
        trigger_track="voiceover",
        threshold=-35,
        ratio=5,
        attack=0.05,
        release=0.3,
        reduction=-18  # Duck music significantly
    )
    config.tracks.append(music)

    # Track 2: Voiceover (product description)
    voiceover = AudioTrack(
        name="voiceover",
        file_path="assets/product_voiceover.wav",
        track_type=AudioTrackType.VOICEOVER,
        start_time=2.0
    )
    voiceover.volume = 0  # Full volume
    voiceover.fade_in_duration = 0.1
    voiceover.fade_out_duration = 0.3

    # Voice processing
    voiceover.eq = EQBand(
        low_gain=-4,   # Cut low rumble
        mid_gain=4,    # Boost presence
        high_gain=3    # Add clarity
    )
    voiceover.compressor = Compressor(
        threshold=-18,
        ratio=4,
        attack=0.002,
        release=0.08,
        makeup_gain=6
    )
    voiceover.noise_reduction = NoiseReduction(enabled=True, amount=0.6)
    voiceover.de_esser = DeEsser(enabled=True, frequency=6500, amount=0.7)
    config.tracks.append(voiceover)

    # Track 3: Whoosh sound (intro)
    whoosh = AudioTrack(
        name="whoosh_intro",
        file_path="assets/whoosh.wav",
        track_type=AudioTrackType.SFX,
        start_time=0.2
    )
    whoosh.volume = 2
    config.tracks.append(whoosh)

    # Track 4: Impact sound (product reveal at 5s)
    impact = AudioTrack(
        name="product_reveal",
        file_path="assets/impact_heavy.wav",
        track_type=AudioTrackType.SFX,
        start_time=5.0
    )
    impact.volume = 4
    impact.bass_boost = 8  # Maximum impact
    config.tracks.append(impact)

    # Track 5: UI click (call-to-action at 13s)
    click = AudioTrack(
        name="cta_click",
        file_path="assets/ui_click.wav",
        track_type=AudioTrackType.SFX,
        start_time=13.0
    )
    click.volume = -3
    config.tracks.append(click)

    # Master bus for social media
    config.master_bus = MasterBus()
    config.master_bus.normalization = NormalizationStandard.SOCIAL_MEDIA
    config.master_bus.target_lufs = -16.0
    config.master_bus.true_peak = -1.0
    config.master_bus.limiter_enabled = True
    config.master_bus.compressor = Compressor(
        threshold=-6,
        ratio=3,
        attack=0.003,
        release=0.1,
        makeup_gain=0
    )

    # Mix
    with AudioMixer(config) as mixer:
        filter_complex, input_files = mixer.generate_filter_complex()
        print(f"\nTracks: {len(config.tracks)}")
        print(f"Target loudness: {config.master_bus.target_lufs} LUFS")
        print(f"\nTo render:")
        print(f"  mixer.mix_to_file('product_launch_ad.aac')")
        print(f"\nExpected output:")
        print(f"  - High-energy music with auto-ducking")
        print(f"  - Clear, punchy voiceover")
        print(f"  - Impactful sound effects")
        print(f"  - Optimized for social media (-16 LUFS)")

        return config


def create_social_media_ad_30s():
    """
    Example 2: Social Media Ad (30 seconds)
    - Multiple voiceover segments
    - Music with volume automation
    - Strategic sound effects
    - YouTube/Facebook optimized
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Social Media Ad (30 seconds)")
    print("Platform: YouTube, Facebook, Instagram Feed")
    print("="*70)

    config = AudioMixerConfig()

    # Track 1: Background music with volume automation
    music = AudioTrack(
        name="bg_music",
        file_path="assets/uplifting_music.mp3",
        track_type=AudioTrackType.MUSIC,
        start_time=0.0
    )

    # Create dynamic volume automation
    vol_auto = VolumeAutomation()
    vol_auto.add_keyframe(0.0, -18)    # Start quiet
    vol_auto.add_keyframe(1.5, -12)    # Ramp up during intro
    vol_auto.add_keyframe(5.0, -12)    # Hold for intro
    vol_auto.add_keyframe(6.0, -20)    # Duck for first voiceover
    vol_auto.add_keyframe(12.0, -20)   # Stay ducked
    vol_auto.add_keyframe(13.0, -10)   # Come up between segments
    vol_auto.add_keyframe(15.0, -10)   # Hold
    vol_auto.add_keyframe(16.0, -20)   # Duck for second voiceover
    vol_auto.add_keyframe(24.0, -20)   # Stay ducked
    vol_auto.add_keyframe(25.0, -8)    # Final ramp up
    vol_auto.add_keyframe(28.0, -8)    # Hold loud
    vol_auto.add_keyframe(30.0, -30)   # Fade out

    music.volume_automation = vol_auto
    music.eq = EQBand(low_gain=2, mid_gain=-1, high_gain=1)
    config.tracks.append(music)

    # Track 2: First voiceover segment (introduce problem)
    vo1 = AudioPresets.voiceover_professional()
    vo1.name = "voiceover_1"
    vo1.file_path = "assets/vo_segment_1.wav"
    vo1.start_time = 6.0
    vo1.fade_in_duration = 0.15
    vo1.fade_out_duration = 0.2
    config.tracks.append(vo1)

    # Track 3: Second voiceover segment (present solution)
    vo2 = AudioPresets.voiceover_professional()
    vo2.name = "voiceover_2"
    vo2.file_path = "assets/vo_segment_2.wav"
    vo2.start_time = 16.0
    vo2.fade_in_duration = 0.15
    vo2.fade_out_duration = 0.2
    config.tracks.append(vo2)

    # Track 4: Sound effects at key moments
    sfx_transition1 = AudioTrack(
        name="transition_1",
        file_path="assets/transition_whoosh.wav",
        track_type=AudioTrackType.SFX,
        start_time=5.5
    )
    sfx_transition1.volume = 0
    config.tracks.append(sfx_transition1)

    sfx_transition2 = AudioTrack(
        name="transition_2",
        file_path="assets/transition_whoosh.wav",
        track_type=AudioTrackType.SFX,
        start_time=15.5
    )
    sfx_transition2.volume = 0
    config.tracks.append(sfx_transition2)

    # Track 5: Impact on CTA
    cta_impact = AudioTrack(
        name="cta_impact",
        file_path="assets/impact.wav",
        track_type=AudioTrackType.SFX,
        start_time=25.0
    )
    cta_impact.volume = 3
    cta_impact.bass_boost = 5
    config.tracks.append(cta_impact)

    # Master for YouTube (-14 LUFS)
    config.master_bus = AudioPresets.master_streaming()

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print(f"\nTracks: {len(config.tracks)}")
        print(f"Voiceover segments: 2")
        print(f"Sound effects: 3")
        print(f"Target loudness: -14 LUFS (YouTube/Facebook)")
        print(f"\nVolume automation points: {len(vol_auto.keyframes)}")
        print(f"\nTo render:")
        print(f"  mixer.mix_to_file('social_media_ad_30s.aac')")

        return config


def create_youtube_preroll_6s():
    """
    Example 3: YouTube Pre-roll Ad (6 seconds)
    - Quick, punchy messaging
    - High-energy throughout
    - Optimized for skippable ads
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: YouTube Pre-roll Ad (6 seconds)")
    print("Platform: YouTube (skippable)")
    print("="*70)

    config = AudioMixerConfig()

    # Track 1: High-energy music (constant level)
    music = AudioPresets.music_energetic()
    music.file_path = "assets/fast_energetic.mp3"
    music.start_time = 0.0
    music.duration = 6.0
    music.volume = -14
    music.fade_in_duration = 0.3
    music.fade_out_duration = 0.5
    music.auto_ducking = AutoDucking(
        enabled=True,
        trigger_track="voiceover",
        threshold=-30,
        ratio=6,
        attack=0.05,
        release=0.2,
        reduction=-15
    )
    config.tracks.append(music)

    # Track 2: Fast-paced voiceover
    voiceover = AudioPresets.voiceover_professional()
    voiceover.file_path = "assets/quick_pitch.wav"
    voiceover.start_time = 0.5
    voiceover.fade_in_duration = 0.05
    voiceover.fade_out_duration = 0.1
    # Extra compression for punchy delivery
    voiceover.compressor = Compressor(
        threshold=-15,
        ratio=6,
        attack=0.001,
        release=0.05,
        makeup_gain=8
    )
    config.tracks.append(voiceover)

    # Track 3: Logo whoosh
    logo_sfx = AudioTrack(
        name="logo_reveal",
        file_path="assets/logo_whoosh.wav",
        track_type=AudioTrackType.SFX,
        start_time=4.5
    )
    logo_sfx.volume = 2
    config.tracks.append(logo_sfx)

    # Aggressive master compression for loudness
    config.master_bus = MasterBus()
    config.master_bus.normalization = NormalizationStandard.STREAMING
    config.master_bus.target_lufs = -14.0
    config.master_bus.compressor = Compressor(
        threshold=-6,
        ratio=4,
        attack=0.002,
        release=0.08,
        makeup_gain=0
    )
    config.master_bus.limiter_enabled = True

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print(f"\nTracks: {len(config.tracks)}")
        print(f"Duration: 6 seconds")
        print(f"Style: High-energy, punchy, attention-grabbing")
        print(f"Target loudness: -14 LUFS")
        print(f"\nTo render:")
        print(f"  mixer.mix_to_file('youtube_preroll_6s.aac')")

        return config


def create_podcast_sponsorship():
    """
    Example 4: Podcast Sponsorship (60 seconds)
    - Warm, conversational voiceover
    - Subtle background music
    - Optimized for podcast insertion
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Podcast Sponsorship (60 seconds)")
    print("Platform: Podcast insertion")
    print("="*70)

    config = AudioMixerConfig()

    # Track 1: Subtle background music
    music = AudioTrack(
        name="bg_music",
        file_path="assets/ambient_background.mp3",
        track_type=AudioTrackType.MUSIC,
        start_time=0.0,
        duration=60.0
    )
    music.volume = -24  # Very quiet
    music.eq = EQBand(
        low_gain=-2,   # Reduce bass to not compete with voice
        mid_gain=-3,   # Reduce mids significantly
        high_gain=-1   # Slight high reduction
    )
    music.fade_in_duration = 3.0
    music.fade_out_duration = 4.0
    music.auto_ducking = AutoDucking(
        enabled=True,
        trigger_track="voiceover",
        threshold=-35,
        ratio=3,
        attack=0.2,
        release=0.6,
        reduction=-8
    )
    config.tracks.append(music)

    # Track 2: Conversational voiceover
    voiceover = AudioTrack(
        name="voiceover",
        file_path="assets/podcast_read.wav",
        track_type=AudioTrackType.VOICEOVER,
        start_time=2.0
    )
    voiceover.volume = 0

    # Warm, natural processing
    voiceover.eq = EQBand(
        low_gain=2,    # Slight bass warmth
        mid_gain=2,    # Presence
        high_gain=1    # Natural clarity
    )
    voiceover.compressor = Compressor(
        threshold=-22,
        ratio=3,
        attack=0.005,
        release=0.15,
        makeup_gain=4
    )
    voiceover.noise_reduction = NoiseReduction(enabled=True, amount=0.5)
    voiceover.de_esser = DeEsser(enabled=True, frequency=6000, amount=0.6)
    config.tracks.append(voiceover)

    # Track 3: Subtle transition sound (mid-roll)
    transition = AudioTrack(
        name="mid_transition",
        file_path="assets/subtle_tone.wav",
        track_type=AudioTrackType.SFX,
        start_time=30.0
    )
    transition.volume = -6
    config.tracks.append(transition)

    # Master for podcast (-16 LUFS)
    config.master_bus = MasterBus()
    config.master_bus.normalization = NormalizationStandard.STREAMING
    config.master_bus.target_lufs = -16.0
    config.master_bus.true_peak = -1.0
    config.master_bus.compressor = Compressor(
        threshold=-10,
        ratio=2,
        attack=0.01,
        release=0.2,
        makeup_gain=0
    )
    config.master_bus.limiter_enabled = True

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print(f"\nTracks: {len(config.tracks)}")
        print(f"Duration: 60 seconds")
        print(f"Style: Warm, conversational, natural")
        print(f"Target loudness: -16 LUFS (podcast standard)")
        print(f"\nTo render:")
        print(f"  mixer.mix_to_file('podcast_sponsorship_60s.aac')")

        return config


def demonstrate_filter_output():
    """Show actual FFmpeg filter output for one example"""
    print("\n" + "="*70)
    print("ACTUAL FFMPEG FILTER COMPLEX OUTPUT")
    print("="*70)

    # Create simple 2-track mix
    config = AudioMixerConfig()

    voiceover = AudioPresets.voiceover_professional()
    voiceover.file_path = "vo.wav"
    config.tracks.append(voiceover)

    music = AudioPresets.music_background()
    music.file_path = "music.mp3"
    config.tracks.append(music)

    config.master_bus = AudioPresets.master_streaming()

    with AudioMixer(config) as mixer:
        filter_complex, input_files = mixer.generate_filter_complex()

        print("\nInput files:")
        for i, f in enumerate(input_files):
            print(f"  [{i}] {f}")

        print("\nFilter complex (formatted):")
        # Split by semicolon for readability
        filters = filter_complex.split(";")
        for i, f in enumerate(filters, 1):
            print(f"\n  Filter {i}:")
            print(f"    {f}")

        print("\n\nFull FFmpeg command would be:")
        print("  ffmpeg -y \\")
        for i, f in enumerate(input_files):
            print(f"    -i {f} \\")
        print(f"    -filter_complex '{filter_complex}' \\")
        print(f"    -map '[aout]' \\")
        print(f"    -c:a aac \\")
        print(f"    -b:a 192k \\")
        print(f"    -ar 48000 \\")
        print(f"    output.aac")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PRACTICAL AUDIO MIXING EXAMPLES FOR VIDEO ADS")
    print("="*70)

    # Run all examples
    create_product_launch_ad()
    create_social_media_ad_30s()
    create_youtube_preroll_6s()
    create_podcast_sponsorship()
    demonstrate_filter_output()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\nAll examples demonstrate:")
    print("  ✓ Real FFmpeg audio filters")
    print("  ✓ Platform-specific loudness targets")
    print("  ✓ Auto-ducking for voiceover clarity")
    print("  ✓ Professional audio processing")
    print("  ✓ Sound design for engagement")
    print("  ✓ NO MOCK DATA - production ready")
    print("\nReady to render professional video ad audio!")
    print("="*70 + "\n")
