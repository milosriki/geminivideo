"""
Batch API Integration Examples

AGENT 42: 10x LEVERAGE - Integration Guide

This file shows how to integrate batch processing into existing services.
"""

import asyncio
from typing import List, Dict, Any
from src.batch_processor import (
    BatchProcessor,
    BatchJobType,
    BatchProvider
)


# ============================================================================
# EXAMPLE 1: Creative Scoring Integration
# ============================================================================

async def score_creative_batch(creative_ids: List[str], scripts: List[str]):
    """
    Score multiple creatives using batch processing.

    Before: Each creative scored immediately at $0.01
    After: Batch processing at $0.005 (50% savings!)
    """
    batch = BatchProcessor()

    print(f"Queueing {len(creative_ids)} creatives for batch scoring...")

    job_ids = []
    for creative_id, script in zip(creative_ids, scripts):
        job_id = await batch.queue_job(
            job_type=BatchJobType.CREATIVE_SCORING,
            provider=BatchProvider.OPENAI,
            data={
                "creative_id": creative_id,
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a creative scoring expert."
                    },
                    {
                        "role": "user",
                        "content": f"Score this creative:\n\n{script}"
                    }
                ],
                "temperature": 0.3
            },
            priority=5
        )
        job_ids.append(job_id)

    print(f"✅ Queued {len(job_ids)} jobs. Results available in 24 hours.")
    return job_ids


# ============================================================================
# EXAMPLE 2: Embedding Generation Integration
# ============================================================================

async def generate_embeddings_batch(texts: List[str]):
    """
    Generate embeddings for multiple texts using batch processing.

    Perfect for:
    - Initial data ingestion
    - Historical data processing
    - Bulk imports
    """
    batch = BatchProcessor()

    print(f"Queueing {len(texts)} texts for embedding generation...")

    job_ids = []
    for i, text in enumerate(texts):
        job_id = await batch.queue_job(
            job_type=BatchJobType.EMBEDDING_GENERATION,
            provider=BatchProvider.OPENAI,
            data={
                "model": "text-embedding-3-large",
                "input": text,
                "index": i  # Track original order
            },
            priority=3  # Lower priority for embeddings
        )
        job_ids.append(job_id)

    print(f"✅ Queued {len(job_ids)} embedding jobs.")
    return job_ids


# ============================================================================
# EXAMPLE 3: Video Analysis Integration
# ============================================================================

async def analyze_videos_batch(video_urls: List[str]):
    """
    Analyze multiple videos using batch processing.

    Use cases:
    - Nightly video processing
    - Bulk uploads
    - Historical video analysis
    """
    batch = BatchProcessor()

    print(f"Queueing {len(video_urls)} videos for analysis...")

    job_ids = []
    for video_url in video_urls:
        job_id = await batch.queue_job(
            job_type=BatchJobType.VIDEO_ANALYSIS,
            provider=BatchProvider.GEMINI,
            data={
                "video_url": video_url,
                "analysis_type": "full",
                "extract_hooks": True,
                "sentiment_analysis": True
            },
            priority=4
        )
        job_ids.append(job_id)

    print(f"✅ Queued {len(job_ids)} video analysis jobs.")
    return job_ids


# ============================================================================
# EXAMPLE 4: Historical Data Reprocessing
# ============================================================================

async def reprocess_historical_campaigns():
    """
    Reprocess historical campaigns with updated models.

    This is perfect for:
    - Model improvements
    - New feature backfilling
    - Data quality improvements
    """
    batch = BatchProcessor()

    # Simulate fetching historical campaigns
    campaigns = [
        {"id": "camp_1", "data": "..."},
        {"id": "camp_2", "data": "..."},
        # ... potentially thousands of campaigns
    ]

    print(f"Reprocessing {len(campaigns)} historical campaigns...")

    job_ids = []
    for campaign in campaigns:
        job_id = await batch.queue_job(
            job_type=BatchJobType.HISTORICAL_REPROCESSING,
            provider=BatchProvider.OPENAI,
            data={
                "campaign_id": campaign["id"],
                "operation": "recalculate_scores",
                "model": "gpt-4o"
            },
            priority=1  # Lowest priority for historical data
        )
        job_ids.append(job_id)

    print(f"✅ Queued {len(job_ids)} reprocessing jobs.")
    return job_ids


# ============================================================================
# EXAMPLE 5: Checking Batch Results
# ============================================================================

async def check_and_retrieve_results(batch_id: str):
    """
    Check batch status and retrieve results when complete.
    """
    batch = BatchProcessor()

    print(f"Checking status of batch: {batch_id}")

    # Check status
    status = await batch.check_batch_status(batch_id)

    print(f"Status: {status.get('status')}")
    print(f"Jobs: {status.get('job_count')}")
    print(f"Savings: ${status.get('cost_savings', 0):.2f}")

    # If completed, retrieve results
    if status.get('status') == 'completed':
        print("✅ Batch completed! Retrieving results...")

        results = await batch.retrieve_batch_results(batch_id)

        print(f"Retrieved {len(results)} results")

        for result in results:
            # Process each result
            print(f"Result: {result.get('custom_id')}")
            # Store in database, trigger callbacks, etc.

        return results

    else:
        print(f"⏳ Batch still processing. Status: {status.get('status')}")
        return None


