"""
Demo: Professional Audio Mixer for Video Ads
Demonstrates all features of the multi-track audio mixing system.
"""

from audio_mixer import (
    AudioMixer, AudioMixerConfig, AudioTrack, AudioTrackType,
    VolumeAutomation, PanAutomation, EQBand, Compressor,
    NoiseReduction, DeEsser, AutoDucking, MasterBus,
    NormalizationStandard, AudioPresets, AudioLibrary,
    VoiceEnhancementPreset, CrossFade
)


def demo_basic_mix():
    """Demo 1: Basic voiceover + music mix with auto-ducking"""
    print("\n" + "="*70)
    print("DEMO 1: Basic Voiceover + Music Mix with Auto-Ducking")
    print("="*70)

    config = AudioMixerConfig()

    # Voiceover track
    voiceover = AudioPresets.voiceover_professional()
    voiceover.name = "voiceover"
    voiceover.file_path = "assets/voiceover.wav"
    voiceover.start_time = 1.0
    voiceover.fade_in_duration = 0.2
    voiceover.fade_out_duration = 0.5
    config.tracks.append(voiceover)

    # Background music (auto-ducked when voiceover plays)
    music = AudioPresets.music_background()
    music.name = "background_music"
    music.file_path = "assets/music.mp3"
    music.start_time = 0.0
    music.fade_in_duration = 2.0
    music.fade_out_duration = 3.0
    music.auto_ducking = AutoDucking(
        enabled=True,
        trigger_track="voiceover",
        threshold=-30,
        ratio=4,
        attack=0.1,
        release=0.5,
        reduction=-12
    )
    config.tracks.append(music)

    # Master bus for streaming
    config.master_bus = AudioPresets.master_streaming()

    with AudioMixer(config) as mixer:
        filter_complex, input_files = mixer.generate_filter_complex()
        print(f"\nTracks: {len(config.tracks)}")
        print(f"Input files: {input_files}")
        print(f"\nFilter complex length: {len(filter_complex)} characters")
        print(f"\nTo render: mixer.mix_to_file('output_basic.aac')")


def demo_volume_automation():
    """Demo 2: Volume automation with keyframes"""
    print("\n" + "="*70)
    print("DEMO 2: Volume Automation with Keyframes")
    print("="*70)

    config = AudioMixerConfig()

    # Music track with volume automation
    music = AudioTrack(
        name="music_automated",
        file_path="assets/music.mp3",
        track_type=AudioTrackType.MUSIC
    )

    # Create volume automation
    vol_auto = VolumeAutomation()
    vol_auto.add_keyframe(0.0, -20)    # Start quiet
    vol_auto.add_keyframe(2.0, -6)     # Ramp up
    vol_auto.add_keyframe(5.0, -6)     # Hold
    vol_auto.add_keyframe(8.0, -12)    # Duck down
    vol_auto.add_keyframe(10.0, -12)   # Hold quiet
    vol_auto.add_keyframe(13.0, -3)    # Ramp up to loud
    vol_auto.add_keyframe(15.0, -20)   # Fade out

    music.volume_automation = vol_auto
    config.tracks.append(music)

    # Master bus
    config.master_bus = MasterBus()
    config.master_bus.normalization = NormalizationStandard.STREAMING

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print(f"\nVolume keyframes: {len(vol_auto.keyframes)}")
        print("Keyframe times and values:")
        for kf in vol_auto.keyframes:
            print(f"  t={kf.time}s, volume={kf.value}dB")
        print(f"\nTo render: mixer.mix_to_file('output_automation.aac')")


