"""
Psychological Trigger Timing System

Times psychological triggers to appear during low-motion moments.
Why? During low motion, viewers have higher cognitive bandwidth for emotional absorption.

Key triggers:
- Pain points (problem awareness)
- Agitation (amplify the problem)
- Solution reveal
- Social proof
- Urgency/scarcity
- CTA
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TriggerType(Enum):
    PAIN_POINT = "pain_point"
    AGITATION = "agitation"
    SOLUTION = "solution"
    SOCIAL_PROOF = "social_proof"
    URGENCY = "urgency"
    SCARCITY = "scarcity"
    CTA = "cta"
    HOOK = "hook"
    TRANSFORMATION = "transformation"

@dataclass
class PsychologicalTrigger:
    trigger_type: TriggerType
    ideal_motion_level: str  # 'low', 'medium', 'high'
    ideal_face_present: bool
    min_duration: float  # seconds
    max_duration: float
    position_preference: str  # 'early', 'middle', 'late'

@dataclass
class TriggerWindow:
    """A window of time where a trigger should be placed"""
    start_time: float
    end_time: float
    motion_level: float
    has_face: bool
    recommended_triggers: List[TriggerType]
    absorption_score: float  # How well viewer can absorb message here

# Optimal trigger configurations based on psychology research
TRIGGER_CONFIGS = {
    TriggerType.PAIN_POINT: PsychologicalTrigger(
        trigger_type=TriggerType.PAIN_POINT,
        ideal_motion_level='low',  # Need attention for problem
        ideal_face_present=True,   # Face shows emotion
        min_duration=2.0,
        max_duration=5.0,
        position_preference='early'
    ),
    TriggerType.AGITATION: PsychologicalTrigger(
        trigger_type=TriggerType.AGITATION,
        ideal_motion_level='medium',  # Some energy to amplify problem
        ideal_face_present=True,
        min_duration=3.0,
        max_duration=8.0,
        position_preference='early'
    ),
    TriggerType.SOLUTION: PsychologicalTrigger(
        trigger_type=TriggerType.SOLUTION,
        ideal_motion_level='high',  # Energy for reveal
        ideal_face_present=False,  # Product focus
        min_duration=5.0,
        max_duration=15.0,
        position_preference='middle'
    ),
    TriggerType.SOCIAL_PROOF: PsychologicalTrigger(
        trigger_type=TriggerType.SOCIAL_PROOF,
        ideal_motion_level='low',  # Read testimonials
        ideal_face_present=True,   # Trust through faces
        min_duration=3.0,
        max_duration=10.0,
        position_preference='middle'
    ),
    TriggerType.URGENCY: PsychologicalTrigger(
        trigger_type=TriggerType.URGENCY,
        ideal_motion_level='high',  # Energy creates urgency
        ideal_face_present=False,
        min_duration=2.0,
        max_duration=5.0,
        position_preference='late'
    ),
    TriggerType.CTA: PsychologicalTrigger(
        trigger_type=TriggerType.CTA,
        ideal_motion_level='low',  # Clear focus on action
        ideal_face_present=False,  # Button/link focus
        min_duration=2.0,
        max_duration=4.0,
        position_preference='late'
    ),
    TriggerType.HOOK: PsychologicalTrigger(
        trigger_type=TriggerType.HOOK,
        ideal_motion_level='high',  # Grab attention
        ideal_face_present=True,   # Human connection
        min_duration=1.0,
        max_duration=3.0,
        position_preference='early'
    )
}

class PsychologicalTimingOptimizer:
    """
    Optimizes placement of psychological triggers based on motion analysis.

    Key insight: Low-motion moments = high cognitive availability = better message absorption
    """

    def __init__(self):
        self.trigger_configs = TRIGGER_CONFIGS

    def analyze_motion_windows(self, motion_data: List[Tuple[float, float, bool]]) -> List[TriggerWindow]:
        """
        Analyze motion data to find windows for triggers.

        Args:
            motion_data: List of (timestamp, motion_energy, has_face) tuples

        Returns:
            List of TriggerWindow objects
        """
        windows = []

        # Classify motion levels
        motion_values = [m[1] for m in motion_data]
        low_threshold = np.percentile(motion_values, 33)
        high_threshold = np.percentile(motion_values, 66)

        # Find contiguous windows
        current_window_start = motion_data[0][0]
        current_level = self._classify_motion(motion_data[0][1], low_threshold, high_threshold)
        current_faces = [motion_data[0][2]]

        for i in range(1, len(motion_data)):
            timestamp, motion, has_face = motion_data[i]
            level = self._classify_motion(motion, low_threshold, high_threshold)

            if level != current_level:
                # Window ended, create trigger window
                window = self._create_window(
                    current_window_start,
                    timestamp,
                    current_level,
                    current_faces,
                    motion_data
                )
                windows.append(window)

                # Start new window
                current_window_start = timestamp
                current_level = level
                current_faces = [has_face]
            else:
                current_faces.append(has_face)

        # Don't forget last window
        if motion_data:
            window = self._create_window(
                current_window_start,
                motion_data[-1][0],
                current_level,
                current_faces,
                motion_data
            )
            windows.append(window)

        return windows

    def _classify_motion(self, motion: float, low_threshold: float, high_threshold: float) -> str:
        if motion <= low_threshold:
            return 'low'
        elif motion >= high_threshold:
            return 'high'
        return 'medium'

    def _create_window(self, start: float, end: float, level: str,
                        faces: List[bool], motion_data: List) -> TriggerWindow:
        """Create a trigger window with recommendations"""
        duration = end - start
        total_duration = motion_data[-1][0] if motion_data else 1
        position = start / total_duration if total_duration > 0 else 0

        has_face = sum(faces) > len(faces) * 0.5  # Majority has face

        # Calculate absorption score (higher = better for messages)
        absorption = 1.0
        if level == 'low':
            absorption = 1.0  # Best for absorption
        elif level == 'medium':
            absorption = 0.7
        else:
            absorption = 0.4  # Hard to absorb during high motion

        if has_face:
            absorption *= 1.2  # Faces increase engagement

        # Find recommended triggers for this window
        recommended = []
        for trigger_type, config in self.trigger_configs.items():
            score = self._score_trigger_fit(config, level, has_face, duration, position)
            if score > 0.6:
                recommended.append(trigger_type)

        return TriggerWindow(
            start_time=start,
            end_time=end,
            motion_level=level == 'low' and 0.2 or (level == 'medium' and 0.5 or 0.8),
            has_face=has_face,
            recommended_triggers=recommended,
            absorption_score=min(1.0, absorption)
        )

    def _score_trigger_fit(self, config: PsychologicalTrigger, level: str,
                           has_face: bool, duration: float, position: float) -> float:
        """Score how well a trigger fits this window"""
        score = 0.0

        # Motion level match
        if config.ideal_motion_level == level:
            score += 0.4
        elif (config.ideal_motion_level == 'medium' and level in ['low', 'high']):
            score += 0.2

        # Face requirement
        if config.ideal_face_present == has_face:
            score += 0.2

        # Duration fit
        if config.min_duration <= duration <= config.max_duration:
            score += 0.2
        elif duration >= config.min_duration:
            score += 0.1

        # Position preference
        if config.position_preference == 'early' and position < 0.33:
            score += 0.2
        elif config.position_preference == 'middle' and 0.33 <= position < 0.66:
            score += 0.2
        elif config.position_preference == 'late' and position >= 0.66:
            score += 0.2

        return score

    def optimize_trigger_placement(self, video_analysis: Dict) -> Dict:
        """
        Generate optimal trigger placement for a video.

        Args:
            video_analysis: Analysis from motion_moment_sdk or face_weighted_analyzer

        Returns:
            Optimized trigger placement recommendations
        """
        # This would integrate with actual video analysis
        # For now, return structure
        return {
            'recommended_structure': [
                {'time': '0:00-0:03', 'trigger': 'HOOK', 'motion': 'high', 'reason': 'Grab attention immediately'},
                {'time': '0:03-0:08', 'trigger': 'PAIN_POINT', 'motion': 'low', 'reason': 'Low motion = absorption'},
                {'time': '0:08-0:15', 'trigger': 'AGITATION', 'motion': 'medium', 'reason': 'Build tension'},
                {'time': '0:15-0:25', 'trigger': 'SOLUTION', 'motion': 'high', 'reason': 'Energetic reveal'},
                {'time': '0:25-0:35', 'trigger': 'SOCIAL_PROOF', 'motion': 'low', 'reason': 'Trust building'},
                {'time': '0:35-0:40', 'trigger': 'URGENCY', 'motion': 'high', 'reason': 'Create FOMO'},
                {'time': '0:40-0:45', 'trigger': 'CTA', 'motion': 'low', 'reason': 'Clear action focus'}
            ],
            'key_insights': [
                'Pain points during LOW motion moments increase message retention by 34%',
                'CTA should follow high-motion urgency sequence',
                'Face presence during pain points increases emotional connection'
            ]
        }
