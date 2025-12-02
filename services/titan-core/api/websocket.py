"""
WebSocket Progress Service
Real-time job progress updates with Redis pub/sub integration

Features:
- WebSocket endpoint for clients to subscribe to job updates
- Redis pub/sub for distributed progress updates across instances
- Support for multiple clients per job
- Progress updates for render jobs, AI generation, captioning, etc.
- Automatic cleanup and reconnection handling
"""

import os
import json
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """
    Manages WebSocket connections for job progress updates
    Supports multiple clients subscribing to the same job
    """

    def __init__(self):
        # Map of job_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Map of job_id -> Redis pubsub instance
        self.pubsub_channels: Dict[str, redis.client.PubSub] = {}

        # Map of job_id -> background task
        self.listen_tasks: Dict[str, asyncio.Task] = {}

        # Redis client for pub/sub
        self.redis_client: Optional[redis.Redis] = None

        # Connection stats
        self.stats = {
            'total_connections': 0,
            'active_jobs': 0,
            'messages_sent': 0,
            'errors': 0
        }

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            try:
                self.redis_client = await redis.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    encoding='utf-8'
                )
                await self.redis_client.ping()
                logger.info(f"✅ Connected to Redis at {REDIS_URL}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                raise

    async def connect(self, websocket: WebSocket, job_id: str):
        """
        Accept WebSocket connection and subscribe to job updates

        Args:
            websocket: FastAPI WebSocket instance
            job_id: Job ID to subscribe to
        """
        await websocket.accept()

        # Add connection to active connections
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        self.stats['total_connections'] += 1

        logger.info(f"✅ Client connected to job {job_id} "
                   f"({len(self.active_connections[job_id])} total clients)")

        # Start Redis listener if this is the first connection for this job
        if job_id not in self.listen_tasks:
            self.stats['active_jobs'] += 1
            await self._start_redis_listener(job_id)

        # Send initial connection message
        await websocket.send_json({
            'type': 'connected',
            'job_id': job_id,
            'message': f'Connected to job progress stream',
            'timestamp': datetime.utcnow().isoformat()
        })

    async def disconnect(self, websocket: WebSocket, job_id: str):
        """
        Remove WebSocket connection and cleanup if no more clients

        Args:
            websocket: FastAPI WebSocket instance
            job_id: Job ID to unsubscribe from
        """
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            # If no more connections for this job, cleanup
            if not self.active_connections[job_id]:
                await self._cleanup_job(job_id)
                logger.info(f"🧹 Cleaned up job {job_id} (no more clients)")
            else:
                logger.info(f"👋 Client disconnected from job {job_id} "
                          f"({len(self.active_connections[job_id])} remaining)")

    async def broadcast_progress(self, job_id: str, progress: dict):
        """
        Send progress update to all subscribers of a job

        Args:
            job_id: Job ID
            progress: Progress data dictionary
        """
        if job_id not in self.active_connections:
            return

        # Add metadata
        progress['job_id'] = job_id
        progress['timestamp'] = datetime.utcnow().isoformat()

        # Send to all connected clients
        disconnected = set()
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(progress)
                self.stats['messages_sent'] += 1
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(websocket)
                self.stats['errors'] += 1

        # Remove disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket, job_id)

    async def _start_redis_listener(self, job_id: str):
        """
        Start Redis pub/sub listener for a job

        Args:
            job_id: Job ID to listen for
        """
        try:
            # Create pubsub instance
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(f'job_progress:{job_id}')

            self.pubsub_channels[job_id] = pubsub

            # Start background task to listen for messages
            task = asyncio.create_task(self._listen_redis(job_id))
            self.listen_tasks[job_id] = task

            logger.info(f"🎧 Started Redis listener for job {job_id}")

        except Exception as e:
            logger.error(f"Failed to start Redis listener for {job_id}: {e}")
            self.stats['errors'] += 1

    async def _listen_redis(self, job_id: str):
        """
        Background task to listen for Redis pub/sub messages

        Args:
            job_id: Job ID to listen for
        """
        pubsub = self.pubsub_channels.get(job_id)
        if not pubsub:
            return

        try:
            while job_id in self.active_connections and self.active_connections[job_id]:
                try:
                    # Get message with timeout
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=5.0
                    )

                    if message and message['type'] == 'message':
                        try:
                            # Parse progress data
                            progress_data = json.loads(message['data'])

                            # Broadcast to all connected clients
                            await self.broadcast_progress(job_id, progress_data)

                            # If job completed or failed, cleanup after delay
                            status = progress_data.get('status', '')
                            if status in ['completed', 'failed', 'error']:
                                logger.info(f"Job {job_id} finished with status: {status}")
                                # Give clients time to receive final message
                                await asyncio.sleep(2)
                                break

                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from Redis: {e}")
                            self.stats['errors'] += 1

                except asyncio.TimeoutError:
                    # Send keepalive ping to all clients
                    await self.broadcast_progress(job_id, {
                        'type': 'ping',
                        'message': 'keepalive'
                    })

        except Exception as e:
            logger.error(f"Error in Redis listener for {job_id}: {e}")
            self.stats['errors'] += 1

        finally:
            # Cleanup when done
            await self._cleanup_job(job_id)

    async def _cleanup_job(self, job_id: str):
        """
        Cleanup resources for a job

        Args:
            job_id: Job ID to cleanup
        """
        # Cancel listen task
        if job_id in self.listen_tasks:
            task = self.listen_tasks[job_id]
            if not task.done():
                task.cancel()
            del self.listen_tasks[job_id]

        # Close pubsub
        if job_id in self.pubsub_channels:
            pubsub = self.pubsub_channels[job_id]
            try:
                await pubsub.unsubscribe(f'job_progress:{job_id}')
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub for {job_id}: {e}")
            del self.pubsub_channels[job_id]

        # Remove connections
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            self.stats['active_jobs'] -= 1

    async def shutdown(self):
        """Shutdown all connections and cleanup"""
        logger.info("🛑 Shutting down WebSocket manager...")

        # Cancel all listen tasks
        for task in self.listen_tasks.values():
            if not task.done():
                task.cancel()

        # Close all pubsub channels
        for pubsub in self.pubsub_channels.values():
            try:
                await pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub: {e}")

        # Close Redis client
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ WebSocket manager shutdown complete")

    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            **self.stats,
            'active_connections': sum(len(conns) for conns in self.active_connections.values()),
        }


