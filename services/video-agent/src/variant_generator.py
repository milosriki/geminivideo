"""
Variant Generator - Automatically create multiple ad variations
Generates variants with different hooks, CTAs, and avatars for A/B testing
"""
import logging
from typing import List, Dict, Any, Optional
import random
import copy

logger = logging.getLogger(__name__)


class VariantGenerator:
    """Generate multiple ad variants for A/B testing"""
    
    # Pre-defined hook variations
    HOOK_TEMPLATES = {
        "question": [
            "What if {product} could {benefit}?",
            "Are you tired of {pain_point}?",
            "Did you know {product} can {benefit}?",
            "Why do {target_audience} love {product}?",
            "How does {product} help with {pain_point}?"
        ],
        "statement": [
            "{product} is changing how {target_audience} {action}",
            "The secret to {benefit} is finally here",
            "{number}+ {target_audience} are using {product}",
            "{product}: The {adjective} solution for {pain_point}",
            "Introducing {product} - {tagline}"
        ],
        "challenge": [
            "{target_audience}! Try this {adjective} trick",
            "You won't believe what {product} can do",
            "This one simple change will {benefit}",
            "Stop {pain_point} - Start {benefit}",
            "{target_audience}: This changes everything"
        ],
        "urgency": [
            "Limited time: Get {product} now",
            "Only {number} spots left for {product}",
            "Last chance to {benefit}",
            "Don't miss out on {product}",
            "{sale_period} special: {discount}% off {product}"
        ]
    }
    
    # CTA variations
    CTA_TEMPLATES = {
        "learn_more": ["Learn More", "Discover How", "See How It Works", "Find Out More"],
        "shop_now": ["Shop Now", "Get Started", "Try It Free", "Start Today"],
        "sign_up": ["Sign Up Free", "Join Now", "Get Access", "Claim Your Spot"],
        "limited": ["Claim Offer", "Get Yours", "Limited Time", "Act Now"]
    }
    
    def __init__(self):
        """Initialize variant generator"""
        self.hook_templates = self.HOOK_TEMPLATES
        self.cta_templates = self.CTA_TEMPLATES
    
    def generate_hook_variants(
        self,
        base_hook: str,
        product_name: str,
        pain_point: str,
        benefit: str,
        target_audience: str,
        count: int = 5
    ) -> List[str]:
        """
        Generate hook variations
        
        Args:
            base_hook: Original hook text
            product_name: Name of the product
            pain_point: Main pain point being addressed
            benefit: Key benefit
            target_audience: Target audience description
            count: Number of variants to generate
        
        Returns:
            List of hook variants
        """
        variants = [base_hook]  # Always include original
        
        # Detect hook type
        base_type = "question" if "?" in base_hook else "statement"
        
        # Generate variants from templates
        all_templates = []
        for hook_type, templates in self.hook_templates.items():
            all_templates.extend(templates)
        
        # Shuffle for variety
        random.shuffle(all_templates)
        
        for template in all_templates[:count-1]:
            try:
                variant = template.format(
                    product=product_name,
                    pain_point=pain_point,
                    benefit=benefit,
                    target_audience=target_audience,
                    action="work",
                    number=random.choice(["1000", "5000", "10000"]),
                    adjective=random.choice(["proven", "powerful", "revolutionary", "simple"]),
                    tagline=f"Your solution for {pain_point}",
                    sale_period=random.choice(["Today", "This Week", "This Month"]),
                    discount=random.choice(["20", "30", "40", "50"])
                )
                variants.append(variant)
            except KeyError:
                # Skip templates with missing placeholders
                continue
        
        return variants[:count]
    
    def generate_cta_variants(
        self,
        base_cta: str,
        cta_type: str = "learn_more",
        count: int = 3
    ) -> List[str]:
        """
        Generate CTA variations
        
        Args:
            base_cta: Original CTA text
            cta_type: Type of CTA (learn_more, shop_now, sign_up, limited)
            count: Number of variants to generate
        
        Returns:
            List of CTA variants
        """
        variants = [base_cta]  # Always include original
        
        templates = self.cta_templates.get(cta_type, self.cta_templates["learn_more"])
        
        for template in templates[:count-1]:
            variants.append(template)
        
        return variants[:count]
    
    def generate_variants(
        self,
        base_creative: Dict[str, Any],
        variant_count: int = 5,
        vary_hooks: bool = True,
        vary_ctas: bool = True,
        vary_avatars: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple ad variants from a base creative
        
        Args:
            base_creative: Base creative data with script, hook, cta
            variant_count: Number of variants to generate
            vary_hooks: Whether to generate hook variants
            vary_ctas: Whether to generate CTA variants
            vary_avatars: Whether to vary avatars (if multiple available)
        
        Returns:
            List of creative variants
        """
        variants = []
        
        # Extract base data
        product_name = base_creative.get("product_name", "our product")
        pain_point = base_creative.get("pain_point", "challenges")
        benefit = base_creative.get("benefit", "better results")
        target_audience = base_creative.get("target_avatar", "customers")
        base_hook = base_creative.get("hook", "Discover something amazing")
        base_cta = base_creative.get("cta", "Learn More")
        cta_type = base_creative.get("cta_type", "learn_more")
        
        # Generate hook variants
        hook_variants = [base_hook]
        if vary_hooks:
            hook_variants = self.generate_hook_variants(
                base_hook,
                product_name,
                pain_point,
                benefit,
                target_audience,
                count=variant_count
            )
        
        # Generate CTA variants
        cta_variants = [base_cta]
        if vary_ctas:
            cta_variants = self.generate_cta_variants(
                base_cta,
                cta_type,
                count=min(3, variant_count)
            )
        
        # Generate avatar variants (if enabled and available)
        avatar_variants = [base_creative.get("avatar_id")]
        if vary_avatars and base_creative.get("available_avatars"):
            available = base_creative["available_avatars"]
            avatar_variants = available[:min(len(available), variant_count)]
        
        # Create combinations
        for i in range(variant_count):
            variant = copy.deepcopy(base_creative)
            
            # Assign variants with rotation
            variant["hook"] = hook_variants[i % len(hook_variants)]
            variant["cta"] = cta_variants[i % len(cta_variants)]
            variant["avatar_id"] = avatar_variants[i % len(avatar_variants)]
            
            # Add metadata
            variant["variant_id"] = f"{base_creative.get('id', 'base')}#v{i+1}"
            variant["is_variant"] = i > 0
            variant["base_id"] = base_creative.get("id")
            variant["variant_type"] = self._get_variant_type(i, vary_hooks, vary_ctas, vary_avatars)
            
            variants.append(variant)
        
        logger.info(f"Generated {len(variants)} variants")
        return variants
    
    def _get_variant_type(
        self,
        index: int,
        vary_hooks: bool,
        vary_ctas: bool,
        vary_avatars: bool
    ) -> str:
        """Determine variant type based on what was varied"""
        types = []
        if vary_hooks:
            types.append("hook")
        if vary_ctas:
            types.append("cta")
        if vary_avatars:
            types.append("avatar")
        
        if index == 0:
            return "original"
        
        return "+".join(types) if types else "copy"


# Global instance
variant_generator = VariantGenerator()