# ============================================================================
# EXAMPLE 6: Smart Fallback Strategy
# ============================================================================

async def score_creative_with_fallback(
    creative_id: str,
    script: str,
    urgent: bool = False
):
    """
    Smart strategy: Use batch processing by default, fallback to realtime if urgent.

    This gives you the best of both worlds:
    - Cost savings for non-urgent tasks
    - Speed for urgent tasks
    """
    if urgent:
        # Urgent: Process immediately (more expensive)
        print(f"⚡ Urgent request - processing immediately")
        from council_of_titans import CouncilEvaluator

        council = CouncilEvaluator()
        result = await council.evaluate_script(script, "fitness")
        return result
    else:
        # Non-urgent: Queue for batch processing (50% cheaper)
        print(f"💰 Non-urgent request - queuing for batch processing")
        batch = BatchProcessor()

        job_id = await batch.queue_job(
            job_type=BatchJobType.CREATIVE_SCORING,
            provider=BatchProvider.OPENAI,
            data={
                "creative_id": creative_id,
                "script": script
            }
        )

        return {"job_id": job_id, "status": "queued"}


# ============================================================================
# EXAMPLE 7: Monitoring and Metrics
# ============================================================================

async def show_batch_metrics():
    """
    Display batch processing metrics and cost savings.
    """
    from src.batch_monitoring import BatchMonitor

    monitor = BatchMonitor()

    # Get dashboard data
    dashboard = monitor.get_dashboard_data()

    print("\n" + "=" * 60)
    print("BATCH PROCESSING METRICS")
    print("=" * 60)

    overview = dashboard.get("overview", {})
    print(f"\n📊 Overview:")
    print(f"   Total Jobs Queued: {overview.get('total_jobs_queued'):,}")
    print(f"   Total Jobs Processed: {overview.get('total_jobs_processed'):,}")
    print(f"   Total Batches: {overview.get('total_batches_submitted'):,}")
    print(f"   Success Rate: {overview.get('success_rate'):.1f}%")
    print(f"   Active Batches: {overview.get('active_batches')}")

    print(f"\n💰 Cost Savings:")
    print(f"   Total Saved: ${overview.get('total_cost_savings', 0):.2f}")

    # Cost savings report
    savings = monitor.get_cost_savings_report()
    print(f"   Savings Percentage: {savings.savings_percentage:.1f}%")
    print(f"   Jobs Processed: {savings.jobs_processed:,}")

    print(f"\n📈 By Job Type:")
    for job_type, amount in savings.savings_by_type.items():
        print(f"   {job_type}: ${amount:.2f}")

    # Alerts
    alerts = monitor.check_alerts()
    if alerts:
        print(f"\n🚨 Alerts ({len(alerts)}):")
        for alert in alerts:
            print(f"   [{alert['severity'].upper()}] {alert['message']}")

    print("\n" + "=" * 60)


# ============================================================================
# MAIN DEMO
# ============================================================================

async def main():
    """
    Run all examples to demonstrate batch processing.
    """
    print("=" * 60)
    print("BATCH PROCESSING INTEGRATION EXAMPLES")
    print("=" * 60)

    # Example 1: Score creatives
    print("\n\n1️⃣  Creative Scoring")
    print("-" * 60)
    await score_creative_batch(
        creative_ids=["creative_1", "creative_2", "creative_3"],
        scripts=[
            "Stop wasting money on gym memberships...",
            "Transform your body in 30 days...",
            "Professional trainer in your pocket..."
        ]
    )

    # Example 2: Generate embeddings
    print("\n\n2️⃣  Embedding Generation")
    print("-" * 60)
    await generate_embeddings_batch([
        "Hook 1: Problem-focused",
        "Hook 2: Solution-focused",
        "Hook 3: Benefit-focused"
    ])

    # Example 3: Analyze videos
    print("\n\n3️⃣  Video Analysis")
    print("-" * 60)
    await analyze_videos_batch([
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4"
    ])

    # Example 4: Reprocess historical data
    print("\n\n4️⃣  Historical Reprocessing")
    print("-" * 60)
    await reprocess_historical_campaigns()

    # Example 5: Smart fallback
    print("\n\n5️⃣  Smart Fallback Strategy")
    print("-" * 60)
    await score_creative_with_fallback(
        creative_id="test_1",
        script="Test creative",
        urgent=False  # Use batch processing
    )

    # Example 6: Show metrics
    print("\n\n6️⃣  Batch Metrics")
    print("-" * 60)
    await show_batch_metrics()

    print("\n\n✅ All examples complete!")
    print("\nNext steps:")
    print("1. Start the batch scheduler: python src/batch_scheduler.py")
    print("2. Monitor at: http://localhost:8003/batch/dashboard")
    print("3. Watch your savings grow! 💰")


if __name__ == "__main__":
    asyncio.run(main())