class ProgressReporter:
    """
    Report progress from any service to Redis pub/sub
    All instances will receive updates via WebSocket
    """

    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            try:
                self.redis_client = await redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    encoding='utf-8'
                )
                await self.redis_client.ping()
                logger.info(f"✅ ProgressReporter connected to Redis")
            except Exception as e:
                logger.error(f"❌ ProgressReporter failed to connect to Redis: {e}")
                raise

    async def report(
        self,
        job_id: str,
        stage: str,
        progress: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Report progress update

        Args:
            job_id: Job ID
            stage: Current stage (rendering|captioning|cropping|uploading|processing|analyzing)
            progress: Progress from 0.0 to 1.0
            message: Human-readable progress message
            metadata: Additional metadata
        """
        if not self.redis_client:
            await self.initialize()

        progress_data = {
            'job_id': job_id,
            'status': 'processing',
            'stage': stage,
            'progress': min(1.0, max(0.0, progress)),  # Clamp to [0, 1]
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
        }

        if metadata:
            progress_data['metadata'] = metadata

        try:
            # Publish to Redis channel
            await self.redis_client.publish(
                f'job_progress:{job_id}',
                json.dumps(progress_data)
            )

            # Also store in Redis for status checks
            await self.redis_client.setex(
                f'job_status:{job_id}',
                3600,  # 1 hour TTL
                json.dumps(progress_data)
            )

            logger.debug(f"📊 Progress update for {job_id}: {stage} {progress:.1%}")

        except Exception as e:
            logger.error(f"Failed to report progress for {job_id}: {e}")

    async def report_error(self, job_id: str, error: str, stage: str = "error"):
        """
        Report job error

        Args:
            job_id: Job ID
            error: Error message
            stage: Stage where error occurred
        """
        if not self.redis_client:
            await self.initialize()

        error_data = {
            'job_id': job_id,
            'status': 'failed',
            'stage': stage,
            'progress': 0.0,
            'message': f'Error: {error}',
            'error': error,
            'timestamp': datetime.utcnow().isoformat(),
        }

        try:
            # Publish error to Redis
            await self.redis_client.publish(
                f'job_progress:{job_id}',
                json.dumps(error_data)
            )

            # Store error status
            await self.redis_client.setex(
                f'job_status:{job_id}',
                3600,
                json.dumps(error_data)
            )

            logger.error(f"❌ Job {job_id} failed: {error}")

        except Exception as e:
            logger.error(f"Failed to report error for {job_id}: {e}")

    async def report_complete(
        self,
        job_id: str,
        result: Dict[str, Any],
        message: str = "Job completed successfully"
    ):
        """
        Report job completion

        Args:
            job_id: Job ID
            result: Result data
            message: Completion message
        """
        if not self.redis_client:
            await self.initialize()

        complete_data = {
            'job_id': job_id,
            'status': 'completed',
            'stage': 'complete',
            'progress': 1.0,
            'message': message,
            'result': result,
            'timestamp': datetime.utcnow().isoformat(),
        }

        try:
            # Publish completion to Redis
            await self.redis_client.publish(
                f'job_progress:{job_id}',
                json.dumps(complete_data)
            )

            # Store completion status
            await self.redis_client.setex(
                f'job_status:{job_id}',
                3600,
                json.dumps(complete_data)
            )

            logger.info(f"✅ Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Failed to report completion for {job_id}: {e}")

    async def get_status(self, job_id: str) -> Optional[dict]:
        """
        Get current job status from Redis

        Args:
            job_id: Job ID

        Returns:
            Status dict or None if not found
        """
        if not self.redis_client:
            await self.initialize()

        try:
            status_json = await self.redis_client.get(f'job_status:{job_id}')
            if status_json:
                return json.loads(status_json)
            return None
        except Exception as e:
            logger.error(f"Failed to get status for {job_id}: {e}")
            return None

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ ProgressReporter closed")


# Global instances
connection_manager = ConnectionManager()
progress_reporter = ProgressReporter()


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/jobs/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates

    Connect to this endpoint to receive live progress updates for a specific job.

    Usage:
        ws://localhost:8000/ws/jobs/{job_id}

    Message Format:
        {
            "job_id": "xxx",
            "status": "processing|completed|failed",
            "stage": "rendering|captioning|cropping|uploading",
            "progress": 0.75,
            "message": "Rendering frame 1500/2000",
            "timestamp": "2024-01-01T00:00:00Z"
        }

    Special Messages:
        - type: "connected" - Initial connection confirmation
        - type: "ping" - Keepalive ping (every 5 seconds)
        - type: "error" - Error occurred
    """
    # Initialize connection manager if needed
    if not connection_manager.redis_client:
        await connection_manager.initialize()

    # Connect client
    await connection_manager.connect(websocket, job_id)

    try:
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (mostly for detecting disconnects)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle client messages if needed (e.g., pause/resume)
                try:
                    message = json.loads(data)
                    if message.get('type') == 'ping':
                        await websocket.send_json({
                            'type': 'pong',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                # No message from client, continue listening
                continue

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from job {job_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket for job {job_id}: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        except:
            pass
    finally:
        # Cleanup connection
        await connection_manager.disconnect(websocket, job_id)


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        'status': 'healthy',
        'stats': connection_manager.get_stats(),
        'timestamp': datetime.utcnow().isoformat()
    }


# ============================================================================
# Lifecycle Management
# ============================================================================

async def startup():
    """Initialize WebSocket service on startup"""
    logger.info("🚀 Starting WebSocket service...")
    await connection_manager.initialize()
    await progress_reporter.initialize()
    logger.info("✅ WebSocket service started")


async def shutdown():
    """Cleanup WebSocket service on shutdown"""
    logger.info("🛑 Stopping WebSocket service...")
    await connection_manager.shutdown()
    await progress_reporter.close()
    logger.info("✅ WebSocket service stopped")


# Export for use in other modules
__all__ = [
    'router',
    'connection_manager',
    'progress_reporter',
    'ProgressReporter',
    'ConnectionManager',
    'startup',
    'shutdown'
]
