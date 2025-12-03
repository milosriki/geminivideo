"""
Titan-Core API
Ultimate API for winning ad generation

Endpoints:
- /pipeline/* - End-to-end pipeline (MAIN ENDPOINT)
- /storage/* - Video upload/download
- /ws/* - WebSocket for progress

Note: For the complete API with all endpoints, use main.py directly.
This module provides just the essential pipeline router for integration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import routers
try:
    from .pipeline import router as pipeline_router
except ImportError as e:
    logging.warning(f"Pipeline router import failed: {e}")
    pipeline_router = None

try:
    from .storage import router as storage_router
except ImportError as e:
    logging.warning(f"Storage router import failed: {e}")
    storage_router = None

try:
    from .websocket import router as ws_router
except ImportError as e:
    logging.warning(f"WebSocket router import failed: {e}")
    ws_router = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Titan-Core API...")
    # Initialize database
    # Initialize Redis and WebSocket service
    if ws_router:
        try:
            from .websocket import startup as ws_startup
            await ws_startup()
        except Exception as e:
            logger.warning(f"WebSocket startup failed: {e}")
    # Initialize AI Council
    yield
    # Shutdown
    logger.info("👋 Shutting down Titan-Core API...")
    if ws_router:
        try:
            from .websocket import shutdown as ws_shutdown
            await ws_shutdown()
        except Exception as e:
            logger.warning(f"WebSocket shutdown failed: {e}")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Titan-Core API",
        description="Ultimate AI-powered winning ad generation system",
        version="1.0.0",
        lifespan=lifespan
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers (only if successfully imported)
    if pipeline_router:
        app.include_router(pipeline_router)
    if storage_router:
        app.include_router(storage_router)
    if ws_router:
        app.include_router(ws_router)

    return app

app = create_app()

# For running directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
