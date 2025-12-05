# =============================================================================
# ML Service - Production-Grade Multi-Stage Dockerfile
# =============================================================================
# PyTorch + scikit-learn + XGBoost + pgvector
# Optimized for CPU inference with memory efficiency
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install ML dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Install build dependencies for ML packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    git \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements and install
COPY services/ml-service/requirements.txt .
RUN pip install --user --no-cache-dir --default-timeout=1000 -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production - Optimized ML runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    # PyTorch CPU optimization
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    OPENBLAS_NUM_THREADS=4 \
    # Memory optimization
    MALLOC_ARENA_MAX=2 \
    # Numba optimization
    NUMBA_NUM_THREADS=4

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenMP for parallel processing
    libgomp1 \
    # BLAS/LAPACK for numerical computing
    libopenblas0 \
    # Utilities
    curl \
    wget \
    ca-certificates \
    dumb-init \
    # PostgreSQL client libraries for pgvector
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash mluser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/mluser/.local

# Copy application code
COPY services/ml-service/ .

# Create directories for models and cache
RUN mkdir -p \
    /app/models \
    /app/cache \
    /app/logs \
    /tmp/ml-service \
    && chown -R mluser:mluser /app /tmp/ml-service

# Switch to non-root user
USER mluser

# Add local packages to PATH
ENV PATH=/home/mluser/.local/bin:$PATH

# Expose port
EXPOSE 8080

# Health check - longer start period for model loading
HEALTHCHECK --interval=20s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Labels for metadata
LABEL maintainer="GeminiVideo DevOps" \
      version="1.0.0" \
      description="ML Service with PyTorch and pgvector" \
      service="ml-service"

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Graceful shutdown with signal handling
CMD ["sh", "-c", "trap 'echo Received SIGTERM, shutting down gracefully...; kill -TERM $PID; wait $PID' TERM; uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2 --log-level info & PID=$!; wait $PID"]
