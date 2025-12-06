"""
AI Enrichment Pipeline - Make Ads Searchable & Intelligent

Uses OUR AI stack (not third-party):
- Whisper: Transcription with timestamps
- Gemini 2.0 Flash: Visual analysis
- Llama 4: NLP, emotion, patterns

This is where we BEAT Foreplay:
- They use basic ML models
- We use Gemini 2.0 + Llama 4 (state of the art)
- Better pattern detection = better ad recommendations
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import aiohttp

logger = logging.getLogger(__name__)


# =============================================================================
# Enrichment Results
# =============================================================================

@dataclass
class TranscriptionResult:
    """Whisper transcription output"""
    full_text: str
    segments: List[Dict]  # [{start: 0.0, end: 2.5, text: "..."}]
    language: str
    duration: float


@dataclass
class VisualAnalysis:
    """Gemini visual analysis output"""
    elements: List[str]  # ["person", "product", "text_overlay"]
    style: str  # "ugc", "professional", "animated"
    dominant_colors: List[str]
    scene_count: int
    has_face: bool
    has_product: bool
    has_text_overlay: bool
    hook_visual: str  # What grabs attention
    thumbnail_quality: float  # 0-1


@dataclass
class NLPAnalysis:
    """Llama 4 NLP analysis output"""
    emotional_drivers: List[str]  # ["fomo", "curiosity", "trust"]
    emotion_intensity: Dict[str, float]  # {"fomo": 0.8, "curiosity": 0.6}
    product_category: str
    target_audience: str
    cta_type: str
    cta_urgency: float
    key_benefits: List[str]
    objections_addressed: List[str]
    persuasion_techniques: List[str]


@dataclass
class HookAnalysis:
    """Hook (first 3 seconds) analysis"""
    text: str
    type: str  # "question", "number", "story", "pattern_interrupt"
    effectiveness_score: float  # 0-1
    attention_grabbers: List[str]
    improvement_suggestions: List[str]


@dataclass
class EnrichedAd:
    """Fully enriched ad with all AI analysis"""
    ad_id: str

    # Transcription
    transcription: TranscriptionResult

    # Visual
    visual: VisualAnalysis

    # NLP
    nlp: NLPAnalysis

    # Hook
    hook: HookAnalysis

    # Aggregated patterns (for search/filtering)
    winning_patterns: List[str]
    winner_score: float  # 0-100

    # Embeddings for vector search
    text_embedding: List[float] = field(default_factory=list)

    # Processing metadata
    enriched_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0


# =============================================================================
# AI Clients (Use our existing infrastructure)
# =============================================================================

class WhisperClient:
    """
    Transcription using Whisper.

    Options:
    1. OpenAI Whisper API (easiest)
    2. Local Whisper model (cheaper at scale)
    3. Replicate/Fireworks hosted Whisper
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"

    async def transcribe(
        self,
        audio_path: str,
        language: str = None
    ) -> TranscriptionResult:
        """Transcribe audio/video file"""

        # For video, extract audio first
        if audio_path.endswith(('.mp4', '.mov', '.webm')):
            audio_path = await self._extract_audio(audio_path)

        async with aiohttp.ClientSession() as session:
            with open(audio_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='audio.mp3')
                data.add_field('model', 'whisper-1')
                data.add_field('response_format', 'verbose_json')
                data.add_field('timestamp_granularities[]', 'segment')

                if language:
                    data.add_field('language', language)

                async with session.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return TranscriptionResult(
                            full_text=result.get('text', ''),
                            segments=[
                                {
                                    'start': s['start'],
                                    'end': s['end'],
                                    'text': s['text']
                                }
                                for s in result.get('segments', [])
                            ],
                            language=result.get('language', 'en'),
                            duration=result.get('duration', 0)
                        )
                    else:
                        error = await resp.text()
                        logger.error(f"Whisper error: {error}")
                        return TranscriptionResult("", [], "en", 0)

    async def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video using FFmpeg"""
        import subprocess

        audio_path = video_path.rsplit('.', 1)[0] + '.mp3'

        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'mp3', '-y',
            audio_path
        ], capture_output=True)

        return audio_path


class GeminiAnalyzer:
    """
    Visual analysis using Gemini 2.0 Flash.

    Gemini 2.0 Flash is multimodal - can analyze video directly!
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

    async def analyze_video(self, video_path: str) -> VisualAnalysis:
        """Analyze video frames for visual patterns"""

        # For now, analyze key frames
        frames = await self._extract_key_frames(video_path)

        prompt = """Analyze this advertisement video/image and return JSON:
{
    "elements": ["list visual elements: person, product, text_overlay, before_after, testimonial, unboxing, lifestyle, animation"],
    "style": "ugc|professional|animated|slideshow|talking_head",
    "dominant_colors": ["top 3 colors"],
    "scene_count": number,
    "has_face": boolean,
    "has_product": boolean,
    "has_text_overlay": boolean,
    "hook_visual": "describe what grabs attention in first 3 seconds",
    "thumbnail_quality": 0-1 score
}

Be specific about advertising patterns you see."""

        # Call Gemini API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}?key={self.api_key}",
                json={
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            # Include frame images here
                        ]
                    }],
                    "generationConfig": {
                        "response_mime_type": "application/json"
                    }
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    try:
                        text = result['candidates'][0]['content']['parts'][0]['text']
                        data = json.loads(text)
                        return VisualAnalysis(**data)
                    except:
                        pass

        # Return defaults on error
        return VisualAnalysis(
            elements=[],
            style="unknown",
            dominant_colors=[],
            scene_count=1,
            has_face=False,
            has_product=False,
            has_text_overlay=False,
            hook_visual="",
            thumbnail_quality=0.5
        )

    async def _extract_key_frames(self, video_path: str, count: int = 5) -> List[str]:
        """Extract key frames from video"""
        import subprocess

        output_dir = Path(video_path).parent / "frames"
        output_dir.mkdir(exist_ok=True)

        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vf', f'select=eq(n\\,0)+eq(n\\,30)+eq(n\\,60)+eq(n\\,90)+eq(n\\,120)',
            '-vsync', 'vfr',
            '-frames:v', str(count),
            f'{output_dir}/frame_%d.jpg'
        ], capture_output=True)

        return list(output_dir.glob('frame_*.jpg'))


