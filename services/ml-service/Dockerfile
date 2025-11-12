FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ML packages
# - build-essential: C/C++ compilers for Python extensions (numpy, scipy, xgboost)
# - libgomp1: OpenMP library for parallel processing in ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
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

# Run the service - respect PORT environment variable from Cloud Run
CMD uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
