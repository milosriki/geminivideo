FROM python:3.11-slim as build

WORKDIR /app

# Install system dependencies for building Python packages
# vowpalwabbit requires boost-python, cmake, and zlib
# libgomp1: OpenMP library for parallel processing in ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-dev \
    libboost-python-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libboost-program-options-dev \
    libgomp1 \
    zlib1g-dev \
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
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
