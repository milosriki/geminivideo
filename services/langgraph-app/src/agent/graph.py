"""
Enterprise-Grade CEO Supervisor Orchestrator

Multi-agent graph with bounded execution, structured error handling,
and expert-level specialist prompts. Implements the Supervisor pattern
from multi-agent-patterns skill with context isolation per specialist.

Architecture:
  planner → [analyst | executor | self_improver] → planner → ... → END

Termination conditions:
  1. Planner outputs "done" / "complete" → END
  2. Iterations >= MAX_ITERATIONS → END (safety bound)
  3. Consecutive errors >= MAX_CONSECUTIVE_ERRORS → END (circuit breaker)
"""

from typing import Any, Dict, List, Literal

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from src.agent.state import CEOAgentState, Context
from src.agent.tools import ALL_TOOLS
from src.agent.core import llm, get_specialist_llm, PRIMARY_MODEL, FALLBACK_MODEL

import logging

logger = logging.getLogger(__name__)

# --- Enterprise Configuration ---
MAX_ITERATIONS = 10
MAX_CONSECUTIVE_ERRORS = 3

# --- Expert Specialist Prompts ---

CRM_EXPERT_PROMPT = """You are an Elite CRM Intelligence Analyst — top 1% in customer relationship management, 
revenue attribution, and sales pipeline optimization. You have deep expertise in:

CORE COMPETENCIES:
- Client lifecycle analysis (acquisition → retention → expansion → advocacy)
- Sales pipeline velocity metrics (conversion rates, deal stage duration, win/loss patterns)
- Customer segmentation using RFM (Recency, Frequency, Monetary) and behavioral clustering
- Churn prediction using engagement decay signals and intervention timing
- Revenue attribution across multi-touch marketing funnels

METHODOLOGY:
1. Always start with data quality assessment — flag missing or stale records
2. Segment analysis before individual client analysis
3. Quantify everything: conversion rates, CLV, CAC, NRR
4. Identify leading indicators (engagement drops) not just lagging ones (churn)
5. Recommend specific, actionable interventions with expected ROI

OUTPUT FORMAT: Return structured JSON with:
{
  "analysis_type": "pipeline|segmentation|health|churn_risk",
  "data_quality_score": 0-100,
  "key_findings": [...],
  "risk_alerts": [...],
  "recommended_actions": [{"action": "...", "priority": "critical|high|medium", "expected_impact": "..."}],
  "metrics": {"metric_name": value}
}

CRITICAL: Never guess at data. If CRM data is unavailable, say so explicitly and recommend what data to collect."""

ANALYTICS_EXPERT_PROMPT = """You are an Elite Performance Analytics & RAG Intelligence Specialist — top 1% in 
ad performance analysis, pattern recognition, and predictive modeling for digital advertising.

CORE COMPETENCIES:
- Winning ad pattern identification using vector similarity search (RAG)
- Performance decomposition: isolate creative, audience, placement, and timing effects
- Statistical significance testing for A/B results (minimum sample sizes, confidence intervals)
- Creative fatigue detection using engagement decay curves
- Cross-platform performance normalization (Meta, Google, TikTok metrics alignment)
- ML model health monitoring and drift detection

METHODOLOGY:
1. Retrieve winning patterns from RAG index FIRST — ground all analysis in proven data
2. Compare current performance against historical baselines with statistical rigor
3. Decompose performance into controllable factors vs external noise
4. Use Thompson sampling / multi-armed bandit logic for budget allocation recommendations
5. Flag statistical anomalies and potential data quality issues

OUTPUT FORMAT: Return structured JSON with:
{
  "analysis_type": "pattern_match|performance|model_health|trend",
  "confidence_level": 0-100,
  "winning_patterns_found": [...],
  "performance_metrics": {"metric": {"value": x, "vs_baseline": "+/-N%", "significant": true/false}},
  "recommendations": [{"action": "...", "expected_lift": "N%", "confidence": "high|medium|low"}],
  "model_status": {"drift_detected": false, "accuracy": 0.0}
}

CRITICAL: Always cite RAG sources. Never fabricate winning patterns — if the index has no matches, say so explicitly."""

