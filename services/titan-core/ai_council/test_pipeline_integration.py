"""
Integration test for WinningAdsGenerator in Ultimate Pipeline
Verifies the wiring is correct without needing actual video generation
"""

import asyncio
import sys
from pathlib import Path

# Add video-agent to path
video_agent_path = Path(__file__).parent.parent.parent / "video-agent"
if video_agent_path.exists():
    sys.path.insert(0, str(video_agent_path))


async def test_pipeline_initialization():
    """Test that pipeline initializes and WinningAdsGenerator is available"""
    print("Testing Ultimate Pipeline with WinningAdsGenerator integration...\n")

    from ultimate_pipeline import UltimatePipeline, PipelineConfig

    # Create pipeline
    pipeline = UltimatePipeline()

    # Initialize (this will attempt to load WinningAdsGenerator)
    await pipeline.initialize()

    # Check if WinningAdsGenerator loaded
    if pipeline.winning_ads:
        print("✅ WinningAdsGenerator successfully loaded!")
        print(f"   Output directory: {pipeline.winning_ads.output_dir}")
        print(f"   Type: {type(pipeline.winning_ads).__name__}")
        return True
    else:
        print("⚠️  WinningAdsGenerator not available")
        print("   This is expected if dependencies are missing")
        return False


async def test_helper_methods():
    """Test that helper methods work correctly"""
    print("\nTesting helper methods...\n")

    from ultimate_pipeline import UltimatePipeline, PipelineConfig

    pipeline = UltimatePipeline()
    await pipeline.initialize()

    # Create test config
    config = PipelineConfig(
        product_name="Test Product",
        offer="Free consultation",
        target_avatar="Tech professionals",
        pain_points=["long hours", "stress"],
        desires=["work-life balance", "more income"],
        platforms=["instagram"],
        caption_style="hormozi",
        color_grade="cinematic"
    )

    # Create test blueprint
    blueprint = {
        "hook_text": "Struggling with burnout?",
        "hook_type": "problem_solution",
        "cta_text": "Book your free call",
        "emotional_triggers": ["urgency", "inspiration"]
    }

    try:
        # Test _prepare_ad_assets
        assets = pipeline._prepare_ad_assets(blueprint, config)
        print(f"✅ _prepare_ad_assets works - Type: {type(assets).__name__}")

        # Test _prepare_ad_config
        ad_config = pipeline._prepare_ad_config(blueprint, config)
        print(f"✅ _prepare_ad_config works - Template: {ad_config.template}")
        print(f"   Platform: {ad_config.platform}")
        print(f"   Caption style: {ad_config.caption_style}")
        print(f"   Color grade: {ad_config.color_grade}")

        return True
    except Exception as e:
        print(f"❌ Helper methods failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("ULTIMATE PIPELINE INTEGRATION TEST")
    print("Testing WinningAdsGenerator Integration")
    print("=" * 60)
    print()

    test1 = await test_pipeline_initialization()
    test2 = await test_helper_methods()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("🎉 ALL TESTS PASSED!")
        print("WinningAdsGenerator is properly wired into the pipeline")
    elif test2:
        print("⚠️  PARTIAL SUCCESS")
        print("Helper methods work, but WinningAdsGenerator not available")
        print("This is OK if video-agent dependencies aren't installed")
    else:
        print("❌ TESTS FAILED")
        print("Check the errors above")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
