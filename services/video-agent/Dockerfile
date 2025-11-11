FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

# Create outputs directory
RUN mkdir -p /outputs

# Expose port
EXPOSE 8082

# Run the application
CMD ["uvicorn", "src.index:app", "--host", "0.0.0.0", "--port", "8082"]
