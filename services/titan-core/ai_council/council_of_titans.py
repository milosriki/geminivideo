import os
import re
import asyncio
import json
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
from datetime import datetime
from base64 import b64encode

# Import prompt caching system
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from prompts.cache_manager import (
    prompt_loader,
    cache_monitor,
    get_cached_system_prompt,
    print_cache_report
)

# Lazy imports for AI clients
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class OpenAIModelType(str, Enum):
    """
    OpenAI Model Selection Strategy (November 2025)

    Reference: https://platform.openai.com/docs/models
    """
    # Reasoning Models (Extended Chain-of-Thought)
    O1 = "o1"  # Full reasoning - complex logic, structural analysis, deep thinking
    O1_MINI = "o1-mini"  # Fast reasoning - quick logical checks, cost-optimized

    # GPT-4o Family (Multimodal)
    GPT4O_LATEST = "gpt-4o-2024-11-20"  # Latest - improved vision, audio, faster
    GPT4O = "gpt-4o"  # Standard - production stable
    GPT4O_MINI = "gpt-4o-mini"  # Cost-optimized - 90% cheaper, simple tasks

    @classmethod
    def select_for_task(cls, task_type: Literal["reasoning", "vision", "scoring", "fast"]) -> str:
        """
        Intelligent model selection based on task requirements

        Args:
            task_type: Type of task to perform
                - "reasoning": Complex logical reasoning (o1)
                - "vision": Multimodal analysis - images/video (gpt-4o-latest)
                - "scoring": Simple numerical scoring (gpt-4o-mini)
                - "fast": Fast reasoning checks (o1-mini)
        """
        selection_map = {
            "reasoning": cls.O1.value,  # Complex reasoning with extended thinking
            "vision": cls.GPT4O_LATEST.value,  # Multimodal analysis (images/video)
            "scoring": cls.GPT4O_MINI.value,  # Simple numerical scoring
            "fast": cls.O1_MINI.value  # Fast reasoning checks
        }
        return selection_map.get(task_type, cls.GPT4O_LATEST.value)


class ScoreSchema:
    """
    JSON Schemas for Structured Outputs (November 2025 Feature)

    Uses response_format: { type: "json_schema" } for consistent, validated responses.
    Reference: https://platform.openai.com/docs/guides/structured-outputs
    """

    @staticmethod
    def get_simple_score_schema() -> Dict[str, Any]:
        """Schema for simple numeric scoring"""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "viral_score_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "score": {
                            "type": "number",
                            "description": "Viral potential score from 0-100"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence level 0-1"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation of the score"
                        }
                    },
                    "required": ["score", "confidence", "reasoning"],
                    "additionalProperties": False
                }
            }
        }

    @staticmethod
    def get_detailed_critique_schema() -> Dict[str, Any]:
        """Schema for detailed video analysis with o1 reasoning"""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "detailed_critique_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "overall_score": {
                            "type": "number",
                            "description": "Overall score 0-100"
                        },
                        "hook_strength": {
                            "type": "number",
                            "description": "Hook effectiveness 0-100"
                        },
                        "emotional_resonance": {
                            "type": "number",
                            "description": "Emotional impact 0-100"
                        },
                        "cta_clarity": {
                            "type": "number",
                            "description": "Call-to-action clarity 0-100"
                        },
                        "pacing_score": {
                            "type": "number",
                            "description": "Content pacing 0-100"
                        },
                        "viral_potential": {
                            "type": "number",
                            "description": "Viral likelihood 0-100"
                        },
                        "strengths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key strengths identified"
                        },
                        "weaknesses": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Areas for improvement"
                        },
                        "improvement_suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific recommendations"
                        }
                    },
                    "required": ["overall_score", "hook_strength", "emotional_resonance",
                               "cta_clarity", "pacing_score", "viral_potential"],
                    "additionalProperties": False
                }
            }
        }

    @staticmethod
    def get_vision_analysis_schema() -> Dict[str, Any]:
        """Schema for visual element analysis with GPT-4o Vision"""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "vision_analysis_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "visual_score": {
                            "type": "number",
                            "description": "Visual quality score 0-100"
                        },
                        "has_human_face": {
                            "type": "boolean",
                            "description": "Detected human face(s)"
                        },
                        "scene_description": {
                            "type": "string",
                            "description": "Description of the visual scene"
                        },
                        "color_palette": {
                            "type": "string",
                            "description": "Dominant colors and mood"
                        },
                        "text_overlays_detected": {
                            "type": "boolean",
                            "description": "Text overlays present"
                        },
                        "composition_quality": {
                            "type": "number",
                            "description": "Visual composition score 0-100"
                        },
                        "attention_grabbing_elements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Elements that capture attention"
                        },
                        "recommended_improvements": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Visual improvement suggestions"
                        }
                    },
                    "required": ["visual_score", "has_human_face", "scene_description"],
                    "additionalProperties": False
                }
            }
        }


