"""
Titan Bridge Examples
=====================

Comprehensive examples demonstrating all Titan Bridge capabilities.

Run examples:
    python -m examples.titan_bridge_examples example1
    python -m examples.titan_bridge_examples example2
    python -m examples.titan_bridge_examples all
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.titan_bridge.titan_tools import (
    evaluate_with_council,
    generate_with_director,
    run_antigravity_loop
)
from src.titan_bridge import TitanBridgeState, create_council_node, create_director_node
from src.agent.graph import graph
from src.agent.state import CEOAgentState


# =============================================================================
# EXAMPLE 1: Basic Council Evaluation
# =============================================================================

async def example1_basic_evaluation():
    """
    Example 1: Evaluate a fitness ad script with the Titan Council.

    This demonstrates:
    - Using evaluate_with_council tool
    - Interpreting verdict and scores
    - Understanding council breakdown
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Council Evaluation")
    print("="*70 + "\n")

    # Sample ad script
    script = """
    Hook: Are you tired of yo-yo dieting and gym memberships you never use?

    Body:
    Imagine transforming your body in just 30 days - no equipment needed.
    Our AI-powered fitness system adapts to YOUR schedule, YOUR fitness level.
    Join 50,000+ people who've already transformed their lives.

    CTA: Start your FREE 7-day trial now. Cancel anytime.
    """

    print("📝 Script to evaluate:")
    print(script)
    print("\n🏛️ Sending to Council for evaluation...\n")

    # Evaluate with council
    result = await evaluate_with_council(script, niche="fitness")

    # Display results
    print(f"⚖️ VERDICT: {result['verdict']}")
    print(f"📊 FINAL SCORE: {result['final_score']}/100")
    print(f"🎯 CONFIDENCE: {result['confidence']:.0%}")
    print("\n💡 FEEDBACK:")
    print(f"   {result['feedback']}")

    print("\n📊 MODEL BREAKDOWN:")
    for model, score in result['breakdown'].items():
        print(f"   {model:20s}: {score:.1f}/100")

    # Decision logic
    print("\n🤔 DECISION:")
    if result['verdict'] == "APPROVED":
        print("   ✅ Script is ready for production!")
    else:
        print("   ⚠️ Script needs revision. Follow the feedback above.")

    return result


# =============================================================================
# EXAMPLE 2: Director Generation with Iterations
# =============================================================================

async def example2_director_generation():
    """
    Example 2: Generate a viral ad script using the Titan Director.

    This demonstrates:
    - Using generate_with_director tool
    - Iterative improvement process
    - Understanding generation status
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Director Generation with Iterations")
    print("="*70 + "\n")

    # Creative brief
    context = "High-intensity interval training program for busy professionals who want to get fit in 20 minutes per day"

    print("📋 Creative Brief:")
    print(f"   {context}")
    print("\n🎬 Director is generating script...\n")

    # Generate with director
    result = await generate_with_director(
        video_context=context,
        niche="fitness",
        max_iterations=3
    )

    # Display results
    print(f"🎥 GENERATION STATUS: {result['status']}")
    print(f"🔄 TURNS TAKEN: {result['turns_taken']}")
    print(f"🤖 MODEL USED: {result['model_used']}")

    print("\n📜 GENERATED SCRIPT:")
    print("-" * 70)
    print(result['blueprint'])
    print("-" * 70)

    # Council review
    if result['council_review']:
        review = result['council_review']
        print(f"\n⚖️ COUNCIL REVIEW:")
        print(f"   Verdict: {review['verdict']}")
        print(f"   Score: {review['final_score']}/100")
        print(f"   Feedback: {review['feedback']}")

    return result


# =============================================================================
# EXAMPLE 3: Full Antigravity Loop
# =============================================================================

async def example3_antigravity_loop():
    """
    Example 3: Run the complete Titan Antigravity Loop.

    This demonstrates:
    - Using run_antigravity_loop tool
    - Complete Director → Council → Iterate flow
    - Performance metrics
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Full Antigravity Loop")
    print("="*70 + "\n")

    context = "New Year fitness challenge: Transform your body in 90 days with our proven system"

    print("🌀 Starting Antigravity Loop...")
    print(f"📋 Context: {context}")
    print(f"🎯 Niche: fitness")
    print(f"📊 Approval Threshold: 87.0")
    print("\n")

    # Run antigravity loop
    result = await run_antigravity_loop(
        video_context=context,
        niche="fitness",
        approval_threshold=87.0
    )

    # Display results
    print(f"🏁 LOOP COMPLETE!")
    print(f"   Status: {result['status']}")
    print(f"   Final Score: {result['final_score']}/100")
    print(f"   Iterations: {result['iterations']}")
    print(f"   Time Taken: {result['total_time']:.2f} seconds")

    print("\n📜 FINAL OUTPUT:")
    print("-" * 70)
    print(result['blueprint'])
    print("-" * 70)

    # Performance analysis
    print(f"\n⏱️ PERFORMANCE METRICS:")
    print(f"   Average time per iteration: {result['total_time'] / max(result['iterations'], 1):.2f}s")
    print(f"   Status: {'✅ APPROVED' if result['status'] == 'APPROVED' else '⚠️ NEEDS WORK'}")

    return result


