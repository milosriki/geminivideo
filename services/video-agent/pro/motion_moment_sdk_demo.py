"""
Motion Moment SDK Demo
Quick reference for using the temporal intelligence SDK
"""

from motion_moment_sdk import MotionMomentSDK, MotionMoment, TemporalWindow

# Example 1: Analyze video for motion moments
def analyze_video_moments(video_path: str):
    """Detect all high-energy motion moments in a video"""
    sdk = MotionMomentSDK(fps=30.0)
    moments = sdk.detect_motion_moments(video_path)

    print(f"Found {len(moments)} motion moments:")
    for i, moment in enumerate(moments, 1):
        print(f"\n{i}. {moment.moment_type.upper()} @ {moment.timestamp_start:.2f}s")
        print(f"   Energy: {moment.motion_energy:.2f}")
        print(f"   Face: {'Yes' if moment.face_present else 'No'} (Weight: {moment.face_weight}x)")
        print(f"   Peak Frame: {moment.peak_frame}")

    return moments

# Example 2: Find optimal cut points
def find_cut_points(video_path: str):
    """Find the best places to cut for different ad lengths"""
    sdk = MotionMomentSDK(fps=30.0)
    moments = sdk.detect_motion_moments(video_path)
    cut_points = sdk.find_optimal_cut_points(moments)

    print(f"Optimal cut points: {cut_points}")
    return cut_points

# Example 3: Get attention curve
def get_attention_prediction(video_path: str):
    """Predict viewer attention over time"""
    sdk = MotionMomentSDK(fps=30.0)
    attention_data = sdk.get_attention_curve(video_path)

    print(f"Attention curve has {len(attention_data['timeline'])} data points")
    print(f"Peak attention: {max(attention_data['attention']):.2f}")
    print(f"Average attention: {sum(attention_data['attention'])/len(attention_data['attention']):.2f}")

    return attention_data

# Example 4: Real-time window analysis
def analyze_single_window(frames, face_detections):
    """Analyze a single 30-frame window"""
    sdk = MotionMomentSDK(fps=30.0)
    window = sdk.analyze_temporal_window(frames, face_detections)

    print(f"Window analysis:")
    print(f"  Weighted Energy: {window.weighted_energy:.2f}")
    print(f"  Peak Index: {window.peak_index}")
    print(f"  Faces Detected: {sum(window.face_detections)} frames")

    return window

if __name__ == "__main__":
    # Demo usage
    print("Motion Moment SDK v1.0 - Demo")
    print("=" * 50)
    print("\nKey Features:")
    print("✓ 30-frame sliding window (1 second @ 30fps)")
    print("✓ Optical flow motion energy calculation")
    print("✓ 3.2x face weighting for human attention")
    print("✓ Automatic moment classification (hook/transition/emotional/action)")
    print("✓ Optimal cut point detection")
    print("✓ Attention prediction curves")
    print("\nExample usage:")
    print("  sdk = MotionMomentSDK(fps=30.0)")
    print("  moments = sdk.detect_motion_moments('video.mp4')")
    print("  attention = sdk.get_attention_curve('video.mp4')")
    print("\nThis is what makes ads win or lose.")
