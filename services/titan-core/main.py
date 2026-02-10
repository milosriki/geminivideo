import os
import time
print("🚀 TITAN CORE: Starting up...", flush=True)
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
try:
    from orchestrator import run_titan_flow
except Exception as e:
    print(f"CRITICAL ERROR IMPORTING ORCHESTRATOR: {e}")
    import traceback
    traceback.print_exc()
    run_titan_flow = None

# Track startup time for uptime calculation
_start_time = time.time()

# Import Auth (Zero-Trust)
from fastapi import Security
try:
    from gemini_common.auth import verify_internal_api_key
    AUTH_ENABLED = True
except ImportError:
    print("gemini-common auth not available - security disabled")
    AUTH_ENABLED = False

app = FastAPI(
    title="Titan Core Service",
    dependencies=[Security(verify_internal_api_key)] if AUTH_ENABLED else []
)

# Production safety check - prevent debug mode in production
if app.debug and os.environ.get('ENVIRONMENT') == 'production':
    raise RuntimeError("Debug mode detected in production!")

class GenerateRequest(BaseModel):
    video_context: str
    niche: str = "fitness"

@app.post("/generate")
async def generate_script(request: GenerateRequest):
    if run_titan_flow is None:
        raise HTTPException(status_code=500, detail="Orchestrator failed to load. Check container logs for import error.")
    try:
        result = await run_titan_flow(request.video_context, request.niche)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    uptime = int(time.time() - _start_time)
    return {
        "status": "healthy",
        "service": "titan-core",
        "uptime": uptime
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
