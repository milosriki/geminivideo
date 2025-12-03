"""
ULTIMATE PIPELINE API - Example Usage
Demonstrates how to use the end-to-end ad generation pipeline
"""

import asyncio
import httpx
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"


async def generate_campaign_example():
    """
    Example 1: Generate a complete ad campaign

    This will:
    1. Generate 50 ad blueprint variations using Director
    2. Evaluate each with Council of Titans
    3. Predict ROAS with Oracle
    4. Return ranked blueprints
    """

    print("=" * 80)
    print("EXAMPLE 1: Generate Ad Campaign")
    print("=" * 80)
    print()

    # Campaign request
    campaign_request = {
        "product_name": "PTD Fitness Coaching",
        "offer": "Book your free consultation - Limited spots available",
        "target_avatar": "Busy professionals in Dubai aged 30-45 who want to get in shape",
        "pain_points": [
            "no time for gym",
            "low energy throughout the day",
            "gaining weight despite trying diets",
            "feeling tired and unmotivated",
            "can't keep up with kids"
        ],
        "desires": [
            "look great in photos",
            "feel confident at work",
            "have high energy all day",
            "fit into old clothes",
            "be a role model for kids"
        ],
        "num_variations": 50,
        "platforms": ["instagram_reels", "tiktok", "youtube_shorts"],
        "approval_threshold": 85.0
    }

    print(f"📝 Requesting campaign generation...")
    print(f"   Product: {campaign_request['product_name']}")
    print(f"   Variations: {campaign_request['num_variations']}")
    print(f"   Platforms: {', '.join(campaign_request['platforms'])}")
    print()

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Generate campaign
        print("⏳ Generating campaign (this takes ~60 seconds)...")
        start_time = datetime.now()

        response = await client.post(
            f"{BASE_URL}/pipeline/generate-campaign",
            json=campaign_request
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if response.status_code == 200:
            result = response.json()

            print()
            print("✅ Campaign generated successfully!")
            print(f"   Duration: {duration:.1f} seconds")
            print(f"   Campaign ID: {result['campaign_id']}")
            print()

            print("📊 RESULTS:")
            print(f"   Total generated: {result['total_generated']}")
            print(f"   ✅ Approved: {result['approved']}")
            print(f"   ❌ Rejected: {result['rejected']}")
            print(f"   Approval rate: {result['approved'] / result['total_generated'] * 100:.1f}%")
            print()

            print("📈 PERFORMANCE METRICS:")
            print(f"   Avg Council Score: {result['avg_council_score']:.1f}/100")
            print(f"   Avg Predicted ROAS: {result['avg_predicted_roas']:.2f}x")
            print(f"   Best Predicted ROAS: {result['best_predicted_roas']:.2f}x")
            print()

            print("🏆 TOP 5 BLUEPRINTS (by predicted ROAS):")
            for i, bp in enumerate(result['blueprints'][:5], 1):
                print(f"\n   {i}. {bp['title']}")
                print(f"      Hook: {bp['hook_text'][:80]}...")
                print(f"      Council Score: {bp['council_score']:.1f}/100")
                print(f"      Predicted ROAS: {bp['predicted_roas']:.2f}x")
                print(f"      Confidence: {bp['confidence_level']}")
                print(f"      Emotional Triggers: {', '.join(bp['emotional_triggers'])}")

            print()
            print(f"💾 Full results: {len(result['blueprints'])} approved blueprints ready for rendering")
            print(f"🔗 WebSocket URL: {result['websocket_url']}")
            print()

            return result['campaign_id']
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None


async def render_winners_example(campaign_id: str):
    """
    Example 2: Render the top performing blueprints

    This will:
    1. Queue render jobs for top 10 blueprints
    2. Generate videos with GPU acceleration
    3. Add Hormozi-style captions
    4. Smart crop to platform format
    5. Upload to GCS
    """

    print("=" * 80)
    print("EXAMPLE 2: Render Winning Ads")
    print("=" * 80)
    print()

    render_request = {
        "campaign_id": campaign_id,
        "blueprint_ids": [],  # Empty = render top 10
        "platform": "instagram_reels",
        "quality": "HIGH",
        "add_captions": True,
        "caption_style": "hormozi",
        "smart_crop": True
    }

    print(f"🎬 Queuing render jobs for campaign: {campaign_id}")
    print(f"   Platform: {render_request['platform']}")
    print(f"   Quality: {render_request['quality']}")
    print(f"   Captions: {render_request['caption_style']}")
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/pipeline/render-winners",
            json=render_request
        )

        if response.status_code == 200:
            result = response.json()

            print("✅ Render jobs queued successfully!")
            print(f"   Total jobs: {result['total_jobs']}")
            print(f"   Estimated time: {result['estimated_time_seconds']} seconds")
            print(f"   ({result['estimated_time_seconds'] / 60:.1f} minutes)")
            print()

            print("📋 JOB IDs:")
            for job_id in result['render_job_ids']:
                print(f"   - {job_id}")

            print()
            print(f"🔗 WebSocket URL: {result['websocket_url']}")
            print(f"📊 Status URL: {result['status_url']}")
            print()

            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False


