"""
Prompt Cache Manager - 10x Cost Reduction System

Implements caching strategies for:
- Anthropic (90% cost reduction on cached tokens)
- OpenAI (50% cost reduction with automatic caching)
- Gemini (Context caching for repeated use)

Performance Metrics:
- Cache hit rate tracking
- Cost savings calculation
- Token usage monitoring
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio


@dataclass
class CacheMetrics:
    """Track cache performance and cost savings"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_cached: int = 0
    tokens_uncached: int = 0
    cost_saved: float = 0.0
    cost_spent: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def cost_reduction(self) -> float:
        """Calculate total cost reduction percentage"""
        total_cost = self.cost_saved + self.cost_spent
        if total_cost == 0:
            return 0.0
        return (self.cost_saved / total_cost) * 100

    @property
    def roi_multiplier(self) -> float:
        """Calculate ROI multiplier (e.g., 10x = 10.0)"""
        if self.cost_spent == 0:
            return 0.0
        return (self.cost_saved + self.cost_spent) / self.cost_spent


class PromptCacheLoader:
    """Load and manage cached system prompts"""

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            # Default to prompts/cached directory
            cache_dir = Path(__file__).parent / "cached"
        self.cache_dir = Path(cache_dir)
        self._cache: Dict[str, str] = {}

    def load_prompt(self, prompt_name: str) -> str:
        """
        Load a cached prompt from disk

        Args:
            prompt_name: Name of the prompt file (without .txt extension)

        Returns:
            Prompt content as string
        """
        # Check in-memory cache first
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        # Load from disk
        prompt_path = self.cache_dir / f"{prompt_name}.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Cache in memory
        self._cache[prompt_name] = content
        return content

    def get_anthropic_cached_system(self, prompt_name: str) -> List[Dict[str, Any]]:
        """
        Create Anthropic system message with cache control

        Args:
            prompt_name: Name of the cached prompt

        Returns:
            System message array with cache_control directive
        """
        prompt_content = self.load_prompt(prompt_name)

        return [
            {
                "type": "text",
                "text": prompt_content,
                "cache_control": {"type": "ephemeral"}
            }
        ]

    def get_openai_system_message(self, prompt_name: str) -> str:
        """
        Load system message for OpenAI (automatic caching)

        OpenAI automatically caches prompts with consistent prefixes.
        Keep system messages consistent for optimal caching.

        Args:
            prompt_name: Name of the cached prompt

        Returns:
            System message content
        """
        return self.load_prompt(prompt_name)


