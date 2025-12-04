
import json

def get_andromeda_hook_prompt(clip_path: str, context: dict = None) -> str:
    """
    Generates a prompt for analyzing the hook of a video ad with Chain-of-Thought reasoning.
    """
    context_str = f"Context: {json.dumps(context)}" if context else ""
    return f"""
    Analyze the first 3 seconds of this video (The Hook).
    {context_str}

    Think step by step:

    STEP 1: Visual Analysis
    - What visual elements appear in the first 3 seconds?
    - Is there any unusual movement, text overlay, or pattern interrupt?
    - Rate visual attention-grabbing power (1-10)

    STEP 2: Audio Analysis
    - What sounds, music, or voiceover is present?
    - Does it create curiosity or pattern interrupt?
    - Rate audio hook strength (1-10)

    STEP 3: Hook Pattern Classification
    Identify the specific 'Hook Type' used from this list of 2025 Winning Patterns:
    1. The "Pattern Interrupt" (Visual glitch, weird movement)
    2. The "Negative Hook" ("Stop doing this", "Don't buy X until")
    3. The "Result Tease" (End result shown first)
    4. The "ASMR/Satisfying" (Visual texture/sound)
    5. The "Question" (Direct address to pain point)

    STEP 4: Overall Assessment
    - Calculate final hook strength based on visual + audio + pattern effectiveness
    - Identify specific improvement opportunities

    Output JSON with your reasoning included:
    {{
        "reasoning": "Your step-by-step analysis from steps 1-4",
        "hook_type": "string",
        "hook_strength": 0-10,
        "visual_description": "string",
        "audio_description": "string",
        "improvement_suggestion": "string"
    }}
    """

def get_andromeda_roas_prompt(ad_data: dict) -> str:
    """
    Generates a prompt for predicting ROAS based on ad components with Chain-of-Thought reasoning.
    """
    return f"""
    Act as a Meta Ads Expert (Andromeda Algorithm).
    Predict the ROAS (Return on Ad Spend) for this video ad based on its components.

    Ad Data:
    {json.dumps(ad_data, indent=2)}

    Think step by step through each winning pattern:

    STEP 1: Hook Analysis (Max 20 points)
    - Is the hook strong enough to stop the scroll in <3 seconds?
    - Does it use proven pattern interrupts?
    - Score: __/20

    STEP 2: Visual Energy Assessment (Max 20 points)
    - Are visuals high-energy and dynamic?
    - Is there movement and visual interest throughout?
    - Score: __/20

    STEP 3: Platform Fit Evaluation (Max 15 points)
    - Does it feel native to the platform (UGC style)?
    - Avoids "ad-like" production that users skip?
    - Score: __/15

    STEP 4: Pacing & Editing (Max 10 points)
    - Are there cuts/transitions every 2-3 seconds?
    - Does it maintain attention throughout?
    - Score: __/10

    STEP 5: Call-to-Action Clarity (Max 10 points)
    - Is the CTA clear and compelling?
    - Is it presented at the optimal moment?
    - Score: __/10

    STEP 6: Audio Effectiveness (Max 10 points)
    - Trending audio or clear voiceover?
    - Does audio reinforce the message?
    - Score: __/10

    STEP 7: Final Calculations
    - Total Score: Sum of all steps (0-100)
    - Predicted CTR Range based on score
    - Overall viral potential assessment
    - List top 3 strengths and weaknesses

    Output JSON with complete reasoning:
    {{
        "reasoning": "Your detailed step-by-step analysis from steps 1-7, showing your work",
        "predicted_roas_score": 0-100,
        "predicted_ctr": "0.0% - 0.0%",
        "strengths": ["string"],
        "weaknesses": ["string"],
        "viral_potential": "Low/Medium/High"
    }}
    """

def get_competitor_analysis_prompt(niche: str = "fitness", platform: str = "instagram") -> str:
    """
    Generates a prompt for analyzing competitor ads in a specific niche with Chain-of-Thought reasoning.
    """
    return f"""
    Analyze the current top-performing ads in the '{niche}' niche on {platform}.

    Think step by step through the competitive landscape:

    STEP 1: Hook Pattern Analysis
    - What are the most common hook types in top ads?
    - Which specific opening lines/visuals are being used repeatedly?
    - What makes these hooks effective for this niche?
    - Identify 3-5 specific winning hook patterns

    STEP 2: Visual Style Assessment
    - What is the dominant visual style? (UGC vs. High Production)
    - What camera angles, lighting, and editing techniques are trending?
    - How do top performers make their content feel "native" to {platform}?
    - What visual elements correlate with high engagement?

    STEP 3: CTA Strategy Breakdown
    - What types of CTAs are top ads using? (Link, Comment, DM, etc.)
    - At what point in the video do they present the CTA?
    - What language/psychology do they use in CTAs?
    - Which CTA approaches get the best response?

    STEP 4: Market Gap & Opportunity Identification
    - What patterns are OVERSATURATED (avoid these)?
    - What angles are UNDERUTILIZED (opportunities)?
    - What unique angle would stand out in this niche?
    - Based on all analysis, what's the recommended strategic approach?

    STEP 5: Synthesis & Recommendations
    - Summarize the 3-5 most important insights
    - Provide specific, actionable recommendations
    - Suggest a differentiated angle that leverages winning patterns but avoids saturation

    Output JSON with your complete reasoning:
    {{
        "reasoning": "Your detailed step-by-step analysis from steps 1-5",
        "winning_hooks": ["string", "string", "string"],
        "visual_trends": ["string", "string", "string"],
        "cta_strategies": ["string", "string", "string"],
        "oversaturated_patterns": ["string"],
        "opportunities": ["string"],
        "recommended_angle": "string - specific strategic recommendation with rationale"
    }}
    """