async def monitor_campaign_example(campaign_id: str):
    """
    Example 3: Monitor campaign progress

    Poll the status endpoint to check progress
    """

    print("=" * 80)
    print("EXAMPLE 3: Monitor Campaign Progress")
    print("=" * 80)
    print()

    print(f"📊 Checking status for campaign: {campaign_id}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/pipeline/campaign/{campaign_id}"
        )

        if response.status_code == 200:
            status = response.json()

            print("📝 GENERATION PHASE:")
            print(f"   Status: {status['generation_status']}")
            print(f"   Total blueprints: {status['total_blueprints']}")
            print(f"   Approved: {status['approved_blueprints']}")
            print(f"   Rejected: {status['rejected_blueprints']}")
            print()

            print("🎬 RENDER PHASE:")
            print(f"   Status: {status['render_status']}")
            print(f"   Total jobs: {status['total_render_jobs']}")
            print(f"   Completed: {status['completed_renders']}")
            print(f"   Failed: {status['failed_renders']}")

            if status['render_jobs']:
                print()
                print("📋 RENDER JOBS:")
                for job in status['render_jobs'][:5]:  # Show first 5
                    print(f"\n   Job: {job['job_id']}")
                    print(f"   Blueprint: {job['blueprint_id']}")
                    print(f"   Status: {job['status']}")
                    print(f"   Progress: {job['progress']}%")
                    if job['message']:
                        print(f"   Message: {job['message']}")
                    if job['download_url']:
                        print(f"   Download: {job['download_url']}")

            print()
            return status
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None


async def get_videos_example(campaign_id: str):
    """
    Example 4: Download rendered videos

    Get all completed videos with download URLs
    """

    print("=" * 80)
    print("EXAMPLE 4: Get Rendered Videos")
    print("=" * 80)
    print()

    print(f"📥 Fetching videos for campaign: {campaign_id}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{BASE_URL}/pipeline/campaign/{campaign_id}/videos"
        )

        if response.status_code == 200:
            result = response.json()

            print(f"✅ Found {result['total_videos']} completed videos")
            print()

            if result['videos']:
                print("📹 VIDEOS:")
                for i, video in enumerate(result['videos'], 1):
                    print(f"\n   {i}. Video ID: {video['video_id']}")
                    print(f"      Blueprint: {video['blueprint_id']}")
                    print(f"      Platform: {video['platform']}")
                    print(f"      Duration: {video['duration_seconds']}s")
                    print(f"      Size: {video['file_size_bytes'] / 1024 / 1024:.1f} MB")
                    print(f"      Council Score: {video['council_score']:.1f}")
                    print(f"      Predicted ROAS: {video['predicted_roas']:.2f}x")
                    print(f"      Hook: {video['hook_text'][:60]}...")
                    print(f"      CTA: {video['cta_text']}")
                    print(f"      Download URL: {video['video_url']}")
            else:
                print("⏳ No videos rendered yet. Check back in a few minutes.")

            print()
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None


async def full_workflow_example():
    """
    Complete workflow: Generate → Render → Monitor → Download
    """

    print("\n" + "=" * 80)
    print("COMPLETE WORKFLOW: Generate → Render → Monitor → Download")
    print("=" * 80)
    print()

    # Step 1: Generate campaign
    campaign_id = await generate_campaign_example()

    if not campaign_id:
        print("❌ Campaign generation failed. Exiting.")
        return

    print()
    input("Press Enter to continue to rendering...")
    print()

    # Step 2: Render top performers
    success = await render_winners_example(campaign_id)

    if not success:
        print("❌ Rendering failed. Exiting.")
        return

    print()
    print("⏳ Rendering in progress...")
    print("   In production, you would:")
    print("   1. Connect to WebSocket for real-time updates")
    print("   2. Show progress bar to user")
    print("   3. Send notification when complete")
    print()

    # Step 3: Monitor progress
    await monitor_campaign_example(campaign_id)

    print()
    input("Press Enter to fetch rendered videos...")
    print()

    # Step 4: Get videos
    await get_videos_example(campaign_id)

    print()
    print("🎉 WORKFLOW COMPLETE!")
    print()
    print("Next steps:")
    print("   1. Download videos from URLs")
    print("   2. Upload to Meta Ads Manager")
    print("   3. Launch campaigns")
    print("   4. Track ROAS in learning loop")
    print()


