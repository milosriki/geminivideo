"""
Titan Knowledge Base - Dynamic context provider for ad script generation
Loads knowledge from config files with hot-reloading support
"""
import os
import json
import yaml
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class TitanKnowledge:
    """
    Centralized knowledge base for Titan-Core engine.
    Loads from config files and provides context blocks for prompts.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize knowledge base from config files.

        Args:
            config_path: Path to shared/config directory. If None, auto-detect.
        """
        # Auto-detect config path if not provided
        if config_path is None:
            # Try relative path from titan-core service
            current_dir = Path(__file__).parent.parent.parent.parent
            config_path = current_dir / "shared" / "config"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise ValueError(f"Config path does not exist: {config_path}")

        self.config_path = config_path
        self._triggers: Dict[str, Any] = {}
        self._personas: List[Dict[str, Any]] = []
        self._weights: Dict[str, Any] = {}
        self._last_reload: Optional[datetime] = None
        self._reload_interval = 300  # 5 minutes

        # Initial load
        self.reload()

        logger.info(f"Titan Knowledge Base initialized from {config_path}")

    def reload(self) -> None:
        """Reload all config files from disk"""
        try:
            # Load triggers config
            triggers_file = self.config_path / "triggers_config.json"
            if triggers_file.exists():
                with open(triggers_file, 'r') as f:
                    self._triggers = json.load(f)
                logger.info(f"Loaded {len(self._triggers)} trigger categories")
            else:
                logger.warning(f"Triggers config not found: {triggers_file}")

            # Load personas config
            personas_file = self.config_path / "personas.json"
            if personas_file.exists():
                with open(personas_file, 'r') as f:
                    data = json.load(f)
                    self._personas = data.get('personas', [])
                logger.info(f"Loaded {len(self._personas)} personas")
            else:
                logger.warning(f"Personas config not found: {personas_file}")

            # Load weights config
            weights_file = self.config_path / "weights.yaml"
            if weights_file.exists():
                with open(weights_file, 'r') as f:
                    self._weights = yaml.safe_load(f)
                logger.info(f"Loaded weights version {self._weights.get('version', 'unknown')}")
            else:
                logger.warning(f"Weights config not found: {weights_file}")

            self._last_reload = datetime.utcnow()

        except Exception as e:
            logger.error(f"Failed to reload knowledge base: {e}", exc_info=True)
            raise

    def _check_reload(self) -> None:
        """Auto-reload if cache expired"""
        if self._last_reload is None:
            return

        elapsed = (datetime.utcnow() - self._last_reload).total_seconds()
        if elapsed > self._reload_interval:
            logger.info("Auto-reloading knowledge base (cache expired)")
            self.reload()

    def get_context_block(self, niche: str = "fitness") -> str:
        """
        Generate formatted context block for prompt engineering.

        Args:
            niche: Business vertical (fitness, e-commerce, education, etc.)

        Returns:
            Formatted multi-line string with knowledge context
        """
        self._check_reload()

        # Build context sections
        sections = []

        # 1. Hormozi's Direct Response Rules (Universal)
        sections.append(self._get_hormozi_rules())

        # 2. Psychology Triggers
        sections.append(self._get_psychology_section(niche))

        # 3. Persona Intelligence
        sections.append(self._get_persona_section(niche))

        # 4. Meta Andromeda Patterns (2025 Winners)
        sections.append(self._get_meta_patterns())

        # 5. Scoring Weights
        sections.append(self._get_weights_section())

        return "\n\n".join(sections)

    def _get_hormozi_rules(self) -> str:
        """Alex Hormozi's proven direct response framework"""
        return """### HORMOZI'S DIRECT RESPONSE RULES (Proven Framework):

1. **Hook (0-3s)**: Pattern interrupt - something visually shocking or contrarian
   - Use numbers ("I lost 47 pounds in 90 days")
   - Ask provocative questions ("What if everything you know about fitness is wrong?")
   - Show visual transformation (before/after in first frame)

2. **Pain Agitation (3-10s)**: Make them FEEL the problem
   - "You're tired of starting over every Monday..."
   - "Your knees hurt, your energy is gone..."
   - Use visceral language (pain, struggle, frustration)

3. **Value Proposition (10-20s)**: The NEW mechanism
   - NOT just "lose weight" - that's commoditized
   - "A 15-minute protocol that targets stubborn fat WITHOUT cardio"
   - Make it sound proprietary and specific

4. **Proof (20-30s)**: Social proof or authority
   - "This worked for 2,847 clients in 90 days"
   - Show real results (numbers, testimonials)
   - Establish credibility fast

5. **Call-to-Action (30-45s)**: Clear next step with urgency
   - "Link in bio - first 50 people get free meal plan"
   - "DM me 'READY' to start Monday"
   - Create scarcity (time-limited, quantity-limited)

**CRITICAL**: Every second must EARN the next second of attention."""

    def _get_psychology_section(self, niche: str) -> str:
        """Psychology triggers from config"""
        driver_keywords = self._triggers.get('driver_keywords', {})
        niche_triggers = self._triggers.get(f'{niche}_triggers', {})

        section = f"### PSYCHOLOGY TRIGGERS ({niche.upper()}):\n\n"

        # Universal drivers
        if driver_keywords:
            section += "**Universal Drivers:**\n"
            for category, keywords in driver_keywords.items():
                keywords_str = ", ".join(keywords[:5])  # First 5 examples
                section += f"- {category.replace('_', ' ').title()}: {keywords_str}...\n"
            section += "\n"

        # Niche-specific triggers
        if niche_triggers:
            section += f"**{niche.title()}-Specific Triggers:**\n"
            for category, keywords in niche_triggers.items():
                keywords_str = ", ".join(keywords[:5])
                section += f"- {category.replace('_', ' ').title()}: {keywords_str}...\n"

        return section

    def _get_persona_section(self, niche: str) -> str:
        """Persona intelligence from config"""
        if not self._personas:
            return ""

        section = f"### TARGET PERSONAS ({niche.upper()}):\n\n"

        # Show top 3 personas most relevant to niche
        relevant_personas = self._personas[:3]

        for persona in relevant_personas:
            section += f"**{persona.get('name', 'Unknown')}** (Age {persona.get('age_range', [0,0])[0]}-{persona.get('age_range', [0,0])[1]}):\n"
            section += f"  - Pain Points: {', '.join(persona.get('pain_points', [])[:3])}\n"
            section += f"  - Goals: {', '.join(persona.get('goals', [])[:3])}\n"
            section += f"  - Keywords: {', '.join(persona.get('keywords', [])[:5])}...\n\n"

        return section

    def _get_meta_patterns(self) -> str:
        """Meta Andromeda 2025 winning patterns"""
        return """### META ANDROMEDA PATTERNS (2025 Winners):

**Top Performing Hooks (Live Data):**
1. **Before/After Split Screen** - 4.8% CTR average
   - Visual: Side-by-side transformation in first frame
   - Caption: "90 days. Same person. What changed?"

2. **Contrarian Statement** - 4.2% CTR average
   - Visual: Person looking directly at camera
   - Caption: "Cardio is keeping you fat. Here's why..."

3. **Rapid Results Promise** - 3.9% CTR average
   - Visual: Stopwatch or calendar visual
   - Caption: "Lose your first 10 lbs in 14 days (guaranteed)"

4. **Problem Agitation** - 3.7% CTR average
   - Visual: Frustrated person (relatable moment)
   - Caption: "Tried keto, paleo, IF... Still stuck at 180?"

5. **Social Proof Avalanche** - 3.5% CTR average
   - Visual: Grid of client results
   - Caption: "2,847 transformations. You're next."

**IMPORTANT**: First 3 seconds must create "scroll stop" - use motion, numbers, or questions."""

    def _get_weights_section(self) -> str:
        """Scoring weights from config"""
        psych_weights = self._weights.get('psychology_weights', {})
        hook_weights = self._weights.get('hook_weights', {})

        section = "### SCORING CRITERIA:\n\n"

        if psych_weights:
            section += "**Psychology Score (Weighted):**\n"
            for factor, weight in psych_weights.items():
                section += f"- {factor.replace('_', ' ').title()}: {weight*100:.0f}%\n"
            section += "\n"

        if hook_weights:
            section += "**Hook Strength (Weighted):**\n"
            for factor, weight in hook_weights.items():
                section += f"- {factor.replace('_', ' ').title()}: {weight*100:.0f}%\n"

        return section

    def get_triggers(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get trigger keywords by category.

        Args:
            category: Specific category (e.g., 'pain_points', 'urgency')
                     If None, returns all triggers
        """
        self._check_reload()

        if category:
            return self._triggers.get('driver_keywords', {}).get(category, [])
        return self._triggers

    def get_personas(self, fitness_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get personas filtered by fitness level.

        Args:
            fitness_level: Filter by level (beginner, intermediate, advanced)
        """
        self._check_reload()

        if fitness_level:
            return [p for p in self._personas if fitness_level in p.get('fitness_level', '')]
        return self._personas

    def get_weights(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get scoring weights by category.

        Args:
            category: Specific category (e.g., 'psychology_weights', 'hook_weights')
                     If None, returns all weights
        """
        self._check_reload()

        if category:
            return self._weights.get(category, {})
        return self._weights

    def match_persona(self, keywords: List[str]) -> Optional[Dict[str, Any]]:
        """
        Match input keywords to best-fit persona.

        Args:
            keywords: List of keywords from user input

        Returns:
            Best matching persona dict or None
        """
        self._check_reload()

        if not keywords or not self._personas:
            return None

        # Score each persona by keyword overlap
        best_match = None
        best_score = 0

        keywords_lower = [k.lower() for k in keywords]

        for persona in self._personas:
            persona_keywords = [k.lower() for k in persona.get('keywords', [])]
            persona_pain = [p.lower() for p in persona.get('pain_points', [])]
            persona_goals = [g.lower() for g in persona.get('goals', [])]

            all_persona_text = ' '.join(persona_keywords + persona_pain + persona_goals)

            # Count matches
            score = sum(1 for kw in keywords_lower if kw in all_persona_text)

            if score > best_score:
                best_score = score
                best_match = persona

        return best_match if best_score > 0 else None

    def get_niche_config(self, niche: str) -> Dict[str, Any]:
        """
        Get complete configuration for a specific niche.

        Args:
            niche: Business vertical (fitness, e-commerce, education, etc.)

        Returns:
            Dictionary with triggers, personas, and weights for the niche
        """
        self._check_reload()

        return {
            'niche': niche,
            'triggers': self._triggers.get(f'{niche}_triggers', {}),
            'driver_keywords': self._triggers.get('driver_keywords', {}),
            'personas': self.get_personas(),
            'weights': self._weights,
            'last_updated': self._last_reload.isoformat() if self._last_reload else None
        }

# Singleton instance
# Auto-detect config path relative to this file
_config_path = Path(__file__).parent.parent.parent.parent / "shared" / "config"

try:
    titan_knowledge = TitanKnowledge(config_path=str(_config_path))
    logger.info("✅ Titan Knowledge singleton initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Titan Knowledge: {e}")
    # Create with minimal functionality in case of config issues
    titan_knowledge = None
    raise