# =============================================================================
# EXAMPLE 4: CEO Agent with Titan Integration
# =============================================================================

async def example4_ceo_integration():
    """
    Example 4: Use CEO Agent with built-in Titan integration.

    This demonstrates:
    - CEO Agent orchestration
    - Automatic routing to creative_review
    - Integration of Titan insights into CEO decisions
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: CEO Agent with Titan Integration")
    print("="*70 + "\n")

    # Initialize CEO state with creative content
    initial_state = CEOAgentState(
        current_plan=["Review and evaluate new ad campaign creative"],
        business_metrics={"monthly_revenue": 100000},
        analysis_results={
            "creative_content": """
            Hook: Stop wasting money on gym memberships you never use!
            Body: Our 20-minute home workout system has helped 10,000+ busy professionals get in the best shape of their lives.
            CTA: Join now and get 50% off your first month!
            """
        }
    )

    print("🧠 CEO Agent starting...")
    print("📋 Initial Plan: Review new ad campaign creative")
    print("\n")

    # Run CEO agent (it will automatically route to creative_review if needed)
    # Note: This is a simplified example - actual CEO agent has more complex logic
    print("🎯 CEO is analyzing the situation...")
    print("🎨 CEO detects creative content - routing to Titan Council...")

    # Manually trigger creative review for this example
    from src.agent.graph import creative_review_node
    result = await creative_review_node(initial_state)

    print("\n✅ Creative Review Complete!")
    print("\n📊 RESULTS:")
    if 'creative_review' in result.get('analysis_results', {}):
        review = result['analysis_results']['creative_review']
        print(f"   Verdict: {review['council_verdict']}")
        print(f"   Score: {review['council_score']}/100")
        print(f"   Feedback: {review['council_feedback']}")

    print("\n🧠 CEO can now make strategic decisions based on Titan insights...")

    return result


# =============================================================================
# EXAMPLE 5: TitanBridgeState Direct Usage
# =============================================================================

async def example5_bridge_state():
    """
    Example 5: Use TitanBridgeState directly for custom workflows.

    This demonstrates:
    - Creating custom LangGraph workflows with TitanBridgeState
    - State management and routing
    - Tracking council results and director output
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: TitanBridgeState Direct Usage")
    print("="*70 + "\n")

    from langgraph.graph import StateGraph

    # Create workflow with TitanBridgeState
    workflow = StateGraph(TitanBridgeState)

    # Add nodes
    council_node = create_council_node()
    director_node = create_director_node()

    workflow.add_node("director", director_node)
    workflow.add_node("council", council_node)

    # Set up routing
    workflow.add_edge("__start__", "director")
    workflow.add_edge("director", "council")

    # Compile
    custom_graph = workflow.compile()

    # Initialize state
    print("📝 Initializing TitanBridgeState...")
    state = TitanBridgeState(
        titan_context="Create a compelling fitness ad for weight loss transformation",
        titan_niche="fitness",
        max_titan_iterations=2,
        titan_approval_threshold=85.0
    )

    print(f"   Context: {state.titan_context}")
    print(f"   Niche: {state.titan_niche}")
    print(f"   Max Iterations: {state.max_titan_iterations}")
    print("\n🚀 Running custom workflow...\n")

    # Run workflow
    final_state = await custom_graph.ainvoke(state)

    # Display state summary
    print("\n📊 FINAL STATE SUMMARY:")
    print(final_state.get_titan_summary())

    # Access results
    latest_council = final_state.get_latest_council_result()
    latest_director = final_state.get_latest_director_output()

    if latest_council:
        print(f"\n⚖️ LATEST COUNCIL RESULT:")
        print(f"   Verdict: {latest_council.verdict}")
        print(f"   Score: {latest_council.final_score}/100")

    if latest_director:
        print(f"\n🎬 LATEST DIRECTOR OUTPUT:")
        print(f"   Status: {latest_director.status}")
        print(f"   Turns: {latest_director.turns_taken}")
        print(f"\n   Blueprint:")
        print(f"   {latest_director.blueprint[:200]}...")

    return final_state