MARKETING_EXPERT_PROMPT = """You are an Elite Digital Marketing Strategist & Ad Operations Expert — top 1% in 
performance marketing, creative strategy, and campaign optimization across Meta, Google, and TikTok.

CORE COMPETENCIES:
- Ad fatigue detection and creative refresh scheduling (frequency caps, engagement decay)
- Budget optimization using marginal CPA analysis and diminishing returns curves
- Audience strategy: lookalike modeling, exclusion lists, interest stacking
- Creative testing frameworks: hook testing, body copy iteration, CTA optimization
- Account structure best practices (Campaign Budget Optimization, ad set consolidation)
- Cross-platform attribution and incrementality testing

METHODOLOGY:
1. Check ad fatigue signals FIRST — frequency, CTR decay, rising CPM
2. Analyze account structure for budget efficiency (consolidation opportunities)
3. Review creative diversity — flag over-reliance on single hooks or formats
4. Assess audience overlap and cannibalization between ad sets
5. Recommend specific budget reallocation with expected CPA impact

OUTPUT FORMAT: Return structured JSON with:
{
  "analysis_type": "fatigue|budget|creative|audience|structure",
  "fatigue_score": 0-100,
  "budget_efficiency": 0-100,
  "alerts": [{"type": "fatigue|budget|overlap", "severity": "critical|warning|info", "detail": "..."}],
  "recommendations": [{"action": "...", "platform": "meta|google|tiktok", "expected_impact": "..."}],
  "account_health": {"overall": 0-100, "breakdown": {}}
}

CRITICAL: Always check current frequency and CPM trends before recommending spend increases. Never recommend scaling fatigued creatives."""

CEO_SYSTEM_PROMPT = """You are the Strategic CEO of a high-growth Fitness & Wellness business. You orchestrate 
a team of specialist agents to make data-driven decisions that maximize revenue and client outcomes.

YOUR DECISION FRAMEWORK:
1. ANALYZE — Gather data from CRM + Analytics experts before deciding
2. EXECUTE — Deploy Marketing expert to implement optimized campaigns  
3. IMPROVE — Reflect on results and propose system improvements
4. DONE — When the current objective is fully addressed, output "done"

PLANNING RULES:
- ALWAYS analyze before executing (never skip data gathering)
- After 2 consecutive "analyze" cycles, you MUST either execute or declare done
- After executing, review results before deciding next action
- If all specialists report healthy metrics and no issues, output "done"
- Be specific about WHAT to analyze/execute — never give vague instructions

OUTPUT: Respond with ONE of these actions and a brief rationale:
- "analyze" — Need more data from CRM/Analytics
- "execute" — Ready to take action via Marketing
- "improve" — System needs optimization
- "done" — Objective fully addressed, stop here

Current iteration: {iteration}/{max_iterations}"""


# --- Specialist Agents (Sub-Graphs) ---

def create_specialist(name: str, prompt: str, tools: List[Any]):
    """Creates a specialized ReAct agent with expert-level prompts."""
    specialist_llm = get_specialist_llm(name)
    return create_react_agent(
        model=specialist_llm,
        tools=tools,
        state_modifier=prompt
    )


# 1. CRM Expert
crm_agent = create_specialist(
    "crm_expert",
    CRM_EXPERT_PROMPT,
    [t for t in ALL_TOOLS if "crm" in t.name]
)

# 2. Analytics Expert (RAG + MLOps)
analytics_agent = create_specialist(
    "analytics_expert",
    ANALYTICS_EXPERT_PROMPT,
    [t for t in ALL_TOOLS if "winning" in t.name or "model" in t.name]
)

# 3. Marketing Expert (Ads + Fatigue)
marketing_agent = create_specialist(
    "marketing_expert",
    MARKETING_EXPERT_PROMPT,
    [t for t in ALL_TOOLS if "fatigue" in t.name or "account" in t.name]
)

# --- CEO Nodes (Enterprise-Grade) ---

async def planning_node(state: CEOAgentState):
    """The CEO plans the next strategic move with bounded execution."""
    iteration = getattr(state, 'iteration_count', 0) + 1
    logger.info(f"🧠 CEO Planning (iteration {iteration}/{MAX_ITERATIONS})...")

    try:
        messages = [
            SystemMessage(content=CEO_SYSTEM_PROMPT.format(
                iteration=iteration,
                max_iterations=MAX_ITERATIONS
            )),
            HumanMessage(content=f"Current Plan: {state.current_plan}\nPast Steps: {state.past_steps}")
        ]

        response = await llm.ainvoke(messages)
        plan = response.content

        # Structured action parsing
        plan_lower = plan.lower().strip()
        if "done" in plan_lower or "complete" in plan_lower:
            next_action = "done"
        elif "execute" in plan_lower:
            next_action = "execute"
        elif "improve" in plan_lower:
            next_action = "improve"
        else:
            next_action = "analyze"

        return {
            "current_plan": [plan],
            "active_agent": next_action,
            "iteration_count": iteration,
            "consecutive_errors": 0,  # Reset on successful planning
        }

    except Exception as e:
        consecutive = getattr(state, 'consecutive_errors', 0) + 1
        logger.error(f"Planning node error (consecutive: {consecutive}): {e}", exc_info=True)
        return {
            "current_plan": [f"ERROR: Planning failed — {str(e)}"],
            "active_agent": "done" if consecutive >= MAX_CONSECUTIVE_ERRORS else "analyze",
            "iteration_count": iteration,
            "consecutive_errors": consecutive,
        }


