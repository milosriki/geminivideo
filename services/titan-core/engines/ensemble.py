"""
Council of Titans - Multi-model ensemble evaluation
Production-grade implementation with real API calls
"""
import os
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

# API clients
try:
    import google.generativeai as genai
    from anthropic import AsyncAnthropic
    from openai import AsyncOpenAI
    import httpx
except ImportError as e:
    logging.error(f"Missing required dependencies: {e}")
    raise

logger = logging.getLogger(__name__)

class CouncilEvaluator:
    """
    Ensemble evaluation using:
    - Gemini 3 Pro (40% weight) - Creative reasoning
    - Claude 3.5 Sonnet (30% weight) - Psychology expertise
    - GPT-4o (20% weight) - Logic verification
    - DeepCTR (10% weight) - Data-driven predictions
    """

    # Niche-specific approval thresholds (configurable per vertical)
    NICHE_THRESHOLDS = {
        "fitness": 85.0,       # High bar for competitive fitness market
        "e-commerce": 82.0,    # Slightly lower for product ads
        "education": 88.0,     # Higher bar for credibility-focused content
        "finance": 90.0,       # Highest bar for trust-sensitive vertical
        "entertainment": 80.0, # Lower bar for viral/fun content
        "default": 85.0        # Fallback threshold
    }

    def __init__(self):
        """Initialize API clients from environment variables"""
        # Gemini configuration
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=gemini_api_key)

        # Claude configuration
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.anthropic = AsyncAnthropic(api_key=anthropic_api_key)

        # OpenAI configuration
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.openai = AsyncOpenAI(api_key=openai_api_key)

        # DeepCTR service URL
        self.deepctr_url = os.getenv("ML_SERVICE_URL")
        if not self.deepctr_url:
            # TODO: [CRITICAL] Ensure ML_SERVICE_URL is set in production
            # Without this, the Council loses its data-driven "gut feeling" (10% of score)
            logger.warning("ML_SERVICE_URL not set - DeepCTR predictions will use fallback scores")
            self.deepctr_url = None

        # Response cache (5 minute TTL)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # seconds

        # Allow override of thresholds via environment variable
        env_threshold = os.getenv("COUNCIL_APPROVAL_THRESHOLD")
        if env_threshold:
            try:
                self.default_threshold = float(env_threshold)
                logger.info(f"Using custom approval threshold: {self.default_threshold}")
            except ValueError:
                logger.warning(f"Invalid COUNCIL_APPROVAL_THRESHOLD: {env_threshold}, using niche-specific defaults")
                self.default_threshold = None
        else:
            self.default_threshold = None

        logger.info("Council of Titans initialized successfully")

    def get_approval_threshold(self, niche: str) -> float:
        """
        Get the approval threshold for a specific niche.
        Priority: env variable > niche-specific > default
        """
        if self.default_threshold is not None:
            return self.default_threshold
        return self.NICHE_THRESHOLDS.get(niche, self.NICHE_THRESHOLDS["default"])

    async def evaluate_script(self, script_content: str, niche: str = "fitness") -> Dict[str, Any]:
        """
        Evaluate script with Council of Titans

        Args:
            script_content: The script/content to evaluate
            niche: Business vertical (fitness, e-commerce, education, etc.)

        Returns:
            {
                "verdict": "APPROVED" | "NEEDS_REVISION",
                "final_score": float (0-100),
                "breakdown": {
                    "gemini_3_pro": float,
                    "claude_3_5": float,
                    "gpt_4o": float,
                    "deep_ctr": float
                },
                "feedback": str,
                "confidence": float,
                "timestamp": str
            }
        """
        # Check cache
        cache_key = self._generate_cache_key(script_content, niche)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.utcnow().timestamp() - cached['timestamp']) < self._cache_ttl:
                logger.info("Returning cached evaluation")
                return cached['result']

        logger.info(f"Evaluating script with Council of Titans (niche: {niche})")

        # Run all evaluators in parallel
        try:
            results = await asyncio.gather(
                self._evaluate_with_gemini(script_content, niche),
                self._evaluate_with_claude(script_content, niche),
                self._evaluate_with_gpt(script_content, niche),
                self._evaluate_with_deepctr(script_content, niche),
                return_exceptions=True
            )

            # Handle any exceptions
            scores = []
            breakdown = {}
            errors = []

            for i, (name, result) in enumerate([
                ("gemini_3_pro", results[0]),
                ("claude_3_5", results[1]),
                ("gpt_4o", results[2]),
                ("deep_ctr", results[3])
            ]):
                if isinstance(result, Exception):
                    logger.error(f"{name} evaluation failed: {result}")
                    errors.append(f"{name}: {str(result)}")
                    # Use neutral score if model fails
                    breakdown[name] = 70.0
                    scores.append(70.0)
                else:
                    breakdown[name] = result
                    scores.append(result)

            # Calculate weighted final score
            # Weights: Gemini 40%, Claude 30%, GPT 20%, DeepCTR 10%
            final_score = (
                scores[0] * 0.4 +
                scores[1] * 0.3 +
                scores[2] * 0.2 +
                scores[3] * 0.1
            )

            # Calculate confidence (lower if any models failed)
            confidence = 1.0 - (len(errors) * 0.2)

            # Determine verdict with niche-specific threshold
            threshold = self.get_approval_threshold(niche)
            verdict = "APPROVED" if final_score >= threshold else "NEEDS_REVISION"
            logger.info(f"Verdict: {verdict} (score: {final_score:.2f}, threshold: {threshold} for {niche})")

            # Generate feedback
            feedback = self._generate_feedback(breakdown, script_content, errors)

            result = {
                "verdict": verdict,
                "final_score": round(final_score, 2),
                "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
                "feedback": feedback,
                "confidence": round(confidence, 2),
                "errors": errors if errors else None,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Cache result
            self._cache[cache_key] = {
                'result': result,
                'timestamp': datetime.utcnow().timestamp()
            }

            return result

        except Exception as e:
            logger.error(f"Council evaluation failed: {e}", exc_info=True)
            raise

    async def _evaluate_with_gemini(self, script: str, niche: str) -> float:
        """Evaluate with Gemini 3 Pro (creative reasoning with structured output)"""
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-1219')

            prompt = f"""You are a world-class creative director evaluating an ad script for the {niche} industry.

Script to evaluate:
{script}

Think step by step and rate this script on a scale of 0-100 based on:
1. Hook strength (first 3 seconds) - 30 points
2. Emotional resonance - 25 points
3. Clarity of value proposition - 20 points
4. Call-to-action effectiveness - 15 points
5. Overall virality potential - 10 points

First, provide your reasoning for each criterion, then calculate the final score."""

            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    top_p=0.95,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "reasoning": {
                                "type": "string",
                                "description": "Step-by-step analysis of each criterion"
                            },
                            "score": {
                                "type": "number",
                                "description": "Final score from 0-100"
                            }
                        },
                        "required": ["reasoning", "score"]
                    }
                )
            )

            # Parse structured JSON response
            result = json.loads(response.text)
            score = float(result["score"])
            logger.info(f"Gemini score: {score} | Reasoning: {result['reasoning'][:100]}...")
            return max(0, min(100, score))

        except json.JSONDecodeError as e:
            logger.error(f"Gemini JSON parsing error: {e}")
            return 70.0  # Default neutral score
        except Exception as e:
            logger.error(f"Gemini evaluation error: {e}")
            raise

    async def _evaluate_with_claude(self, script: str, niche: str) -> float:
        """Evaluate with Claude 3.5 Sonnet (psychology expertise with structured output)"""
        try:
            message = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": f"""You are a psychology expert analyzing advertising effectiveness for {niche}.

