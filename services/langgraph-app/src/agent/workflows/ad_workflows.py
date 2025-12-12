"""Ad-specific workflows optimized for ad problem solving."""

from __future__ import annotations

from typing import Any, Dict

from agent.core.orchestrator import AgentTask


def create_winning_ad_workflow(input_data: Dict[str, Any]) -> list[AgentTask]:
    """Workflow to create a winning ad - optimized for ad problem solving."""
    from agent.graph import _AGENTS
    
    campaign_data = input_data.get("campaign_data", {})
    target_audience = input_data.get("target_audience", {})
    
    return [
        # Step 1: Creative + Psychology (MOST IMPORTANT for ads)
        AgentTask(
            agent=_AGENTS["creative_intelligence"],
            input_data={
                "operation": "generate_content",
                "problem": "Create high-converting ad creative with psychological triggers",
                "campaign_data": campaign_data,
                "target_audience": target_audience,
            },
            priority=1,
        ),
        AgentTask(
            agent=_AGENTS["psychology_expert"],
            input_data={
                "operation": "apply_psychological_triggers",
                "problem": "Apply psychological triggers to maximize conversion",
                "creative": campaign_data.get("creative", {}),
                "target_audience": target_audience,
            },
            dependencies=["creative_intelligence"],
            priority=1,
        ),
        # Step 2: Predict performance
        AgentTask(
            agent=_AGENTS["ml_intelligence"],
            input_data={
                "operation": "predict_performance",
                "problem": "Predict CTR and ROAS for generated creative",
                "ad_data": {
                    "creative": campaign_data,
                    "target_audience": target_audience,
                },
            },
            dependencies=["creative_intelligence", "psychology_expert"],
            priority=2,
        ),
        # Step 3: Optimize campaign
        AgentTask(
            agent=_AGENTS["business_intelligence"],
            input_data={
                "operation": "optimize_campaign",
                "problem": "Optimize campaign setup for maximum ROAS",
                "campaign_id": input_data.get("campaign_id"),
                "predicted_performance": {},  # Will be filled from ml_intelligence
            },
            dependencies=["ml_intelligence"],
            priority=3,
        ),
        # Step 4: Deploy to platform
        AgentTask(
            agent=_AGENTS["system_intelligence"],
            input_data={
                "operation": "integrate_api",
                "problem": "Integrate with Meta Ads API",
                "service": "meta_ads",
                "endpoint": "create_ad",
            },
            dependencies=["business_intelligence"],
            priority=4,
        ),
        AgentTask(
            agent=_AGENTS["meta_ads_expert"],
            input_data={
                "operation": "create_ad",
                "problem": "Create ad in Meta Ads with best practices",
                "ad_data": campaign_data,
            },
            dependencies=["system_intelligence"],
            priority=4,
        ),
    ]


def optimize_underperforming_ad_workflow(input_data: Dict[str, Any]) -> list[AgentTask]:
    """Workflow to optimize underperforming ad."""
    from agent.graph import _AGENTS
    
    ad_id = input_data.get("ad_id")
    campaign_id = input_data.get("campaign_id")
    
    return [
        # Step 1: Monitor and analyze
        AgentTask(
            agent=_AGENTS["data_intelligence"],
            input_data={
                "operation": "monitor_metrics",
                "problem": "Analyze ad performance and identify issues",
                "metrics": {
                    "ad_id": ad_id,
                    "campaign_id": campaign_id,
                },
            },
            priority=1,
        ),
        # Step 2: ML analysis
        AgentTask(
            agent=_AGENTS["ml_intelligence"],
            input_data={
                "operation": "analyze_patterns",
                "problem": "Identify why ad is underperforming",
                "ad_data": {"ad_id": ad_id},
            },
            dependencies=["data_intelligence"],
            priority=2,
        ),
        # Step 3: Creative improvements
        AgentTask(
            agent=_AGENTS["creative_intelligence"],
            input_data={
                "operation": "optimize_creative",
                "problem": "Improve creative based on performance data",
                "ad_data": {"ad_id": ad_id},
            },
            dependencies=["ml_intelligence"],
            priority=3,
        ),
        AgentTask(
            agent=_AGENTS["psychology_expert"],
            input_data={
                "operation": "improve_triggers",
                "problem": "Enhance psychological triggers",
                "creative": {},
            },
            dependencies=["creative_intelligence"],
            priority=3,
        ),
        # Step 4: Business optimization
        AgentTask(
            agent=_AGENTS["business_intelligence"],
            input_data={
                "operation": "optimize_campaign",
                "problem": "Optimize campaign settings",
                "campaign_id": campaign_id,
            },
            dependencies=["creative_intelligence"],
            priority=4,
        ),
        # Step 5: Apply changes
        AgentTask(
            agent=_AGENTS["meta_ads_expert"],
            input_data={
                "operation": "update_ad",
                "problem": "Update ad in Meta Ads",
                "ad_id": ad_id,
            },
            dependencies=["business_intelligence"],
            priority=5,
        ),
    ]


def maximize_roas_workflow(input_data: Dict[str, Any]) -> list[AgentTask]:
    """Workflow to maximize ROAS across all ads."""
    from agent.graph import _AGENTS
    
    campaign_id = input_data.get("campaign_id")
    
    return [
        # Step 1: Predict all ads
        AgentTask(
            agent=_AGENTS["ml_intelligence"],
            input_data={
                "operation": "predict_performance",
                "problem": "Predict ROAS for all ads in campaign",
                "campaign_id": campaign_id,
            },
            priority=1,
        ),
        # Step 2: Business + Money optimization
        AgentTask(
            agent=_AGENTS["business_intelligence"],
            input_data={
                "operation": "manage_budget",
                "problem": "Optimize budget allocation for maximum ROAS",
                "campaign_id": campaign_id,
            },
            dependencies=["ml_intelligence"],
            priority=2,
        ),
        AgentTask(
            agent=_AGENTS["money_business_expert"],
            input_data={
                "operation": "optimize_revenue",
                "problem": "Maximize revenue and ROI",
                "campaign_data": {"campaign_id": campaign_id},
            },
            dependencies=["business_intelligence"],
            priority=2,
        ),
        # Step 3: Monitor and adjust
        AgentTask(
            agent=_AGENTS["data_intelligence"],
            input_data={
                "operation": "monitor_metrics",
                "problem": "Monitor real-time performance",
                "campaign_id": campaign_id,
            },
            dependencies=["money_business_expert"],
            priority=3,
        ),
        # Step 4: Apply optimizations
        AgentTask(
            agent=_AGENTS["meta_ads_expert"],
            input_data={
                "operation": "optimize_campaign",
                "problem": "Apply budget optimizations to Meta Ads",
                "campaign_id": campaign_id,
            },
            dependencies=["data_intelligence"],
            priority=4,
        ),
    ]


def fix_low_ctr_workflow(input_data: Dict[str, Any]) -> list[AgentTask]:
    """Workflow to fix low CTR - most critical ad problem."""
    from agent.graph import _AGENTS
    
    ad_id = input_data.get("ad_id")
    
    return [
        # Step 1: Analyze creative (CTR is 60-70% creative)
        AgentTask(
            agent=_AGENTS["creative_intelligence"],
            input_data={
                "operation": "analyze_creative",
                "problem": "Analyze why CTR is low - focus on hook and first 3 seconds",
                "ad_data": {"ad_id": ad_id},
            },
            priority=1,
        ),
        # Step 2: Psychology analysis
        AgentTask(
            agent=_AGENTS["psychology_expert"],
            input_data={
                "operation": "analyze_triggers",
                "problem": "Identify missing psychological triggers",
                "creative": {},
            },
            dependencies=["creative_intelligence"],
            priority=1,
        ),
        # Step 3: Generate improved creative
        AgentTask(
            agent=_AGENTS["creative_intelligence"],
            input_data={
                "operation": "generate_content",
                "problem": "Generate new hook and creative with better CTR potential",
                "ad_data": {"ad_id": ad_id},
            },
            dependencies=["psychology_expert"],
            priority=2,
        ),
        # Step 4: Predict improvement
        AgentTask(
            agent=_AGENTS["ml_intelligence"],
            input_data={
                "operation": "predict_performance",
                "problem": "Predict CTR improvement",
                "ad_data": {"ad_id": ad_id},
            },
            dependencies=["creative_intelligence"],
            priority=3,
        ),
        # Step 5: Update ad
        AgentTask(
            agent=_AGENTS["meta_ads_expert"],
            input_data={
                "operation": "update_ad",
                "problem": "Update ad with improved creative",
                "ad_id": ad_id,
            },
            dependencies=["ml_intelligence"],
            priority=4,
        ),
    ]


# Export workflows
AD_WORKFLOWS = {
    "create_winning_ad": create_winning_ad_workflow,
    "optimize_underperforming_ad": optimize_underperforming_ad_workflow,
    "maximize_roas": maximize_roas_workflow,
    "fix_low_ctr": fix_low_ctr_workflow,
}