class CouncilOfTitans:
    """
    The Ultimate AI Council - December 2025 Edition

    Model Strategy:
    1. Gemini 3 Pro (Extended Reasoning) - 40%
    2. OpenAI o1 (Complex Logic/Structure) - 20%
    3. Claude Sonnet 4.5 (Nuance/Psychology) - 30%
    4. DeepCTR (Data/Heuristics) - 10%

    OpenAI Upgrades (November 2025):
    - o1: Complex reasoning with extended chain-of-thought
    - o1-mini: Fast reasoning for quick checks
    - GPT-4o (2024-11-20): Latest multimodal (vision, audio)
    - GPT-4o-mini: Cost-optimized for simple tasks
    - Structured Outputs: JSON schema validation
    - Vision API: Video thumbnail/frame analysis
    - Batch API: 50% cost savings for non-urgent tasks
    """

    # Model Configuration with Fallbacks
    GEMINI_MODEL = "gemini-3-pro"
    GEMINI_MODEL_FALLBACK = "gemini-2.0-flash-thinking-exp-1219"
    CLAUDE_MODEL = "claude-sonnet-4-5-20250514"
    CLAUDE_MODEL_FALLBACK = "claude-3-5-sonnet-20241022"

    def __init__(self):
        # Initialize Clients with proper error handling
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        self.openai_client = AsyncOpenAI(api_key=openai_key) if AsyncOpenAI and openai_key else None
        self.anthropic_client = AsyncAnthropic(api_key=anthropic_key) if AsyncAnthropic and anthropic_key else None

        # Configure Gemini
        if genai and gemini_key:
            genai.configure(api_key=gemini_key)

        # Use Gemini 3 Pro (December 2025 - Extended Reasoning) with fallback
        self.gemini_model = os.getenv("GEMINI_MODEL_ID", self.GEMINI_MODEL)
        self.gemini_model_fallback = self.GEMINI_MODEL_FALLBACK
        self.display_name = "Gemini 3 Pro"

        # Configure Claude Sonnet 4.5 with fallback
        self.claude_model = os.getenv("CLAUDE_MODEL_ID", self.CLAUDE_MODEL)
        self.claude_model_fallback = self.CLAUDE_MODEL_FALLBACK

        # Configure generation settings for thinking mode
        self.generation_config = {
            "temperature": 1.0,  # Higher for creative thinking
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,  # Thinking models need more tokens
        }

        # Batch API queue for cost optimization
        self.batch_queue: List[Dict[str, Any]] = []
        self.batch_enabled = os.getenv("OPENAI_BATCH_ENABLED", "false").lower() == "true"

        # Prompt caching enabled (10x cost reduction)
        self.caching_enabled = os.getenv("PROMPT_CACHING_ENABLED", "true").lower() == "true"

        print(f"🏛️ COUNCIL: Initialized with {self.display_name} + Claude Sonnet 4.5 + OpenAI November 2025 Models")
        print(f"   - Gemini: {self.gemini_model} (Fallback: {self.gemini_model_fallback})")
        print(f"   - Claude: {self.claude_model} (Fallback: {self.claude_model_fallback})")
        print(f"   - o1: Complex reasoning")
        print(f"   - GPT-4o (2024-11-20): Latest multimodal")
        print(f"   - GPT-4o-mini: Cost-optimized scoring")
        print(f"   - Batch API: {'Enabled' if self.batch_enabled else 'Disabled'}")
        print(f"   - Prompt Caching: {'Enabled (10x cost reduction)' if self.caching_enabled else 'Disabled'}")

    def _calculate_deep_ctr_score(self, visual_features: dict) -> float:
        """
        Heuristic-based DeepCTR scoring (0-100).
        Analyzes visual features to predict engagement potential.
        """
        score = 50.0  # Base score

        # Boost for human faces (proven engagement driver)
        if visual_features.get("has_human_face", False):
            score += 15.0

        # Hook type bonuses
        hook_type = visual_features.get("hook_type", "").lower()
        hook_bonuses = {
            "pattern_interrupt": 20.0,
            "curiosity_gap": 15.0,
            "shock": 18.0,
            "question": 12.0,
            "bold_claim": 10.0,
            "story": 8.0
        }
        score += hook_bonuses.get(hook_type, 5.0)

        # Visual quality indicators
        if visual_features.get("high_contrast", False):
            score += 5.0
        if visual_features.get("fast_paced", False):
            score += 5.0
        if visual_features.get("text_overlays", False):
            score += 3.0

        # Scene variety (dynamic content performs better)
        scene_count = visual_features.get("scene_count", 0)
        if scene_count >= 5:
            score += 7.0
        elif scene_count >= 3:
            score += 4.0

        # Clamp to 0-100 range
        return max(0.0, min(100.0, score))

    async def get_gemini_critique(self, script: str) -> Dict[str, Any]:
        """
        Gemini 3 Pro - Extended reasoning with chain-of-thought

        WITH CONTEXT CACHING: Gemini supports caching for repeated context (coming soon)
        Currently using optimized system prompts for consistency
        Includes automatic fallback to Gemini 2.0 Flash Thinking if primary model fails
        """
        if not genai:
            return {"score": 75.0, "source": "Gemini (Not Installed)"}

        # Try primary model first, then fallback
        models_to_try = [
            (self.gemini_model, "Gemini 3 Pro"),
            (self.gemini_model_fallback, "Gemini 2.0 Flash Thinking (Fallback)")
        ]

        for model_id, model_name in models_to_try:
            try:
                # Create model with generation config for thinking mode
                model = genai.GenerativeModel(
                    model_id,
                    generation_config=self.generation_config
                )

                # Use cached system prompt for consistency (Gemini will auto-cache in future)
                if self.caching_enabled:
                    system_context = get_cached_system_prompt("viral_ad_expert", provider="gemini")
                    enhanced_prompt = f"""{system_context}

TASK: Analyze this ad script and provide a viral potential score (0-100).

Use chain-of-thought reasoning:
1. First, identify the hook type and strength
2. Analyze psychological triggers deployed
3. Evaluate pacing and emotional arc
4. Consider viral pattern matching (2025 trends)
5. Assess clarity of call-to-action

After your analysis, return ONLY the final score as a number (0-100).

SCRIPT:
{script}

FINAL SCORE (number only):"""
                else:
                    # Fallback to simple prompt
                    enhanced_prompt = f"""You are an Elite Viral Ad Strategist with deep analytical reasoning.

TASK: Analyze this ad script and provide a viral potential score (0-100).

Use chain-of-thought reasoning:
1. First, identify the hook type and strength
2. Analyze psychological triggers deployed
3. Evaluate pacing and emotional arc
4. Consider viral pattern matching (2025 trends)
5. Assess clarity of call-to-action

After your analysis, return ONLY the final score as a number (0-100).

SCRIPT:
{script}

FINAL SCORE (number only):"""

                response = model.generate_content(enhanced_prompt)

                # Handle thinking models which may have different response structure
                score_text = response.text.strip()

                # Extract the final number from thinking output
                # Look for numbers that appear to be scores (0-100 range)
                numbers = re.findall(r'(?<![.\d])\d{1,3}(?:\.\d+)?(?![.\d])', score_text)

                # Filter for valid scores in 0-100 range
                valid_scores = [float(n) for n in numbers if 0 <= float(n) <= 100]
                score = valid_scores[-1] if valid_scores else 75.0  # Use last valid score

                # Clamp to valid range
                score = max(0.0, min(100.0, score))

                return {
                    "score": score,
                    "source": model_name,
                    "reasoning_used": True,
                    "model": model_id
                }

            except Exception as e:
                print(f"⚠️ {model_name} Error: {e}")
                # Continue to next model in the loop
                continue

        # If all models failed, return fallback score
        return {
            "score": 75.0,
            "source": "Gemini (All Models Failed)",
            "error": "All Gemini models failed"
        }

    async def get_openai_o1_critique(self, script: str, mode: Literal["full", "mini"] = "full") -> Dict[str, Any]:
        """
        OpenAI o1 Reasoning Models (November 2025)

        Features:
        - Extended chain-of-thought reasoning
        - Deep structural analysis
        - Complex logical evaluation

        Args:
            script: The ad script to analyze
            mode: "full" (o1) or "mini" (o1-mini for faster/cheaper)
        """
        if not self.openai_client:
            return {"score": 75.0, "source": "OpenAI o1 (Disabled)"}

        model = OpenAIModelType.O1.value if mode == "full" else OpenAIModelType.O1_MINI.value

        try:
            # o1 models use reasoning tokens and have specific requirements
            # No system messages, no temperature control (uses internal reasoning)
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this viral ad script using deep logical reasoning.