Script to evaluate:
{script}

Think step by step and rate this script on a scale of 0-100 based on psychological principles:
1. Pain point clarity (how well it identifies customer pain) - 30 points
2. Emotional triggers (fear, desire, urgency) - 25 points
3. Social proof potential - 20 points
4. Authority signals - 15 points
5. Scarcity/urgency - 10 points

First, analyze each criterion with your reasoning, then provide the final score.

You MUST respond with valid JSON in this exact format:
{{
    "reasoning": "Your step-by-step analysis of each psychological principle",
    "score": 85.5
}}"""
                }]
            )

            # Parse structured JSON response
            text = message.content[0].text
            result = json.loads(text)
            score = float(result["score"])
            logger.info(f"Claude score: {score} | Reasoning: {result['reasoning'][:100]}...")
            return max(0, min(100, score))

        except json.JSONDecodeError as e:
            logger.error(f"Claude JSON parsing error: {e}, response: {text}")
            return 70.0  # Default neutral score
        except Exception as e:
            logger.error(f"Claude evaluation error: {e}")
            raise

    async def _evaluate_with_gpt(self, script: str, niche: str) -> float:
        """Evaluate with GPT-4o (logic verification with structured output)"""
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o",
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[{
                    "role": "system",
                    "content": f"You are a logical analyzer evaluating ad scripts for {niche}. Focus on structure, coherence, and clarity. Always respond with valid JSON."
                }, {
                    "role": "user",
                    "content": f"""Think step by step and rate this script on a scale of 0-100 based on logical structure:
1. Clear narrative flow - 30 points
2. Logical argument progression - 25 points
3. Absence of contradictions - 20 points
4. Fact-checkable claims - 15 points
5. Clear next steps - 10 points

Script:
{script}

First, analyze each criterion with detailed reasoning, then provide the final score.

You MUST respond with valid JSON in this exact format:
{{
    "reasoning": "Your step-by-step logical analysis of each criterion",
    "score": 85.5
}}"""
                }]
            )

            # Parse structured JSON response
            text = response.choices[0].message.content
            result = json.loads(text)
            score = float(result["score"])
            logger.info(f"GPT-4o score: {score} | Reasoning: {result['reasoning'][:100]}...")
            return max(0, min(100, score))

        except json.JSONDecodeError as e:
            logger.error(f"GPT-4o JSON parsing error: {e}, response: {text}")
            return 70.0  # Default neutral score
        except Exception as e:
            logger.error(f"GPT-4o evaluation error: {e}")
            raise

    async def _evaluate_with_deepctr(self, script: str, niche: str) -> float:
        """Evaluate with DeepCTR (data-driven prediction)"""
        try:
            # If ML service URL not configured, return neutral score
            if not self.deepctr_url:
                logger.warning("ML_SERVICE_URL not configured - using neutral DeepCTR score")
                return 70.0

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.deepctr_url}/predict/ctr",
                    json={
                        "content": script,
                        "niche": niche,
                        "return_score": True
                    }
                )
                response.raise_for_status()
                data = response.json()

                # DeepCTR returns predicted CTR (0-1), convert to 0-100 score
                predicted_ctr = data.get("predicted_ctr", 0.02)
                # Scale: 2% CTR = 70, 5% CTR = 95, 1% CTR = 50
                score = 50 + (predicted_ctr - 0.01) * 1500
                score = max(0, min(100, score))

                logger.info(f"DeepCTR score: {score} (CTR: {predicted_ctr:.4f})")
                return score

        except httpx.HTTPError as e:
            logger.error(f"DeepCTR HTTP error: {e}")
            return 70.0  # Fallback to neutral score
        except Exception as e:
            logger.error(f"DeepCTR evaluation error: {e}")
            raise

    def _generate_feedback(self, breakdown: Dict[str, float], script: str, errors: List[str]) -> str:
        """Generate actionable feedback based on scores"""
        weakest = min(breakdown, key=breakdown.get)
        weakest_score = breakdown[weakest]

        feedback_parts = []

        if weakest_score < 75:
            suggestions = {
                "gemini_3_pro": "Strengthen hook and emotional appeal in first 3 seconds",
                "claude_3_5": "Add more psychological triggers (pain, urgency, social proof)",
                "gpt_4o": "Improve logical flow and clarity of argument",
                "deep_ctr": "Optimize for higher CTR (simplify message, stronger CTA)"
            }
            feedback_parts.append(f"⚠️ Weakest area: {weakest} ({weakest_score:.0f}/100)")
            feedback_parts.append(f"💡 Suggestion: {suggestions.get(weakest, 'Review and strengthen')}")

        # Check for consistency
        score_variance = max(breakdown.values()) - min(breakdown.values())
        if score_variance > 20:
            feedback_parts.append("⚖️ Inconsistent scores across evaluators - script may need more clarity")

        if errors:
            feedback_parts.append(f"⚠️ {len(errors)} evaluator(s) failed - confidence reduced")

        if not feedback_parts:
            feedback_parts.append("✅ Strong performance across all evaluators")

        return " | ".join(feedback_parts)

    def _generate_cache_key(self, script: str, niche: str) -> str:
        """Generate cache key for evaluation"""
        import hashlib
        content = f"{script}:{niche}"
        return hashlib.sha256(content.encode()).hexdigest()

# Singleton instance
council = CouncilEvaluator()
