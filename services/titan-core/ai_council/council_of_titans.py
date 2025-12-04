import os
import re
import asyncio
from typing import Dict, Any

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


class CouncilOfTitans:
    """
    The Ultimate Ensemble:
    1. Gemini 2.0 Flash Thinking (Newest - Extended Reasoning) - 40%
    2. GPT-4o (Logic/Structure) - 20%
    3. Claude 3.5 Sonnet (Nuance/Psychology) - 30%
    4. DeepCTR (Data/Math) - 10%
    """
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
        
        # Use newest Gemini 3 Pro (Preview)
        self.gemini_model = os.getenv("GEMINI_MODEL_ID", "gemini-3-pro-preview")
        self.display_name = "Gemini 3 Pro (Preview)"

        print(f"🏛️ COUNCIL: Initialized with {self.display_name}")

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
        """Gemini 2.0 Flash Thinking - Newest model with extended reasoning"""
        if not genai:
            return {"score": 75.0, "source": "Gemini (Not Installed)"}
            
        try:
            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content(
                f"You are a Viral Ad Strategist with deep reasoning capabilities. Analyze this script thoroughly and rate it 0-100 based on hook strength, psychological triggers, pacing, and viral potential. Return ONLY a number.\n\nSCRIPT:\n{script}"
            )
            # Handle thinking models which may have different response structure
            score_text = response.text.strip()
            # Extract numbers that look like scores (integers or decimals, not version numbers like 2.0)
            # Match standalone numbers or numbers at the beginning/end of the text
            numbers = re.findall(r'(?<![.\d])\d{1,3}(?:\.\d+)?(?![.\d])', score_text)
            score = float(numbers[0]) if numbers else 75.0
            # Clamp to valid range
            score = max(0.0, min(100.0, score))
            return {"score": score, "source": "Gemini 2.0 Thinking"}
        except Exception as e:
            print(f"⚠️ Gemini Error: {e}")
            return {"score": 75.0, "source": "Gemini 2.0 Thinking (Fallback)"}

    async def get_gpt4_critique(self, script: str) -> Dict[str, Any]:
        if not self.openai_client:
            return {"score": 75.0, "source": "GPT-4o (Disabled)"}
            
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Viral Ad Critic. Rate this script 0-100 based on logical structure, hook clarity, and CTA strength. Return ONLY a number."},
                    {"role": "user", "content": script}
                ]
            )
            score = float(response.choices[0].message.content.strip())
            return {"score": score, "source": "GPT-4o"}
        except Exception as e:
            print(f"⚠️ GPT-4o Error: {e}")
            return {"score": 75.0, "source": "GPT-4o (Fallback)"}

    async def get_claude_critique(self, script: str) -> Dict[str, Any]:
        if not self.anthropic_client:
            return {"score": 75.0, "source": "Claude 3.5 (Disabled)"}
            
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                messages=[
                    {"role": "user", "content": f"You are a Psychology Expert. Rate this ad script 0-100 based on emotional resonance and persuasion. Return ONLY a number.\n\nSCRIPT:\n{script}"}
                ]
            )
            score = float(response.content[0].text.strip())
            return {"score": score, "source": "Claude 3.5"}
        except Exception as e:
            print(f"⚠️ Claude Error: {e}")
            return {"score": 75.0, "source": "Claude 3.5 (Fallback)"}

    async def evaluate_script(self, script: str, visual_features: dict = None) -> Dict[str, Any]:
        """
        Runs the Council. Returns weighted average score.
        """
        print("🏛️ THE COUNCIL IS CONVENING...")
        
        # 1. Run ALL LLMs in Parallel (including Gemini 2.0 Thinking)
        gemini_task = self.get_gemini_critique(script)
        gpt_task = self.get_gpt4_critique(script)
        claude_task = self.get_claude_critique(script)
        
        # 2. Run DeepCTR (Heuristic-based scoring)
        if not visual_features:
            visual_features = {"has_human_face": True, "hook_type": "pattern_interrupt"}

        # Calculate DeepCTR score using heuristic function
        deep_ctr_normalized = self._calculate_deep_ctr_score(visual_features)
        
        # 3. Gather Results
        gemini_res, gpt_res, claude_res = await asyncio.gather(gemini_task, gpt_task, claude_task)
        
        # 4. Calculate Weighted Score
        # Gemini 2.0 Thinking (Newest + Extended Reasoning): 40%
        # Claude (Psych): 30%
        # GPT (Logic): 20%
        # DeepCTR (Data): 10%
        final_score = (
            gemini_res['score'] * 0.40 + 
            claude_res['score'] * 0.30 + 
            gpt_res['score'] * 0.20 + 
            deep_ctr_normalized * 0.10
        )
        
        return {
            "final_score": round(final_score, 1),
            "breakdown": {
                "gemini_2_0_thinking": gemini_res['score'],
                "gpt_4o": gpt_res['score'],
                "claude_3_5": claude_res['score'],
                "deep_ctr": deep_ctr_normalized
            },
            "verdict": "APPROVE" if final_score > 85 else "REJECT"
        }


# Global Council Instance
council = CouncilOfTitans()
