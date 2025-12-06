"""
Motion Energy Calculator

Calculates motion energy across video frames using multiple methods:
1. Optical Flow (Farneback)
2. Frame Differencing
3. Block Matching
4. Dense Motion Fields

Motion energy is the foundation for:
- Cut timing optimization
- Attention prediction
- Beat sync alignment
- Psychological trigger placement
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MotionMethod(Enum):
    OPTICAL_FLOW = "optical_flow"
    FRAME_DIFF = "frame_diff"
    BLOCK_MATCHING = "block_matching"
    HYBRID = "hybrid"  # Combines all methods

@dataclass
class MotionFrame:
    """Motion analysis for a single frame"""
    frame_idx: int
    timestamp: float

    # Energy metrics
    total_energy: float
    mean_energy: float
    max_energy: float

    # Directional analysis
    horizontal_motion: float
    vertical_motion: float
    dominant_direction: str  # 'left', 'right', 'up', 'down', 'mixed'

    # Spatial distribution
    center_energy: float
    edge_energy: float
    energy_distribution: str  # 'centered', 'peripheral', 'uniform'

    # Classification
    motion_type: str  # 'static', 'smooth', 'fast', 'chaotic'

@dataclass
class MotionSegment:
    """A segment of consistent motion"""
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    avg_energy: float
    motion_type: str

class MotionEnergyCalculator:
    """
    Comprehensive motion energy analysis.

    Use this to:
    - Find high-energy moments for cuts
    - Identify low-energy windows for text overlays
    - Match beats to motion peaks
    - Optimize psychological trigger timing
    """

    # Thresholds for motion classification
    STATIC_THRESHOLD = 1.0
    SMOOTH_THRESHOLD = 5.0
    FAST_THRESHOLD = 15.0

    def __init__(self, method: MotionMethod = MotionMethod.OPTICAL_FLOW):
        self.method = method

    def calculate_optical_flow_energy(self, frame1: np.ndarray, frame2: np.ndarray) -> Dict:
        """Calculate motion energy using Farneback optical flow"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )

        # Calculate magnitude and angle
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        angle = np.arctan2(flow[..., 1], flow[..., 0])

        # Energy metrics
        total_energy = float(np.sum(magnitude))
        mean_energy = float(np.mean(magnitude))
        max_energy = float(np.max(magnitude))

        # Directional analysis
        horizontal = float(np.mean(np.abs(flow[..., 0])))
        vertical = float(np.mean(np.abs(flow[..., 1])))

        # Determine dominant direction
        if horizontal > vertical * 1.5:
            if np.mean(flow[..., 0]) > 0:
                direction = 'right'
            else:
                direction = 'left'
        elif vertical > horizontal * 1.5:
            if np.mean(flow[..., 1]) > 0:
                direction = 'down'
            else:
                direction = 'up'
        else:
            direction = 'mixed'

        # Spatial distribution (center vs edges)
        h, w = magnitude.shape
        center_roi = magnitude[h//4:3*h//4, w//4:3*w//4]
        center_energy = float(np.mean(center_roi))

        edge_mask = np.ones_like(magnitude, dtype=bool)
        edge_mask[h//4:3*h//4, w//4:3*w//4] = False
        edge_energy = float(np.mean(magnitude[edge_mask]))

        if center_energy > edge_energy * 1.3:
            distribution = 'centered'
        elif edge_energy > center_energy * 1.3:
            distribution = 'peripheral'
        else:
            distribution = 'uniform'

        return {
            'total_energy': total_energy,
            'mean_energy': mean_energy,
            'max_energy': max_energy,
            'horizontal_motion': horizontal,
            'vertical_motion': vertical,
            'dominant_direction': direction,
            'center_energy': center_energy,
            'edge_energy': edge_energy,
            'energy_distribution': distribution,
            'flow_field': flow,
            'magnitude': magnitude
        }

    def calculate_frame_diff_energy(self, frame1: np.ndarray, frame2: np.ndarray) -> Dict:
        """Calculate motion energy using frame differencing"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        # Absolute difference
        diff = cv2.absdiff(gray1, gray2)

        # Apply threshold to reduce noise
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # Calculate energy
        total_energy = float(np.sum(diff))
        mean_energy = float(np.mean(diff))
        max_energy = float(np.max(diff))

        # Motion pixels
        motion_pixels = np.sum(thresh > 0)
        motion_ratio = motion_pixels / (diff.shape[0] * diff.shape[1])

        return {
            'total_energy': total_energy,
            'mean_energy': mean_energy,
            'max_energy': max_energy,
            'motion_ratio': motion_ratio,
            'diff_map': diff
        }

    def classify_motion(self, mean_energy: float) -> str:
        """Classify motion type based on energy level"""
        if mean_energy < self.STATIC_THRESHOLD:
            return 'static'
        elif mean_energy < self.SMOOTH_THRESHOLD:
            return 'smooth'
        elif mean_energy < self.FAST_THRESHOLD:
            return 'fast'
        else:
            return 'chaotic'

    def analyze_frame_pair(self, frame1: np.ndarray, frame2: np.ndarray,
                            frame_idx: int, fps: float) -> MotionFrame:
        """Complete motion analysis between two frames"""
        if self.method == MotionMethod.OPTICAL_FLOW:
            analysis = self.calculate_optical_flow_energy(frame1, frame2)
        elif self.method == MotionMethod.FRAME_DIFF:
            analysis = self.calculate_frame_diff_energy(frame1, frame2)
        else:
            # Hybrid - combine both
            of_analysis = self.calculate_optical_flow_energy(frame1, frame2)
            fd_analysis = self.calculate_frame_diff_energy(frame1, frame2)

            # Merge with optical flow as primary
            analysis = of_analysis
            analysis['frame_diff_energy'] = fd_analysis['mean_energy']

        motion_type = self.classify_motion(analysis['mean_energy'])

        return MotionFrame(
            frame_idx=frame_idx,
            timestamp=frame_idx / fps,
            total_energy=analysis['total_energy'],
            mean_energy=analysis['mean_energy'],
            max_energy=analysis['max_energy'],
            horizontal_motion=analysis.get('horizontal_motion', 0),
            vertical_motion=analysis.get('vertical_motion', 0),
            dominant_direction=analysis.get('dominant_direction', 'mixed'),
            center_energy=analysis.get('center_energy', 0),
            edge_energy=analysis.get('edge_energy', 0),
            energy_distribution=analysis.get('energy_distribution', 'uniform'),
            motion_type=motion_type
        )

    def analyze_video(self, video_path: str, sample_rate: int = 1) -> Dict:
        """
        Analyze motion energy throughout a video.

        Returns comprehensive motion analysis with timeline and segments.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frames = []
        prev_frame = None
        frame_idx = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_rate == 0 and prev_frame is not None:
                motion_frame = self.analyze_frame_pair(prev_frame, frame, frame_idx, fps)
                frames.append(motion_frame)

            if frame_idx % sample_rate == 0:
                prev_frame = frame.copy()

            frame_idx += 1

        cap.release()

        # Find segments of consistent motion
        segments = self._find_motion_segments(frames)

        # Calculate statistics
        energies = [f.mean_energy for f in frames]

        return {
            'video_path': video_path,
            'total_frames': total_frames,
            'analyzed_frames': len(frames),
            'fps': fps,
            'duration': total_frames / fps,

            'energy_stats': {
                'mean': float(np.mean(energies)) if energies else 0,
                'std': float(np.std(energies)) if energies else 0,
                'min': float(np.min(energies)) if energies else 0,
                'max': float(np.max(energies)) if energies else 0,
                'median': float(np.median(energies)) if energies else 0
            },

            'motion_distribution': {
                'static': sum(1 for f in frames if f.motion_type == 'static') / len(frames) if frames else 0,
                'smooth': sum(1 for f in frames if f.motion_type == 'smooth') / len(frames) if frames else 0,
                'fast': sum(1 for f in frames if f.motion_type == 'fast') / len(frames) if frames else 0,
                'chaotic': sum(1 for f in frames if f.motion_type == 'chaotic') / len(frames) if frames else 0
            },

            'segments': [
                {
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'duration': s.end_time - s.start_time,
                    'avg_energy': s.avg_energy,
                    'motion_type': s.motion_type
                }
                for s in segments
            ],

            'timeline': [
                {
                    'frame': f.frame_idx,
                    'timestamp': f.timestamp,
                    'energy': f.mean_energy,
                    'motion_type': f.motion_type,
                    'direction': f.dominant_direction
                }
                for f in frames
            ],

            'recommendations': self._generate_recommendations(frames, segments)
        }

    def _find_motion_segments(self, frames: List[MotionFrame]) -> List[MotionSegment]:
        """Find contiguous segments of similar motion"""
        if not frames:
            return []

        segments = []
        current_type = frames[0].motion_type
        segment_start = frames[0]
        energies = [frames[0].mean_energy]

        for frame in frames[1:]:
            if frame.motion_type != current_type:
                # End current segment
                segments.append(MotionSegment(
                    start_frame=segment_start.frame_idx,
                    end_frame=frame.frame_idx,
                    start_time=segment_start.timestamp,
                    end_time=frame.timestamp,
                    avg_energy=float(np.mean(energies)),
                    motion_type=current_type
                ))

                # Start new segment
                current_type = frame.motion_type
                segment_start = frame
                energies = [frame.mean_energy]
            else:
                energies.append(frame.mean_energy)

        # Don't forget last segment
        if frames:
            segments.append(MotionSegment(
                start_frame=segment_start.frame_idx,
                end_frame=frames[-1].frame_idx,
                start_time=segment_start.timestamp,
                end_time=frames[-1].timestamp,
                avg_energy=float(np.mean(energies)),
                motion_type=current_type
            ))

        return segments

    def _generate_recommendations(self, frames: List[MotionFrame],
                                   segments: List[MotionSegment]) -> List[Dict]:
        """Generate recommendations based on motion analysis"""
        recommendations = []

        # Find best moments for text overlays (low motion)
        low_motion_segments = [s for s in segments if s.motion_type in ['static', 'smooth']]
        if low_motion_segments:
            best = max(low_motion_segments, key=lambda s: s.end_time - s.start_time)
            recommendations.append({
                'type': 'text_overlay',
                'start_time': best.start_time,
                'end_time': best.end_time,
                'reason': 'Low motion period - viewers can read text easily'
            })

        # Find best moments for cuts (high motion)
        high_motion_frames = [f for f in frames if f.motion_type in ['fast', 'chaotic']]
        if high_motion_frames:
            peak = max(high_motion_frames, key=lambda f: f.mean_energy)
            recommendations.append({
                'type': 'cut_point',
                'timestamp': peak.timestamp,
                'reason': f'Peak motion energy ({peak.mean_energy:.1f}) - natural cut point'
            })

        # Find attention peaks
        energies = [f.mean_energy for f in frames]
        if energies:
            mean_e = np.mean(energies)
            peaks = [f for f in frames if f.mean_energy > mean_e * 1.5]
            for peak in peaks[:3]:  # Top 3
                recommendations.append({
                    'type': 'attention_peak',
                    'timestamp': peak.timestamp,
                    'reason': f'High motion ({peak.mean_energy:.1f}) draws attention'
                })

        return recommendations

    def find_cut_points(self, video_path: str, num_cuts: int = 5) -> List[Dict]:
        """Find optimal cut points based on motion energy"""
        analysis = self.analyze_video(video_path, sample_rate=2)

        timeline = analysis['timeline']

        # Find local maxima of energy
        energies = [t['energy'] for t in timeline]

        from scipy.signal import find_peaks
        peaks, properties = find_peaks(energies, height=np.mean(energies), distance=10)

        cut_points = []
        for idx in peaks[:num_cuts]:
            if idx < len(timeline):
                cut_points.append({
                    'timestamp': timeline[idx]['timestamp'],
                    'frame': timeline[idx]['frame'],
                    'energy': timeline[idx]['energy'],
                    'motion_type': timeline[idx]['motion_type']
                })

        return sorted(cut_points, key=lambda c: c['timestamp'])
