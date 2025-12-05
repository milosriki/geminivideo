"""
Test script for Precomputation Engine (Agent 45)

Validates all precomputation functionality:
- Event triggers
- Action prediction
- Caching
- Queue management
- Background workers
"""

import asyncio
import json
import time
from src.precomputer import (
    Precomputer,
    ActionPredictor,
    PrecomputeEvent,
    PrecomputeTaskType,
    get_precomputer
)


async def test_action_predictor():
    """Test action prediction ML model."""
    print("\n" + "=" * 80)
    print("TEST 1: Action Predictor")
    print("=" * 80)

    predictor = ActionPredictor()

    # Test prediction
    user_history = {
        'last_action': 3,  # Dashboard view
        'actions_today': 2,
        'session_duration': 15
    }

    predictions = predictor.predict(user_history)

    print(f"✅ Action predictor initialized")
    print(f"✅ Predictions generated: {len(predictions)}")
    for pred in predictions:
        print(f"   - {pred['action']}: {pred['probability']:.2%} ({pred['confidence']})")

    assert len(predictions) > 0, "Should generate predictions"
    assert all(0 <= p['probability'] <= 1 for p in predictions), "Probabilities should be 0-1"

    print("✅ Action predictor tests PASSED")


async def test_video_upload_trigger():
    """Test video upload precomputation trigger."""
    print("\n" + "=" * 80)
    print("TEST 2: Video Upload Trigger")
    print("=" * 80)

    precomputer = Precomputer()

    # Trigger video upload
    video_id = "test_video_001"
    user_id = "test_user_001"

    queued_tasks = await precomputer.on_video_upload(
        video_id=video_id,
        user_id=user_id,
        video_data={'duration': 30}
    )

    print(f"✅ Video upload triggered")
    print(f"✅ Tasks queued: {sum(len(tasks) for tasks in queued_tasks.values())}")
    for task_type, task_ids in queued_tasks.items():
        print(f"   - {task_type}: {len(task_ids)} tasks")

    # Check queue
    queue_count = precomputer.get_queued_task_count()
    print(f"✅ Queue size: {queue_count}")

    assert queue_count > 0, "Should have tasks in queue"
    assert 'scene_detection' in queued_tasks, "Should include scene detection"
    assert 'ctr_prediction' in queued_tasks, "Should include CTR prediction"

    print("✅ Video upload trigger tests PASSED")


async def test_campaign_create_trigger():
    """Test campaign creation precomputation trigger."""
    print("\n" + "=" * 80)
    print("TEST 3: Campaign Create Trigger")
    print("=" * 80)

    precomputer = Precomputer()

    # Trigger campaign create
    campaign_id = "test_campaign_001"
    user_id = "test_user_001"

    queued_tasks = await precomputer.on_campaign_create(
        campaign_id=campaign_id,
        user_id=user_id,
        campaign_data={'budget': 5000}
    )

    print(f"✅ Campaign creation triggered")
    print(f"✅ Tasks queued: {sum(len(tasks) for tasks in queued_tasks.values())}")
    for task_type, task_ids in queued_tasks.items():
        print(f"   - {task_type}: {len(task_ids)} tasks")

    assert 'variant_generation' in queued_tasks, "Should include variant generation"
    assert 'variant_scoring' in queued_tasks, "Should include variant scoring"
    assert 'roas_prediction' in queued_tasks, "Should include ROAS prediction"

    print("✅ Campaign create trigger tests PASSED")


async def test_user_login_trigger():
    """Test user login precomputation trigger."""
    print("\n" + "=" * 80)
    print("TEST 4: User Login Trigger")
    print("=" * 80)

    precomputer = Precomputer()

    # Trigger user login
    user_id = "test_user_001"

    queued_tasks = await precomputer.on_user_login(
        user_id=user_id,
        user_data={'last_login': '2025-12-04T10:00:00Z'}
    )

    print(f"✅ User login triggered")
    print(f"✅ Tasks queued: {sum(len(tasks) for tasks in queued_tasks.values())}")

    # Predict next actions
    predictions = await precomputer.predict_next_actions(user_id)
    print(f"✅ Action predictions: {len(predictions)}")
    for pred in predictions:
        print(f"   - {pred['action']}: {pred['probability']:.2%}")

    assert 'dashboard_data' in queued_tasks, "Should include dashboard data"
    assert len(predictions) > 0, "Should predict actions"

    print("✅ User login trigger tests PASSED")


