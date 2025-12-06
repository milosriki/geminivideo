"""
Motion Moment SDK v1.0
Temporal intelligence for video ads - analyze 30-frame windows (1 second)
to detect precise micro-moments where attention peaks.

Critical: This is what makes ads win or lose.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MotionMoment:
    """A detected moment of high motion energy"""
    frame_start: int
    frame_end: int
    timestamp_start: float
    timestamp_end: float
    motion_energy: float
    peak_frame: int
    peak_energy: float
    moment_type: str  # 'hook', 'transition', 'cta', 'emotional'
    face_present: bool
    face_weight: float  # 3.2x if face present

@dataclass
class TemporalWindow:
    """30-frame analysis window"""
    frames: List[np.ndarray]
    motion_energies: List[float]
    face_detections: List[bool]
    weighted_energy: float
    peak_index: int

class MotionMomentSDK:
    """
    Analyze video temporal dynamics for ad optimization.

    Key features:
    - 30-frame sliding window (1 second at 30fps)
    - Motion energy calculation with optical flow
    - Face weighting (3.2x priority for human faces)
    - Peak moment detection
    - Audio-visual sync points
    """

    WINDOW_SIZE = 30  # 1 second at 30fps
    FACE_WEIGHT = 3.2  # Faces get 3.2x weight

    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.window_size = int(self.WINDOW_SIZE * (fps / 30.0))

    def calculate_motion_energy(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Calculate motion energy between two frames using optical flow"""
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        # Calculate optical flow
        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )

        # Calculate magnitude
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        return float(np.mean(magnitude))

    def analyze_temporal_window(self, frames: List[np.ndarray],
                                 face_detections: List[bool]) -> TemporalWindow:
        """Analyze a 30-frame window for motion patterns"""
        motion_energies = []

        for i in range(1, len(frames)):
            energy = self.calculate_motion_energy(frames[i-1], frames[i])
            # Apply 3.2x weight if face present
            if face_detections[i]:
                energy *= self.FACE_WEIGHT
            motion_energies.append(energy)

        # Find peak
        peak_idx = int(np.argmax(motion_energies))
        weighted_avg = float(np.mean(motion_energies))

        return TemporalWindow(
            frames=frames,
            motion_energies=motion_energies,
            face_detections=face_detections,
            weighted_energy=weighted_avg,
            peak_index=peak_idx
        )

    def detect_motion_moments(self, video_path: str) -> List[MotionMoment]:
        """Detect all motion moments in a video"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        moments = []
        frames_buffer = []
        faces_buffer = []
        frame_idx = 0

        # Load face detector (placeholder - should use YOLOv8)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            has_face = len(faces) > 0

            frames_buffer.append(frame)
            faces_buffer.append(has_face)

            # When we have a full window
            if len(frames_buffer) >= self.window_size:
                window = self.analyze_temporal_window(frames_buffer, faces_buffer)

                # Detect if this is a significant moment
                if window.weighted_energy > np.mean([m.motion_energy for m in moments] or [0]) * 1.5:
                    moment = MotionMoment(
                        frame_start=frame_idx - self.window_size,
                        frame_end=frame_idx,
                        timestamp_start=(frame_idx - self.window_size) / fps,
                        timestamp_end=frame_idx / fps,
                        motion_energy=window.weighted_energy,
                        peak_frame=frame_idx - self.window_size + window.peak_index,
                        peak_energy=max(window.motion_energies),
                        moment_type=self._classify_moment(window),
                        face_present=any(faces_buffer),
                        face_weight=self.FACE_WEIGHT if any(faces_buffer) else 1.0
                    )
                    moments.append(moment)

                # Slide window by half
                frames_buffer = frames_buffer[self.window_size // 2:]
                faces_buffer = faces_buffer[self.window_size // 2:]

            frame_idx += 1

        cap.release()
        return moments

    def _classify_moment(self, window: TemporalWindow) -> str:
        """Classify what type of moment this is"""
        # First 3 seconds = hook
        if window.peak_index < 90:  # 3 sec at 30fps
            return 'hook'
        # High energy after low = transition
        elif window.motion_energies[window.peak_index] > np.mean(window.motion_energies) * 2:
            return 'transition'
        # Face with low motion = emotional
        elif any(window.face_detections) and window.weighted_energy < 5:
            return 'emotional'
        else:
            return 'action'

    def find_optimal_cut_points(self, moments: List[MotionMoment]) -> List[float]:
        """Find optimal timestamps for cuts based on motion moments"""
        cut_points = []
        for moment in moments:
            if moment.moment_type in ['transition', 'hook']:
                cut_points.append(moment.timestamp_start)
        return sorted(cut_points)

    def get_attention_curve(self, video_path: str) -> Dict[str, List[float]]:
        """Get attention prediction curve based on motion analysis"""
        moments = self.detect_motion_moments(video_path)

        # Create timeline
        cap = cv2.VideoCapture(video_path)
        duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        timeline = np.linspace(0, duration, 100)
        attention = np.zeros(100)

        for moment in moments:
            # Add attention spike at moment
            idx = int((moment.timestamp_start / duration) * 100)
            if idx < 100:
                attention[idx] = moment.motion_energy * moment.face_weight

        # Smooth the curve
        try:
            from scipy.ndimage import gaussian_filter1d
            attention = gaussian_filter1d(attention, sigma=2)
        except ImportError:
            logger.warning("scipy not available, using raw attention curve")

        return {
            'timeline': timeline.tolist(),
            'attention': attention.tolist(),
            'moments': [m.__dict__ for m in moments]
        }