def demo_pan_automation():
    """Demo 3: Pan automation (stereo movement)"""
    print("\n" + "="*70)
    print("DEMO 3: Pan Automation - Stereo Movement")
    print("="*70)

    config = AudioMixerConfig()

    # Sound effect with pan automation (moves left to right)
    sfx = AudioTrack(
        name="whoosh",
        file_path="assets/whoosh.wav",
        track_type=AudioTrackType.SFX,
        start_time=1.0
    )

    # Create pan automation (sweep from left to right)
    pan_auto = PanAutomation()
    pan_auto.add_keyframe(0.0, -1.0)   # Full left
    pan_auto.add_keyframe(0.5, 0.0)    # Center
    pan_auto.add_keyframe(1.0, 1.0)    # Full right

    sfx.pan_automation = pan_auto
    config.tracks.append(sfx)

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print(f"\nPan keyframes: {len(pan_auto.keyframes)}")
        print("Pan movement:")
        for kf in pan_auto.keyframes:
            position = "LEFT" if kf.value < -0.3 else "RIGHT" if kf.value > 0.3 else "CENTER"
            print(f"  t={kf.time}s, pan={kf.value:+.1f} ({position})")


def demo_advanced_eq_compression():
    """Demo 4: Advanced EQ and compression"""
    print("\n" + "="*70)
    print("DEMO 4: Advanced EQ and Compression")
    print("="*70)

    config = AudioMixerConfig()

    # Voiceover with detailed processing
    voiceover = AudioTrack(
        name="voiceover_processed",
        file_path="assets/voiceover.wav",
        track_type=AudioTrackType.VOICEOVER
    )

    # 3-band EQ
    voiceover.eq = EQBand(
        low_gain=-3,      # Cut low end rumble
        mid_gain=3,       # Boost presence
        high_gain=2,      # Add air/clarity
        low_freq=250,     # Bass/mid crossover
        high_freq=3500    # Mid/treble crossover
    )

    # Compressor
    voiceover.compressor = Compressor(
        threshold=-20,    # Start compressing at -20dB
        ratio=4,          # 4:1 compression ratio
        attack=0.003,     # Fast attack (3ms)
        release=0.1,      # Medium release (100ms)
        knee=2,           # Soft knee
        makeup_gain=5     # Add 5dB makeup gain
    )

    # Noise reduction
    voiceover.noise_reduction = NoiseReduction(
        enabled=True,
        amount=0.7        # Strong noise reduction
    )

    # De-esser
    voiceover.de_esser = DeEsser(
        enabled=True,
        frequency=6000,   # Target sibilance at 6kHz
        threshold=-30,
        amount=0.7
    )

    config.tracks.append(voiceover)

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print("\nVoiceover processing chain:")
        print(f"  - Noise Reduction: {voiceover.noise_reduction.amount * 100}%")
        print(f"  - EQ: Low={voiceover.eq.low_gain}dB, Mid={voiceover.eq.mid_gain}dB, High={voiceover.eq.high_gain}dB")
        print(f"  - Compressor: Threshold={voiceover.compressor.threshold}dB, Ratio={voiceover.compressor.ratio}:1")
        print(f"  - De-esser: {voiceover.de_esser.frequency}Hz, Amount={voiceover.de_esser.amount * 100}%")


