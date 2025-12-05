"""
OpenAI November 2025 Features - Example Usage Guide

This file demonstrates how to use the upgraded AI Council with:
- o1 reasoning models for complex analysis
- GPT-4o (2024-11-20) for vision analysis
- GPT-4o-mini for cost-optimized scoring
- Batch API for bulk processing
- Structured outputs with JSON schemas

Updated: December 2025
"""

import asyncio
import os
from typing import List
from council_of_titans import council


# ============================================================================
# EXAMPLE 1: Simple Script Evaluation (Cost-Optimized)
# ============================================================================

async def example_simple_evaluation():
    """
    Uses GPT-4o-mini for fast, cost-effective scoring
    Perfect for: Quick checks, A/B test validation, high-volume processing
    Cost: ~90% cheaper than GPT-4o
    """
    print("=" * 80)
    print("EXAMPLE 1: Simple Script Evaluation (Cost-Optimized)")
    print("=" * 80)

    script = """
    Hook: "You're doing your morning routine all wrong..."
    Body: Here's the 5-minute ritual that successful people use to 10X their day.
    CTA: Download the free morning routine checklist below!
    """

    # Standard evaluation uses GPT-4o-mini by default
    result = await council.evaluate_script(script, use_o1=False)

    print(f"\nFinal Score: {result['final_score']}/100")
    print(f"Verdict: {result['verdict']}")
    print(f"OpenAI Model Used: {result['breakdown']['openai_model']}")
    print(f"\nBreakdown:")
    for model, score in result['breakdown'].items():
        if isinstance(score, (int, float)):
            print(f"  - {model}: {score}")


# ============================================================================
# EXAMPLE 2: Deep Reasoning Analysis with o1
# ============================================================================

async def example_o1_reasoning():
    """
    Uses OpenAI o1 for complex logical reasoning
    Perfect for: Final approval decisions, complex script analysis, strategic evaluation
    Features: Extended chain-of-thought, deep structural analysis
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Deep Reasoning Analysis with o1")
    print("=" * 80)

    script = """
    Hook: "I lost $100K following traditional advice..."
    Body: Then I discovered this counterintuitive approach that made me $2M in 18 months.
    Story: I was broke, desperate, and ready to quit. Everyone told me to play it safe...
    CTA: Click to learn the 3 rules that changed everything.
    """

    # Use o1 for deep reasoning (higher quality, higher cost)
    result = await council.evaluate_script(script, use_o1=True)

    print(f"\nFinal Score: {result['final_score']}/100")
    print(f"Verdict: {result['verdict']}")
    print(f"OpenAI Model Used: {result['breakdown']['openai_model']}")
    print(f"Council Members:")
    for member, source in result['council_members'].items():
        print(f"  - {member}: {source}")


# ============================================================================
# EXAMPLE 3: Vision Analysis with GPT-4o (Latest)
# ============================================================================

async def example_vision_analysis():
    """
    Uses GPT-4o (2024-11-20) for multimodal analysis
    Perfect for: Video thumbnail analysis, visual element extraction
    Features: Improved vision, color detection, composition analysis
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Vision Analysis with GPT-4o (Latest)")
    print("=" * 80)

    script = "Transform your body in 90 days with our proven system!"

    # Example: If you have a video thumbnail
    # image_path = "/path/to/thumbnail.jpg"
    # Or use a URL:
    image_path = "https://example.com/video-thumbnail.jpg"

    # Note: This will fail without a real image, but demonstrates the API
    try:
        result = await council.evaluate_script(
            script,
            image_path=image_path,  # Pass image for vision analysis
            use_o1=False
        )

        if "vision_analysis" in result:
            print(f"\nVision Analysis Results:")
            print(f"  - Visual Score: {result['vision_analysis']['visual_score']}")
            print(f"  - Has Human Face: {result['vision_analysis']['has_human_face']}")
            print(f"  - Scene: {result['vision_analysis']['scene_description']}")
            print(f"  - Attention Elements: {result['vision_analysis']['attention_elements']}")
    except Exception as e:
        print(f"\nNote: Vision analysis requires a valid image path/URL")
        print(f"Error: {e}")


# ============================================================================
# EXAMPLE 4: Batch API for Bulk Processing
# ============================================================================