class LlamaAnalyzer:
    """
    NLP analysis using Llama 4.

    Uses our existing Llama 4 integration via Together AI.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TOGETHER_API_KEY")
        self.api_url = "https://api.together.xyz/v1/chat/completions"
        self.model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

    async def analyze_text(self, text: str) -> NLPAnalysis:
        """Analyze ad copy for marketing patterns"""

        prompt = f"""You are an expert ad copywriter and marketing psychologist.
Analyze this advertisement text and return detailed JSON:

AD TEXT:
{text}

Return this exact JSON structure:
{{
    "emotional_drivers": ["list emotions triggered: fomo, curiosity, trust, fear, desire, urgency, social_proof, exclusivity"],
    "emotion_intensity": {{"emotion_name": 0.0-1.0 intensity}},
    "product_category": "specific category like skincare, fitness_equipment, saas_tool, fashion",
    "target_audience": "demographic like women_25_35, male_entrepreneurs, parents_young_children",
    "cta_type": "shop_now|learn_more|sign_up|download|get_started|book_call",
    "cta_urgency": 0.0-1.0,
    "key_benefits": ["list of benefits mentioned"],
    "objections_addressed": ["list of objections/concerns handled"],
    "persuasion_techniques": ["list techniques: scarcity, social_proof, authority, reciprocity, liking, commitment"]
}}"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    try:
                        text = result['choices'][0]['message']['content']
                        # Extract JSON from response
                        start = text.find('{')
                        end = text.rfind('}') + 1
                        if start >= 0 and end > start:
                            data = json.loads(text[start:end])
                            return NLPAnalysis(**data)
                    except Exception as e:
                        logger.warning(f"Failed to parse Llama response: {e}")

        return NLPAnalysis(
            emotional_drivers=[],
            emotion_intensity={},
            product_category="general",
            target_audience="general",
            cta_type="learn_more",
            cta_urgency=0.5,
            key_benefits=[],
            objections_addressed=[],
            persuasion_techniques=[]
        )

    async def analyze_hook(
        self,
        hook_text: str,
        full_transcript: str = ""
    ) -> HookAnalysis:
        """Analyze the hook (first 3 seconds)"""

        prompt = f"""You are an expert at analyzing video ad hooks.
The hook is the first 3 seconds - it must grab attention immediately.

HOOK TEXT (first 3 seconds):
{hook_text}

FULL CONTEXT:
{full_transcript[:500]}

Analyze and return JSON:
{{
    "text": "the hook text",
    "type": "question|number|bold_statement|story_start|pattern_interrupt|demonstration|controversy|before_after",
    "effectiveness_score": 0.0-1.0,
    "attention_grabbers": ["list what makes it grab attention"],
    "improvement_suggestions": ["how to make it better"]
}}"""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    try:
                        text = result['choices'][0]['message']['content']
                        start = text.find('{')
                        end = text.rfind('}') + 1
                        if start >= 0 and end > start:
                            data = json.loads(text[start:end])
                            return HookAnalysis(**data)
                    except:
                        pass

        return HookAnalysis(
            text=hook_text,
            type="statement",
            effectiveness_score=0.5,
            attention_grabbers=[],
            improvement_suggestions=[]
        )