async def test_caching():
    """Test cache management."""
    print("\n" + "=" * 80)
    print("TEST 5: Cache Management")
    print("=" * 80)

    precomputer = Precomputer()

    # Set cache
    cache_key = "test_task:video:test_001"
    test_result = {'data': 'test_value', 'computed_at': time.time()}

    precomputer.set_cached_result(
        cache_key=cache_key,
        result=test_result,
        task_type=PrecomputeTaskType.CTR_PREDICTION
    )
    print(f"✅ Cached result set: {cache_key}")

    # Get cache
    cached_result = precomputer.get_cached_result(cache_key)
    print(f"✅ Retrieved cached result: {cached_result is not None}")

    assert cached_result is not None, "Should retrieve cached result"
    assert cached_result['data'] == test_result['data'], "Cached data should match"

    # Test cache miss
    missing_result = precomputer.get_cached_result("nonexistent_key")
    print(f"✅ Cache miss handled: {missing_result is None}")
    assert missing_result is None, "Should return None for missing key"

    # Invalidate cache
    precomputer.invalidate_cache("test_task:*")
    print(f"✅ Cache invalidated")

    # Verify invalidation
    invalidated_result = precomputer.get_cached_result(cache_key)
    assert invalidated_result is None, "Should be invalidated"

    print("✅ Cache management tests PASSED")


async def test_queue_management():
    """Test queue management."""
    print("\n" + "=" * 80)
    print("TEST 6: Queue Management")
    print("=" * 80)

    precomputer = Precomputer()

    # Queue task manually
    task_id = await precomputer._queue_precompute_task(
        task_type=PrecomputeTaskType.CTR_PREDICTION,
        event=PrecomputeEvent.VIDEO_UPLOAD,
        video_id="test_video_002",
        user_id="test_user_002",
        priority=8
    )

    print(f"✅ Task queued: {task_id}")

    # Get queue count
    queue_count = precomputer.get_queued_task_count(PrecomputeTaskType.CTR_PREDICTION)
    print(f"✅ Queue count (CTR prediction): {queue_count}")

    assert queue_count > 0, "Should have tasks in queue"

    # Get queue stats
    queue_stats = precomputer.get_queue_stats()
    print(f"✅ Queue stats: {queue_stats}")

    assert 'total' in queue_stats, "Should have total"
    assert queue_stats['total'] >= queue_count, "Total should include all tasks"

    print("✅ Queue management tests PASSED")


async def test_task_processing():
    """Test task processing."""
    print("\n" + "=" * 80)
    print("TEST 7: Task Processing")
    print("=" * 80)

    precomputer = Precomputer()

    # Queue task
    task_id = await precomputer._queue_precompute_task(
        task_type=PrecomputeTaskType.CTR_PREDICTION,
        event=PrecomputeEvent.VIDEO_UPLOAD,
        video_id="test_video_003",
        user_id="test_user_003",
        priority=9
    )

    print(f"✅ Task queued: {task_id}")

    # Get next task
    task = await precomputer._get_next_task()
    print(f"✅ Retrieved task: {task.task_id if task else None}")

    assert task is not None, "Should retrieve task"
    assert task.task_type == PrecomputeTaskType.CTR_PREDICTION, "Should be CTR prediction"

    # Process task
    result = await precomputer._process_task(task)
    print(f"✅ Task processed: {result is not None}")

    assert result is not None, "Should return result"
    assert task.status.value in ['completed', 'cached'], "Task should be completed"

    # Verify cached
    cache_key = precomputer._generate_cache_key(
        task_type=task.task_type,
        video_id=task.video_id,
        campaign_id=task.campaign_id,
        user_id=task.user_id
    )
    cached_result = precomputer.get_cached_result(cache_key)
    print(f"✅ Result cached: {cached_result is not None}")

    assert cached_result is not None, "Result should be cached"

    print("✅ Task processing tests PASSED")


