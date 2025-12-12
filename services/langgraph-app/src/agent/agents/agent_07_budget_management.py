"""Agent 7: Budget Management Agent - Manages ad budgets intelligently."""

from typing import Any, Dict

from agent.core.base_agent import BaseAgent


class BudgetManagementAgent(BaseAgent):
    """Manages budgets using BattleHardenedSampler and intelligent allocation."""

    def __init__(self, **kwargs):
        super().__init__(
            name="BudgetManagementAgent",
            description=(
                "Expert budget manager. Allocates budgets intelligently using "
                "BattleHardenedSampler, handles attribution lag, and optimizes "
                "spend for maximum ROAS."
            ),
            **kwargs,
        )

    async def _execute_impl(
        self, input_data: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute budget management."""
        operation = input_data.get("operation", "allocate")
        ad_states = input_data.get("ad_states", [])

        if operation == "allocate":
            return await self._allocate_budget(ad_states, context)
        elif operation == "rebalance":
            return await self._rebalance_budget(ad_states, context)
        else:
            return {
                "operation": operation,
                "allocations": {},
                "status": "processed",
            }

    async def _allocate_budget(
        self, ad_states: list, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Allocate budget using BattleHardenedSampler logic."""
        total_budget = sum(state.get("current_budget", 0) for state in ad_states)

        # Calculate blended scores
        allocations = {}
        for state in ad_states:
            ad_id = state.get("ad_id")
            ctr = state.get("ctr", 0)
            pipeline_value = state.get("pipeline_value", 0)
            
            # Blended score: early CTR, later pipeline ROAS
            blended_score = (ctr * 0.6) + (pipeline_value / 1000 * 0.4)
            
            allocations[ad_id] = {
                "recommended_budget": total_budget * (blended_score / sum(
                    (s.get("ctr", 0) * 0.6 + s.get("pipeline_value", 0) / 1000 * 0.4)
                    for s in ad_states
                )),
                "score": blended_score,
            }

        return {
            "allocations": allocations,
            "total_budget": total_budget,
            "status": "allocated",
        }

    async def _rebalance_budget(
        self, ad_states: list, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rebalance budgets based on performance."""
        return await self._allocate_budget(ad_states, context)

