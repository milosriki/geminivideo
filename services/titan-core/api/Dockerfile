# Titan-Core Master API - Production Dockerfile
# NOTE: This Dockerfile is deprecated. Use the root titan-core/Dockerfile instead.
# Build from services/titan-core directory, NOT from services/titan-core/api

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements - expects to be built from titan-core root
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY core/ ./core/
COPY config/ ./config/

# Create output directories
RUN mkdir -p /tmp/titan-core/outputs /tmp/titan-core/cache && \
    chmod -R 777 /tmp/titan-core

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Health check using curl (more reliable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run the application - respect PORT env var
CMD ["sh", "-c", "cd api && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2"]
