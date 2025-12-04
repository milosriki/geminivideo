# Titan Engine - Deployment Handover & Setup Guide

**Date:** December 4, 2025
**Status:** Cloud Deployment In Progress (Build ID: `8b7e04aa`)
**Repository:** `https://github.com/milosriki/geminivideo`

## 1. Cloud Deployment Access

Once the current deployment completes, the Titan Engine will be accessible at the following URLs:

*   **Frontend Dashboard:** `https://frontend-489769736562.us-central1.run.app` (Estimated)
*   **Gateway API:** `https://ptd-fitness-backend-489769736562.us-central1.run.app`
*   **API Documentation:** See `docs/API_REFERENCE.md` in the repo.

## 2. Setting Up on a New Machine

To run the Titan Engine locally or develop on another machine, follow these steps:

### Prerequisites
*   Git
*   Docker & Docker Desktop (Running)
*   Node.js (v18+) & npm
*   Python 3.11+

### Step-by-Step Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/milosriki/geminivideo.git
    cd geminivideo
    ```

2.  **Configure Environment Variables:**
    *   Copy the `.env.template` to `.env` (if I created one, otherwise use the provided keys).
    *   **CRITICAL:** You must populate the `.env` file with the API keys provided in our chat history (Gemini, OpenAI, Anthropic, Meta, Firebase, Supabase).
    *   *Note: For security, keys are not committed to the repo.*

3.  **Start with Docker (Recommended):**
    This will spin up the Frontend, all Microservices, Redis, and Postgres.
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
