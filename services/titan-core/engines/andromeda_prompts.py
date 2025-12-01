
import json

def get_andromeda_hook_prompt(clip_path: str, context: dict = None) -> str:
    """
    Generates a prompt for analyzing the hook of a video ad.
    """
    context_str = f"Context: {json.dumps(context)}" if context else ""
    return f"""
    Analyze the first 3 seconds of this video (The Hook).
    {context_str}
    
    Identify the specific 'Hook Type' used from this list of 2025 Winning Patterns:
    1. The "Pattern Interrupt" (Visual glitch, weird movement)
    2. The "Negative Hook" ("Stop doing this", "Don't buy X until")
    3. The "Result Tease" (End result shown first)
    4. The "ASMR/Satisfying" (Visual texture/sound)
    5. The "Question" (Direct address to pain point)
    
    Output JSON:
    {{
        "hook_type": "string",
        "hook_strength": 0-10,
        "visual_description": "string",
        "audio_description": "string",
        "improvement_suggestion": "string"
    }}
    """

def get_andromeda_roas_prompt(ad_data: dict) -> str:
    """
    Generates a prompt for predicting ROAS based on ad components.
    """
    return f"""
    Act as a Meta Ads Expert (Andromeda Algorithm).
    Predict the ROAS (Return on Ad Spend) for this video ad based on its components.
    
    Ad Data:
    {json.dumps(ad_data, indent=2)}
    
    Scoring Rubric (2025 Meta Winning Patterns):
    - High Energy Visuals: +20 points
    - Clear CTA: +10 points
    - Native Platform Feel (UGC): +15 points
    - Strong Hook (<3s): +20 points
    - Pacing (Cut every 2-3s): +10 points
    - Audio (Trending/Clear Voiceover): +10 points
    
    Output JSON:
    {{
        "predicted_roas_score": 0-100,
        "predicted_ctr": "0.0% - 0.0%",
        "strengths": ["string"],
        "weaknesses": ["string"],
        "viral_potential": "Low/Medium/High",
        "reasoning": "string"
    }}
    """

def get_competitor_analysis_prompt(niche: str = "fitness", platform: str = "instagram") -> str:
    """
    Generates a prompt for analyzing competitor ads in a specific niche.
    """
    return f"""
    Analyze the current top-performing ads in the '{niche}' niche on {platform}.
    Identify the common patterns for:
    1. Hooks (What is stopping the scroll?)
    2. Visual Style (UGC vs. High Production)
    3. CTAs (What are they asking users to do?)
    
    Output JSON:
    {{
        "winning_hooks": ["string"],
        "visual_trends": ["string"],
        "cta_strategies": ["string"],
        "recommended_angle": "string"
    }}
    """
