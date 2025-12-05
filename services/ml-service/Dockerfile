FROM --platform=linux/amd64 python:3.11-slim as build

WORKDIR /app

# Install system dependencies
# libgomp1: OpenMP library for parallel processing in ML libraries (XGBoost, LightGBM)
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models

# Expose port (Cloud Run will set PORT env var, defaults to 8080)
EXPOSE 8080

# Health check (longer start period for ML model loading)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run the service - respect PORT environment variable from Cloud Run
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
