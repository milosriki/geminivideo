#!/usr/bin/env python3
"""
Quick test script for WebSocket Progress Service

Run this to verify the WebSocket service is working correctly.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_progress_reporter():
    """Test the ProgressReporter class"""
    print("=" * 60)
    print("Testing ProgressReporter")
    print("=" * 60)

    from api.websocket import ProgressReporter

    reporter = ProgressReporter()

    try:
        # Initialize
        print("\n1. Initializing connection to Redis...")
        await reporter.initialize()
        print("   ✅ Connected to Redis")

        # Test job ID
        job_id = "test_job_001"

        # Report initial progress
        print(f"\n2. Reporting initial progress for job {job_id}...")
        await reporter.report(
            job_id=job_id,
            stage="testing",
            progress=0.0,
            message="Starting test job"
        )
        print("   ✅ Initial progress reported")

        # Report intermediate progress
        print("\n3. Reporting intermediate progress...")
        for i in range(1, 6):
            await reporter.report(
                job_id=job_id,
                stage="testing",
                progress=i / 5,
                message=f"Test progress {i}/5",
                metadata={"step": i}
            )
            await asyncio.sleep(0.5)
            print(f"   ✅ Progress: {i*20}%")

        # Report completion
        print("\n4. Reporting completion...")
        await reporter.report_complete(
            job_id=job_id,
            result={
                "status": "success",
                "test_data": "Test completed successfully"
            },
            message="Test job completed"
        )
        print("   ✅ Completion reported")

        # Check status
        print("\n5. Checking job status from Redis...")
        status = await reporter.get_status(job_id)
        if status:
            print(f"   ✅ Status retrieved: {status.get('status')}")
            print(f"      Stage: {status.get('stage')}")
            print(f"      Progress: {status.get('progress', 0) * 100:.1f}%")
            print(f"      Message: {status.get('message')}")
        else:
            print("   ❌ No status found")

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await reporter.close()
        print("\n6. Closed reporter connection")


async def test_connection_manager():
    """Test the ConnectionManager class"""
    print("\n" + "=" * 60)
    print("Testing ConnectionManager")
    print("=" * 60)

    from api.websocket import connection_manager

    try:
        # Initialize
        print("\n1. Initializing ConnectionManager...")
        await connection_manager.initialize()
        print("   ✅ ConnectionManager initialized")

        # Get stats
        print("\n2. Getting connection stats...")
        stats = connection_manager.get_stats()
        print(f"   ✅ Stats: {stats}")

        print("\n✅ ConnectionManager test passed!")
        return True

    except Exception as e:
        print(f"\n❌ ConnectionManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_reporting():
    """Test error reporting"""
    print("\n" + "=" * 60)
    print("Testing Error Reporting")
    print("=" * 60)

    from api.websocket import ProgressReporter

    reporter = ProgressReporter()

    try:
        await reporter.initialize()
        print("   ✅ Connected to Redis")

        job_id = "test_error_job"

        # Report error
        print(f"\n1. Reporting error for job {job_id}...")
        await reporter.report_error(
            job_id=job_id,
            error="Test error: Something went wrong",
            stage="testing"
        )
        print("   ✅ Error reported")

        # Check status
        print("\n2. Checking error status...")
        status = await reporter.get_status(job_id)
        if status and status.get('status') == 'failed':
            print(f"   ✅ Error status confirmed: {status.get('error')}")
        else:
            print("   ❌ Error status not found")

        print("\n✅ Error reporting test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error reporting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await reporter.close()


async def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("WebSocket Progress Service - Test Suite")
    print("🚀" * 30)

    results = []

    # Test 1: ProgressReporter
    results.append(await test_progress_reporter())

    # Test 2: ConnectionManager
    results.append(await test_connection_manager())

    # Test 3: Error Reporting
    results.append(await test_error_reporting())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")

    if failed_tests == 0:
        print("\n🎉 All tests passed! WebSocket service is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


def main():
    """Main entry point"""
    print("\nChecking prerequisites...")

    # Check Redis
    try:
        import redis.asyncio as redis
        print("✅ redis.asyncio module found")
    except ImportError:
        print("❌ redis module not found. Install with: pip install redis[hiredis]")
        return 1

    # Check FastAPI
    try:
        import fastapi
        print("✅ FastAPI module found")
    except ImportError:
        print("❌ FastAPI not found. Install with: pip install fastapi")
        return 1

    # Check Redis connection
    print("\nChecking Redis connection...")
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    print(f"Using Redis URL: {redis_url}")

    try:
        import redis as redis_sync
        r = redis_sync.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        print("✅ Redis is accessible")
    except Exception as e:
        print(f"❌ Cannot connect to Redis: {e}")
        print("\nMake sure Redis is running:")
        print("  - Docker: docker-compose up redis")
        print("  - Local: redis-server")
        return 1

    # Run tests
    print("\nStarting tests...\n")
    return asyncio.run(run_all_tests())


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
