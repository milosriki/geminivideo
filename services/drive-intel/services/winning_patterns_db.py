"""
Winning Ad Pattern Database

Stores patterns extracted from high-performing ads to train models
and generate new winning variations.

Data sources:
- Meta Ad Library (scraped legally)
- Google Ads transparency
- Manual winning ad uploads
- Platform API performance data

This is the KNOWLEDGE that makes the AI smart.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import os
from collections import defaultdict

logger = logging.getLogger(__name__)

class AdPlatform(Enum):
    META = "meta"
    GOOGLE = "google"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"

class AdFormat(Enum):
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"
    STORIES = "stories"
    REELS = "reels"

class AdObjective(Enum):
    CONVERSIONS = "conversions"
    TRAFFIC = "traffic"
    AWARENESS = "awareness"
    LEADS = "leads"
    SALES = "sales"
    APP_INSTALLS = "app_installs"

@dataclass
class HookPattern:
    """Pattern for the first 3 seconds"""
    hook_type: str  # face, motion, text, question, transformation
    first_element: str  # What appears first
    timing: Dict[str, float]  # Element timing
    text_used: Optional[str]
    emotion: str
    motion_level: str

@dataclass
class VisualPattern:
    """Visual patterns from winning ads"""
    color_palette: List[str]
    dominant_colors: List[str]
    composition: str  # centered, rule-of-thirds, dynamic
    face_ratio: float  # % of time faces shown
    text_overlay_style: str
    transitions: List[str]
    aspect_ratio: str

@dataclass
class AudioPattern:
    """Audio patterns from winning ads"""
    has_music: bool
    music_genre: Optional[str]
    has_voiceover: bool
    voice_gender: Optional[str]
    voice_energy: str  # calm, excited, urgent
    beat_sync: bool
    audio_hooks: List[str]

@dataclass
class CTAPattern:
    """CTA patterns from winning ads"""
    cta_type: str
    cta_text: str
    cta_timing: float  # % into video
    urgency_used: bool
    scarcity_used: bool
    button_color: str
    animation: str

@dataclass
class WinningAdPattern:
    """Complete pattern from a winning ad"""
    id: str
    source_platform: AdPlatform
    ad_format: AdFormat
    objective: AdObjective
    industry: str

    # Performance metrics
    estimated_spend: float
    estimated_impressions: int
    estimated_ctr: float
    estimated_roas: float

    # Patterns
    hook_pattern: HookPattern
    visual_pattern: VisualPattern
    audio_pattern: AudioPattern
    cta_pattern: CTAPattern

    # Metadata
    duration_seconds: float
    extracted_at: datetime
    confidence_score: float
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return asdict(self)

class WinningPatternsDB:
    """
    Database for storing and querying winning ad patterns.

    This is the BRAIN of the system - patterns learned from winners.
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "/tmp/winning_patterns"
        self.patterns: Dict[str, WinningAdPattern] = {}
        self.indexes = {
            'by_industry': defaultdict(list),
            'by_platform': defaultdict(list),
            'by_objective': defaultdict(list),
            'by_hook_type': defaultdict(list),
            'by_performance': []  # Sorted by ROAS
        }

        # Load existing patterns
        self._load_patterns()

    def add_pattern(self, pattern: WinningAdPattern) -> str:
        """Add a winning pattern to database"""
        # Generate ID if not set
        if not pattern.id:
            pattern.id = self._generate_id(pattern)

        # Store pattern
        self.patterns[pattern.id] = pattern

        # Update indexes
        self.indexes['by_industry'][pattern.industry].append(pattern.id)
        self.indexes['by_platform'][pattern.source_platform.value].append(pattern.id)
        self.indexes['by_objective'][pattern.objective.value].append(pattern.id)
        self.indexes['by_hook_type'][pattern.hook_pattern.hook_type].append(pattern.id)

        # Update performance index
        self.indexes['by_performance'].append((pattern.estimated_roas, pattern.id))
        self.indexes['by_performance'].sort(reverse=True)

        # Persist
        self._save_patterns()

        logger.info(f"Added winning pattern: {pattern.id}")
        return pattern.id

    def get_pattern(self, pattern_id: str) -> Optional[WinningAdPattern]:
        """Get a specific pattern by ID"""
        return self.patterns.get(pattern_id)

    def find_patterns(self,
                      industry: str = None,
                      platform: AdPlatform = None,
                      objective: AdObjective = None,
                      hook_type: str = None,
                      min_roas: float = None,
                      limit: int = 10) -> List[WinningAdPattern]:
        """Find patterns matching criteria"""
        # Start with all pattern IDs
        candidate_ids = set(self.patterns.keys())

        # Filter by criteria
        if industry:
            candidate_ids &= set(self.indexes['by_industry'].get(industry, []))
        if platform:
            candidate_ids &= set(self.indexes['by_platform'].get(platform.value, []))
        if objective:
            candidate_ids &= set(self.indexes['by_objective'].get(objective.value, []))
        if hook_type:
            candidate_ids &= set(self.indexes['by_hook_type'].get(hook_type, []))

        # Get patterns and filter by ROAS
        results = []
        for pid in candidate_ids:
            pattern = self.patterns[pid]
            if min_roas is None or pattern.estimated_roas >= min_roas:
                results.append(pattern)

        # Sort by ROAS descending
        results.sort(key=lambda p: p.estimated_roas, reverse=True)

        return results[:limit]

    def get_top_performers(self, limit: int = 10) -> List[WinningAdPattern]:
        """Get top performing patterns by ROAS"""
        top_ids = [pid for _, pid in self.indexes['by_performance'][:limit]]
        return [self.patterns[pid] for pid in top_ids if pid in self.patterns]

    def get_hook_statistics(self) -> Dict:
        """Get statistics about hook types and their performance"""
        stats = defaultdict(lambda: {'count': 0, 'avg_roas': 0, 'patterns': []})

        for pattern in self.patterns.values():
            hook_type = pattern.hook_pattern.hook_type
            stats[hook_type]['count'] += 1
            stats[hook_type]['patterns'].append(pattern.estimated_roas)

        # Calculate averages
        for hook_type, data in stats.items():
            if data['patterns']:
                data['avg_roas'] = sum(data['patterns']) / len(data['patterns'])
            del data['patterns']

        return dict(stats)

    def get_industry_benchmarks(self, industry: str) -> Dict:
        """Get performance benchmarks for an industry"""
        patterns = self.find_patterns(industry=industry, limit=100)

        if not patterns:
            return {'error': 'No patterns found for industry'}

        roas_values = [p.estimated_roas for p in patterns]
        ctr_values = [p.estimated_ctr for p in patterns]

        return {
            'industry': industry,
            'sample_size': len(patterns),
            'roas': {
                'avg': sum(roas_values) / len(roas_values),
                'min': min(roas_values),
                'max': max(roas_values),
                'p25': sorted(roas_values)[len(roas_values) // 4],
                'p75': sorted(roas_values)[3 * len(roas_values) // 4]
            },
            'ctr': {
                'avg': sum(ctr_values) / len(ctr_values),
                'min': min(ctr_values),
                'max': max(ctr_values)
            },
            'top_hook_types': self._get_top_hooks_for_industry(patterns),
            'common_colors': self._get_common_colors(patterns)
        }

    def extract_creative_dna(self, patterns: List[WinningAdPattern]) -> Dict:
        """Extract common DNA from a set of patterns"""
        if not patterns:
            return {}

        # Aggregate patterns
        hook_types = defaultdict(int)
        colors = defaultdict(int)
        cta_types = defaultdict(int)
        emotions = defaultdict(int)

        avg_face_ratio = 0
        avg_duration = 0

        for p in patterns:
            hook_types[p.hook_pattern.hook_type] += 1
            for color in p.visual_pattern.dominant_colors:
                colors[color] += 1
            cta_types[p.cta_pattern.cta_type] += 1
            emotions[p.hook_pattern.emotion] += 1
            avg_face_ratio += p.visual_pattern.face_ratio
            avg_duration += p.duration_seconds

        n = len(patterns)

        return {
            'dominant_hook': max(hook_types, key=hook_types.get),
            'common_colors': sorted(colors, key=colors.get, reverse=True)[:3],
            'best_cta_type': max(cta_types, key=cta_types.get),
            'dominant_emotion': max(emotions, key=emotions.get),
            'avg_face_ratio': avg_face_ratio / n,
            'avg_duration': avg_duration / n,
            'sample_size': n
        }

    def _generate_id(self, pattern: WinningAdPattern) -> str:
        """Generate unique ID for pattern"""
        data = f"{pattern.source_platform.value}_{pattern.industry}_{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    def _get_top_hooks_for_industry(self, patterns: List[WinningAdPattern]) -> List[Dict]:
        """Get top performing hooks for patterns"""
        hook_perf = defaultdict(list)
        for p in patterns:
            hook_perf[p.hook_pattern.hook_type].append(p.estimated_roas)

        results = []
        for hook_type, roas_list in hook_perf.items():
            results.append({
                'hook_type': hook_type,
                'avg_roas': sum(roas_list) / len(roas_list),
                'count': len(roas_list)
            })

        return sorted(results, key=lambda x: x['avg_roas'], reverse=True)[:3]

    def _get_common_colors(self, patterns: List[WinningAdPattern]) -> List[str]:
        """Get most common colors"""
        colors = defaultdict(int)
        for p in patterns:
            for color in p.visual_pattern.dominant_colors:
                colors[color] += 1
        return sorted(colors, key=colors.get, reverse=True)[:5]

    def _save_patterns(self):
        """Save patterns to disk"""
        os.makedirs(self.storage_path, exist_ok=True)
        filepath = os.path.join(self.storage_path, 'patterns.json')

        data = {
            pid: p.to_dict() for pid, p in self.patterns.items()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, default=str)

    def _load_patterns(self):
        """Load patterns from disk"""
        filepath = os.path.join(self.storage_path, 'patterns.json')

        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                # Would need to reconstruct dataclasses
                logger.info(f"Loaded {len(data)} patterns from disk")
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")

    def seed_with_examples(self):
        """Seed database with example winning patterns"""
        # Example patterns based on industry research
        examples = [
            WinningAdPattern(
                id="example_ecom_1",
                source_platform=AdPlatform.META,
                ad_format=AdFormat.REELS,
                objective=AdObjective.SALES,
                industry="ecommerce",
                estimated_spend=50000,
                estimated_impressions=2000000,
                estimated_ctr=0.032,
                estimated_roas=4.2,
                hook_pattern=HookPattern(
                    hook_type="transformation",
                    first_element="before_state",
                    timing={"before": 0.0, "transition": 1.5, "after": 2.0},
                    text_used="Watch this transformation",
                    emotion="surprise",
                    motion_level="high"
                ),
                visual_pattern=VisualPattern(
                    color_palette=["#FF6B6B", "#4ECDC4", "#45B7D1"],
                    dominant_colors=["red", "teal"],
                    composition="centered",
                    face_ratio=0.4,
                    text_overlay_style="bold_center",
                    transitions=["swipe", "zoom"],
                    aspect_ratio="9:16"
                ),
                audio_pattern=AudioPattern(
                    has_music=True,
                    music_genre="upbeat_pop",
                    has_voiceover=True,
                    voice_gender="female",
                    voice_energy="excited",
                    beat_sync=True,
                    audio_hooks=["beat_drop", "voice_hook"]
                ),
                cta_pattern=CTAPattern(
                    cta_type="shop_now",
                    cta_text="Shop Now - 50% Off Today",
                    cta_timing=0.85,
                    urgency_used=True,
                    scarcity_used=True,
                    button_color="#FF4444",
                    animation="pulse"
                ),
                duration_seconds=15,
                extracted_at=datetime.now(),
                confidence_score=0.92,
                tags=["transformation", "ecommerce", "high_roas"]
            )
        ]

        for pattern in examples:
            self.add_pattern(pattern)

        logger.info(f"Seeded {len(examples)} example patterns")