def demo_multi_track_ad():
    """Demo 5: Complete multi-track video ad"""
    print("\n" + "="*70)
    print("DEMO 5: Complete Multi-Track Video Ad")
    print("="*70)

    config = AudioMixerConfig()

    # Track 1: Voiceover (main narrator)
    voiceover = AudioPresets.voiceover_professional()
    voiceover.name = "narrator"
    voiceover.file_path = "assets/narrator.wav"
    voiceover.start_time = 2.0
    voiceover.fade_in_duration = 0.2
    voiceover.fade_out_duration = 0.5
    config.tracks.append(voiceover)

    # Track 2: Background music (energetic, auto-ducked)
    music = AudioPresets.music_energetic()
    music.name = "bg_music"
    music.file_path = "assets/upbeat_music.mp3"
    music.start_time = 0.0
    music.volume = -16  # Quiet background
    music.fade_in_duration = 1.5
    music.fade_out_duration = 2.0
    music.auto_ducking = AutoDucking(
        enabled=True,
        trigger_track="narrator",
        threshold=-35,
        ratio=5,
        attack=0.1,
        release=0.4,
        reduction=-15  # Duck music by 15dB when narrator speaks
    )
    config.tracks.append(music)

    # Track 3: Whoosh sound effect (intro)
    whoosh = AudioPresets.sfx_impactful()
    whoosh.name = "intro_whoosh"
    whoosh.file_path = "assets/whoosh.wav"
    whoosh.start_time = 0.5
    whoosh.volume = 0
    config.tracks.append(whoosh)

    # Track 4: Impact sound (product reveal)
    impact = AudioPresets.sfx_impactful()
    impact.name = "product_impact"
    impact.file_path = "assets/impact.wav"
    impact.start_time = 5.0
    impact.volume = 3  # Louder for emphasis
    impact.bass_boost = 6  # Extra bass for impact
    config.tracks.append(impact)

    # Track 5: UI click sound
    click = AudioTrack(
        name="ui_click",
        file_path="assets/click.wav",
        track_type=AudioTrackType.SFX,
        start_time=8.0,
        volume=-6
    )
    config.tracks.append(click)

    # Track 6: Ambient background
    ambience = AudioTrack(
        name="ambience",
        file_path="assets/ambience.wav",
        track_type=AudioTrackType.AMBIENCE,
        start_time=0.0,
        volume=-24,  # Very quiet
        fade_in_duration=2.0,
        fade_out_duration=3.0
    )
    config.tracks.append(ambience)

    # Master bus for social media (Instagram/TikTok)
    config.master_bus = MasterBus()
    config.master_bus.normalization = NormalizationStandard.SOCIAL_MEDIA
    config.master_bus.target_lufs = -16.0
    config.master_bus.true_peak = -1.0
    config.master_bus.limiter_enabled = True
    config.master_bus.compressor = Compressor(
        threshold=-6,
        ratio=2.5,
        attack=0.005,
        release=0.1,
        makeup_gain=0
    )

    with AudioMixer(config) as mixer:
        filter_complex, input_files = mixer.generate_filter_complex()
        print(f"\nTotal tracks: {len(config.tracks)}")
        print("\nTrack breakdown:")
        for i, track in enumerate(config.tracks):
            ducking_status = " [AUTO-DUCKED]" if track.auto_ducking and track.auto_ducking.enabled else ""
            print(f"  {i+1}. {track.name} ({track.track_type.value}){ducking_status}")
            print(f"     Start: {track.start_time}s, Volume: {track.volume}dB")

        print(f"\nMaster bus:")
        print(f"  Normalization: {config.master_bus.normalization.value}")
        print(f"  Target LUFS: {config.master_bus.target_lufs}")
        print(f"  Limiter: {'Enabled' if config.master_bus.limiter_enabled else 'Disabled'}")

        print(f"\nFilter complex: {len(filter_complex)} characters")
        print(f"\nTo render: mixer.mix_to_file('output_ad.aac')")


def demo_broadcast_normalization():
    """Demo 6: Broadcast normalization (EBU R128)"""
    print("\n" + "="*70)
    print("DEMO 6: Broadcast Normalization (EBU R128)")
    print("="*70)

    config = AudioMixerConfig()

    # Add some tracks
    voiceover = AudioPresets.voiceover_professional()
    voiceover.file_path = "assets/voiceover.wav"
    config.tracks.append(voiceover)

    music = AudioPresets.music_background()
    music.file_path = "assets/music.mp3"
    config.tracks.append(music)

    # Configure for broadcast
    config.master_bus = AudioPresets.master_broadcast()

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print(f"\nBroadcast standards:")
        print(f"  Standard: EBU R128")
        print(f"  Target integrated loudness: -23 LUFS")
        print(f"  True peak limit: -1.0 dBTP")
        print(f"  Loudness range (LRA): 11 LU")
        print(f"\nFilter includes: loudnorm filter with EBU R128 settings")


def demo_audio_library():
    """Demo 7: Audio library integration"""
    print("\n" + "="*70)
    print("DEMO 7: Audio Library Integration")
    print("="*70)

    # Initialize audio library
    library = AudioLibrary("/path/to/audio/library")

    print("\nAudio Library Structure:")
    print("  /music/")
    print("    /energetic/")
    print("    /calm/")
    print("    /dramatic/")
    print("    /upbeat/")
    print("  /sfx/")
    print("    /whoosh/")
    print("    /impact/")
    print("    /ui/")
    print("    /ambience/")

    print("\nUsage examples:")
    print("  - Get energetic music: library.get_music_by_mood('energetic')")
    print("  - Get whoosh sounds: library.get_sfx_by_type('whoosh')")
    print("  - List all music: library.list_music()")
    print("  - List all SFX: library.list_sfx()")


