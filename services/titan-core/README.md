# Titan Core Service

This service powers the AI orchestration for Gemini Video.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Set the following environment variables (e.g., in a `.env` file):
    ```bash
    GEMINI_API_KEY=your_gemini_key
    ```

3.  **Run**:
    ```bash
    python orchestrator.py
    ```

## Docker

Build and run with Docker:

```bash
docker build -t titan-core .
docker run -e GEMINI_API_KEY=your_key titan-core
```
