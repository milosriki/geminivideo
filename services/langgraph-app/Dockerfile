FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv pip install --system .
RUN uv pip install --system fastapi uvicorn langserve[all]

# Copy source code
COPY . .

# Expose port
ENV PORT=8000
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