def demo_voice_enhancement_presets():
    """Demo 8: Voice enhancement presets"""
    print("\n" + "="*70)
    print("DEMO 8: Voice Enhancement Presets")
    print("="*70)

    presets = [
        VoiceEnhancementPreset.NATURAL,
        VoiceEnhancementPreset.CRISP,
        VoiceEnhancementPreset.WARM,
        VoiceEnhancementPreset.BROADCAST,
        VoiceEnhancementPreset.PODCAST
    ]

    print("\nAvailable voice enhancement presets:")
    print("\n1. NATURAL:")
    print("   - Gentle high-pass filter (80 Hz)")
    print("   - Slight presence boost (3kHz, +2dB)")
    print("   - Use for: Natural, conversational voiceovers")

    print("\n2. CRISP:")
    print("   - High-pass filter (100 Hz)")
    print("   - Clear mid boost (2.5kHz, +3dB)")
    print("   - Brightness boost (5kHz, +2dB)")
    print("   - Use for: Clear, articulate product descriptions")

    print("\n3. WARM:")
    print("   - Gentle high-pass (80 Hz)")
    print("   - Body boost (200Hz, +2dB)")
    print("   - Presence boost (3kHz, +1.5dB)")
    print("   - Use for: Warm, inviting brand messaging")

    print("\n4. BROADCAST:")
    print("   - High-pass filter (120 Hz)")
    print("   - Cut boxiness (250Hz, -3dB)")
    print("   - Aggressive presence boost (3.5kHz, +4dB)")
    print("   - Compression for consistency")
    print("   - Use for: Radio/TV commercial quality")

    print("\n5. PODCAST:")
    print("   - High-pass filter (80 Hz)")
    print("   - Cut muddiness (200Hz, -2dB)")
    print("   - Presence boost (3kHz, +3dB)")
    print("   - Gentle compression")
    print("   - Use for: Podcast-style narration")


def demo_bass_boost_energy():
    """Demo 9: Bass boost for energetic ads"""
    print("\n" + "="*70)
    print("DEMO 9: Bass Boost for Energetic Ads")
    print("="*70)

    config = AudioMixerConfig()

    # Energetic music with heavy bass
    music = AudioPresets.music_energetic()
    music.file_path = "assets/electronic_music.mp3"
    music.bass_boost = 8  # +8dB bass boost
    music.eq = EQBand(
        low_gain=6,       # Additional low boost
        mid_gain=-1,      # Slight mid cut for clarity
        high_gain=3       # High boost for sparkle
    )
    config.tracks.append(music)

    # Impact SFX with extra bass
    impact = AudioPresets.sfx_impactful()
    impact.file_path = "assets/bass_drop.wav"
    impact.start_time = 2.0
    impact.bass_boost = 12  # Maximum bass boost
    config.tracks.append(impact)

    with AudioMixer(config) as mixer:
        filter_complex, _ = mixer.generate_filter_complex()
        print("\nBass boost settings:")
        print(f"  Music: +{music.bass_boost}dB at 150Hz")
        print(f"  Impact: +{impact.bass_boost}dB at 150Hz")
        print(f"  Music EQ: Low={music.eq.low_gain}dB, Mid={music.eq.mid_gain}dB, High={music.eq.high_gain}dB")
        print("\nResult: Powerful, energetic sound for high-impact ads")