# =============================================================================
# Main Enrichment Pipeline
# =============================================================================

class AdEnrichmentPipeline:
    """
    Full AI enrichment pipeline.

    Takes raw scraped ad → outputs fully enriched ad with:
    - Transcription
    - Visual analysis
    - NLP analysis
    - Hook analysis
    - Patterns extracted
    - Embeddings for search
    """

    def __init__(self):
        self.whisper = WhisperClient()
        self.gemini = GeminiAnalyzer()
        self.llama = LlamaAnalyzer()

    async def enrich(
        self,
        ad_id: str,
        media_path: str = None,
        body_text: str = "",
        existing_transcript: str = None
    ) -> EnrichedAd:
        """
        Full enrichment pipeline.

        Args:
            ad_id: Unique ad identifier
            media_path: Path to video/image file
            body_text: Ad copy text
            existing_transcript: Skip transcription if already have it
        """
        start_time = datetime.now()

        # Step 1: Transcription
        if existing_transcript:
            transcription = TranscriptionResult(
                full_text=existing_transcript,
                segments=[],
                language="en",
                duration=0
            )
        elif media_path and media_path.endswith(('.mp4', '.mov', '.webm')):
            transcription = await self.whisper.transcribe(media_path)
        else:
            transcription = TranscriptionResult("", [], "en", 0)

        # Step 2: Visual analysis
        if media_path:
            visual = await self.gemini.analyze_video(media_path)
        else:
            visual = VisualAnalysis([], "unknown", [], 1, False, False, False, "", 0.5)

        # Step 3: NLP analysis (combine body + transcript)
        full_text = f"{body_text}\n{transcription.full_text}".strip()
        nlp = await self.llama.analyze_text(full_text)

        # Step 4: Hook analysis (first 3 seconds)
        hook_text = self._extract_hook_text(transcription.segments, body_text)
        hook = await self.llama.analyze_hook(hook_text, transcription.full_text)

        # Step 5: Extract winning patterns
        patterns = self._extract_patterns(visual, nlp, hook)

        # Step 6: Calculate winner score
        winner_score = self._calculate_winner_score(visual, nlp, hook, patterns)

        # Step 7: Generate embeddings (optional - for vector search)
        # text_embedding = await self._generate_embedding(full_text)

        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return EnrichedAd(
            ad_id=ad_id,
            transcription=transcription,
            visual=visual,
            nlp=nlp,
            hook=hook,
            winning_patterns=patterns,
            winner_score=winner_score,
            text_embedding=[],
            enriched_at=datetime.now(),
            processing_time_ms=processing_time
        )

    def _extract_hook_text(
        self,
        segments: List[Dict],
        body_text: str,
        max_seconds: float = 3.0
    ) -> str:
        """Extract text from first 3 seconds"""
        hook_parts = []

        for seg in segments:
            if seg['start'] < max_seconds:
                hook_parts.append(seg['text'])

        if hook_parts:
            return " ".join(hook_parts).strip()

        # Fallback to first line of body text
        if body_text:
            return body_text.split('\n')[0].strip()

        return ""

    def _extract_patterns(
        self,
        visual: VisualAnalysis,
        nlp: NLPAnalysis,
        hook: HookAnalysis
    ) -> List[str]:
        """Extract winning patterns from analysis"""
        patterns = []

        # Visual patterns
        if 'before_after' in visual.elements:
            patterns.append('before_after')
        if 'ugc' in visual.style.lower():
            patterns.append('ugc_style')
        if visual.has_face:
            patterns.append('face_in_frame')
        if visual.has_text_overlay:
            patterns.append('text_overlay')
        if 'testimonial' in visual.elements:
            patterns.append('testimonial')
        if 'unboxing' in visual.elements:
            patterns.append('unboxing')

        # Emotional patterns
        for emotion in nlp.emotional_drivers:
            if emotion in ['fomo', 'urgency', 'scarcity']:
                patterns.append('urgency_trigger')
            if emotion in ['trust', 'authority', 'social_proof']:
                patterns.append('trust_signal')
            if emotion == 'curiosity':
                patterns.append('curiosity_gap')

        # CTA patterns
        if nlp.cta_urgency > 0.7:
            patterns.append('strong_cta')
        if nlp.cta_type in ['shop_now', 'buy_now', 'get_started']:
            patterns.append('direct_response')

        # Hook patterns
        if hook.type == 'question':
            patterns.append('question_hook')
        if hook.type == 'number':
            patterns.append('number_hook')
        if hook.type == 'pattern_interrupt':
            patterns.append('pattern_interrupt')
        if hook.effectiveness_score > 0.8:
            patterns.append('strong_hook')

        # Persuasion techniques
        if 'social_proof' in nlp.persuasion_techniques:
            patterns.append('social_proof')
        if 'scarcity' in nlp.persuasion_techniques:
            patterns.append('scarcity')
        if 'authority' in nlp.persuasion_techniques:
            patterns.append('authority')

        return list(set(patterns))  # Deduplicate

    def _calculate_winner_score(
        self,
        visual: VisualAnalysis,
        nlp: NLPAnalysis,
        hook: HookAnalysis,
        patterns: List[str]
    ) -> float:
        """
        Calculate predicted winner score 0-100.

        Based on patterns that correlate with high-performing ads.
        """
        score = 0

        # Hook effectiveness (30 points max)
        score += hook.effectiveness_score * 30

        # Visual quality (20 points max)
        if visual.style in ['ugc', 'talking_head']:
            score += 10  # UGC typically performs better
        if visual.has_face:
            score += 5
        if visual.has_text_overlay:
            score += 5

        # Emotional triggers (25 points max)
        high_converting_emotions = ['fomo', 'curiosity', 'urgency', 'desire']
        emotion_matches = sum(1 for e in nlp.emotional_drivers if e in high_converting_emotions)
        score += min(25, emotion_matches * 8)

        # Pattern count (25 points max)
        winning_pattern_count = len([p for p in patterns if p in [
            'before_after', 'ugc_style', 'social_proof', 'strong_hook',
            'urgency_trigger', 'question_hook', 'testimonial'
        ]])
        score += min(25, winning_pattern_count * 5)

        return min(100, score)


