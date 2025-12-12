"""Super Agent 9: Money/Business Expert - Focuses on ROI, revenue, business strategy, money optimization."""

from typing import Any, Dict, List
import logging
from datetime import datetime

from agent.super_agents.base_super_agent import SuperAgent
from agent.storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class MoneyBusinessExpertAgent(SuperAgent):
    """Expert in money, ROI, revenue, business strategy, financial optimization."""

    def __init__(self, **kwargs):
        super().__init__(
            name="MoneyBusinessExpertAgent",
            description=(
                "Money and business expert. Focuses on ROI optimization, revenue maximization, "
                "business strategy, financial analysis, budget optimization, and money-making "
                "strategies for video ads campaigns."
            ),
            domains=[
                "ROI Optimization",
                "Revenue Maximization",
                "Business Strategy",
                "Financial Analysis",
                "Budget Optimization",
                "Profitability Analysis",
                "Revenue Growth",
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
        """Execute money/business expert operations."""
        operation = input_data.get("operation", "optimize_roi")

        if operation == "optimize_roi":
            return await self._optimize_roi(input_data, thinking)
        elif operation == "maximize_revenue":
            return await self._maximize_revenue(input_data, thinking)
        elif operation == "analyze_profitability":
            return await self._analyze_profitability(input_data, thinking)
        elif operation == "optimize_budget":
            return await self._optimize_budget(input_data, thinking)
        elif operation == "business_strategy":
            return await self._business_strategy(input_data, thinking)
        else:
            return {
                "operation": operation,
                "thinking": thinking.get("final_reasoning"),
                "status": "processed",
            }

    async def _optimize_roi(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize ROI for campaigns."""
        campaign_id = input_data.get("campaign_id")
        campaign_data = input_data.get("campaign_data", {})

        # Calculate current ROI
        spend = float(campaign_data.get("spend", 0))
        revenue = float(campaign_data.get("revenue", 0))
        current_roi = ((revenue - spend) / spend * 100) if spend > 0 else 0

        # Optimization strategies
        optimizations = {
            "reduce_cpc": self._suggest_cpc_reduction(campaign_data),
            "increase_conversion_rate": self._suggest_conversion_improvement(campaign_data),
            "optimize_targeting": self._suggest_targeting_optimization(campaign_data),
            "improve_creative": self._suggest_creative_improvement(campaign_data),
        }

        # Projected ROI
        projected_roi = self._calculate_projected_roi(campaign_data, optimizations)

        result = {
            "campaign_id": campaign_id,
            "current_roi": current_roi,
            "projected_roi": projected_roi,
            "optimizations": optimizations,
            "recommendations": self._generate_roi_recommendations(current_roi, projected_roi),
            "analyzed_at": datetime.now().isoformat(),
        }

        # Save to memory
        if self.client:
            self.client.table("agent_memory").insert({
                "key": f"roi_optimization_{campaign_id}_{datetime.now().isoformat()}",
                "value": result,
                "type": "roi_optimization",
            }).execute()

        return {
            "result": result,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _maximize_revenue(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Maximize revenue from campaigns."""
        campaign_data = input_data.get("campaign_data", {})

        current_revenue = float(campaign_data.get("revenue", 0))
        current_spend = float(campaign_data.get("spend", 0))

        # Revenue maximization strategies
        strategies = {
            "scale_winning_ads": self._suggest_scaling_winning_ads(campaign_data),
            "increase_budget": self._suggest_budget_increase(campaign_data),
            "expand_targeting": self._suggest_targeting_expansion(campaign_data),
            "improve_offer": self._suggest_offer_improvement(campaign_data),
        }

        projected_revenue = self._calculate_projected_revenue(campaign_data, strategies)

        return {
            "current_revenue": current_revenue,
            "projected_revenue": projected_revenue,
            "strategies": strategies,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _analyze_profitability(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze profitability of campaigns."""
        campaign_data = input_data.get("campaign_data", {})

        spend = float(campaign_data.get("spend", 0))
        revenue = float(campaign_data.get("revenue", 0))
        profit = revenue - spend
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0

        analysis = {
            "spend": spend,
            "revenue": revenue,
            "profit": profit,
            "profit_margin": profit_margin,
            "is_profitable": profit > 0,
            "break_even_point": self._calculate_break_even(campaign_data),
            "recommendations": self._generate_profitability_recommendations(profit, profit_margin),
        }

        return {
            "analysis": analysis,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _optimize_budget(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize budget allocation."""
        campaign_data = input_data.get("campaign_data", {})
        total_budget = float(campaign_data.get("total_budget", 0))

        # Budget optimization
        optimization = {
            "current_allocation": campaign_data.get("budget_allocation", {}),
            "recommended_allocation": self._recommend_budget_allocation(campaign_data),
            "expected_improvement": self._calculate_budget_improvement(campaign_data),
        }

        return {
            "total_budget": total_budget,
            "optimization": optimization,
            "thinking": thinking.get("final_reasoning"),
        }

    async def _business_strategy(
        self, input_data: Dict[str, Any], thinking: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provide business strategy recommendations."""
        campaign_data = input_data.get("campaign_data", {})

        strategy = {
            "short_term": self._short_term_strategy(campaign_data),
            "long_term": self._long_term_strategy(campaign_data),
            "growth_opportunities": self._identify_growth_opportunities(campaign_data),
            "risk_mitigation": self._identify_risks(campaign_data),
        }

        return {
            "strategy": strategy,
            "thinking": thinking.get("final_reasoning"),
        }

    # Helper methods
    def _suggest_cpc_reduction(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        current_cpc = float(campaign_data.get("cpc", 0))
        return {
            "current_cpc": current_cpc,
            "target_cpc": current_cpc * 0.8,  # 20% reduction
            "strategy": "Improve ad relevance and targeting",
        }

    def _suggest_conversion_improvement(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        current_cvr = float(campaign_data.get("conversion_rate", 0))
        return {
            "current_cvr": current_cvr,
            "target_cvr": current_cvr * 1.2,  # 20% improvement
            "strategy": "Optimize landing page and offer",
        }

    def _suggest_targeting_optimization(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy": "Refine audience targeting based on performance data",
            "expected_improvement": "15-25% better ROAS",
        }

    def _suggest_creative_improvement(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy": "Test new creative variations based on winning patterns",
            "expected_improvement": "10-20% better CTR",
        }

    def _calculate_projected_roi(
        self, campaign_data: Dict[str, Any], optimizations: Dict[str, Any]
    ) -> float:
        current_roi = float(campaign_data.get("roi", 0))
        # Project 20% improvement from optimizations
        return current_roi * 1.2

    def _generate_roi_recommendations(self, current_roi: float, projected_roi: float) -> List[str]:
        recommendations = []

        if current_roi < 200:
            recommendations.append("Focus on improving conversion rate")
        if current_roi < 300:
            recommendations.append("Optimize targeting to reduce CPC")
        if projected_roi > current_roi * 1.2:
            recommendations.append("Implement optimizations to reach projected ROI")

        return recommendations

    def _suggest_scaling_winning_ads(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy": "Increase budget on ads with ROAS > 3.0",
            "expected_revenue_increase": "30-50%",
        }

    def _suggest_budget_increase(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy": "Scale budget by 20-30% on profitable campaigns",
            "expected_revenue_increase": "20-30%",
        }

    def _suggest_targeting_expansion(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy": "Expand to similar audiences and lookalikes",
            "expected_revenue_increase": "15-25%",
        }

    def _suggest_offer_improvement(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "strategy": "Improve offer value proposition",
            "expected_revenue_increase": "10-20%",
        }

    def _calculate_projected_revenue(
        self, campaign_data: Dict[str, Any], strategies: Dict[str, Any]
    ) -> float:
        current_revenue = float(campaign_data.get("revenue", 0))
        # Project 25% increase from strategies
        return current_revenue * 1.25

    def _calculate_break_even(self, campaign_data: Dict[str, Any]) -> float:
        spend = float(campaign_data.get("spend", 0))
        revenue_per_conversion = float(campaign_data.get("revenue_per_conversion", 0))
        if revenue_per_conversion > 0:
            return spend / revenue_per_conversion
        return 0

    def _generate_profitability_recommendations(
        self, profit: float, profit_margin: float
    ) -> List[str]:
        recommendations = []

        if profit < 0:
            recommendations.append("Campaign is losing money - pause or optimize immediately")
        elif profit_margin < 10:
            recommendations.append("Low profit margin - focus on increasing revenue or reducing costs")
        elif profit_margin < 20:
            recommendations.append("Moderate profit margin - optimize for better profitability")

        return recommendations

    def _recommend_budget_allocation(self, campaign_data: Dict[str, Any]) -> Dict[str, float]:
        # Allocate more budget to high-performing ads
        return {
            "high_performers": 0.6,
            "testing": 0.3,
            "new_creatives": 0.1,
        }

    def _calculate_budget_improvement(self, campaign_data: Dict[str, Any]) -> float:
        return 0.15  # 15% expected improvement

    def _short_term_strategy(self, campaign_data: Dict[str, Any]) -> List[str]:
        return [
            "Scale winning ads by 20-30%",
            "Pause underperforming ads",
            "Test 3-5 new creative variations",
        ]

    def _long_term_strategy(self, campaign_data: Dict[str, Any]) -> List[str]:
        return [
            "Build lookalike audiences from best customers",
            "Develop brand assets and creative library",
            "Optimize funnel for better conversion rates",
        ]

    def _identify_growth_opportunities(self, campaign_data: Dict[str, Any]) -> List[str]:
        return [
            "Expand to new audiences",
            "Test new ad formats",
            "Optimize landing pages",
        ]

    def _identify_risks(self, campaign_data: Dict[str, Any]) -> List[str]:
        return [
            "Ad fatigue risk",
            "Competition increase",
            "Platform policy changes",
        ]

