FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch to save space (approx 2GB saved)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Pre-download ML models during build to avoid runtime delays
# Download YOLO model
RUN python3 -c "\
    try:\n\
    from ultralytics import YOLO;\n\
    print('Downloading YOLO model...');\n\
    model = YOLO('yolov8n.pt');\n\
    print('✅ YOLO model downloaded successfully');\n\
    except Exception as e:\n\
    print(f'⚠️  YOLO model download failed: {e}');\n\
    " || echo "⚠️  YOLO import failed, will download at runtime"

# Download sentence-transformer model
RUN python3 -c "\
    try:\n\
    from sentence_transformers import SentenceTransformer;\n\
    print('Downloading sentence-transformer model...');\n\
    model = SentenceTransformer('all-MiniLM-L6-v2');\n\
    print('✅ Sentence-transformer model downloaded successfully');\n\
    except Exception as e:\n\
    print(f'⚠️  Sentence-transformer download failed: {e}');\n\
    " || echo "⚠️  Sentence-transformer import failed, will download at runtime"

# Copy application code
COPY . .

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Run the application - respect PORT environment variable
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
