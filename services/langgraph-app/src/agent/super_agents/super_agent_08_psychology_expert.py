"""Super Agent 8: Psychology Expert - Focuses on psychology, triggers, persuasion, money psychology."""

from typing import Any, Dict, List
import logging
from datetime import datetime

from agent.super_agents.base_super_agent import SuperAgent
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class PsychologyExpertAgent(SuperAgent):
    """Expert in psychology - triggers, persuasion, money psychology, conversion psychology."""

    def __init__(self, **kwargs):
        super().__init__(
            name="PsychologyExpertAgent",
            description=(
                "Psychology expert. Focuses on psychological triggers, persuasion techniques, "
                "money psychology, conversion psychology, and emotional triggers for video ads. "
                "Applies psychology principles to maximize ad performance."
            ),
            domains=[
                "Psychological Triggers",
                "Persuasion Techniques",
                "Money Psychology",
                "Conversion Psychology",
                "Emotional Triggers",
                "Behavioral Economics",
                "Consumer Psychology",
            ],
            thinking_steps=5,
            **kwargs,
        )
        self.client = supabase_client.client

    async def _execute_with_reasoning(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        thinking: Dict[str, Any],
    ) -> Any:
        """Execute psychology expert operations."""
        operation = input_data.get("operation", "analyze_psychology")

        if operation == "analyze_psychology":
            return await self._analyze_psychology(input_data, thinking)
        elif operation == "apply_triggers":
            return await self._apply_triggers(input_data, thinking)
        elif operation == "optimize_for_conversion":
            return await self._optimize_for_conversion(input_data, thinking)
        elif operation == "analyze_money_psychology":
            return await self._analyze_money_psychology(input_data, thinking)
        else:
            return {
                "operation": operation,
                "thinking": thinking.get("final_reasoning"),
                "status": "processed",
            }

    async def _analyze_psychology(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze psychological aspects of ad content."""
        content = input_data.get("content", "")
        campaign_data = input_data.get("campaign_data", {})

        # Psychological triggers to check
        triggers = {
            "urgency": self._check_urgency(content),
            "scarcity": self._check_scarcity(content),
            "social_proof": self._check_social_proof(content),
            "authority": self._check_authority(content),
            "reciprocity": self._check_reciprocity(content),
            "commitment": self._check_commitment(content),
            "loss_aversion": self._check_loss_aversion(content),
            "anchoring": self._check_anchoring(content),
        }

        # Money psychology
        money_psychology = {
            "price_anchoring": self._analyze_price_anchoring(campaign_data),
            "value_perception": self._analyze_value_perception(content),
            "payment_friction": self._analyze_payment_friction(campaign_data),
        }

        analysis = {
            "triggers": triggers,
            "money_psychology": money_psychology,
            "recommendations": self._generate_psychology_recommendations(triggers, money_psychology),
            "analyzed_at": datetime.now().isoformat(),
        }

        # Save to memory
        if self.client:
            self.client.table("agent_memory").insert({
                "key": f"psychology_analysis_{datetime.now().isoformat()}",
                "value": analysis,
                "type": "psychology_analysis",
            }).execute()

        return {
            "analysis": analysis,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _apply_triggers(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply psychological triggers to content."""
        content = input_data.get("content", "")
        target_triggers = input_data.get("triggers", ["urgency", "social_proof"])

        enhanced_content = content

        # Apply triggers
        if "urgency" in target_triggers:
            enhanced_content = self._add_urgency(enhanced_content)
        if "scarcity" in target_triggers:
            enhanced_content = self._add_scarcity(enhanced_content)
        if "social_proof" in target_triggers:
            enhanced_content = self._add_social_proof(enhanced_content)

        return {
            "original_content": content,
            "enhanced_content": enhanced_content,
            "triggers_applied": target_triggers,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _optimize_for_conversion(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize content for conversion using psychology."""
        content = input_data.get("content", "")

        # Conversion optimization techniques
        optimizations = {
            "clear_value_proposition": self._ensure_value_proposition(content),
            "emotional_appeal": self._add_emotional_appeal(content),
            "call_to_action": self._optimize_cta(content),
            "trust_signals": self._add_trust_signals(content),
        }

        optimized_content = content
        for opt_type, opt_func in optimizations.items():
            if opt_func:
                optimized_content = opt_func(optimized_content)

        return {
            "original_content": content,
            "optimized_content": optimized_content,
            "optimizations": optimizations,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _analyze_money_psychology(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze money psychology aspects."""
        campaign_data = input_data.get("campaign_data", {})
        price = campaign_data.get("price", 0)

        analysis = {
            "price_psychology": {
                "anchoring": self._analyze_price_anchoring(campaign_data),
                "charm_pricing": self._check_charm_pricing(price),
                "value_perception": self._analyze_value_perception(campaign_data),
            },
            "payment_psychology": {
                "payment_friction": self._analyze_payment_friction(campaign_data),
                "payment_options": self._analyze_payment_options(campaign_data),
            },
            "recommendations": self._generate_money_recommendations(campaign_data),
        }

        return {
            "analysis": analysis,
            "thinking": thinking.get("final_reasoning"),
        }

    # Helper methods for psychological analysis
    def _check_urgency(self, content: str) -> bool:
        urgency_words = ["now", "today", "limited", "expires", "hurry", "act fast"]
        return any(word in content.lower() for word in urgency_words)

    def _check_scarcity(self, content: str) -> bool:
        scarcity_words = ["limited", "only", "few left", "sold out", "exclusive"]
        return any(word in content.lower() for word in scarcity_words)

    def _check_social_proof(self, content: str) -> bool:
        social_proof_words = ["join", "thousands", "customers", "reviews", "testimonials"]
        return any(word in content.lower() for word in social_proof_words)

    def _check_authority(self, content: str) -> bool:
        authority_words = ["expert", "certified", "award", "proven", "research"]
        return any(word in content.lower() for word in authority_words)

    def _check_reciprocity(self, content: str) -> bool:
        reciprocity_words = ["free", "gift", "bonus", "trial", "sample"]
        return any(word in content.lower() for word in reciprocity_words)

    def _check_commitment(self, content: str) -> bool:
        commitment_words = ["commit", "promise", "guarantee", "pledge"]
        return any(word in content.lower() for word in commitment_words)

    def _check_loss_aversion(self, content: str) -> bool:
        loss_words = ["lose", "miss", "regret", "don't miss", "avoid"]
        return any(word in content.lower() for word in loss_words)

    def _check_anchoring(self, content: str) -> bool:
        anchor_words = ["was", "originally", "compare", "save", "discount"]
        return any(word in content.lower() for word in anchor_words)

    def _analyze_price_anchoring(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        original_price = campaign_data.get("original_price", 0)
        current_price = campaign_data.get("price", 0)
        discount = ((original_price - current_price) / original_price * 100) if original_price > 0 else 0

        return {
            "has_anchor": original_price > current_price,
            "discount_percentage": discount,
            "effectiveness": "high" if discount > 20 else "medium" if discount > 10 else "low",
        }

    def _analyze_value_perception(self, content: str) -> Dict[str, Any]:
        value_words = ["value", "worth", "investment", "ROI", "results"]
        has_value_language = any(word in content.lower() for word in value_words)

        return {
            "has_value_language": has_value_language,
            "recommendation": "Add value proposition" if not has_value_language else "Good",
        }

    def _analyze_payment_friction(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        payment_options = campaign_data.get("payment_options", [])
        has_multiple_options = len(payment_options) > 1

        return {
            "payment_options_count": len(payment_options),
            "friction_level": "low" if has_multiple_options else "high",
            "recommendation": "Add more payment options" if not has_multiple_options else "Good",
        }

    def _check_charm_pricing(self, price: float) -> bool:
        """Check if price uses charm pricing (ends in .99, .97, etc.)"""
        price_str = str(price)
        return price_str.endswith(".99") or price_str.endswith(".97") or price_str.endswith(".95")

    def _analyze_payment_options(self, campaign_data: Dict[str, Any]) -> List[str]:
        return campaign_data.get("payment_options", [])

    def _generate_psychology_recommendations(
        self, triggers: Dict[str, bool], money_psychology: Dict[str, Any]
    ) -> List[str]:
        recommendations = []

        if not triggers.get("urgency"):
            recommendations.append("Add urgency triggers (limited time, act now)")
        if not triggers.get("social_proof"):
            recommendations.append("Add social proof (testimonials, customer count)")
        if not triggers.get("scarcity"):
            recommendations.append("Add scarcity elements (limited availability)")

        return recommendations

    def _generate_money_recommendations(self, campaign_data: Dict[str, Any]) -> List[str]:
        recommendations = []

        price = campaign_data.get("price", 0)
        if not self._check_charm_pricing(price):
            recommendations.append("Consider charm pricing (e.g., $99.99 instead of $100)")

        if not campaign_data.get("payment_options"):
            recommendations.append("Add multiple payment options to reduce friction")

        return recommendations

    def _add_urgency(self, content: str) -> str:
        if "now" not in content.lower():
            return f"{content} - Act now, limited time offer!"
        return content

    def _add_scarcity(self, content: str) -> str:
        if "limited" not in content.lower():
            return f"{content} - Limited availability!"
        return content

    def _add_social_proof(self, content: str) -> str:
        if "join" not in content.lower() and "customers" not in content.lower():
            return f"{content} - Join thousands of satisfied customers!"
        return content

    def _ensure_value_proposition(self, content: str) -> str:
        if "value" not in content.lower() and "worth" not in content.lower():
            return f"{content} - Get incredible value today!"
        return content

    def _add_emotional_appeal(self, content: str) -> str:
        # Add emotional language
        return content

    def _optimize_cta(self, content: str) -> str:
        # Ensure strong CTA
        if "click" not in content.lower() and "get" not in content.lower():
            return f"{content} - Get started now!"
        return content

    def _add_trust_signals(self, content: str) -> str:
        # Add trust elements
        return content