async def websocket_example(campaign_id: str):
    """
    Example 5: Real-time updates via WebSocket

    Note: This requires websockets library
    """

    print("=" * 80)
    print("EXAMPLE 5: WebSocket Real-Time Updates")
    print("=" * 80)
    print()

    print(f"🔌 Connecting to WebSocket for campaign: {campaign_id}")
    print()

    try:
        import websockets

        ws_url = f"ws://localhost:8000/pipeline/ws/{campaign_id}"

        async with websockets.connect(ws_url) as websocket:
            print("✅ Connected to WebSocket")
            print("📡 Listening for updates...")
            print()

            # Listen for 60 seconds
            import asyncio
            try:
                async with asyncio.timeout(60):
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)

                        msg_type = data.get('type')

                        if msg_type == 'generation_progress':
                            print(f"📝 Generation: {data['progress']}% - {data['message']}")

                        elif msg_type == 'blueprint_evaluated':
                            print(f"✅ Blueprint {data['blueprint_id']}: {data['score']:.1f} - {data.get('verdict', 'N/A')}")

                        elif msg_type == 'generation_complete':
                            print(f"🎉 Generation complete! {data['approved']} approved, {data['rejected']} rejected")

                        elif msg_type == 'render_started':
                            print(f"🎬 Render started: {data['job_id']}")

                        elif msg_type == 'render_progress':
                            print(f"📹 Rendering {data['job_id']}: {data['progress']}%")

                        elif msg_type == 'render_complete':
                            print(f"✅ Render complete: {data['job_id']}")
                            print(f"   Download: {data['download_url']}")

                        elif msg_type == 'campaign_complete':
                            print(f"🎉 Campaign complete!")
                            break

                        else:
                            print(f"📡 {msg_type}: {json.dumps(data, indent=2)}")

            except asyncio.TimeoutError:
                print()
                print("⏱️ Timeout - closing connection")

    except ImportError:
        print("❌ websockets library not installed")
        print("   Install with: pip install websockets")

    except Exception as e:
        print(f"❌ WebSocket error: {e}")


async def main():
    """
    Main function - run examples
    """

    print("\n" + "=" * 80)
    print("ULTIMATE PIPELINE API - USAGE EXAMPLES")
    print("=" * 80)
    print()
    print("Make sure the API server is running:")
    print("  cd /home/user/geminivideo/services/titan-core")
    print("  uvicorn api.main:app --reload")
    print()

    # Check if API is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/pipeline/health")
            if response.status_code == 200:
                print("✅ API server is running")
                print()
            else:
                print("⚠️ API server returned error")
                print()
    except Exception as e:
        print("❌ Cannot connect to API server")
        print(f"   Error: {e}")
        print()
        print("Please start the server first:")
        print("  uvicorn api.main:app --reload")
        print()
        return

    # Menu
    while True:
        print("=" * 80)
        print("EXAMPLES MENU")
        print("=" * 80)
        print()
        print("1. Generate Campaign (50 variations)")
        print("2. Render Winners (top 10 blueprints)")
        print("3. Monitor Campaign Progress")
        print("4. Get Rendered Videos")
        print("5. WebSocket Real-Time Updates")
        print("6. Full Workflow (All steps)")
        print("0. Exit")
        print()

        choice = input("Select example (0-6): ").strip()
        print()

        if choice == "0":
            print("👋 Goodbye!")
            break

        elif choice == "1":
            await generate_campaign_example()

        elif choice == "2":
            campaign_id = input("Enter campaign ID: ").strip()
            await render_winners_example(campaign_id)

        elif choice == "3":
            campaign_id = input("Enter campaign ID: ").strip()
            await monitor_campaign_example(campaign_id)

        elif choice == "4":
            campaign_id = input("Enter campaign ID: ").strip()
            await get_videos_example(campaign_id)

        elif choice == "5":
            campaign_id = input("Enter campaign ID: ").strip()
            await websocket_example(campaign_id)

        elif choice == "6":
            await full_workflow_example()

        else:
            print("❌ Invalid choice")

        print()
        input("Press Enter to continue...")
        print("\n" * 2)


if __name__ == "__main__":
    asyncio.run(main())