Evaluate these dimensions:
1. Hook Structure: Pattern interrupt effectiveness, curiosity gap creation
2. Logical Flow: Argument coherence, premise-to-conclusion strength
3. CTA Clarity: Action steps, friction points, conversion pathway
4. Structural Integrity: Story arc, pacing logic, retention mechanics

Use chain-of-thought reasoning to score 0-100.

SCRIPT:
{script}

Provide your analysis, then return ONLY the final score as a number."""
                    }
                ]
                # Note: o1 models don't support temperature, top_p, or system messages
                # They use internal reasoning optimization
            )

            content = response.choices[0].message.content.strip()

            # Extract score from reasoning output
            numbers = re.findall(r'(?<![.\d])\d{1,3}(?:\.\d+)?(?![.\d])', content)
            valid_scores = [float(n) for n in numbers if 0 <= float(n) <= 100]
            score = valid_scores[-1] if valid_scores else 75.0

            score = max(0.0, min(100.0, score))

            # o1 models provide reasoning_tokens usage
            reasoning_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0

            return {
                "score": score,
                "source": f"OpenAI {model}",
                "reasoning_tokens": reasoning_tokens,
                "model": model
            }

        except Exception as e:
            print(f"⚠️ OpenAI o1 Error: {e}")
            return {
                "score": 75.0,
                "source": f"OpenAI {model} (Fallback)",
                "error": str(e)
            }

    async def get_gpt4o_critique_simple(self, script: str) -> Dict[str, Any]:
        """
        GPT-4o-mini for simple scoring (November 2025)

        Cost-optimized model: 90% cheaper than GPT-4o
        WITH PROMPT CACHING: OpenAI automatically caches consistent prefixes (50% reduction)
        """
        if not self.openai_client:
            return {"score": 75.0, "source": "GPT-4o-mini (Disabled)"}

        try:
            # Use cached system prompt (OpenAI auto-caches consistent prefixes)
            if self.caching_enabled:
                system_content = get_cached_system_prompt("viral_ad_expert", provider="openai")
            else:
                system_content = "You are a Viral Ad Scoring Expert. Analyze scripts quickly and provide structured scores."

            # Use structured outputs for consistent JSON response
            response = await self.openai_client.chat.completions.create(
                model=OpenAIModelType.GPT4O_MINI.value,
                messages=[
                    {
                        "role": "system",
                        "content": system_content  # CACHED (automatic by OpenAI)
                    },
                    {
                        "role": "user",
                        "content": f"Rate this ad script 0-100 based on hook strength, clarity, and viral potential.\n\nSCRIPT:\n{script}"
                    }
                ],
                response_format=ScoreSchema.get_simple_score_schema()
            )

            # Parse structured JSON response
            result = json.loads(response.choices[0].message.content)

            # Track cache performance (if available in response)
            if self.caching_enabled and hasattr(response, 'usage'):
                usage = response.usage
                cache_monitor.record_openai_request(
                    model=OpenAIModelType.GPT4O_MINI.value,
                    input_tokens=usage.prompt_tokens,
                    cached_tokens=getattr(usage, 'prompt_tokens_details', {}).get('cached_tokens', 0),
                    output_tokens=usage.completion_tokens
                )

            return {
                "score": float(result["score"]),
                "confidence": float(result.get("confidence", 0.8)),
                "reasoning": result.get("reasoning", ""),
                "source": "GPT-4o-mini (Cached)" if self.caching_enabled else "GPT-4o-mini (Structured)",
                "model": OpenAIModelType.GPT4O_MINI.value,
                "cached_tokens": getattr(response.usage, 'prompt_tokens_details', {}).get('cached_tokens', 0) if hasattr(response, 'usage') else 0
            }

        except Exception as e:
            print(f"⚠️ GPT-4o-mini Error: {e}")
            return {"score": 75.0, "source": "GPT-4o-mini (Fallback)", "error": str(e)}

    async def get_gpt4o_vision_analysis(self, image_path: str, script: Optional[str] = None) -> Dict[str, Any]:
        """
        GPT-4o Vision Analysis (November 2025 - Latest)

        Features:
        - Improved vision capabilities
        - Video thumbnail analysis
        - Visual element extraction
        - Color palette detection

        Args:
            image_path: Path to image/thumbnail or base64 image data
            script: Optional script text for multimodal analysis
        """
        if not self.openai_client:
            return {"visual_score": 75.0, "source": "GPT-4o Vision (Disabled)"}

        try:
            # Prepare image content
            if os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    image_data = b64encode(img_file.read()).decode("utf-8")
                    image_url = f"data:image/jpeg;base64,{image_data}"
            else:
                # Assume it's a URL
                image_url = image_path

            # Build multimodal message
            content_parts = [
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                },
                {
                    "type": "text",
                    "text": """Analyze this video thumbnail/frame for viral ad potential.