# =============================================================================
# EXAMPLE 6: Batch Evaluation
# =============================================================================

async def example6_batch_evaluation():
    """
    Example 6: Batch evaluate multiple scripts in parallel.

    This demonstrates:
    - Parallel council evaluations
    - Comparing multiple variations
    - Performance optimization with asyncio
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Batch Evaluation")
    print("="*70 + "\n")

    # Multiple script variations
    scripts = {
        "Version A": "Hook: Get fit in 30 days! Body: Our proven system works. CTA: Join now!",
        "Version B": "Hook: Tired of fake fitness promises? Body: Real results, real science. CTA: Start your transformation!",
        "Version C": "Hook: What if you could transform your body in just 20 minutes a day? Body: Join 50,000+ success stories. CTA: Try it free!"
    }

    print("📝 Evaluating 3 script variations in parallel...\n")

    # Evaluate all in parallel
    tasks = [
        evaluate_with_council(script, "fitness")
        for script in scripts.values()
    ]

    import time
    start = time.time()
    results = await asyncio.gather(*tasks)
    end = time.time()

    # Display results
    print("📊 EVALUATION RESULTS:")
    print("-" * 70)
    for (name, script), result in zip(scripts.items(), results):
        print(f"\n{name}:")
        print(f"  Verdict: {result['verdict']}")
        print(f"  Score: {result['final_score']}/100")
        print(f"  Feedback: {result['feedback'][:60]}...")

    # Find winner
    winner_idx = max(range(len(results)), key=lambda i: results[i]['final_score'])
    winner_name = list(scripts.keys())[winner_idx]
    winner_score = results[winner_idx]['final_score']

    print("\n" + "-" * 70)
    print(f"🏆 WINNER: {winner_name} with score {winner_score}/100")
    print(f"⏱️ Total time: {end - start:.2f}s ({(end - start) / len(scripts):.2f}s per script)")

    return results


# =============================================================================
# MAIN: Run Examples
# =============================================================================

async def main():
    """Run all examples or a specific one"""
    examples = {
        "example1": ("Basic Council Evaluation", example1_basic_evaluation),
        "example2": ("Director Generation", example2_director_generation),
        "example3": ("Full Antigravity Loop", example3_antigravity_loop),
        "example4": ("CEO Agent Integration", example4_ceo_integration),
        "example5": ("TitanBridgeState Usage", example5_bridge_state),
        "example6": ("Batch Evaluation", example6_batch_evaluation),
    }

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "all":
            # Run all examples
            for name, (title, func) in examples.items():
                try:
                    await func()
                    print("\n✅ Example completed successfully!\n")
                except Exception as e:
                    print(f"\n❌ Example failed: {e}\n")
        elif arg in examples:
            # Run specific example
            name, func = examples[arg]
            try:
                await func()
                print("\n✅ Example completed successfully!\n")
            except Exception as e:
                print(f"\n❌ Example failed: {e}\n")
        else:
            print(f"Unknown example: {arg}")
            print("Available examples:")
            for name, (title, _) in examples.items():
                print(f"  - {name}: {title}")
    else:
        # Show help
        print("Titan Bridge Examples")
        print("=====================\n")
        print("Usage: python -m examples.titan_bridge_examples [example_name]\n")
        print("Available examples:")
        for name, (title, _) in examples.items():
            print(f"  - {name}: {title}")
        print("\nRun all: python -m examples.titan_bridge_examples all")


if __name__ == "__main__":
    asyncio.run(main())
