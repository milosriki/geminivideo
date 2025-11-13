FROM python:3.11-slim as build

WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libass-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/video-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared config directory
COPY shared/config /app/config

# Copy application code
COPY services/video-agent .

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run the application - respect PORT environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