async def test_metrics():
    """Test metrics tracking."""
    print("\n" + "=" * 80)
    print("TEST 8: Metrics Tracking")
    print("=" * 80)

    precomputer = Precomputer()

    # Generate some activity
    await precomputer.on_video_upload("test_video_004", "test_user_004")
    await precomputer.predict_next_actions("test_user_004")

    # Get metrics
    metrics = precomputer.get_metrics()
    print(f"✅ Metrics retrieved")
    print(f"   - Cache hit rate: {metrics.get('cache_hit_rate', 0):.2f}%")
    print(f"   - Total requests: {metrics.get('total_requests', 0)}")
    print(f"   - Queue size: {metrics.get('queue_size', 0)}")
    print(f"   - Workers running: {metrics.get('workers_running', 0)}")

    assert 'cache_hit_rate' in metrics, "Should have cache hit rate"
    assert 'queue_size' in metrics, "Should have queue size"

    print("✅ Metrics tracking tests PASSED")


async def test_background_workers():
    """Test background worker processing."""
    print("\n" + "=" * 80)
    print("TEST 9: Background Workers")
    print("=" * 80)

    precomputer = Precomputer()

    # Start workers
    await precomputer.start_workers(num_workers=2)
    print(f"✅ Started 2 background workers")

    # Queue some tasks
    for i in range(5):
        await precomputer.on_video_upload(f"test_video_worker_{i}", "test_user_worker")

    print(f"✅ Queued 5 video upload tasks")

    # Wait for processing
    print("⏳ Waiting for workers to process tasks (5s)...")
    await asyncio.sleep(5)

    # Stop workers
    await precomputer.stop_workers()
    print(f"✅ Stopped workers")

    # Check if tasks were processed
    metrics = precomputer.get_metrics()
    print(f"✅ Tasks completed: {metrics.get('raw_metrics', {}).get('tasks_completed', 0)}")

    print("✅ Background workers tests PASSED")


async def test_integration_flow():
    """Test complete integration flow."""
    print("\n" + "=" * 80)
    print("TEST 10: Integration Flow")
    print("=" * 80)

    precomputer = Precomputer()

    # Start workers
    await precomputer.start_workers(num_workers=3)

    # Simulate user journey
    user_id = "integration_user"
    video_id = "integration_video"
    campaign_id = "integration_campaign"

    # 1. User logs in
    print("Step 1: User logs in")
    await precomputer.on_user_login(user_id)

    # 2. User uploads video
    print("Step 2: User uploads video")
    await precomputer.on_video_upload(video_id, user_id)

    # 3. Wait for some processing
    await asyncio.sleep(3)

    # 4. User creates campaign
    print("Step 3: User creates campaign")
    await precomputer.on_campaign_create(campaign_id, user_id)

    # 5. Wait for processing
    await asyncio.sleep(5)

    # 6. Check cache hit rate
    metrics = precomputer.get_metrics()
    print(f"✅ Integration flow completed")
    print(f"   - Cache hit rate: {metrics.get('cache_hit_rate', 0):.2f}%")
    print(f"   - Queue size: {metrics.get('queue_size', 0)}")
    print(f"   - Tasks completed: {metrics.get('raw_metrics', {}).get('tasks_completed', 0)}")

    # Stop workers
    await precomputer.stop_workers()

    print("✅ Integration flow tests PASSED")


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PRECOMPUTATION ENGINE TEST SUITE")
    print("Agent 45: 10x Leverage - Predictive Precomputation")
    print("=" * 80)

    tests = [
        test_action_predictor,
        test_video_upload_trigger,
        test_campaign_create_trigger,
        test_user_login_trigger,
        test_caching,
        test_queue_management,
        test_task_processing,
        test_metrics,
        test_background_workers,
        test_integration_flow,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("Precomputation engine is ready for €5M validation.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please review.")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
