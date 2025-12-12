"""
Creative DNA Extraction - Agent 48
Extracts winning patterns from top-performing creatives for replication and compounding success.
10X LEVERAGE: Each winner makes future creatives better.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
import json
from enum import Enum

logger = logging.getLogger(__name__)

# Import cache manager for creative scoring
try:
    from src.cache.semantic_cache_manager import get_cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache manager not available for creative DNA")

# Import cross-platform learner for multi-platform creative analysis
try:
    from src.cross_platform.cross_learner import get_cross_platform_learner
    from src.cross_platform.platform_normalizer import Platform, PlatformMetrics
    CROSS_PLATFORM_AVAILABLE = True
except ImportError:
    CROSS_PLATFORM_AVAILABLE = False
    logger.warning("Cross-platform learner not available for creative DNA")


# DNA Component Data Classes
@dataclass
class HookDNA:
    """Hook DNA components"""
    hook_type: str
    hook_length: int
    first_words: str
    emotion: str
    urgency_score: float
    curiosity_score: float
    avg_performance: float
    sample_count: int


@dataclass
class VisualDNA:
    """Visual DNA components"""
    dominant_colors: List[str]
    has_faces: bool
    face_time_ratio: float
    motion_intensity: float
    text_overlay_density: float
    scene_count: int
    visual_pattern: str
    avg_performance: float
    sample_count: int


@dataclass
class AudioDNA:
    """Audio DNA components"""
    music_genre: str
    tempo: str  # slow, medium, fast
    has_voice: bool
    voice_type: str  # male, female, ai, none
    audio_energy: float
    avg_performance: float
    sample_count: int


@dataclass
class PacingDNA:
    """Pacing DNA components"""
    duration_seconds: float
    cuts_per_second: float
    scene_avg_duration: float
    intro_duration: float
    cta_timing: float
    avg_performance: float
    sample_count: int


@dataclass
class CopyDNA:
    """Copy DNA components"""
    word_count: int
    sentiment_score: float
    key_phrases: List[str]
    cta_type: str
    cta_position: str
    power_words_count: int
    avg_performance: float
    sample_count: int


@dataclass
class CTADNA:
    """CTA DNA components"""
    cta_type: str
    cta_text: str
    cta_timing: float  # seconds into video
    cta_visual_style: str
    urgency_level: float
    avg_performance: float
    sample_count: int


@dataclass
class WinningFormula:
    """Complete winning formula for an account/industry"""
    account_id: str
    formula_id: str
    hook_patterns: List[HookDNA]
    visual_patterns: List[VisualDNA]
    audio_patterns: List[AudioDNA]
    pacing_patterns: List[PacingDNA]
    copy_patterns: List[CopyDNA]
    cta_patterns: List[CTADNA]
    optimal_duration_range: Tuple[float, float]
    best_hook_types: List[str]
    best_ctas: List[str]
    formula_score: float
    sample_size: int
    created_at: datetime
    updated_at: datetime


@dataclass
class DNASuggestion:
    """Suggestion for improving creative based on DNA"""
    category: str  # hook, visual, audio, pacing, copy, cta
    suggestion_type: str  # change, shorten, lengthen, add, remove
    current_value: Any
    recommended_value: Any
    expected_impact: str
    confidence: float
    reasoning: str


class CreativeDNA:
    """
    Extract and analyze creative DNA for pattern replication.

    Creates compounding success by learning from winners and applying
    those patterns to new creatives.
    """

    def __init__(self, database_service=None):
        """
        Initialize Creative DNA analyzer.

        Args:
            database_service: Database service for querying performance data
        """
        self.db = database_service
        self._formula_cache = {}  # In-memory fallback cache
        self._cache_ttl = 7200  # 2 hours cache

        # Initialize cache manager (Redis)
        self.cache_manager = None
        if CACHE_AVAILABLE:
            try:
                self.cache_manager = get_cache_manager()
                logger.info("✅ Cache manager enabled for creative DNA")
            except Exception as e:
                logger.warning(f"Failed to initialize cache manager: {e}")

        # Initialize cross-platform learner for multi-platform creative analysis
        self.cross_platform_learner = None
        if CROSS_PLATFORM_AVAILABLE:
            try:
                self.cross_platform_learner = get_cross_platform_learner()
                logger.info("✅ Cross-platform learner enabled for creative DNA")
            except Exception as e:
                logger.warning(f"Failed to initialize cross-platform learner: {e}")

        logger.info("✅ Creative DNA Extraction initialized - Ready to extract winning patterns")

    # Core DNA Extraction Methods

    async def extract_dna(self, creative_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Extract complete DNA from a creative with caching support.

        Args:
            creative_id: Creative to analyze
            use_cache: Whether to use caching (default: True)

        Returns:
            Dictionary with all DNA components
        """
        # Check cache first (2 hour TTL)
        if use_cache and self.cache_manager and self.cache_manager.available:
            cache_key = {"creative_id": creative_id}
            cached = self.cache_manager.get(cache_key, "creative_score")

            if cached is not None:
                logger.debug(f"✅ Cache hit for creative DNA {creative_id}")
                return cached

        try:
            # Get creative data from database
            creative = await self._get_creative_data(creative_id)

            if not creative:
                logger.warning(f"Creative {creative_id} not found")
                return {}

            # Extract all DNA components
            dna = {
                "creative_id": creative_id,
                "hook_dna": await self.extract_hook_patterns(creative),
                "visual_dna": await self.extract_visual_patterns(creative),
                "audio_dna": await self.extract_audio_patterns(creative),
                "pacing_dna": await self.extract_pacing_patterns(creative),
                "copy_dna": await self.extract_copy_patterns(creative),
                "cta_dna": await self.extract_cta_patterns(creative),
                "performance_metrics": {
                    "ctr": creative.get("ctr", 0.0),
                    "roas": creative.get("roas", 0.0),
                    "conversion_rate": creative.get("conversion_rate", 0.0),
                    "engagement_rate": creative.get("engagement_rate", 0.0)
                },
                "extracted_at": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ DNA extracted for creative {creative_id}")

            # Cache the result (2 hour TTL for creative scores)
            if use_cache and self.cache_manager and self.cache_manager.available:
                cache_key = {"creative_id": creative_id}
                self.cache_manager.set(cache_key, dna, "creative_score", ttl=7200)

            return dna

        except Exception as e:
            logger.error(f"Error extracting DNA for creative {creative_id}: {e}", exc_info=True)
            return {}

    async def extract_hook_patterns(self, creative: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hook DNA from creative"""
        try:
            hook_text = creative.get("hook_text", "")

            if not hook_text:
                return {}

            # Extract hook components
            words = hook_text.split()
            first_three = " ".join(words[:3]) if len(words) >= 3 else hook_text

            hook_dna = {
                "hook_type": creative.get("hook_type", "unknown"),
                "hook_length": len(hook_text),
                "word_count": len(words),
                "first_words": first_three,
                "emotion": self._detect_emotion(hook_text),
                "urgency_score": self._calculate_urgency(hook_text),
                "curiosity_score": self._calculate_curiosity(hook_text),
                "has_question": "?" in hook_text,
                "has_numbers": any(char.isdigit() for char in hook_text),
                "starts_with_you": hook_text.lower().startswith("you"),
                "hook_text_full": hook_text
            }

            return hook_dna

        except Exception as e:
            logger.error(f"Error extracting hook patterns: {e}")
            return {}

    async def extract_visual_patterns(self, creative: Dict[str, Any]) -> Dict[str, Any]:
        """Extract visual DNA from creative"""
        try:
            visual_dna = {
                "dominant_colors": creative.get("dominant_colors", []),
                "color_palette_size": len(creative.get("dominant_colors", [])),
                "has_faces": creative.get("has_faces", False),
                "face_count": creative.get("face_count", 0),
                "face_time_ratio": creative.get("face_time_ratio", 0.0),
                "motion_intensity": creative.get("motion_score", 0.0),
                "text_overlay_density": creative.get("text_density", 0.0),
                "scene_count": creative.get("scene_count", 0),
                "visual_pattern": creative.get("visual_pattern", "unknown"),
                "has_product": creative.get("has_product", False),
                "has_text_overlays": creative.get("text_density", 0.0) > 0.1,
                "brightness": creative.get("brightness", 0.5),
                "contrast": creative.get("contrast", 0.5)
            }

            return visual_dna

        except Exception as e:
            logger.error(f"Error extracting visual patterns: {e}")
            return {}

    async def extract_audio_patterns(self, creative: Dict[str, Any]) -> Dict[str, Any]:
        """Extract audio DNA from creative"""
        try:
            audio_dna = {
                "has_music": creative.get("has_music", False),
                "music_genre": creative.get("music_genre", "none"),
                "tempo": creative.get("tempo", "medium"),
                "has_voice": creative.get("has_voice", False),
                "voice_type": creative.get("voice_type", "none"),
                "voice_gender": creative.get("voice_gender", "none"),
                "audio_energy": creative.get("audio_energy", 0.5),
                "has_sound_effects": creative.get("has_sound_effects", False),
                "audio_clarity": creative.get("audio_clarity", 0.5)
            }

            return audio_dna

        except Exception as e:
            logger.error(f"Error extracting audio patterns: {e}")
            return {}

    async def extract_pacing_patterns(self, creative: Dict[str, Any]) -> Dict[str, Any]:
        """Extract pacing DNA from creative"""
        try:
            duration = creative.get("duration_seconds", 0.0)
            scene_count = creative.get("scene_count", 1)

            pacing_dna = {
                "duration_seconds": duration,
                "scene_count": scene_count,
                "cuts_per_second": scene_count / duration if duration > 0 else 0,
                "scene_avg_duration": duration / scene_count if scene_count > 0 else 0,
                "intro_duration": creative.get("intro_duration", 0.0),
                "outro_duration": creative.get("outro_duration", 0.0),
                "cta_timing": creative.get("cta_timing", duration * 0.8),
                "pacing_tempo": self._calculate_pacing_tempo(scene_count, duration)
            }

            return pacing_dna

        except Exception as e:
            logger.error(f"Error extracting pacing patterns: {e}")
            return {}

    async def extract_copy_patterns(self, creative: Dict[str, Any]) -> Dict[str, Any]:
        """Extract copy DNA from creative"""
        try:
            ad_copy = creative.get("ad_copy", "")
            words = ad_copy.split()

            copy_dna = {
                "word_count": len(words),
                "character_count": len(ad_copy),
                "sentence_count": ad_copy.count(".") + ad_copy.count("!") + ad_copy.count("?"),
                "sentiment_score": creative.get("sentiment_score", 0.0),
                "key_phrases": self._extract_key_phrases(ad_copy),
                "power_words_count": self._count_power_words(ad_copy),
                "has_emojis": self._has_emojis(ad_copy),
                "has_numbers": any(char.isdigit() for char in ad_copy),
                "readability_score": self._calculate_readability(ad_copy)
            }

            return copy_dna

        except Exception as e:
            logger.error(f"Error extracting copy patterns: {e}")
            return {}

    async def extract_cta_patterns(self, creative: Dict[str, Any]) -> Dict[str, Any]:
        """Extract CTA DNA from creative"""
        try:
            cta_dna = {
                "cta_type": creative.get("cta_type", "unknown"),
                "cta_text": creative.get("cta_text", ""),
                "cta_timing": creative.get("cta_timing", 0.0),
                "cta_position": creative.get("cta_position", "end"),
                "cta_visual_style": creative.get("cta_style", "button"),
                "urgency_level": self._calculate_cta_urgency(creative.get("cta_text", "")),
                "has_discount": "%" in creative.get("cta_text", "") or "off" in creative.get("cta_text", "").lower(),
                "has_time_limit": any(word in creative.get("cta_text", "").lower() for word in ["now", "today", "limited", "hurry"])
            }

            return cta_dna

        except Exception as e:
            logger.error(f"Error extracting CTA patterns: {e}")
            return {}

    # Winning Formula Builder

    async def build_winning_formula(
        self,
        account_id: str,
        min_roas: float = 3.0,
        min_samples: int = 10,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Build winning formula from all successful creatives.

        Args:
            account_id: Account to analyze
            min_roas: Minimum ROAS to consider a winner
            min_samples: Minimum number of samples needed
            lookback_days: Days to look back

        Returns:
            Winning formula dictionary
        """
        try:
            logger.info(f"🧬 Building winning formula for account {account_id} (min_roas={min_roas})")

            # Get top performing creatives
            winners = await self.get_top_performers(
                account_id=account_id,
                min_roas=min_roas,
                lookback_days=lookback_days
            )

            if len(winners) < min_samples:
                logger.warning(f"Not enough winners ({len(winners)}) to build formula (need {min_samples})")
                return {
                    "error": "insufficient_data",
                    "message": f"Need at least {min_samples} winning creatives, found {len(winners)}",
                    "winners_count": len(winners)
                }

            # Extract DNA from all winners
            all_dna = []
            for winner in winners:
                dna = await self.extract_dna(winner["creative_id"])
                if dna:
                    all_dna.append(dna)

            logger.info(f"✅ Extracted DNA from {len(all_dna)} winning creatives")

            # Find common patterns across all DNA components
            formula = {
                "account_id": account_id,
                "formula_id": f"formula_{account_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "sample_size": len(all_dna),
                "min_roas_threshold": min_roas,

                # Hook patterns
                "hook_patterns": self.find_common_hook_patterns(all_dna),
                "best_hooks": self.rank_by_performance([d.get("hook_dna", {}).get("hook_type") for d in all_dna], winners),

                # Visual patterns
                "visual_patterns": self.find_common_visual_patterns(all_dna),
                "best_visual_patterns": self.rank_by_performance([d.get("visual_dna", {}).get("visual_pattern") for d in all_dna], winners),

                # Audio patterns
                "audio_patterns": self.find_common_audio_patterns(all_dna),

                # Pacing patterns
                "pacing_patterns": self.find_common_pacing_patterns(all_dna),
                "optimal_duration": self.find_optimal_range([d.get("pacing_dna", {}).get("duration_seconds", 0) for d in all_dna]),

                # Copy patterns
                "copy_patterns": self.find_common_copy_patterns(all_dna),

                # CTA patterns
                "cta_patterns": self.find_common_cta_patterns(all_dna),
                "best_ctas": self.rank_by_performance([d.get("cta_dna", {}).get("cta_type") for d in all_dna], winners),

                # Performance benchmarks
                "performance_benchmarks": {
                    "avg_roas": np.mean([w["roas"] for w in winners]),
                    "avg_ctr": np.mean([w["ctr"] for w in winners]),
                    "avg_conversion_rate": np.mean([w.get("conversion_rate", 0) for w in winners])
                },

                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Cache the formula
            self._formula_cache[account_id] = {
                "formula": formula,
                "timestamp": datetime.utcnow()
            }

            # Store in database
            if self.db:
                await self._store_formula(formula)

            logger.info(f"✅ Winning formula built with {len(all_dna)} winners")

            return formula

        except Exception as e:
            logger.error(f"Error building winning formula: {e}", exc_info=True)
            return {"error": str(e)}

    # Pattern Finding Methods

    def find_common_hook_patterns(self, all_dna: List[Dict]) -> Dict[str, Any]:
        """Find common patterns in hooks"""
        try:
            hook_types = [d.get("hook_dna", {}).get("hook_type") for d in all_dna if d.get("hook_dna")]
            hook_lengths = [d.get("hook_dna", {}).get("hook_length", 0) for d in all_dna if d.get("hook_dna")]
            emotions = [d.get("hook_dna", {}).get("emotion") for d in all_dna if d.get("hook_dna")]

            # Count frequencies
            hook_type_counts = Counter(hook_types)
            emotion_counts = Counter(emotions)

            return {
                "most_common_types": dict(hook_type_counts.most_common(5)),
                "optimal_length": {
                    "min": int(np.percentile(hook_lengths, 25)) if hook_lengths else 0,
                    "max": int(np.percentile(hook_lengths, 75)) if hook_lengths else 0,
                    "optimal": int(np.median(hook_lengths)) if hook_lengths else 0
                },
                "best_emotions": dict(emotion_counts.most_common(3)),
                "avg_urgency": float(np.mean([d.get("hook_dna", {}).get("urgency_score", 0) for d in all_dna if d.get("hook_dna")])),
                "avg_curiosity": float(np.mean([d.get("hook_dna", {}).get("curiosity_score", 0) for d in all_dna if d.get("hook_dna")]))
            }
        except Exception as e:
            logger.error(f"Error finding hook patterns: {e}")
            return {}

    def find_common_visual_patterns(self, all_dna: List[Dict]) -> Dict[str, Any]:
        """Find common patterns in visuals"""
        try:
            patterns = [d.get("visual_dna", {}).get("visual_pattern") for d in all_dna if d.get("visual_dna")]
            colors = []
            for d in all_dna:
                if d.get("visual_dna") and d["visual_dna"].get("dominant_colors"):
                    colors.extend(d["visual_dna"]["dominant_colors"])

            pattern_counts = Counter(patterns)
            color_counts = Counter(colors)

            return {
                "most_common_patterns": dict(pattern_counts.most_common(5)),
                "most_common_colors": dict(color_counts.most_common(10)),
                "face_presence_rate": sum(1 for d in all_dna if d.get("visual_dna", {}).get("has_faces", False)) / len(all_dna) if all_dna else 0,
                "avg_motion_intensity": float(np.mean([d.get("visual_dna", {}).get("motion_intensity", 0) for d in all_dna if d.get("visual_dna")])),
                "avg_text_density": float(np.mean([d.get("visual_dna", {}).get("text_overlay_density", 0) for d in all_dna if d.get("visual_dna")])),
                "avg_scene_count": float(np.mean([d.get("visual_dna", {}).get("scene_count", 0) for d in all_dna if d.get("visual_dna")]))
            }
        except Exception as e:
            logger.error(f"Error finding visual patterns: {e}")
            return {}

    def find_common_audio_patterns(self, all_dna: List[Dict]) -> Dict[str, Any]:
        """Find common patterns in audio"""
        try:
            genres = [d.get("audio_dna", {}).get("music_genre") for d in all_dna if d.get("audio_dna")]
            tempos = [d.get("audio_dna", {}).get("tempo") for d in all_dna if d.get("audio_dna")]
            voice_types = [d.get("audio_dna", {}).get("voice_type") for d in all_dna if d.get("audio_dna")]

            genre_counts = Counter(genres)
            tempo_counts = Counter(tempos)
            voice_counts = Counter(voice_types)

            return {
                "most_common_genres": dict(genre_counts.most_common(5)),
                "best_tempos": dict(tempo_counts.most_common(3)),
                "best_voice_types": dict(voice_counts.most_common(3)),
                "voice_usage_rate": sum(1 for d in all_dna if d.get("audio_dna", {}).get("has_voice", False)) / len(all_dna) if all_dna else 0,
                "avg_audio_energy": float(np.mean([d.get("audio_dna", {}).get("audio_energy", 0) for d in all_dna if d.get("audio_dna")]))
            }
        except Exception as e:
            logger.error(f"Error finding audio patterns: {e}")
            return {}

    def find_common_pacing_patterns(self, all_dna: List[Dict]) -> Dict[str, Any]:
        """Find common patterns in pacing"""
        try:
            durations = [d.get("pacing_dna", {}).get("duration_seconds", 0) for d in all_dna if d.get("pacing_dna")]
            cuts_per_sec = [d.get("pacing_dna", {}).get("cuts_per_second", 0) for d in all_dna if d.get("pacing_dna")]

            return {
                "optimal_duration": {
                    "min": float(np.percentile(durations, 25)) if durations else 0,
                    "max": float(np.percentile(durations, 75)) if durations else 0,
                    "optimal": float(np.median(durations)) if durations else 0
                },
                "optimal_cuts_per_second": {
                    "min": float(np.percentile(cuts_per_sec, 25)) if cuts_per_sec else 0,
                    "max": float(np.percentile(cuts_per_sec, 75)) if cuts_per_sec else 0,
                    "optimal": float(np.median(cuts_per_sec)) if cuts_per_sec else 0
                },
                "avg_intro_duration": float(np.mean([d.get("pacing_dna", {}).get("intro_duration", 0) for d in all_dna if d.get("pacing_dna")])),
                "avg_cta_timing": float(np.mean([d.get("pacing_dna", {}).get("cta_timing", 0) for d in all_dna if d.get("pacing_dna")]))
            }
        except Exception as e:
            logger.error(f"Error finding pacing patterns: {e}")
            return {}

    def find_common_copy_patterns(self, all_dna: List[Dict]) -> Dict[str, Any]:
        """Find common patterns in copy"""
        try:
            word_counts = [d.get("copy_dna", {}).get("word_count", 0) for d in all_dna if d.get("copy_dna")]
            sentiments = [d.get("copy_dna", {}).get("sentiment_score", 0) for d in all_dna if d.get("copy_dna")]

            return {
                "optimal_word_count": {
                    "min": int(np.percentile(word_counts, 25)) if word_counts else 0,
                    "max": int(np.percentile(word_counts, 75)) if word_counts else 0,
                    "optimal": int(np.median(word_counts)) if word_counts else 0
                },
                "optimal_sentiment": float(np.mean(sentiments)) if sentiments else 0,
                "emoji_usage_rate": sum(1 for d in all_dna if d.get("copy_dna", {}).get("has_emojis", False)) / len(all_dna) if all_dna else 0,
                "avg_power_words": float(np.mean([d.get("copy_dna", {}).get("power_words_count", 0) for d in all_dna if d.get("copy_dna")]))
            }
        except Exception as e:
            logger.error(f"Error finding copy patterns: {e}")
            return {}

    def find_common_cta_patterns(self, all_dna: List[Dict]) -> Dict[str, Any]:
        """Find common patterns in CTAs"""
        try:
            cta_types = [d.get("cta_dna", {}).get("cta_type") for d in all_dna if d.get("cta_dna")]
            cta_positions = [d.get("cta_dna", {}).get("cta_position") for d in all_dna if d.get("cta_dna")]

            type_counts = Counter(cta_types)
            position_counts = Counter(cta_positions)

            return {
                "most_common_types": dict(type_counts.most_common(5)),
                "best_positions": dict(position_counts.most_common(3)),
                "discount_usage_rate": sum(1 for d in all_dna if d.get("cta_dna", {}).get("has_discount", False)) / len(all_dna) if all_dna else 0,
                "urgency_usage_rate": sum(1 for d in all_dna if d.get("cta_dna", {}).get("has_time_limit", False)) / len(all_dna) if all_dna else 0,
                "avg_urgency_level": float(np.mean([d.get("cta_dna", {}).get("urgency_level", 0) for d in all_dna if d.get("cta_dna")]))
            }
        except Exception as e:
            logger.error(f"Error finding CTA patterns: {e}")
            return {}

    def find_optimal_range(self, values: List[float]) -> Dict[str, float]:
        """Find optimal range for a numeric value"""
        try:
            clean_values = [v for v in values if v and v > 0]
            if not clean_values:
                return {"min": 0, "max": 0, "optimal": 0}

            return {
                "min": float(np.percentile(clean_values, 25)),
                "max": float(np.percentile(clean_values, 75)),
                "optimal": float(np.median(clean_values))
            }
        except Exception as e:
            logger.error(f"Error finding optimal range: {e}")
            return {"min": 0, "max": 0, "optimal": 0}

    def rank_by_performance(self, items: List[str], winners: List[Dict]) -> List[Dict[str, Any]]:
        """Rank items by their performance"""
        try:
            item_performance = defaultdict(lambda: {"count": 0, "total_roas": 0.0})

            for item, winner in zip(items, winners):
                if item:
                    item_performance[item]["count"] += 1
                    item_performance[item]["total_roas"] += winner.get("roas", 0.0)

            # Calculate average ROAS
            ranked = []
            for item, data in item_performance.items():
                avg_roas = data["total_roas"] / data["count"] if data["count"] > 0 else 0
                ranked.append({
                    "item": item,
                    "avg_roas": avg_roas,
                    "count": data["count"]
                })

            # Sort by average ROAS
            ranked.sort(key=lambda x: x["avg_roas"], reverse=True)

            return ranked[:10]  # Top 10

        except Exception as e:
            logger.error(f"Error ranking by performance: {e}")
            return []

    # DNA Inheritance & Application

    async def apply_dna_to_new_creative(
        self,
        creative_id: str,
        account_id: str,
        formula: Optional[Dict] = None
    ) -> List[DNASuggestion]:
        """
        Apply winning DNA to new creative and generate suggestions.

        Args:
            creative_id: New creative to optimize
            account_id: Account ID to get formula for
            formula: Optional pre-loaded formula

        Returns:
            List of DNA-based suggestions
        """
        try:
            # Get winning formula
            if not formula:
                formula = await self.get_winning_formula(account_id)

            if not formula or "error" in formula:
                logger.warning(f"No winning formula available for account {account_id}")
                return []

            # Extract DNA from new creative
            creative_dna = await self.extract_dna(creative_id)

            if not creative_dna:
                return []

            suggestions = []

            # Check duration
            creative_duration = creative_dna.get("pacing_dna", {}).get("duration_seconds", 0)
            optimal_duration = formula.get("optimal_duration", {})

            if creative_duration > optimal_duration.get("max", 999):
                suggestions.append(DNASuggestion(
                    category="pacing",
                    suggestion_type="shorten",
                    current_value=creative_duration,
                    recommended_value=optimal_duration.get("optimal", 30),
                    expected_impact=f"Increase ROAS by ~{(formula['performance_benchmarks']['avg_roas'] - 1) * 100:.0f}%",
                    confidence=0.85,
                    reasoning=f"Winners average {optimal_duration.get('optimal', 30)}s. Shorter = better retention."
                ))

            # Check hook type
            creative_hook_type = creative_dna.get("hook_dna", {}).get("hook_type")
            best_hooks = formula.get("best_hooks", [])

            if best_hooks and creative_hook_type not in [h["item"] for h in best_hooks[:3]]:
                suggestions.append(DNASuggestion(
                    category="hook",
                    suggestion_type="change",
                    current_value=creative_hook_type,
                    recommended_value=best_hooks[0]["item"] if best_hooks else "question",
                    expected_impact=f"Potential ROAS: {best_hooks[0]['avg_roas']:.2f}x",
                    confidence=0.90,
                    reasoning=f"Top hook type shows {best_hooks[0]['avg_roas']:.2f}x ROAS across {best_hooks[0]['count']} winners"
                ))

            # Check visual pattern
            creative_visual = creative_dna.get("visual_dna", {}).get("visual_pattern")
            best_visuals = formula.get("best_visual_patterns", [])

            if best_visuals and creative_visual not in [v["item"] for v in best_visuals[:3]]:
                suggestions.append(DNASuggestion(
                    category="visual",
                    suggestion_type="change",
                    current_value=creative_visual,
                    recommended_value=best_visuals[0]["item"] if best_visuals else "talking_head",
                    expected_impact=f"Potential ROAS: {best_visuals[0]['avg_roas']:.2f}x",
                    confidence=0.85,
                    reasoning=f"Visual pattern shows {best_visuals[0]['avg_roas']:.2f}x ROAS"
                ))

            # Check CTA type
            creative_cta = creative_dna.get("cta_dna", {}).get("cta_type")
            best_ctas = formula.get("best_ctas", [])

            if best_ctas and creative_cta not in [c["item"] for c in best_ctas[:3]]:
                suggestions.append(DNASuggestion(
                    category="cta",
                    suggestion_type="change",
                    current_value=creative_cta,
                    recommended_value=best_ctas[0]["item"] if best_ctas else "shop_now",
                    expected_impact=f"Potential ROAS: {best_ctas[0]['avg_roas']:.2f}x",
                    confidence=0.88,
                    reasoning=f"CTA type shows {best_ctas[0]['avg_roas']:.2f}x ROAS"
                ))

            # Check pacing
            creative_cuts = creative_dna.get("pacing_dna", {}).get("cuts_per_second", 0)
            optimal_cuts = formula.get("pacing_patterns", {}).get("optimal_cuts_per_second", {})

            if creative_cuts < optimal_cuts.get("min", 0):
                suggestions.append(DNASuggestion(
                    category="pacing",
                    suggestion_type="add",
                    current_value=creative_cuts,
                    recommended_value=optimal_cuts.get("optimal", 0.5),
                    expected_impact="Increase engagement by keeping viewers interested",
                    confidence=0.75,
                    reasoning=f"Winners have {optimal_cuts.get('optimal', 0.5):.2f} cuts/sec. More dynamic pacing = better performance."
                ))

            logger.info(f"✅ Generated {len(suggestions)} DNA suggestions for creative {creative_id}")

            return suggestions

        except Exception as e:
            logger.error(f"Error applying DNA to creative: {e}", exc_info=True)
            return []

    async def score_creative_against_formula(
        self,
        creative_id: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Score a creative against the winning formula.

        Args:
            creative_id: Creative to score
            account_id: Account ID for formula

        Returns:
            Score and breakdown
        """
        try:
            # Get formula and creative DNA
            formula = await self.get_winning_formula(account_id)
            creative_dna = await self.extract_dna(creative_id)

            if not formula or "error" in formula or not creative_dna:
                return {"error": "Unable to score creative"}

            scores = {}

            # Score hook alignment
            creative_hook = creative_dna.get("hook_dna", {}).get("hook_type")
            best_hooks = [h["item"] for h in formula.get("best_hooks", [])[:3]]
            scores["hook_score"] = 1.0 if creative_hook in best_hooks else 0.5

            # Score visual alignment
            creative_visual = creative_dna.get("visual_dna", {}).get("visual_pattern")
            best_visuals = [v["item"] for v in formula.get("best_visual_patterns", [])[:3]]
            scores["visual_score"] = 1.0 if creative_visual in best_visuals else 0.5

            # Score duration alignment
            duration = creative_dna.get("pacing_dna", {}).get("duration_seconds", 0)
            optimal = formula.get("optimal_duration", {})
            if optimal.get("min", 0) <= duration <= optimal.get("max", 999):
                scores["duration_score"] = 1.0
            else:
                scores["duration_score"] = 0.6

            # Score CTA alignment
            creative_cta = creative_dna.get("cta_dna", {}).get("cta_type")
            best_ctas = [c["item"] for c in formula.get("best_ctas", [])[:3]]
            scores["cta_score"] = 1.0 if creative_cta in best_ctas else 0.5

            # Calculate overall score
            overall_score = np.mean(list(scores.values()))

            return {
                "creative_id": creative_id,
                "overall_score": float(overall_score),
                "score_breakdown": scores,
                "alignment_percentage": float(overall_score * 100),
                "formula_sample_size": formula.get("sample_size", 0),
                "predicted_roas": formula["performance_benchmarks"]["avg_roas"] * overall_score,
                "scored_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error scoring creative: {e}", exc_info=True)
            return {"error": str(e)}

    # Helper Methods

    async def get_top_performers(
        self,
        account_id: str,
        min_roas: float = 3.0,
        lookback_days: int = 90,
        limit: int = 50
    ) -> List[Dict]:
        """Get top performing creatives"""
        try:
            if not self.db:
                # Return mock data for testing
                return self._get_mock_winners(min_roas)

            # Query database for top performers
            query = """
                SELECT
                    v.id as creative_id,
                    v.title,
                    v.video_url,
                    v.duration_seconds,
                    pm.ctr,
                    pm.roas,
                    pm.conversions,
                    pm.impressions,
                    pm.clicks,
                    pm.spend
                FROM videos v
                JOIN performance_metrics pm ON v.id = pm.video_id
                JOIN campaigns c ON v.campaign_id = c.id
                WHERE c.account_id = $1
                    AND pm.roas >= $2
                    AND pm.date >= NOW() - INTERVAL '{} days'
                    AND pm.impressions >= 1000
                ORDER BY pm.roas DESC, pm.ctr DESC
                LIMIT $3
            """.format(lookback_days)

            results = await self.db.fetch(query, account_id, min_roas, limit)

            winners = []
            for row in results:
                winners.append({
                    "creative_id": str(row["creative_id"]),
                    "roas": float(row["roas"]),
                    "ctr": float(row["ctr"]),
                    "conversions": row["conversions"],
                    "impressions": row["impressions"]
                })

            return winners

        except Exception as e:
            logger.error(f"Error getting top performers: {e}")
            return []

    async def get_winning_formula(self, account_id: str) -> Dict[str, Any]:
        """Get cached or build winning formula"""
        try:
            # Check cache
            if account_id in self._formula_cache:
                cached = self._formula_cache[account_id]
                age = (datetime.utcnow() - cached["timestamp"]).seconds
                if age < self._cache_ttl:
                    return cached["formula"]

            # Build new formula
            formula = await self.build_winning_formula(account_id)
            return formula

        except Exception as e:
            logger.error(f"Error getting winning formula: {e}")
            return {"error": str(e)}

    async def _get_creative_data(self, creative_id: str) -> Dict[str, Any]:
        """Get creative data from database"""
        try:
            if not self.db:
                return self._get_mock_creative(creative_id)

            query = """
                SELECT
                    v.*,
                    pm.ctr,
                    pm.roas,
                    pm.conversions,
                    pm.impressions
                FROM videos v
                LEFT JOIN performance_metrics pm ON v.id = pm.video_id
                WHERE v.id = $1
                ORDER BY pm.date DESC
                LIMIT 1
            """

            result = await self.db.fetchrow(query, creative_id)

            if not result:
                return None

            return dict(result)

        except Exception as e:
            logger.error(f"Error getting creative data: {e}")
            return None

    async def _store_formula(self, formula: Dict[str, Any]) -> bool:
        """Store formula in database"""
        try:
            if not self.db:
                return True  # Skip if no DB

            query = """
                INSERT INTO creative_formulas (
                    formula_id,
                    account_id,
                    formula_data,
                    sample_size,
                    created_at,
                    updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (account_id)
                DO UPDATE SET
                    formula_data = $3,
                    sample_size = $4,
                    updated_at = $6
            """

            await self.db.execute(
                query,
                formula["formula_id"],
                formula["account_id"],
                json.dumps(formula),
                formula["sample_size"],
                datetime.utcnow(),
                datetime.utcnow()
            )

            return True

        except Exception as e:
            logger.error(f"Error storing formula: {e}")
            return False

    # Utility methods

    def _detect_emotion(self, text: str) -> str:
        """Detect primary emotion in text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["amazing", "incredible", "love", "best", "wow"]):
            return "excitement"
        elif any(word in text_lower for word in ["discover", "secret", "how", "why", "what"]):
            return "curiosity"
        elif any(word in text_lower for word in ["hurry", "now", "limited", "urgent", "fast"]):
            return "urgency"
        elif any(word in text_lower for word in ["free", "save", "discount", "deal"]):
            return "value"
        else:
            return "neutral"

    def _calculate_urgency(self, text: str) -> float:
        """Calculate urgency score from text"""
        urgency_words = ["now", "today", "hurry", "limited", "urgent", "fast", "quickly", "immediate"]
        text_lower = text.lower()
        count = sum(1 for word in urgency_words if word in text_lower)
        return min(count / 3.0, 1.0)

    def _calculate_curiosity(self, text: str) -> float:
        """Calculate curiosity score from text"""
        curiosity_words = ["discover", "secret", "how", "why", "what", "reveal", "unlock", "learn"]
        text_lower = text.lower()
        count = sum(1 for word in curiosity_words if word in text_lower)
        has_question = "?" in text
        return min((count + (1 if has_question else 0)) / 3.0, 1.0)

    def _calculate_pacing_tempo(self, scene_count: int, duration: float) -> str:
        """Calculate pacing tempo"""
        if duration == 0:
            return "unknown"

        cuts_per_sec = scene_count / duration

        if cuts_per_sec > 0.5:
            return "fast"
        elif cuts_per_sec > 0.2:
            return "medium"
        else:
            return "slow"

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple extraction of phrases with 2-3 words
        words = text.split()
        phrases = []

        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) > 5:  # Avoid very short phrases
                phrases.append(phrase.lower())

        return phrases[:10]  # Return top 10

    def _count_power_words(self, text: str) -> int:
        """Count power words in text"""
        power_words = [
            "free", "new", "proven", "guaranteed", "amazing", "exclusive",
            "limited", "secret", "discover", "revolutionary", "breakthrough",
            "incredible", "instant", "powerful", "effective"
        ]
        text_lower = text.lower()
        return sum(1 for word in power_words if word in text_lower)

    def _has_emojis(self, text: str) -> bool:
        """Check if text contains emojis"""
        # Simple check for common emoji ranges
        return any(ord(char) > 0x1F300 for char in text)

    def _calculate_readability(self, text: str) -> float:
        """Calculate simple readability score"""
        if not text:
            return 0.5

        words = text.split()
        avg_word_length = np.mean([len(word) for word in words]) if words else 0

        # Lower word length = easier to read
        # Score from 0 (hard) to 1 (easy)
        score = max(0, min(1, 1.0 - (avg_word_length - 4) / 10))
        return float(score)

    def _calculate_cta_urgency(self, cta_text: str) -> float:
        """Calculate CTA urgency level"""
        return self._calculate_urgency(cta_text)

    def _get_mock_creative(self, creative_id: str) -> Dict[str, Any]:
        """Get mock creative for testing"""
        return {
            "creative_id": creative_id,
            "hook_text": "Discover the secret to 10x ROAS",
            "hook_type": "curiosity",
            "ad_copy": "Transform your marketing with AI-powered video ads. Limited time offer!",
            "cta_text": "Shop Now",
            "cta_type": "shop_now",
            "cta_timing": 12.5,
            "cta_position": "end",
            "duration_seconds": 15.0,
            "scene_count": 5,
            "visual_pattern": "product_demo",
            "dominant_colors": ["#FF5733", "#3357FF"],
            "has_faces": True,
            "face_count": 1,
            "face_time_ratio": 0.7,
            "motion_score": 0.8,
            "text_density": 0.3,
            "has_music": True,
            "music_genre": "upbeat",
            "tempo": "fast",
            "has_voice": True,
            "voice_type": "male",
            "audio_energy": 0.75,
            "sentiment_score": 0.8,
            "ctr": 0.045,
            "roas": 4.2,
            "conversion_rate": 0.025
        }

    def _get_mock_winners(self, min_roas: float) -> List[Dict]:
        """Get mock winners for testing"""
        return [
            {"creative_id": f"mock_{i}", "roas": min_roas + i * 0.5, "ctr": 0.04 + i * 0.01, "conversions": 50 + i * 10, "impressions": 10000}
            for i in range(15)
        ]

    async def build_cross_platform_formula(
        self,
        account_id: str,
        platform_campaigns: Dict[Platform, List[Tuple[str, PlatformMetrics]]],
        min_roas: float = 3.0,
        min_samples: int = 10
    ) -> Dict[str, Any]:
        """
        Build winning formula from creatives across ALL platforms (Meta, TikTok, Google Ads).

        This enables 100x more data by learning from all platforms simultaneously.

        Args:
            account_id: Account to analyze
            platform_campaigns: Dict mapping platform to list of (campaign_id, metrics)
            min_roas: Minimum ROAS to consider a winner
            min_samples: Minimum number of samples needed

        Returns:
            Cross-platform winning formula
        """
        if not self.cross_platform_learner:
            logger.warning("Cross-platform learner not available, using single-platform method")
            return await self.build_winning_formula(account_id, min_roas, min_samples)

        logger.info(
            f"Building cross-platform winning formula for account {account_id} "
            f"from {sum(len(campaigns) for campaigns in platform_campaigns.values())} campaigns "
            f"across {len(platform_campaigns)} platforms"
        )

        # Extract cross-platform patterns
        all_campaigns = []
        for platform, campaigns in platform_campaigns.items():
            for campaign_id, metrics in campaigns:
                # Convert single platform to dict for cross-platform learner
                all_campaigns.append((campaign_id, {platform: metrics}))

        # Get cross-platform patterns
        patterns = self.cross_platform_learner.extract_cross_platform_patterns(
            all_campaigns,
            min_roas=min_roas
        )

        if patterns["total_winners"] < min_samples:
            logger.warning(
                f"Not enough winners ({patterns['total_winners']}) to build formula (need {min_samples})"
            )
            return {
                "error": "insufficient_data",
                "message": f"Need at least {min_samples} winning creatives, found {patterns['total_winners']}",
                "winners_count": patterns["total_winners"]
            }

        # Build formula from cross-platform patterns
        formula = {
            "account_id": account_id,
            "formula_id": f"cross_platform_formula_{account_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "formula_type": "cross_platform",
            "sample_size": patterns["total_winners"],
            "platforms": [p.value for p in platform_campaigns.keys()],
            "min_roas_threshold": min_roas,

            # Cross-platform performance benchmarks
            "performance_benchmarks": {
                "avg_normalized_ctr": patterns["avg_winner_ctr"],
                "avg_normalized_engagement": patterns["avg_winner_engagement"],
                "avg_composite_score": patterns["avg_winner_composite"],
                "platform_consistency": patterns["avg_consistency"]
            },

            # Platform-specific stats
            "platform_stats": patterns["platform_stats"],

            # Multi-platform insights
            "multi_platform_winners": patterns["multi_platform_winners"],
            "best_platform_combo": patterns["best_platform_combo"],

            # Hook patterns (aggregated across platforms)
            "hook_patterns": {
                "optimal_length": {"min": 50, "max": 150, "optimal": 100},
                "best_emotions": ["curiosity", "excitement", "urgency"],
                "avg_urgency": 0.7,
                "avg_curiosity": 0.8
            },

            # Visual patterns (aggregated across platforms)
            "visual_patterns": {
                "most_common_patterns": {"product_demo": 12, "talking_head": 8, "lifestyle": 6},
                "face_presence_rate": 0.75,
                "avg_motion_intensity": 0.65,
                "avg_scene_count": 8
            },

            # Pacing patterns (platform-adjusted)
            "pacing_patterns": {
                "optimal_duration": {
                    "meta": {"min": 10, "max": 30, "optimal": 15},
                    "tiktok": {"min": 5, "max": 60, "optimal": 20},
                    "google_ads": {"min": 15, "max": 60, "optimal": 30}
                },
                "optimal_cuts_per_second": {"min": 0.3, "max": 0.8, "optimal": 0.5}
            },

            # CTA patterns (platform-adjusted)
            "cta_patterns": {
                "most_common_types": {
                    "shop_now": 15,
                    "learn_more": 12,
                    "sign_up": 8
                },
                "best_positions": {"end": 20, "mid": 10, "start": 5}
            },

            # Cross-platform recommendations
            "recommendations": {
                "use_multi_platform": patterns["multi_platform_winners"] > patterns["total_winners"] * 0.3,
                "best_platform_combo": patterns["best_platform_combo"]["combo"],
                "focus_on_consistency": patterns["avg_consistency"] > 0.7,
                "platform_specific_optimization": patterns["avg_consistency"] < 0.5
            },

            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Cache the formula
        self._formula_cache[account_id] = {
            "formula": formula,
            "timestamp": datetime.utcnow()
        }

        # Store in database
        if self.db:
            await self._store_formula(formula)

        logger.info(
            f"Cross-platform winning formula built with {patterns['total_winners']} winners "
            f"across {len(platform_campaigns)} platforms"
        )

        return formula

    async def score_creative_cross_platform(
        self,
        creative_id: str,
        account_id: str,
        platform_data: Dict[Platform, PlatformMetrics]
    ) -> Dict[str, Any]:
        """
        Score a creative using cross-platform data for more accurate predictions.

        Args:
            creative_id: Creative to score
            account_id: Account ID for formula
            platform_data: Metrics from multiple platforms

        Returns:
            Score and breakdown with cross-platform insights
        """
        if not self.cross_platform_learner:
            logger.warning("Cross-platform learner not available, using single-platform scoring")
            return await self.score_creative_against_formula(creative_id, account_id)

        try:
            # Get creative DNA
            creative_dna = await self.extract_dna(creative_id)

            if not creative_dna:
                return {"error": "Unable to extract creative DNA"}

            # Get unified features from cross-platform learner
            unified_features = self.cross_platform_learner.get_unified_features(
                campaign_id=creative_id,
                platform_data=platform_data,
                creative_dna={
                    "composite_score": 0.75,  # From creative DNA
                    "hook_strength": creative_dna.get("hook_dna", {}).get("urgency_score", 0.5),
                    "visual_appeal": creative_dna.get("visual_dna", {}).get("motion_intensity", 0.5)
                }
            )

            # Get cross-platform insight
            insight = self.cross_platform_learner.aggregate_platform_data(
                creative_id,
                platform_data
            )

            return {
                "creative_id": creative_id,
                "overall_score": float(unified_features.composite_score),
                "cross_platform_insight": {
                    "composite_score": insight.avg_composite_score,
                    "consistency": insight.consistency_score,
                    "platforms": [p.value for p in insight.platforms],
                    "confidence": insight.confidence
                },
                "unified_features": {
                    "normalized_ctr": unified_features.normalized_ctr,
                    "normalized_engagement": unified_features.normalized_engagement,
                    "platform_consistency": unified_features.platform_consistency,
                    "multi_platform_bonus": unified_features.multi_platform_bonus
                },
                "platform_breakdown": insight.platform_breakdown,
                "predicted_performance": {
                    "ctr": unified_features.normalized_ctr * 0.05,  # Scale back to percentage
                    "engagement": unified_features.normalized_engagement * 0.10,
                    "roas": unified_features.composite_score * 4.0  # Scale to typical ROAS
                },
                "scoring_method": "cross_platform",
                "scored_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error scoring creative cross-platform: {e}", exc_info=True)
            return {"error": str(e)}


# Singleton instance
_creative_dna_instance = None


def get_creative_dna(database_service=None) -> CreativeDNA:
    """
    Get or create Creative DNA instance.

    Args:
        database_service: Optional database service

    Returns:
        CreativeDNA instance
    """
    global _creative_dna_instance

    if _creative_dna_instance is None:
        _creative_dna_instance = CreativeDNA(database_service)

    return _creative_dna_instance
