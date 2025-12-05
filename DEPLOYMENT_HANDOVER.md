# Titan Engine - Deployment Handover & Setup Guide

**Date:** December 4, 2025
**Status:** Cloud Deployment In Progress (Build ID: `412fc961`)
**Repository:** `https://github.com/milosriki/geminivideo`

## 1. Cloud Deployment Access

Once the current deployment completes, the Titan Engine will be accessible at the following URLs:

*   **Frontend Dashboard:** `https://frontend-489769736562.us-central1.run.app`
*   **Gateway API:** `https://ptd-fitness-backend-489769736562.us-central1.run.app`
*   **API Documentation:** See `docs/API_REFERENCE.md` in the repo.

## 2. Latest Updates (Merged Fixes)

*   **Redis Stability:** 
    *   `gateway-api`: Redis is now optional (controlled by `REDIS_ENABLED`).
    *   `video-agent`: Connection failures are handled gracefully (no crash on startup).
*   **Dependency Fixes:**
    *   `titan-core`: Updated `autogen` packages to `0.4.0+` to fix missing modules.
    *   `drive-intel`: Resolved `opencv` and `torch` version conflicts.
*   **Build Pipeline:** Fixed race conditions in `cloudbuild.yaml`.
*   **New Services:** Added `drive-worker` and `video-worker` to Cloud Run deployment for background processing.

## 2. Setting Up on a New Machine

To run the Titan Engine locally or develop on another machine, follow these steps:

### Prerequisites
*   Git
*   Docker & Docker Desktop (Running)
*   Node.js (v18+) & npm
*   Python 3.11+

### Step-by-Step Setup

### Step-by-Step Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/milosriki/geminivideo.git
    cd geminivideo
    ```

2.  **Configure Environment Variables (CRITICAL):**
    *   Copy the template: `cp .env.example .env`
    *   **Fill in the `.env` file** with your real API keys.
    *   *Note: You can copy the content from your main machine's `.env` file if available.*

3.  **Start with Docker (Recommended):**
    This will spin up the Frontend, all Microservices, and database connections.
    ```bash
    # Make scripts executable
    chmod +x scripts/*.sh
    
    # Start the full stack
    ./scripts/start-all.sh
    ```
    *   Frontend: `http://localhost:3000`
    *   Gateway API: `http://localhost:8000`

4.  **Verify Installation:**
    Run the verification script to ensure all services are healthy.
    ```bash
    python3 scripts/verify_titan_system.py
    ```

## 3. Latest Features Included

*   **ROI Dashboard:** Real-time visualization of campaign performance (ROAS, CTR).
*   **Prediction Accuracy:** 14-day trend analysis of AI prediction vs. actuals.
*   **Correlation Heatmap:** Visual insights into which creative features drive performance.
*   **Premium SaaS Design:** Updated UI with Tailwind Plus components (Skeleton, Toast, etc.).
*   **API Documentation:** Comprehensive reference in `docs/API_REFERENCE.md`.

## 4. Troubleshooting

*   **Build Errors:** If `npm install` fails, ensure you are using Node v18+.
*   **Docker Memory:** Ensure Docker has at least 6GB of RAM allocated.
*   **Ports:** Free up ports 3000, 8000, 8001, 8002, 8003, 8004, 5432, 6379.

---
**Next Steps:**
1.  Wait for Cloud Build `8b7e04aa` to finish.
2.  Verify the Cloud Run URLs.
3.  Clone on your new machine and run `./scripts/start-all.sh`.
