"""
Auto-Variation Generator

Generate 50 variations per creative concept.
This is how AI beats humans - volume and speed.

A human can make 5 variations. AI makes 50 in the same time.
Testing 50 variations finds winners 10x faster.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random
import hashlib
import json
from itertools import product

logger = logging.getLogger(__name__)

class VariationType(Enum):
    HOOK = "hook"           # First 3 seconds
    CTA = "cta"             # Call to action
    HEADLINE = "headline"   # Text overlays
    COLOR = "color"         # Color scheme
    MUSIC = "music"         # Background music
    VOICE = "voice"         # Voiceover style
    PACING = "pacing"       # Edit rhythm
    DURATION = "duration"   # Video length
    FORMAT = "format"       # Aspect ratio

@dataclass
class CreativeConcept:
    """Base creative concept to vary"""
    id: str
    name: str
    description: str
    target_audience: str
    industry: str
    objective: str  # conversions, awareness, traffic

    # Core elements
    product: str
    key_benefit: str
    pain_point: str
    social_proof: str

    # Style
    brand_colors: List[str]
    tone: str  # energetic, calm, urgent, professional

    # Content
    hook_script: str
    main_script: str
    cta_text: str

@dataclass
class CreativeVariation:
    """A variation of the base concept"""
    id: str
    concept_id: str
    variation_number: int

    # Changed elements
    variations_applied: Dict[str, str]

    # Content
    hook: str
    headline: str
    cta: str
    color_scheme: List[str]
    pacing: str
    duration: int

    # Metadata
    created_at: datetime
    predicted_performance: float
    variation_hash: str

class VariationGenerator:
    """
    Generate 50 creative variations from one concept.

    Variation strategies:
    1. Hook variations (10 different openings)
    2. CTA variations (10 different endings)
    3. Headline variations (10 different texts)
    4. Color variations (5 different schemes)
    5. Pacing variations (3 different rhythms)
    6. Duration variations (3 different lengths)
    7. Cross-combinations for 50 total
    """

    TARGET_VARIATIONS = 50

    def __init__(self):
        self.hook_templates = self._load_hook_templates()
        self.cta_templates = self._load_cta_templates()
        self.color_variations = self._load_color_variations()

    def generate_variations(self, concept: CreativeConcept,
                           count: int = 50) -> List[CreativeVariation]:
        """
        Generate variations from a creative concept.

        Args:
            concept: Base creative concept
            count: Number of variations (default 50)

        Returns:
            List of creative variations
        """
        variations = []

        # Generate all possible variations
        hooks = self._generate_hook_variations(concept, 10)
        ctas = self._generate_cta_variations(concept, 10)
        headlines = self._generate_headline_variations(concept, 10)
        colors = self._generate_color_variations(concept, 5)
        pacings = ["fast", "medium", "slow"]
        durations = [15, 30, 60]

        # Create combinations
        variation_number = 0

        # Strategy 1: Vary hooks (keep other elements)
        for hook in hooks[:10]:
            variation_number += 1
            if variation_number > count:
                break
            variations.append(self._create_variation(
                concept, variation_number,
                hook=hook,
                headline=concept.key_benefit,
                cta=concept.cta_text,
                colors=concept.brand_colors,
                pacing="medium",
                duration=30
            ))

        # Strategy 2: Vary CTAs
        for cta in ctas[:10]:
            variation_number += 1
            if variation_number > count:
                break
            variations.append(self._create_variation(
                concept, variation_number,
                hook=concept.hook_script,
                headline=concept.key_benefit,
                cta=cta,
                colors=concept.brand_colors,
                pacing="medium",
                duration=30
            ))

        # Strategy 3: Vary headlines
        for headline in headlines[:10]:
            variation_number += 1
            if variation_number > count:
                break
            variations.append(self._create_variation(
                concept, variation_number,
                hook=concept.hook_script,
                headline=headline,
                cta=concept.cta_text,
                colors=concept.brand_colors,
                pacing="medium",
                duration=30
            ))

        # Strategy 4: Vary colors
        for color_set in colors[:5]:
            variation_number += 1
            if variation_number > count:
                break
            variations.append(self._create_variation(
                concept, variation_number,
                hook=concept.hook_script,
                headline=concept.key_benefit,
                cta=concept.cta_text,
                colors=color_set,
                pacing="medium",
                duration=30
            ))

        # Strategy 5: Vary pacing and duration combinations
        for pacing, duration in product(pacings, durations):
            variation_number += 1
            if variation_number > count:
                break
            variations.append(self._create_variation(
                concept, variation_number,
                hook=concept.hook_script,
                headline=concept.key_benefit,
                cta=concept.cta_text,
                colors=concept.brand_colors,
                pacing=pacing,
                duration=duration
            ))

        # Strategy 6: Cross-combinations (hook + CTA + color)
        for hook, cta, colors in product(hooks[:3], ctas[:3], colors[:3]):
            variation_number += 1
            if variation_number > count:
                break
            variations.append(self._create_variation(
                concept, variation_number,
                hook=hook,
                headline=concept.key_benefit,
                cta=cta,
                colors=colors,
                pacing="medium",
                duration=30
            ))

        logger.info(f"Generated {len(variations)} variations for concept {concept.id}")
        return variations[:count]

    def _create_variation(self, concept: CreativeConcept, number: int,
                          hook: str, headline: str, cta: str,
                          colors: List[str], pacing: str, duration: int) -> CreativeVariation:
        """Create a single variation"""

        # Track what changed
        variations_applied = {}
        if hook != concept.hook_script:
            variations_applied['hook'] = 'modified'
        if headline != concept.key_benefit:
            variations_applied['headline'] = 'modified'
        if cta != concept.cta_text:
            variations_applied['cta'] = 'modified'
        if colors != concept.brand_colors:
            variations_applied['colors'] = 'modified'
        if pacing != 'medium':
            variations_applied['pacing'] = pacing
        if duration != 30:
            variations_applied['duration'] = str(duration)

        # Generate hash for deduplication
        content_hash = hashlib.md5(
            f"{hook}{headline}{cta}{','.join(colors)}{pacing}{duration}".encode()
        ).hexdigest()[:8]

        # Predict performance (placeholder - would use ML model)
        predicted_performance = self._predict_performance(
            hook, headline, cta, colors, pacing, duration
        )

        return CreativeVariation(
            id=f"{concept.id}_var_{number}",
            concept_id=concept.id,
            variation_number=number,
            variations_applied=variations_applied,
            hook=hook,
            headline=headline,
            cta=cta,
            color_scheme=colors,
            pacing=pacing,
            duration=duration,
            created_at=datetime.now(),
            predicted_performance=predicted_performance,
            variation_hash=content_hash
        )

    def _generate_hook_variations(self, concept: CreativeConcept,
                                   count: int) -> List[str]:
        """Generate hook variations"""
        templates = [
            f"Stop scrolling! {concept.pain_point}?",
            f"What if {concept.key_benefit}?",
            f"I tried {concept.product}... here's what happened",
            f"POV: You discovered {concept.product}",
            f"This changed everything about {concept.pain_point}",
            f"Wait... {concept.product} actually works?!",
            f"Nobody's talking about this {concept.pain_point} solution",
            f"The secret to {concept.key_benefit} is...",
            f"You need to see this if you struggle with {concept.pain_point}",
            f"How {concept.social_proof} with {concept.product}"
        ]
        return templates[:count]

    def _generate_cta_variations(self, concept: CreativeConcept,
                                  count: int) -> List[str]:
        """Generate CTA variations"""
        templates = [
            f"Get {concept.product} Now →",
            f"Try {concept.product} Free",
            f"Shop Now - Limited Time",
            f"Claim Your {concept.product}",
            f"Start Your Journey →",
            f"Yes, I Want This!",
            f"Get {concept.key_benefit} Today",
            f"Join {concept.social_proof}",
            f"Don't Miss Out - Shop Now",
            f"Transform Your {concept.pain_point.split()[0]}"
        ]
        return templates[:count]

    def _generate_headline_variations(self, concept: CreativeConcept,
                                       count: int) -> List[str]:
        """Generate headline variations"""
        templates = [
            concept.key_benefit,
            f"Say goodbye to {concept.pain_point}",
            f"Finally, {concept.key_benefit}",
            f"The {concept.product} everyone's talking about",
            f"Experience {concept.key_benefit} in days",
            f"Why {concept.social_proof} chose this",
            f"Your solution to {concept.pain_point}",
            f"Discover the power of {concept.product}",
            f"Join thousands who {concept.key_benefit}",
            f"The future of {concept.pain_point.split()[0]} is here"
        ]
        return templates[:count]

    def _generate_color_variations(self, concept: CreativeConcept,
                                    count: int) -> List[List[str]]:
        """Generate color scheme variations"""
        # Keep brand colors as base, add variations
        base = concept.brand_colors

        variations = [
            base,  # Original
            ["#FF6B6B", "#4ECDC4", "#45B7D1"],  # Vibrant
            ["#2C3E50", "#E74C3C", "#ECF0F1"],  # Professional
            ["#F39C12", "#27AE60", "#2980B9"],  # Energetic
            ["#9B59B6", "#3498DB", "#1ABC9C"]   # Modern
        ]
        return variations[:count]

    def _predict_performance(self, hook: str, headline: str, cta: str,
                              colors: List[str], pacing: str, duration: int) -> float:
        """Predict variation performance (placeholder for ML model)"""
        # Simple heuristic scoring
        score = 0.5

        # Hook scoring
        if any(word in hook.lower() for word in ['stop', 'wait', 'what if']):
            score += 0.1

        # CTA scoring
        if any(word in cta.lower() for word in ['free', 'now', 'today']):
            score += 0.1

        # Duration scoring (shorter often better)
        if duration == 15:
            score += 0.05
        elif duration == 60:
            score -= 0.05

        # Pacing scoring
        if pacing == "fast":
            score += 0.05

        return min(1.0, max(0.0, score))

    def _load_hook_templates(self) -> List[str]:
        """Load hook templates from knowledge base"""
        return []  # Would load from database

    def _load_cta_templates(self) -> List[str]:
        """Load CTA templates from knowledge base"""
        return []

    def _load_color_variations(self) -> List[List[str]]:
        """Load color variations from knowledge base"""
        return []

    def rank_variations(self, variations: List[CreativeVariation]) -> List[CreativeVariation]:
        """Rank variations by predicted performance"""
        return sorted(variations, key=lambda v: v.predicted_performance, reverse=True)

    def get_top_variations(self, variations: List[CreativeVariation],
                           count: int = 10) -> List[CreativeVariation]:
        """Get top N variations by predicted performance"""
        ranked = self.rank_variations(variations)
        return ranked[:count]

    def export_variations(self, variations: List[CreativeVariation]) -> List[Dict]:
        """Export variations for rendering"""
        return [
            {
                "id": v.id,
                "variation_number": v.variation_number,
                "hook": v.hook,
                "headline": v.headline,
                "cta": v.cta,
                "colors": v.color_scheme,
                "pacing": v.pacing,
                "duration": v.duration,
                "predicted_score": v.predicted_performance,
                "render_priority": i + 1
            }
            for i, v in enumerate(self.rank_variations(variations))
        ]
