"""
Quick test for Batch API Processing

AGENT 42: 10x LEVERAGE - Verification Test

Run this to verify the batch processing system is working correctly.
"""

import asyncio
import os
import sys

# Set up path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.batch_processor import (
    BatchProcessor,
    BatchJobType,
    BatchProvider
)
from src.batch_monitoring import BatchMonitor


async def test_queue_job():
    """Test 1: Queue a job"""
    print("\n" + "=" * 60)
    print("TEST 1: Queue a Job")
    print("=" * 60)

    try:
        batch = BatchProcessor()

        job_id = await batch.queue_job(
            job_type=BatchJobType.CREATIVE_SCORING,
            provider=BatchProvider.OPENAI,
            data={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": "Test creative scoring"
                    }
                ]
            },
            priority=5
        )

        print(f"✅ Job queued successfully: {job_id}")
        return True

    except Exception as e:
        print(f"❌ Failed to queue job: {e}")
        return False


async def test_queue_status():
    """Test 2: Check queue status"""
    print("\n" + "=" * 60)
    print("TEST 2: Check Queue Status")
    print("=" * 60)

    try:
        batch = BatchProcessor()
        count = batch.get_queued_job_count()

        print(f"✅ Queue size: {count} jobs")

        if count > 0:
            print("   Jobs are waiting to be processed")
        else:
            print("   Queue is empty")

        return True

    except Exception as e:
        print(f"❌ Failed to check queue: {e}")
        return False


async def test_metrics():
    """Test 3: Get metrics"""
    print("\n" + "=" * 60)
    print("TEST 3: Get Metrics")
    print("=" * 60)

    try:
        batch = BatchProcessor()
        metrics = batch.get_metrics()

        print(f"✅ Metrics retrieved:")
        totals = metrics.get("totals", {})
        print(f"   Jobs queued: {totals.get('jobs_queued', 0)}")
        print(f"   Jobs processed: {totals.get('jobs_processed', 0)}")
        print(f"   Batches submitted: {totals.get('batches_submitted', 0)}")
        print(f"   Cost savings: ${totals.get('cost_savings', 0):.2f}")

        return True

    except Exception as e:
        print(f"❌ Failed to get metrics: {e}")
        return False


async def test_dashboard():
    """Test 4: Get dashboard data"""
    print("\n" + "=" * 60)
    print("TEST 4: Get Dashboard Data")
    print("=" * 60)

    try:
        monitor = BatchMonitor()
        dashboard = monitor.get_dashboard_data()

        print(f"✅ Dashboard data retrieved:")
        overview = dashboard.get("overview", {})
        print(f"   Total jobs queued: {overview.get('total_jobs_queued', 0)}")
        print(f"   Active batches: {overview.get('active_batches', 0)}")
        print(f"   Success rate: {overview.get('success_rate', 0):.1f}%")
        print(f"   Total savings: ${overview.get('total_cost_savings', 0):.2f}")

        return True

    except Exception as e:
        print(f"❌ Failed to get dashboard: {e}")
        return False


async def test_cost_savings():
    """Test 5: Get cost savings report"""
    print("\n" + "=" * 60)
    print("TEST 5: Get Cost Savings Report")
    print("=" * 60)

    try:
        monitor = BatchMonitor()
        report = monitor.get_cost_savings_report()

        print(f"✅ Cost savings report:")
        print(f"   Total savings: ${report.total_savings:.2f}")
        print(f"   Savings percentage: {report.savings_percentage:.1f}%")
        print(f"   Jobs processed: {report.jobs_processed}")

        return True

    except Exception as e:
        print(f"❌ Failed to get cost savings: {e}")
        return False


async def test_health():
    """Test 6: Health check"""
    print("\n" + "=" * 60)
    print("TEST 6: Health Check")
    print("=" * 60)

    try:
        batch = BatchProcessor()

        # Check Redis connection
        redis_ok = False
        try:
            batch.redis.ping()
            redis_ok = True
            print("✅ Redis connection: OK")
        except Exception:
            print("❌ Redis connection: FAILED")

        # Check queue
        queue_size = batch.get_queued_job_count()
        print(f"✅ Queue size: {queue_size}")

        # Check active batches
        active = len(batch.get_active_batches())
        print(f"✅ Active batches: {active}")

        return redis_ok

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BATCH API PROCESSING - VERIFICATION TESTS")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Health Check", await test_health()))
    results.append(("Queue Job", await test_queue_job()))
    results.append(("Queue Status", await test_queue_status()))
    results.append(("Metrics", await test_metrics()))
    results.append(("Dashboard", await test_dashboard()))
    results.append(("Cost Savings", await test_cost_savings()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Batch processing is working correctly.")
        print("\nNext steps:")
        print("1. Start the scheduler: python src/batch_scheduler.py")
        print("2. View dashboard: curl http://localhost:8003/batch/dashboard")
        print("3. Start saving money! 💰")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("1. Ensure Redis is running: docker-compose up -d redis")
        print("2. Check environment variables (REDIS_URL, API keys)")
        print("3. Install dependencies: pip install -r requirements_batch.txt")

    print("=" * 60 + "\n")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