async def example_batch_processing():
    """
    Uses Batch API for non-urgent bulk analysis
    Perfect for: A/B test variations, historical analysis, overnight processing
    Benefits: 50% cost reduction, process up to 100K requests
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Batch API for Bulk Processing")
    print("=" * 80)

    # Prepare multiple scripts for batch analysis
    scripts = [
        "Hook: Tired of boring workouts? Body: Try this 7-minute routine. CTA: Start now!",
        "Hook: Your diet is sabotaging you. Body: Here's the real problem. CTA: Learn more.",
        "Hook: I made $50K in 30 days. Body: Using this simple strategy. CTA: Get the guide.",
        "Hook: Stop wasting money on ads. Body: Use this framework instead. CTA: Download free.",
        "Hook: The secret to viral content? Body: It's simpler than you think. CTA: Watch now."
    ]

    # Enable batch mode (set OPENAI_BATCH_ENABLED=true in environment)
    if os.getenv("OPENAI_BATCH_ENABLED", "false").lower() == "true":
        # Create batch job
        batch_job_id = await council.batch_create_job(scripts)

        if batch_job_id:
            print(f"\n✅ Batch job created: {batch_job_id}")
            print(f"   - Scripts queued: {len(scripts)}")
            print(f"   - Cost savings: 50%")
            print(f"   - Completion time: 24 hours")
            print(f"\nTo retrieve results later:")
            print(f"   results = await council.batch_retrieve_results('{batch_job_id}')")

            # You can check status later:
            # results = await council.batch_retrieve_results(batch_job_id)
            # if results:
            #     print(f"Batch completed! {len(results)} results available")
    else:
        print("\nBatch API is disabled.")
        print("To enable: export OPENAI_BATCH_ENABLED=true")
        print("\nBenefits of Batch API:")
        print("  - 50% cost reduction vs real-time API")
        print("  - Process up to 100,000 requests per batch")
        print("  - 24-hour turnaround time")
        print("  - Perfect for A/B testing and bulk analysis")


# ============================================================================
# EXAMPLE 5: Detailed Critique with o1
# ============================================================================

async def example_detailed_critique():
    """
    Uses o1 for comprehensive script breakdown
    Perfect for: Final approval, learning from high-performing scripts
    Features: Detailed strengths/weaknesses, improvement suggestions
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Detailed Critique with o1")
    print("=" * 80)

    script = """
    Hook: "I was 40 pounds overweight and hated looking in the mirror..."
    Body: Then I discovered the 3 foods that were sabotaging my metabolism.
    After cutting them out, I lost 40 pounds in 90 days without counting calories.
    Story: Doctors told me it was my age. Trainers said I wasn't working hard enough.
    But the truth was simpler - and it changed everything.
    CTA: Click below to discover the 3 foods and start your transformation today.
    """

    result = await council.evaluate_with_detailed_critique(script)

    if "detailed_analysis" in result:
        print(f"\nDetailed Analysis:")
        print(f"\n{result['detailed_analysis']}")
        print(f"\nModel: {result['model']}")
        print(f"Reasoning Tokens: {result.get('reasoning_tokens', 0)}")
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")


# ============================================================================
# EXAMPLE 6: Model Selection Strategy
# ============================================================================

def example_model_selection_guide():
    """
    Guide for choosing the right OpenAI model
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Model Selection Strategy Guide")
    print("=" * 80)

    print("""
    ┌─────────────────┬──────────────────┬────────────┬─────────────────────────┐
    │ Model           │ Use Case         │ Cost       │ Best For                │
    ├─────────────────┼──────────────────┼────────────┼─────────────────────────┤
    │ o1              │ Complex reasoning│ High       │ Final approvals,        │
    │                 │ Deep analysis    │            │ strategic decisions,    │
    │                 │                  │            │ complex logic           │
    ├─────────────────┼──────────────────┼────────────┼─────────────────────────┤
    │ o1-mini         │ Fast reasoning   │ Medium     │ Quick checks,           │
    │                 │ Logical checks   │            │ validation, QA          │
    ├─────────────────┼──────────────────┼────────────┼─────────────────────────┤
    │ gpt-4o-2024-    │ Multimodal       │ Medium-High│ Vision analysis,        │
    │ 11-20 (Latest)  │ Vision, audio    │            │ video thumbnails,       │
    │                 │                  │            │ image + text            │
    ├─────────────────┼──────────────────┼────────────┼─────────────────────────┤
    │ gpt-4o-mini     │ Simple scoring   │ Very Low   │ Bulk processing,        │
    │                 │ Quick evaluation │ (90% less) │ A/B tests, high-volume  │
    └─────────────────┴──────────────────┴────────────┴─────────────────────────┘

    COST OPTIMIZATION STRATEGIES:

    1. Default Mode (use_o1=False):
       - Uses gpt-4o-mini for scoring
       - 90% cheaper than GPT-4o
       - Perfect for most evaluations

    2. High-Quality Mode (use_o1=True):
       - Uses o1 for deep reasoning
       - Best for final approval decisions
       - Higher cost, higher quality

    3. Batch Processing:
       - 50% cost reduction
       - 24-hour turnaround
       - Best for non-urgent bulk analysis

    4. Vision Analysis:
       - Uses gpt-4o-2024-11-20
       - Only when image_path provided
       - Analyzes thumbnails, frames, visual elements

    EXAMPLE COST COMPARISON (1000 scripts):

    Standard (gpt-4o):        $50.00
    Optimized (gpt-4o-mini):  $5.00   (90% savings)
    Batch (gpt-4o-mini):      $2.50   (95% savings)
    """)


# ============================================================================
# MAIN RUNNER
# ============================================================================

async def main():
    """
    Run all examples
    """
    print("\n" + "=" * 80)
    print("OpenAI November 2025 Features - Complete Examples")
    print("AI Council Upgrade Demonstration")
    print("=" * 80)

    # Run examples
    await example_simple_evaluation()
    await example_o1_reasoning()
    await example_vision_analysis()
    await example_batch_processing()
    await example_detailed_critique()
    example_model_selection_guide()

    print("\n" + "=" * 80)
    print("Examples Complete!")
    print("=" * 80)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
