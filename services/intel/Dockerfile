FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for scraping)
RUN playwright install chromium --with-deps

# Copy source code
COPY . .

# Expose port
EXPOSE 8090

# Default command - run API
CMD ["python", "-m", "uvicorn", "intel.adintel_api:app", "--host", "0.0.0.0", "--port", "8090"]
