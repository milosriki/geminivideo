FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ML packages
# - build-essential: C/C++ compilers for building Python extensions
# - cmake: Required for vowpalwabbit
# - libboost-all-dev: Boost libraries required by vowpalwabbit
# - zlib1g-dev: Compression library
# - libgomp1: OpenMP library for parallel processing
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    zlib1g-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models

# Expose port
EXPOSE 8003

# Run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