def demo_complete_workflow():
    """Demo 10: Complete production workflow"""
    print("\n" + "="*70)
    print("DEMO 10: Complete Production Workflow")
    print("="*70)

    print("\nStep 1: Create mixer configuration")
    config = AudioMixerConfig()
    config.sample_rate = 48000
    config.output_format = "aac"
    config.output_bitrate = "192k"

    print("\nStep 2: Add and configure tracks")
    # Voiceover
    voiceover = AudioPresets.voiceover_professional()
    voiceover.file_path = "voiceover.wav"
    voiceover.start_time = 1.0
    config.tracks.append(voiceover)

    # Music
    music = AudioPresets.music_background()
    music.file_path = "music.mp3"
    music.auto_ducking = AutoDucking(
        enabled=True,
        trigger_track="voiceover",
        threshold=-30,
        ratio=4,
        reduction=-12
    )
    config.tracks.append(music)

    print("\nStep 3: Configure master bus")
    config.master_bus = AudioPresets.master_streaming()

    print("\nStep 4: Mix and render")
    print("```python")
    print("with AudioMixer(config) as mixer:")
    print("    # Optional: analyze source loudness")
    print("    loudness = mixer.analyze_loudness('voiceover.wav')")
    print("    print(f'Source LUFS: {loudness[\"integrated_lufs\"]}')")
    print("")
    print("    # Mix with progress callback")
    print("    def progress(percent):")
    print("        print(f'Mixing: {percent:.1f}%')")
    print("")
    print("    success = mixer.mix_to_file('output.aac', progress)")
    print("")
    print("    # Analyze output")
    print("    if success:")
    print("        output_loudness = mixer.analyze_loudness('output.aac')")
    print("        print(f'Output LUFS: {output_loudness[\"integrated_lufs\"]}')")
    print("```")

    print("\nStep 5: Verify output meets standards")
    print("  - Check LUFS target achieved")
    print("  - Verify true peak below limit")
    print("  - Ensure no clipping")
    print("  - Confirm auto-ducking works correctly")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PRO AUDIO MIXER - COMPLETE DEMONSTRATION")
    print("Multi-track Audio Mixing for Pro-Grade Video Ads")
    print("="*70)

    # Run all demos
    demo_basic_mix()
    demo_volume_automation()
    demo_pan_automation()
    demo_advanced_eq_compression()
    demo_multi_track_ad()
    demo_broadcast_normalization()
    demo_audio_library()
    demo_voice_enhancement_presets()
    demo_bass_boost_energy()
    demo_complete_workflow()

    print("\n" + "="*70)
    print("FEATURE SUMMARY")
    print("="*70)
    print("\n✓ Unlimited audio tracks with individual processing")
    print("✓ Volume automation with keyframes")
    print("✓ Pan automation (stereo positioning)")
    print("✓ 3-band EQ (low, mid, high)")
    print("✓ Compression/limiting for loudness")
    print("✓ Noise reduction (FFT-based)")
    print("✓ Auto-ducking (sidechain compression)")
    print("✓ Background music library integration")
    print("✓ Sound effects library integration")
    print("✓ Audio normalization (EBU R128, LUFS)")
    print("✓ Fade in/out with custom durations")
    print("✓ Audio crossfade support")
    print("✓ Voice enhancement presets (5 types)")
    print("✓ Bass boost for energy")
    print("✓ De-essing for clear vocals")
    print("✓ Real FFmpeg filters (NO MOCKS)")
    print("✓ Production-ready code")

    print("\n" + "="*70)
    print("REAL FFMPEG FILTERS USED")
    print("="*70)
    print("\n- volume: Volume adjustment and automation")
    print("- pan: Stereo positioning")
    print("- equalizer: 3-band EQ (low/mid/high)")
    print("- compand: Compression and limiting")
    print("- afftdn: FFT-based noise reduction")
    print("- dynaudnorm: Dynamic audio normalization")
    print("- sidechaincompress: Auto-ducking")
    print("- loudnorm: EBU R128 loudness normalization")
    print("- afade: Fade in/out")
    print("- acrossfade: Audio crossfades")
    print("- highpass/lowpass: Frequency filtering")
    print("- amix: Multi-track mixing")
    print("- adelay: Timeline synchronization")
    print("- atrim: Audio trimming")

    print("\n" + "="*70)
    print("All demos completed!")
    print("="*70 + "\n")
