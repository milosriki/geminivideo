# =============================================================================
# Titan-Core Master API - Production Dockerfile for Cloud Run
# =============================================================================
# Multi-service FastAPI application with AI Council, video processing, and ML
# Optimized for Cloud Run with proper health checks and security
# =============================================================================

FROM --platform=linux/amd64 python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for video processing and ML
RUN apt-get update && apt-get install -y \
    # FFmpeg for video processing
    ffmpeg \
    # OpenCV dependencies
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgomp1 \
    # Audio processing
    libass-dev \
    # Utilities
    curl \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p \
    /tmp/titan-core/outputs \
    /tmp/titan-core/cache \
    /tmp/titan-core/uploads \
    /tmp/titan-core/models \
    && chmod -R 777 /tmp/titan-core

# Create non-root user for security
RUN useradd -m -u 1000 titanuser && \
    chown -R titanuser:titanuser /app /tmp/titan-core

# Switch to non-root user
USER titanuser

# Expose port (Cloud Run will set PORT env var, defaults to 8080)
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run the application
# Note: Cloud Run sets PORT environment variable, we respect it
CMD ["sh", "-c", "cd api && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2 --log-level info"]