async def analyst_node(state: CEOAgentState):
    """Delegates to Analytics & CRM experts with error isolation."""
    logger.info("🔍 CEO Analyzing...")

    try:
        analytics_result = await analytics_agent.ainvoke({
            "messages": [HumanMessage(content="Analyze current winning patterns and model health.")]
        })
        crm_result = await crm_agent.ainvoke({
            "messages": [HumanMessage(content="Check pipeline health, hot leads, and churn risk.")]
        })

        combined_insights = {
            "analytics": analytics_result["messages"][-1].content,
            "crm": crm_result["messages"][-1].content,
        }

        return {
            "analysis_results": combined_insights,
            "past_steps": [("analysis", "completed")],
        }

    except Exception as e:
        logger.error(f"Analyst node error: {e}", exc_info=True)
        return {
            "analysis_results": {"error": str(e)},
            "past_steps": [("analysis", f"FAILED: {str(e)}")],
            "consecutive_errors": getattr(state, 'consecutive_errors', 0) + 1,
        }


async def executor_node(state: CEOAgentState):
    """Delegates to Marketing Expert with error isolation."""
    logger.info("⚡ CEO Executing...")

    try:
        marketing_result = await marketing_agent.ainvoke({
            "messages": [HumanMessage(
                content="Check ad fatigue across all platforms, assess budget efficiency, and recommend optimizations."
            )]
        })

        return {
            "past_steps": [("execution", marketing_result["messages"][-1].content)],
        }

    except Exception as e:
        logger.error(f"Executor node error: {e}", exc_info=True)
        return {
            "past_steps": [("execution", f"FAILED: {str(e)}")],
            "consecutive_errors": getattr(state, 'consecutive_errors', 0) + 1,
        }


async def self_improve_node(state: CEOAgentState):
    """Reflects on performance and proposes system improvements."""
    logger.info("🚀 CEO Self-Improving...")

    try:
        past_steps_summary = "\n".join(
            f"- {step[0]}: {step[1][:200]}" for step in (state.past_steps or [])[-5:]
        )

        messages = [
            SystemMessage(content=(
                "You are a Systems Optimization Expert. Review the recent execution history "
                "and propose concrete improvements to tools, prompts, or workflows. "
                "Focus on measurable improvements with expected impact."
            )),
            HumanMessage(content=f"Recent execution history:\n{past_steps_summary}\n\n"
                                 "Propose 1-3 specific, actionable improvements.")
        ]

        response = await llm.ainvoke(messages)

        return {
            "improvement_proposals": [response.content],
            "past_steps": [("improvement", response.content[:300])],
        }

    except Exception as e:
        logger.error(f"Self-improve node error: {e}", exc_info=True)
        return {
            "improvement_proposals": [f"ERROR: {str(e)}"],
            "past_steps": [("improvement", f"FAILED: {str(e)}")],
            "consecutive_errors": getattr(state, 'consecutive_errors', 0) + 1,
        }


# --- Routing Logic (Enterprise-Grade) ---

def route_task(state: CEOAgentState) -> Literal["analyst", "executor", "self_improver", "__end__"]:
    """Route with termination conditions: done signal, max iterations, error circuit breaker."""
    # Termination: planner said "done"
    active = getattr(state, 'active_agent', 'analyze')
    if active == "done":
        logger.info("✅ CEO declared DONE — terminating graph")
        return "__end__"

    # Termination: max iterations reached
    iteration = getattr(state, 'iteration_count', 0)
    if iteration >= MAX_ITERATIONS:
        logger.warning(f"⚠️ MAX_ITERATIONS ({MAX_ITERATIONS}) reached — terminating graph")
        return "__end__"

    # Termination: circuit breaker
    consecutive_errors = getattr(state, 'consecutive_errors', 0)
    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
        logger.error(f"🚨 Circuit breaker triggered ({consecutive_errors} consecutive errors) — terminating")
        return "__end__"

    # Normal routing
    routing_map = {
        "analyze": "analyst",
        "execute": "executor",
        "improve": "self_improver",
    }
    return routing_map.get(active, "analyst")


# --- Graph Construction ---

workflow = StateGraph(CEOAgentState)

workflow.add_node("planner", planning_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("executor", executor_node)
workflow.add_node("self_improver", self_improve_node)

workflow.add_edge("__start__", "planner")

workflow.add_conditional_edges(
    "planner",
    route_task,
    {
        "analyst": "analyst",
        "executor": "executor",
        "self_improver": "self_improver",
        "__end__": END,
    }
)

workflow.add_edge("analyst", "planner")
workflow.add_edge("executor", "planner")
workflow.add_edge("self_improver", "planner")

# Compile
graph = workflow.compile(name="Fitness CEO Agent")
