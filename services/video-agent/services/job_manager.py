"""
Job management service for async video processing.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any
from threading import Lock
from enum import Enum

logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobManager:
    """Manages async video processing jobs."""
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._tasks: Dict[str, asyncio.Task] = {}
        logger.info("Job manager initialized")
    
    async def create_job(self, job_id: str, job_data: Dict[str, Any]):
        """Create a new job."""
        with self._lock:
            self._jobs[job_id] = job_data
            logger.info(f"Created job: {job_id}")
    
    async def process_job(self, job_id: str, services: Dict[str, Any]):
        """Start processing a job asynchronously."""
        task = asyncio.create_task(self._process_job_async(job_id, services))
        self._tasks[job_id] = task
    
    async def _process_job_async(self, job_id: str, services: Dict[str, Any]):
        """Process a job asynchronously."""
        try:
            job = self._jobs.get(job_id)
            if not job:
                return
            
            # Update status
            self._update_job(job_id, {"status": JobStatus.PROCESSING, "progress": 0.1})
            
            # Get services
            renderer = services.get("renderer")
            overlay = services.get("overlay")
            subtitle = services.get("subtitle")
            compliance = services.get("compliance")
            
            request = job["request"]
            
            # Render video
            self._update_job(job_id, {"progress": 0.3})
            output_path = await renderer.render(request, job_id)
            
            # Check compliance
            self._update_job(job_id, {"progress": 0.8})
            compliance_result = await compliance.check(output_path)
            
            # Complete job
            self._update_job(job_id, {
                "status": JobStatus.COMPLETED,
                "progress": 1.0,
                "outputUrl": output_path,
                "compliance": compliance_result
            })
            
            logger.info(f"Job completed: {job_id}")
        except Exception as e:
            logger.error(f"Job failed: {job_id} - {e}", exc_info=True)
            self._update_job(job_id, {
                "status": JobStatus.FAILED,
                "error": str(e)
            })
    
    def _update_job(self, job_id: str, updates: Dict[str, Any]):
        """Update job data."""
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(updates)
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List all jobs."""
        jobs = list(self._jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        
        return jobs[:limit]
    
    async def shutdown(self):
        """Shutdown and cancel all running tasks."""
        logger.info("Shutting down job manager...")
        for task in self._tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