Evaluate:
1. Visual appeal and attention-grabbing elements
2. Composition quality and framing
3. Color psychology and mood
4. Presence of human faces (engagement driver)
5. Text overlays and readability
6. Overall viral potential

Provide detailed structured analysis."""
                }
            ]

            if script:
                content_parts.append({
                    "type": "text",
                    "text": f"\n\nAD SCRIPT (for context):\n{script}"
                })

            # Use latest GPT-4o model with vision capabilities
            response = await self.openai_client.chat.completions.create(
                model=OpenAIModelType.GPT4O_LATEST.value,
                messages=[
                    {
                        "role": "user",
                        "content": content_parts
                    }
                ],
                response_format=ScoreSchema.get_vision_analysis_schema(),
                max_tokens=1000
            )

            # Parse structured JSON response
            result = json.loads(response.choices[0].message.content)

            return {
                **result,
                "source": "GPT-4o Vision (2024-11-20)",
                "model": OpenAIModelType.GPT4O_LATEST.value
            }

        except Exception as e:
            print(f"⚠️ GPT-4o Vision Error: {e}")
            return {
                "visual_score": 75.0,
                "has_human_face": False,
                "scene_description": "Analysis failed",
                "source": "GPT-4o Vision (Fallback)",
                "error": str(e)
            }

    async def get_claude_critique(self, script: str) -> Dict[str, Any]:
        """
        Claude Sonnet 4.5 - Psychology and emotional resonance expert

        WITH PROMPT CACHING:
        - 90% cost reduction on cached tokens
        - System prompt (~2000 tokens) cached automatically
        - Only script content (~500 tokens) sent fresh each time
        Includes automatic fallback to Claude 3.5 Sonnet if primary model fails
        """
        if not self.anthropic_client:
            return {"score": 75.0, "source": "Claude Sonnet (Disabled)"}

        # Try primary model first, then fallback
        models_to_try = [
            (self.claude_model, "Claude Sonnet 4.5"),
            (self.claude_model_fallback, "Claude 3.5 Sonnet (Fallback)")
        ]

        for model_id, model_name in models_to_try:
            try:
                # Use cached system prompt for 90% cost reduction
                if self.caching_enabled:
                    system_prompt = get_cached_system_prompt("psychology_expert", provider="anthropic")
                else:
                    # Fallback to simple prompt
                    system_prompt = [
                        {
                            "type": "text",
                            "text": "You are a Psychology Expert. Rate ad scripts 0-100 based on emotional resonance and persuasion."
                        }
                    ]

                response = await self.anthropic_client.messages.create(
                    model=model_id,
                    max_tokens=100,
                    system=system_prompt,  # CACHED system prompt
                    messages=[
                        {
                            "role": "user",
                            "content": f"Rate this ad script 0-100 based on emotional resonance and persuasion. Return ONLY a number.\n\nSCRIPT:\n{script}"
                        }
                    ]
                )

                # Extract score
                score = float(response.content[0].text.strip())

                # Track cache performance
                if self.caching_enabled and hasattr(response, 'usage'):
                    usage = response.usage
                    cache_monitor.record_anthropic_request(
                        input_tokens=usage.input_tokens,
                        cached_tokens=getattr(usage, 'cache_read_input_tokens', 0),
                        output_tokens=usage.output_tokens,
                        cache_hit=getattr(usage, 'cache_read_input_tokens', 0) > 0
                    )

                cached_suffix = " (Cached)" if self.caching_enabled else ""
                return {
                    "score": score,
                    "source": f"{model_name}{cached_suffix}",
                    "cached_tokens": getattr(response.usage, 'cache_read_input_tokens', 0) if hasattr(response, 'usage') else 0,
                    "model": model_id
                }

            except Exception as e:
                print(f"⚠️ {model_name} Error: {e}")
                # Continue to next model in the loop
                continue

        # If all models failed, return fallback score
        return {
            "score": 75.0,
            "source": "Claude (All Models Failed)",
            "error": "All Claude models failed"
        }

    async def batch_create_job(self, scripts: List[str]) -> Optional[str]:
        """
        Batch API for Non-Urgent Analysis (November 2025)

        Benefits:
        - 50% cost reduction compared to real-time API
        - Process up to 100K requests per batch
        - 24-hour turnaround time

        Use for: Bulk script analysis, A/B testing variations, historical data processing

        Reference: https://platform.openai.com/docs/guides/batch
        """
        if not self.openai_client or not self.batch_enabled:
            print("⚠️ Batch API disabled or client not available")
            return None

        try:
            # Prepare batch requests in JSONL format
            batch_requests = []
            for idx, script in enumerate(scripts):
                batch_requests.append({
                    "custom_id": f"script-{idx}-{datetime.now().timestamp()}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": OpenAIModelType.GPT4O_MINI.value,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Rate this ad script 0-100 for viral potential."
                            },
                            {
                                "role": "user",
                                "content": script
                            }
                        ],
                        "response_format": ScoreSchema.get_simple_score_schema()
                    }
                })

            # Create batch input file
            batch_file_path = f"/tmp/batch_input_{datetime.now().timestamp()}.jsonl"
            with open(batch_file_path, "w") as f:
                for req in batch_requests:
                    f.write(json.dumps(req) + "\n")

            # Upload batch file
            with open(batch_file_path, "rb") as f:
                batch_file = await self.openai_client.files.create(
                    file=f,
                    purpose="batch"
                )

            # Create batch job
            batch_job = await self.openai_client.batches.create(
                input_file_id=batch_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )

            print(f"📦 Batch Job Created: {batch_job.id}")
            print(f"   - Scripts: {len(scripts)}")
            print(f"   - Est. Cost Savings: 50%")
            print(f"   - Completion: 24h")

            return batch_job.id

        except Exception as e:
            print(f"⚠️ Batch API Error: {e}")
            return None

    async def batch_retrieve_results(self, batch_job_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve results from a batch job

        Returns:
            List of results if job completed, None if still processing
        """
        if not self.openai_client:
            return None

        try:
            # Check batch status
            batch = await self.openai_client.batches.retrieve(batch_job_id)

            print(f"📦 Batch Job {batch_job_id}: {batch.status}")

            if batch.status != "completed":
                print(f"   - Status: {batch.status}")
                return None

            # Download results
            result_file_id = batch.output_file_id
            result_content = await self.openai_client.files.content(result_file_id)

            # Parse JSONL results
            results = []
            for line in result_content.text.strip().split("\n"):
                result = json.loads(line)
                results.append(result)

            print(f"✅ Batch Results Retrieved: {len(results)} items")
            return results

        except Exception as e:
            print(f"⚠️ Batch Retrieval Error: {e}")
            return None

    async def evaluate_script(
        self,
        script: str,
        visual_features: Optional[dict] = None,
        image_path: Optional[str] = None,
        use_o1: bool = False
    ) -> Dict[str, Any]:
        """
        Main Council Evaluation (November 2025 Edition)

        Args:
            script: Ad script text
            visual_features: Optional visual metadata
            image_path: Optional image/thumbnail for vision analysis
            use_o1: Use o1 reasoning model instead of standard GPT (higher quality, higher cost)

        Returns:
            Comprehensive evaluation with weighted scores from all models
        """
        print("🏛️ THE COUNCIL IS CONVENING (November 2025 Edition)...")

        # 1. Run ALL LLMs in Parallel
        tasks = []

        # Gemini 3 Pro (40% weight) - Extended Reasoning
        tasks.append(self.get_gemini_critique(script))

        # OpenAI Selection: o1 (complex reasoning) OR gpt-4o-mini (cost-optimized)
        if use_o1:
            print("   🧠 Using OpenAI o1 for deep reasoning...")
            tasks.append(self.get_openai_o1_critique(script, mode="full"))
        else:
            print("   💰 Using GPT-4o-mini for cost-optimized scoring...")
            tasks.append(self.get_gpt4o_critique_simple(script))

        # Claude Sonnet 4.5 (30% weight) - Psychology
        tasks.append(self.get_claude_critique(script))

        # Optional: Vision Analysis
        if image_path:
            print("   👁️ Analyzing visual elements with GPT-4o Vision...")
            tasks.append(self.get_gpt4o_vision_analysis(image_path, script))

        # 2. Calculate DeepCTR Score (10% weight)
        if not visual_features:
            visual_features = {"has_human_face": True, "hook_type": "pattern_interrupt"}

        deep_ctr_score = self._calculate_deep_ctr_score(visual_features)

        # 3. Gather Results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        gemini_res = results[0] if not isinstance(results[0], Exception) else {"score": 75.0, "source": "Gemini (Error)"}
        openai_res = results[1] if not isinstance(results[1], Exception) else {"score": 75.0, "source": "OpenAI (Error)"}
        claude_res = results[2] if not isinstance(results[2], Exception) else {"score": 75.0, "source": "Claude (Error)"}

        vision_res = None
        if image_path and len(results) > 3:
            vision_res = results[3] if not isinstance(results[3], Exception) else None

        # 4. Calculate Weighted Score
        # Weights: Gemini (40%), Claude (30%), OpenAI (20%), DeepCTR (10%)
        final_score = (
            gemini_res['score'] * 0.40 +
            claude_res['score'] * 0.30 +
            openai_res['score'] * 0.20 +
            deep_ctr_score * 0.10
        )

        # Build response
        response = {
            "final_score": round(final_score, 1),
            "breakdown": {
                "gemini_3_pro": gemini_res['score'],
                "openai": openai_res['score'],
                "openai_model": openai_res.get('model', 'gpt-4o-mini'),
                "claude_sonnet_4_5": claude_res['score'],
                "deep_ctr": deep_ctr_score
            },
            "verdict": "APPROVE" if final_score > 85 else "REJECT",
            "council_members": {
                "gemini": gemini_res.get('source'),
                "openai": openai_res.get('source'),
                "claude": claude_res.get('source')
            }
        }

        # Add vision analysis if available
        if vision_res:
            response["vision_analysis"] = {
                "visual_score": vision_res.get("visual_score", 0),
                "has_human_face": vision_res.get("has_human_face", False),
                "scene_description": vision_res.get("scene_description", ""),
                "attention_elements": vision_res.get("attention_grabbing_elements", [])
            }

        # Print detailed breakdown
        print(f"\n📊 COUNCIL VERDICT: {response['verdict']} (Score: {final_score:.1f}/100)")
        print(f"   - {gemini_res.get('source', 'Gemini 3 Pro')}: {gemini_res['score']:.1f}")
        print(f"   - {openai_res.get('source', 'OpenAI')}: {openai_res['score']:.1f}")
        print(f"   - {claude_res.get('source', 'Claude Sonnet 4.5')}: {claude_res['score']:.1f}")
        print(f"   - DeepCTR: {deep_ctr_score:.1f}")
        if vision_res:
            print(f"   - Vision Score: {vision_res.get('visual_score', 0):.1f}")

        # Show cache performance metrics
        if self.caching_enabled:
            total_cached = (
                gemini_res.get('cached_tokens', 0) +
                openai_res.get('cached_tokens', 0) +
                claude_res.get('cached_tokens', 0)
            )
            if total_cached > 0:
                print(f"\n💰 CACHE PERFORMANCE:")
                print(f"   - Total Cached Tokens: {total_cached:,}")
                print(f"   - Estimated Cost Savings: ~90% reduction")

        return response

    async def evaluate_with_detailed_critique(self, script: str) -> Dict[str, Any]:
        """
        Deep Analysis with o1 Reasoning Model

        Uses o1 with structured outputs for comprehensive script breakdown.
        Best for: Final approval decisions, complex script evaluation
        """
        if not self.openai_client:
            return {"error": "OpenAI client not available"}

        try:
            print("🧠 Running Deep Analysis with OpenAI o1...")

            response = await self.openai_client.chat.completions.create(
                model=OpenAIModelType.O1.value,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Perform a comprehensive analysis of this viral ad script.

Evaluate these dimensions thoroughly:
1. Hook Strength: Pattern interrupt, curiosity gap, immediate impact
2. Emotional Resonance: Psychological triggers, relatability, emotional arc
3. CTA Clarity: Call-to-action strength, friction reduction, conversion pathway
4. Pacing: Content flow, retention mechanics, attention maintenance
5. Viral Potential: Shareability factors, trend alignment, cultural resonance

Use deep chain-of-thought reasoning to provide:
- Numerical scores for each dimension (0-100)
- Key strengths and weaknesses
- Specific improvement suggestions

SCRIPT:
{script}

Provide your detailed analysis with structured scores."""
                    }
                ],
                # Note: o1 doesn't support response_format yet (as of Nov 2025)
                # Parse JSON from response manually
            )

            content = response.choices[0].message.content

            # Try to extract structured data or return raw analysis
            return {
                "detailed_analysis": content,
                "model": OpenAIModelType.O1.value,
                "reasoning_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0
            }

        except Exception as e:
            print(f"⚠️ Deep Analysis Error: {e}")
            return {"error": str(e)}

    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get current cache performance metrics

        Returns:
            Dictionary with cache statistics and cost savings
        """
        return cache_monitor.get_summary()

    def print_cache_report(self):
        """Print detailed cache performance report"""
        print_cache_report()

    def reset_cache_metrics(self):
        """Reset cache performance metrics"""
        cache_monitor.reset_metrics()


# Global Council Instance
council = CouncilOfTitans()
