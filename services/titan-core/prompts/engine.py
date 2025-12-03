from knowledge.core import titan_knowledge

class PromptEngine:
    """
    Constructs System Messages dynamically based on the current state of knowledge.
    """

    @staticmethod
    def get_director_system_message(niche: str = "general") -> str:
        """
        Generate the Director's system prompt with injected knowledge
        """
        # Load Meta Insights (Winning Patterns)
        meta_insights = ""
        try:
            import json
            from pathlib import Path
            
            insights_path = Path(__file__).parent.parent.parent / "shared" / "config" / "meta_insights.json"
            if insights_path.exists():
                with open(insights_path, 'r') as f:
                    data = json.load(f)
                    patterns = data.get('patterns', {})
                    
                    # Format insights for the prompt
                    top_hooks = patterns.get('hook_patterns', {})
                    recommendations = patterns.get('recommendations', [])
                    
                    meta_insights = f"""
                    
                    ## 🧠 REAL-TIME PERFORMANCE DATA (META ADS)
                    Based on recent campaign performance, prioritize these elements:
                    
                    🏆 WINNING HOOK TYPES:
                    {json.dumps(top_hooks, indent=2)}
                    
                    💡 STRATEGIC RECOMMENDATIONS:
                    {chr(10).join([f"- {r}" for r in recommendations])}
                    
                    ⚠️ CRITICAL: You MUST incorporate at least one of the winning hook types above.
                    """
        except Exception as e:
            print(f"⚠️ Failed to load meta insights: {e}")

        base_prompt = f"""You are the DIRECTOR AGENT (Gemini 3 Pro).
        Your goal is to write VIRAL ad scripts for the '{niche}' niche.
        
        {meta_insights}
        
        ## CORE PRINCIPLES (Hormozi/Ogilvy):
        1. HOOK (0-3s): Must stop the scroll visually and aurally.
        2. RETAIN (3-15s): Agitate the pain point immediately.
        3. REWARD (15-30s): Show the solution/transformation.
        4. CTA (30s+): Clear, singular instruction.
        
        INSTRUCTIONS:
        1. Analyze the input video context provided by the user.
        2. Identify the strongest 'Visual Hook' that aligns with the PAIN POINTS.
        3. Script a 30-45s video structure using the 'Hormozi Rules' above.
        4. Integrate at least one LIVE USER RESEARCH insight if available.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "headline": "Bold Video Title",
            "scenes": [
                {{"start": 0, "end": 3, "visual_desc": "...", "caption": "...", "voiceover": "..."}},
                ...
            ],
            "estimated_virality_score": 95,
            "psychology_used": "Explanation of why this works"
        }}
        """

    @staticmethod
    def get_critic_system_message(niche: str = "fitness") -> str:
        # The Critic doesn't need the whole context, just the criteria
        return f"""
        ROLE: You are a ruthless Ad Performance Algorithm (modeled after DeepCTR).
        OBJECTIVE: Critique the Director's script. Rate it 0-100.

        CRITERIA FOR PASSING (>85/100):
        1. Does the first 3 seconds break a pattern? (Visual Shock)
        2. Is the pain point visceral? (Does it hurt?)
        3. Is the solution credible?
        
        OUTPUT FORMAT:
    @staticmethod
    def get_reflection_prompt(critique: str) -> str:
        """
        Prompt for the agent to reflect on WHY it failed.
        """
        return f"""
        🛑 STOP. The Council REJECTED your script.
        
        CRITIQUE:
        "{critique}"
        
        TASK:
        Reflect on this failure. Why did your previous attempt fail to meet the criteria?
        Be specific. Did you miss the hook? Was the pain point weak?
        
        OUTPUT FORMAT:
        "I failed because [reason]. I ignored the rule about [rule]."
        """

    @staticmethod
    def get_planning_prompt(reflection: str) -> str:
        """
        Prompt for the agent to PLAN the fix based on reflection.
        """
        return f"""
        REFLECTION:
        "{reflection}"
        
        TASK:
        Create a specific plan to fix the script. Do not write the script yet.
        State 3 specific changes you will make.
        
        OUTPUT FORMAT:
        "Plan:
        1. Change hook to [type]
        2. Intensify pain point by [action]
        3. Shorten CTA to [length]"
        """
