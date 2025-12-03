#!/usr/bin/env python3
"""
Test script for Celery distributed task queue

This script demonstrates how to:
1. Submit tasks to the queue
2. Track task progress
3. Get results
4. Monitor system resources

Usage:
    python3 test_celery.py
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import redis
    from celery.result import AsyncResult
    from services.video_agent.pro.celery_app import (
        app as celery_app,
        render_video_task,
        generate_preview_task,
        transcode_task,
        caption_task,
        batch_render_task,
        cleanup_task,
        monitor_resources_task,
        get_system_resources,
        detect_gpu
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("\nPlease ensure:")
    print("1. Redis is running: redis-server")
    print("2. Dependencies installed: pip install -r requirements_celery.txt")
    print("3. You're in the correct directory")
    sys.exit(1)


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_connection():
    """Test Redis and Celery connection"""
    print_section("Testing Connection")

    try:
        # Test Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        print("✓ Redis connection successful")

        # Test Celery app
        print(f"✓ Celery app configured")
        print(f"  Broker: {celery_app.conf.broker_url}")
        print(f"  Backend: {celery_app.conf.result_backend}")

        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_system_resources():
    """Test system resource monitoring"""
    print_section("System Resources")

    try:
        resources = get_system_resources()

        print(f"CPU:")
        print(f"  Usage: {resources['cpu']['percent']}%")
        print(f"  Cores: {resources['cpu']['count']}")

        print(f"\nMemory:")
        print(f"  Usage: {resources['memory']['percent']}%")
        print(f"  Total: {resources['memory']['total'] / (1024**3):.2f} GB")
        print(f"  Available: {resources['memory']['available'] / (1024**3):.2f} GB")

        print(f"\nDisk:")
        print(f"  Usage: {resources['disk']['percent']}%")
        print(f"  Total: {resources['disk']['total'] / (1024**3):.2f} GB")
        print(f"  Free: {resources['disk']['free'] / (1024**3):.2f} GB")

        gpu_info = detect_gpu()
        print(f"\nGPU:")
        print(f"  Available: {gpu_info['available']}")
        if gpu_info['available']:
            print(f"  Count: {gpu_info['count']}")
            for gpu in gpu_info['gpus']:
                print(f"    GPU {gpu['index']}: {gpu['name']}")
                print(f"      Memory: {gpu['memory_free']}/{gpu['memory_total']} MB free")
                print(f"      Utilization: {gpu['utilization']}%")
        else:
            print("  No GPU detected (NVIDIA GPU required)")

        return True

    except Exception as e:
        print(f"✗ Resource monitoring failed: {e}")
        return False


def test_worker_status():
    """Test worker status"""
    print_section("Worker Status")

    try:
        # Get active workers
        inspect = celery_app.control.inspect()

        active_workers = inspect.active()
        if active_workers:
            print(f"✓ Active workers: {len(active_workers)}")
            for worker_name, tasks in active_workers.items():
                print(f"\n  Worker: {worker_name}")
                print(f"    Active tasks: {len(tasks)}")
                if tasks:
                    for task in tasks[:3]:  # Show first 3
                        print(f"      - {task['name']} [{task['id'][:8]}...]")
        else:
            print("⚠ No active workers found")
            print("\nTo start a worker, run:")
            print("  celery -A services.video-agent.pro.celery_app worker --loglevel=info")
            return False

        # Get registered tasks
        registered = inspect.registered()
        if registered:
            worker_name = list(registered.keys())[0]
            print(f"\n✓ Registered tasks on {worker_name}:")
            for task in registered[worker_name]:
                if 'services.video-agent.pro.celery_app' in task:
                    task_short = task.split('.')[-1]
                    print(f"    - {task_short}")

        return True

    except Exception as e:
        print(f"✗ Worker status check failed: {e}")
        return False


def create_test_video():
    """Create a simple test video using FFmpeg"""
    print_section("Creating Test Video")

    try:
        # Create a simple 5-second test video
        output_path = os.path.join(tempfile.gettempdir(), 'test_video.mp4')

        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'testsrc=duration=5:size=1280x720:rate=30',
            '-f', 'lavfi',
            '-i', 'sine=frequency=1000:duration=5',
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        import subprocess
        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024
            print(f"✓ Test video created: {output_path}")
            print(f"  Size: {file_size:.2f} KB")
            return output_path
        else:
            print("✗ Failed to create test video")
            print(f"  Error: {result.stderr.decode()}")
            return None

    except Exception as e:
        print(f"✗ Test video creation failed: {e}")
        return None


def test_preview_task(video_path):
    """Test preview generation task"""
    print_section("Testing Preview Generation")

    if not video_path:
        print("⚠ Skipping preview test (no test video)")
        return False

    try:
        print("Submitting preview generation task...")
        result = generate_preview_task.apply_async(
            args=[video_path],
            kwargs={'num_frames': 5}
        )

        task_id = result.id
        print(f"✓ Task submitted: {task_id}")

        # Wait for result
        print("Waiting for result (max 60 seconds)...")
        output = result.get(timeout=60)

        print(f"✓ Preview generation completed!")
        print(f"  Preview directory: {output['preview_dir']}")
        print(f"  Frames generated: {output['num_frames']}")
        print(f"  Video duration: {output['video_duration']:.2f}s")

        return True

    except Exception as e:
        print(f"✗ Preview task failed: {e}")
        return False


def test_monitor_task():
    """Test resource monitoring task"""
    print_section("Testing Resource Monitoring Task")

    try:
        print("Submitting resource monitoring task...")
        result = monitor_resources_task.apply_async()

        task_id = result.id
        print(f"✓ Task submitted: {task_id}")

        # Wait for result
        output = result.get(timeout=30)

        print(f"✓ Resource monitoring completed!")
        print(f"  CPU: {output['cpu']['percent']}%")
        print(f"  Memory: {output['memory']['percent']}%")
        print(f"  GPU Available: {output['gpu']['available']}")

        return True

    except Exception as e:
        print(f"✗ Monitor task failed: {e}")
        return False


def test_cleanup_task():
    """Test cleanup task"""
    print_section("Testing Cleanup Task")

    try:
        print("Submitting cleanup task...")
        result = cleanup_task.apply_async(
            kwargs={'max_age_days': 30, 'max_size_gb': 100}
        )

        task_id = result.id
        print(f"✓ Task submitted: {task_id}")

        # Wait for result
        print("Waiting for result (max 60 seconds)...")
        output = result.get(timeout=60)

        print(f"✓ Cleanup completed!")
        print(f"  Files deleted: {output['deleted_files']}")
        print(f"  Space freed: {output['freed_space_gb']:.2f} GB")

        return True

    except Exception as e:
        print(f"✗ Cleanup task failed: {e}")
        return False


def demonstrate_progress_tracking():
    """Demonstrate progress tracking with Redis pub/sub"""
    print_section("Progress Tracking Demo")

    print("Progress tracking allows real-time monitoring of long-running tasks.")
    print("\nTo track progress:")
    print("1. Submit a task and get the task_id")
    print("2. Subscribe to Redis pub/sub channel: task_progress:<task_id>")
    print("3. Or get current status from Redis key: task_status:<task_id>")

    print("\nExample code:")
    print("""
    import redis
    import json

    redis_client = redis.from_url('redis://localhost:6379/0', decode_responses=True)

    # Subscribe to progress updates
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f'task_progress:{task_id}')

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            print(f"Progress: {data['progress']}% - {data['message']}")
            if data['status'] in ['completed', 'failed']:
                break
    """)


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  CELERY DISTRIBUTED TASK QUEUE - TEST SUITE")
    print("=" * 70)

    # Test connection
    if not test_connection():
        print("\n✗ Connection test failed. Exiting.")
        return 1

    # Test system resources
    test_system_resources()

    # Test worker status
    has_workers = test_worker_status()

    if not has_workers:
        print("\n" + "=" * 70)
        print("⚠ WARNING: No workers detected!")
        print("=" * 70)
        print("\nPlease start a worker before running task tests:")
        print("  celery -A services.video-agent.pro.celery_app worker --loglevel=info")
        print("\nConnection and configuration tests passed.")
        return 0

    # Create test video
    test_video = create_test_video()

    # Test tasks
    test_monitor_task()

    if test_video:
        test_preview_task(test_video)

    test_cleanup_task()

    # Progress tracking demo
    demonstrate_progress_tracking()

    # Summary
    print_section("Test Summary")
    print("✓ All basic tests completed!")
    print("\nNext steps:")
    print("1. Start Celery Beat for periodic tasks:")
    print("   celery -A services.video-agent.pro.celery_app beat --loglevel=info")
    print("\n2. Start Flower for web monitoring:")
    print("   celery -A services.video-agent.pro.celery_app flower --port=5555")
    print("\n3. Submit production tasks using the API")
    print("\n4. Monitor via Flower dashboard: http://localhost:5555")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
