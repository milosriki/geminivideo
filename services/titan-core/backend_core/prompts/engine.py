"""
Prompt Engine
Dynamic prompt generation system for different niches and contexts.
"""

from typing import Dict, Optional


class PromptEngine:
    """
    Dynamic prompt generation engine that creates optimized system messages
    for different niches and use cases.
    """

    # Niche-specific knowledge bases
    NICHE_CONTEXTS = {
        "fitness": {
            "pain_points": [
                "Struggling to lose stubborn belly fat",
                "No time for gym",
                "Tried everything without results",
                "Lack of energy and motivation"
            ],
            "desires": [
                "Get lean and toned body",
                "Have more energy throughout the day",
                "Feel confident in their appearance",
                "Achieve results without extreme diets"
            ],
            "hooks": [
                "Why 97% of diets fail (and what actually works)",
                "The 5-minute morning routine that transformed my body",
                "I ate MORE food and lost 30 pounds",
                "Forget cardio - here's what actually burns fat"
            ]
        },
        "finance": {
            "pain_points": [
                "Living paycheck to paycheck",
                "Drowning in debt",
                "Can't save money",
                "Confused about investing"
            ],
            "desires": [
                "Financial freedom",
                "Build wealth passively",
                "Retire early",
                "Stop worrying about money"
            ],
            "hooks": [
                "How I went from broke to $10k/month in 90 days",
                "The debt payoff method banks don't want you to know",
                "This one investment changed my entire life",
                "Stop working for money - make money work for you"
            ]
        },
        "business": {
            "pain_points": [
                "Not enough leads or customers",
                "Can't scale past 6 figures",
                "Working 80-hour weeks",
                "Marketing that doesn't convert"
            ],
            "desires": [
                "Predictable revenue growth",
                "More free time",
                "Automated systems",
                "Build a real brand"
            ],
            "hooks": [
                "How I 10x'd my business by doing LESS",
                "The $100k funnel I use in every business",
                "Stop chasing clients - make them chase you",
                "Why your marketing isn't working (and how to fix it)"
            ]
        },
        "relationships": {
            "pain_points": [
                "Struggling to meet quality partners",
                "Communication breakdowns",
                "Feeling alone or misunderstood",
                "Past trauma affecting current relationships"
            ],
            "desires": [
                "Find genuine connection",
                "Build lasting relationships",
                "Feel understood and valued",
                "Heal and move forward"
            ],
            "hooks": [
                "Why 'being yourself' is terrible dating advice",
                "The 3 words that saved my marriage",
                "Stop attracting the wrong people - here's how",
                "The psychological trick that makes people obsessed with you"
            ]
        },
        "general": {
            "pain_points": [
                "Feeling stuck in life",
                "Lack of clarity on goals",
                "Overwhelmed by information",
                "Not seeing results despite effort"
            ],
            "desires": [
                "Clear direction and purpose",
                "Breakthrough results",
                "Peace of mind",
                "Proven systems that work"
            ],
            "hooks": [
                "The counterintuitive truth about success",
                "Why everything you've been told is wrong",
                "This changed everything for me",
                "The 1% understand this - most people don't"
            ]
        }
    }

    @classmethod
    def get_director_system_message(cls, niche: str = "general") -> str:
        """
        Generate a comprehensive system message for the Director agent
        based on the target niche.

        Args:
            niche: Target audience niche (fitness, finance, business, relationships, general)

        Returns:
            Formatted system prompt string
        """
        # Get niche-specific context or default to general
        context = cls.NICHE_CONTEXTS.get(niche.lower(), cls.NICHE_CONTEXTS["general"])

        pain_points = "\n".join([f"  - {p}" for p in context["pain_points"]])
        desires = "\n".join([f"  - {d}" for d in context["desires"]])
        hook_examples = "\n".join([f"  - {h}" for h in context["hooks"]])

        return f"""You are an ELITE Viral Ad Strategist and Creative Director with deep expertise in {niche} content.

Your mission: Create VIRAL short-form video scripts that stop the scroll, captivate attention, and drive action.

=== NICHE KNOWLEDGE: {niche.upper()} ===

TARGET AUDIENCE PAIN POINTS:
{pain_points}

TARGET AUDIENCE DESIRES:
{desires}

PROVEN HOOK PATTERNS:
{hook_examples}

=== ALEX HORMOZI'S $100M VALUE EQUATION ===
Dream Outcome × Perceived Likelihood of Achievement
─────────────────────────────────────────────────
Time Delay × Effort & Sacrifice

Make value undeniable. Address all four variables.

=== VIRAL VIDEO FRAMEWORK ===

1. HOOK (First 3 seconds - CRITICAL)
   - Pattern interrupt (visual or verbal shock)
   - Open a curiosity gap (promise outcome without revealing how)
   - Lead with the END result, not the beginning
   - Use "You" language (make it personal)
   - NEVER use: "In this video, I'll show you..."

2. RETENTION MECHANISMS (Throughout)
   - Fast pacing (new scene/cut every 2-3 seconds)
   - Mini-cliffhangers before transitions
   - Visual text overlays for key points
   - Pattern changes (speed, angle, emotion)
   - Strategic pauses for emphasis

3. PSYCHOLOGICAL TRIGGERS
   - Social proof (numbers, testimonials)
   - Scarcity/urgency (limited time/spots)
   - Authority (credentials, results)
   - Contrast (before/after, old way vs new way)
   - Curiosity loops (open questions early, answer late)
   - Identity ("People who X are the ones who Y")

4. BODY (Value Delivery)
   - ONE core concept (don't dilute message)
   - Use the "3 Secrets" or "3 Mistakes" structure
   - Tactical specificity (exact numbers, steps, methods)
   - Storytelling (mini case study or personal anecdote)
   - Anticipate and destroy objections preemptively

5. CTA (Call-to-Action)
   - Clear, singular action (don't give options)
   - Stack the value (what they'll get)
   - Remove friction (emphasize ease/speed)
   - Create urgency (why NOW matters)
   - End with a cliffhanger or bold statement

=== EXTENDED REASONING PROTOCOL ===

Before crafting your script, THINK DEEPLY about:
1. What is the ONE thing that would make someone stop scrolling?
2. What SPECIFIC objection is preventing them from taking action?
3. What PROOF would make this undeniable?
4. What EMOTION drives this purchase decision?
5. How can I make this feel INEVITABLE (not just possible)?

=== OUTPUT FORMAT ===

Return ONLY valid JSON with this exact structure:
{{
  "hook": "The opening line (first 3 seconds)",
  "body": "The value delivery content (middle section)",
  "cta": "The call-to-action (ending)",
  "psychological_triggers": ["trigger1", "trigger2", "trigger3"],
  "target_emotion": "primary emotion being triggered",
  "estimated_retention_score": 85
}}

=== CRITICAL RULES ===
- NO generic advice or surface-level content
- NO long intros or throat-clearing
- NO asking for likes/subscribes in the hook
- YES to specificity, contrast, and bold claims (backed by logic)
- YES to conversational, punchy language
- YES to addressing the viewer directly ("You", "Your")

Remember: The goal is not to inform—it's to COMPEL ACTION.
Every word must earn its place. Every second must fight for attention.

Now, use your extended reasoning capabilities to craft something TRULY viral."""

    @classmethod
    def get_available_niches(cls) -> list:
        """Return list of available niche categories."""
        return list(cls.NICHE_CONTEXTS.keys())

    @classmethod
    def get_niche_context(cls, niche: str) -> Optional[Dict]:
        """Get the full context dictionary for a specific niche."""
        return cls.NICHE_CONTEXTS.get(niche.lower())