class CacheMonitor:
    """Monitor and track cache performance metrics"""

    def __init__(self, metrics_file: Optional[str] = None):
        if metrics_file is None:
            metrics_file = "/tmp/prompt_cache_metrics.json"
        self.metrics_file = Path(metrics_file)
        self.metrics = self._load_metrics()

        # Cost per 1M tokens (as of December 2024)
        self.anthropic_costs = {
            "input_base": 3.00,  # $3 per 1M input tokens
            "input_cached": 0.30,  # $0.30 per 1M cached tokens (90% reduction)
            "output": 15.00  # $15 per 1M output tokens
        }

        self.openai_costs = {
            "gpt4o_input": 2.50,  # $2.50 per 1M tokens
            "gpt4o_input_cached": 1.25,  # $1.25 per 1M cached (50% reduction)
            "gpt4o_output": 10.00,
            "gpt4o_mini_input": 0.15,
            "gpt4o_mini_input_cached": 0.075,
            "gpt4o_mini_output": 0.60
        }

    def _load_metrics(self) -> CacheMetrics:
        """Load metrics from disk or create new"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                return CacheMetrics(**data)
            except Exception as e:
                print(f"⚠️ Failed to load metrics: {e}")
        return CacheMetrics()

    def _save_metrics(self):
        """Persist metrics to disk"""
        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metrics_file, 'w') as f:
                json.dump(asdict(self.metrics), f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save metrics: {e}")

    def record_anthropic_request(
        self,
        input_tokens: int,
        cached_tokens: int,
        output_tokens: int,
        cache_hit: bool
    ):
        """
        Record Anthropic API request metrics

        Args:
            input_tokens: Total input tokens sent
            cached_tokens: Number of tokens read from cache
            output_tokens: Output tokens generated
            cache_hit: Whether this was a cache hit
        """
        self.metrics.total_requests += 1

        if cache_hit:
            self.metrics.cache_hits += 1
            self.metrics.tokens_cached += cached_tokens

            # Calculate savings
            # Uncached cost
            uncached_cost = (input_tokens / 1_000_000) * self.anthropic_costs["input_base"]
            # Cached cost
            cached_cost = (cached_tokens / 1_000_000) * self.anthropic_costs["input_cached"]
            uncached_portion_cost = ((input_tokens - cached_tokens) / 1_000_000) * self.anthropic_costs["input_base"]
            actual_cost = cached_cost + uncached_portion_cost

            savings = uncached_cost - actual_cost
            self.metrics.cost_saved += savings
            self.metrics.cost_spent += actual_cost
        else:
            self.metrics.cache_misses += 1
            self.metrics.tokens_uncached += input_tokens

            cost = (input_tokens / 1_000_000) * self.anthropic_costs["input_base"]
            self.metrics.cost_spent += cost

        # Add output cost (not cached)
        output_cost = (output_tokens / 1_000_000) * self.anthropic_costs["output"]
        self.metrics.cost_spent += output_cost

        self._save_metrics()

    def record_openai_request(
        self,
        model: str,
        input_tokens: int,
        cached_tokens: int,
        output_tokens: int
    ):
        """Record OpenAI API request metrics"""
        self.metrics.total_requests += 1

        # Determine costs based on model
        if "mini" in model.lower():
            input_cost = self.openai_costs["gpt4o_mini_input"]
            cached_cost = self.openai_costs["gpt4o_mini_input_cached"]
            output_cost_rate = self.openai_costs["gpt4o_mini_output"]
        else:
            input_cost = self.openai_costs["gpt4o_input"]
            cached_cost = self.openai_costs["gpt4o_input_cached"]
            output_cost_rate = self.openai_costs["gpt4o_output"]

        if cached_tokens > 0:
            self.metrics.cache_hits += 1
            self.metrics.tokens_cached += cached_tokens

            # Calculate savings
            uncached_cost = (input_tokens / 1_000_000) * input_cost
            actual_cost = (cached_tokens / 1_000_000) * cached_cost + \
                         ((input_tokens - cached_tokens) / 1_000_000) * input_cost

            savings = uncached_cost - actual_cost
            self.metrics.cost_saved += savings
            self.metrics.cost_spent += actual_cost
        else:
            self.metrics.cache_misses += 1
            self.metrics.tokens_uncached += input_tokens
            cost = (input_tokens / 1_000_000) * input_cost
            self.metrics.cost_spent += cost

        # Add output cost
        output_cost = (output_tokens / 1_000_000) * output_cost_rate
        self.metrics.cost_spent += output_cost

        self._save_metrics()

    def get_summary(self) -> Dict[str, Any]:
        """Get current cache performance summary"""
        return {
            "total_requests": self.metrics.total_requests,
            "cache_hit_rate": f"{self.metrics.hit_rate:.1f}%",
            "tokens_cached": f"{self.metrics.tokens_cached:,}",
            "tokens_uncached": f"{self.metrics.tokens_uncached:,}",
            "cost_saved": f"${self.metrics.cost_saved:.4f}",
            "cost_spent": f"${self.metrics.cost_spent:.4f}",
            "cost_reduction": f"{self.metrics.cost_reduction:.1f}%",
            "roi_multiplier": f"{self.metrics.roi_multiplier:.1f}x"
        }

    def print_summary(self):
        """Print formatted cache performance summary"""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("💰 PROMPT CACHE PERFORMANCE REPORT")
        print("="*60)
        print(f"📊 Total Requests: {summary['total_requests']}")
        print(f"✅ Cache Hit Rate: {summary['cache_hit_rate']}")
        print(f"🎯 Tokens Cached: {summary['tokens_cached']}")
        print(f"📝 Tokens Uncached: {summary['tokens_uncached']}")
        print(f"💸 Cost Saved: {summary['cost_saved']}")
        print(f"💵 Cost Spent: {summary['cost_spent']}")
        print(f"📉 Cost Reduction: {summary['cost_reduction']}")
        print(f"🚀 ROI Multiplier: {summary['roi_multiplier']}")
        print("="*60)

        # Alert if cache hit rate is low
        if self.metrics.total_requests > 10 and self.metrics.hit_rate < 50:
            print("⚠️  WARNING: Cache hit rate below 50%!")
            print("   - Ensure system prompts are consistent")
            print("   - Check cache_control directives")
            print("="*60)

    def reset_metrics(self):
        """Reset all metrics to zero"""
        self.metrics = CacheMetrics()
        self._save_metrics()
        print("✅ Cache metrics reset")


# Global instances
prompt_loader = PromptCacheLoader()
cache_monitor = CacheMonitor()


# Convenience functions
def get_cached_system_prompt(prompt_name: str, provider: str = "anthropic") -> Any:
    """
    Get cached system prompt for specified provider

    Args:
        prompt_name: Name of the cached prompt file
        provider: "anthropic", "openai", or "gemini"

    Returns:
        Formatted system message for the provider
    """
    if provider == "anthropic":
        return prompt_loader.get_anthropic_cached_system(prompt_name)
    elif provider == "openai":
        return prompt_loader.get_openai_system_message(prompt_name)
    elif provider == "gemini":
        return prompt_loader.load_prompt(prompt_name)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def print_cache_report():
    """Print current cache performance report"""
    cache_monitor.print_summary()