# =============================================================================
# Batch Processing
# =============================================================================

async def enrich_ads_batch(
    ads: List[Dict],
    max_concurrent: int = 5
) -> List[EnrichedAd]:
    """
    Enrich multiple ads in parallel.

    Args:
        ads: List of dicts with {ad_id, media_path, body_text}
        max_concurrent: Max parallel processing
    """
    pipeline = AdEnrichmentPipeline()
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(ad: Dict) -> EnrichedAd:
        async with semaphore:
            return await pipeline.enrich(
                ad_id=ad['ad_id'],
                media_path=ad.get('media_path'),
                body_text=ad.get('body_text', '')
            )

    tasks = [process_one(ad) for ad in ads]
    return await asyncio.gather(*tasks)


# =============================================================================
# Integration with Scraped Ads
# =============================================================================

async def enrich_scraped_ad(ad) -> Dict:
    """
    Enrich a ScrapedAd and return combined data.

    Returns dict that can be indexed in Typesense.
    """
    from .ad_library_scraper import ScrapedAd, to_foreplay_format

    pipeline = AdEnrichmentPipeline()

    enriched = await pipeline.enrich(
        ad_id=ad.id,
        media_path=ad.local_media_path,
        body_text=ad.body_text,
        existing_transcript=ad.transcript
    )

    # Update ad with enrichment
    ad.transcript = enriched.transcription.full_text
    ad.timestamped_transcription = [
        {"start": s["start"], "end": s["end"], "text": s["text"]}
        for s in enriched.transcription.segments
    ]
    ad.emotional_drivers = enriched.nlp.emotional_drivers
    ad.product_category = enriched.nlp.product_category
    ad.hook_text = enriched.hook.text
    ad.hook_type = enriched.hook.type
    ad.winning_patterns = enriched.winning_patterns

    # Return combined data for indexing
    base = to_foreplay_format(ad)
    base.update({
        "visual_style": enriched.visual.style,
        "visual_elements": enriched.visual.elements,
        "has_face": enriched.visual.has_face,
        "has_product": enriched.visual.has_product,
        "has_text_overlay": enriched.visual.has_text_overlay,
        "hook_score": enriched.hook.effectiveness_score,
        "winner_score": enriched.winner_score,
        "cta_type": enriched.nlp.cta_type,
        "cta_urgency": enriched.nlp.cta_urgency,
        "target_audience": enriched.nlp.target_audience,
        "persuasion_techniques": enriched.nlp.persuasion_techniques,
        "enriched_at": enriched.enriched_at.isoformat(),
    })

    return base
