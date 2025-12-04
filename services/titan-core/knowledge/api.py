"""
Knowledge Base API Endpoints
FastAPI routes for knowledge management with hot-reload

Endpoints:
- POST /knowledge/upload - Upload new knowledge
- GET /knowledge/{category} - Get knowledge
- GET /knowledge/{category}/versions - List versions
- POST /knowledge/activate/{category}/{version} - Activate version
- GET /knowledge/status - Get all categories status
- POST /knowledge/reload - Trigger hot reload
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .manager import get_manager, VersionInfo

logger = logging.getLogger(__name__)

# Pydantic models for request/response validation


class UploadRequest(BaseModel):
    """Request model for uploading knowledge"""
    category: str = Field(..., description="Knowledge category")
    data: Dict[str, Any] = Field(..., description="Knowledge data")
    description: str = Field("", description="Version description")
    author: str = Field("api_user", description="Author name")


class VersionInfoResponse(BaseModel):
    """Response model for version information"""
    version_id: str
    category: str
    timestamp: str
    checksum: str
    size_bytes: int
    description: str
    author: str
    is_active: bool

    @classmethod
    def from_version_info(cls, v: VersionInfo) -> 'VersionInfoResponse':
        return cls(
            version_id=v.version_id,
            category=v.category,
            timestamp=v.timestamp.isoformat(),
            checksum=v.checksum,
            size_bytes=v.size_bytes,
            description=v.description,
            author=v.author,
            is_active=v.is_active
        )


class CategoryStatus(BaseModel):
    """Status information for a category"""
    active_version: Optional[str]
    active_timestamp: Optional[str]
    total_versions: int
    latest_version: Optional[str]
    cached: bool


class ReloadRequest(BaseModel):
    """Request model for reload operations"""
    category: Optional[str] = Field(None, description="Category to reload (all if not specified)")


class ActivateRequest(BaseModel):
    """Request model for activating a version"""
    version_id: str = Field(..., description="Version ID to activate")


# Create FastAPI app
app = FastAPI(
    title="Knowledge Base API",
    description="Hot-reload knowledge management system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize knowledge manager on startup"""
    try:
        manager = get_manager()
        logger.info("Knowledge Base API started")
        logger.info(f"Available categories: {manager.CATEGORIES}")
    except Exception as e:
        logger.error(f"Failed to initialize knowledge manager: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Knowledge Base API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        manager = get_manager()
        status = manager.get_all_status()
        return {
            "status": "healthy",
            "categories": len(status),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/knowledge/categories")
async def list_categories():
    """List all available categories"""
    manager = get_manager()
    return {
        "categories": manager.CATEGORIES,
        "count": len(manager.CATEGORIES)
    }


@app.post("/knowledge/upload")
async def upload_knowledge(request: UploadRequest):
    """
    Upload new knowledge version

    Creates a new versioned entry for the specified category.
    Auto-activates if it's the first version for the category.
    """
    try:
        manager = get_manager()

        version_id = manager.upload_knowledge(
            category=request.category,
            data=request.data,
            description=request.description,
            author=request.author
        )

        return {
            "success": True,
            "version_id": version_id,
            "category": request.category,
            "message": f"Knowledge uploaded successfully as version {version_id}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/knowledge/{category}")
async def get_knowledge(category: str, version: str = "latest"):
    """
    Get knowledge data for a category

    Args:
        category: Knowledge category
        version: Version ID or 'latest' for active version
    """
    try:
        manager = get_manager()

        data = manager.download_knowledge(category, version)

        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Knowledge not found for category '{category}' version '{version}'"
            )

        return {
            "success": True,
            "category": category,
            "version": version if version != "latest" else manager.get_current_version(category),
            "data": data
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.get("/knowledge/{category}/versions", response_model=List[VersionInfoResponse])
async def list_versions(category: str):
    """
    List all versions for a category

    Returns version history sorted by timestamp (newest first)
    """
    try:
        manager = get_manager()
        versions = manager.list_versions(category)

        return [VersionInfoResponse.from_version_info(v) for v in versions]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"List versions failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@app.post("/knowledge/activate/{category}/{version_id}")
async def activate_version(category: str, version_id: str):
    """
    Activate a specific version

    Makes the specified version the active version for the category.
    Triggers hot-reload and notifies subscribers.
    """
    try:
        manager = get_manager()

        success = manager.activate_version(category, version_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to activate version")

        return {
            "success": True,
            "category": category,
            "version_id": version_id,
            "message": f"Version {version_id} activated successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Activation failed: {str(e)}")


@app.delete("/knowledge/{category}/versions/{version_id}")
async def delete_version(category: str, version_id: str):
    """
    Delete a specific version

    Cannot delete the currently active version.
    """
    try:
        manager = get_manager()

        success = manager.delete_version(category, version_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")

        return {
            "success": True,
            "category": category,
            "version_id": version_id,
            "message": f"Version {version_id} deleted successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.get("/knowledge/status", response_model=Dict[str, CategoryStatus])
async def get_status():
    """
    Get status of all categories

    Returns information about active versions, total versions, and cache status
    """
    try:
        manager = get_manager()
        status = manager.get_all_status()

        # Convert to Pydantic models
        return {
            category: CategoryStatus(**info)
            for category, info in status.items()
        }

    except Exception as e:
        logger.error(f"Get status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.post("/knowledge/reload")
async def reload_knowledge(request: ReloadRequest):
    """
    Trigger hot reload

    Reloads knowledge from storage and notifies subscribers.
    Can reload a specific category or all categories.
    """
    try:
        manager = get_manager()

        if request.category:
            # Reload specific category
            success = manager.trigger_reload(request.category)

            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"No active version to reload for category '{request.category}'"
                )

            return {
                "success": True,
                "reloaded": [request.category],
                "message": f"Category {request.category} reloaded successfully"
            }

        else:
            # Reload all categories
            results = manager.reload_all()

            return {
                "success": True,
                "reloaded": list(results.keys()),
                "count": len(results),
                "message": f"Reloaded {len(results)} categories"
            }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")


@app.get("/knowledge/{category}/current-version")
async def get_current_version(category: str):
    """Get the currently active version ID for a category"""
    try:
        manager = get_manager()
        version_id = manager.get_current_version(category)

        if not version_id:
            raise HTTPException(
                status_code=404,
                detail=f"No active version for category '{category}'"
            )

        return {
            "success": True,
            "category": category,
            "version_id": version_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current version failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/knowledge/validate")
async def validate_knowledge(category: str = Body(...), data: Dict[str, Any] = Body(...)):
    """
    Validate knowledge data without uploading

    Useful for checking data structure before actual upload
    """
    try:
        manager = get_manager()
        manager._validate_category(category)
        manager._validate_knowledge_data(category, data)

        return {
            "success": True,
            "valid": True,
            "category": category,
            "message": "Knowledge data is valid"
        }

    except ValueError as e:
        return {
            "success": False,
            "valid": False,
            "category": category,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# Webhook support for external notifications
class WebhookConfig(BaseModel):
    """Webhook configuration"""
    url: str
    events: List[str] = ["version_activated", "version_uploaded"]


@app.post("/knowledge/webhooks/subscribe")
async def subscribe_webhook(config: WebhookConfig):
    """
    Subscribe a webhook to knowledge updates

    Note: This is a placeholder. Full implementation would require
    a webhook delivery system with retry logic.
    """
    try:
        manager = get_manager()

        # Create callback that posts to webhook
        async def webhook_callback(category: str, new_version: str, old_version: Optional[str]):
            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        config.url,
                        json={
                            "event": "version_activated",
                            "category": category,
                            "new_version": new_version,
                            "old_version": old_version,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        timeout=5.0
                    )
            except Exception as e:
                logger.error(f"Webhook delivery failed: {e}")

        # Subscribe (note: needs to be wrapped to be non-async for manager)
        def sync_wrapper(category, new_version, old_version):
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            loop.create_task(webhook_callback(category, new_version, old_version))

        subscription_id = manager.subscribe_to_updates(sync_wrapper)

        return {
            "success": True,
            "subscription_id": subscription_id,
            "webhook_url": config.url,
            "message": "Webhook subscribed successfully"
        }

    except Exception as e:
        logger.error(f"Webhook subscription failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Subscription failed: {str(e)}")


# Main entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )
