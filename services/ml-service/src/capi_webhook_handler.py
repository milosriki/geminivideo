"""
CAPI Webhook Handler - Receive Meta Conversion API events

Endpoints for receiving webhooks from Meta:
- POST /webhooks/capi - Main conversion events
- GET /webhooks/capi - Verification challenge
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, List
import hmac
import hashlib
import logging
import os

from .capi_feedback_loop import CAPIFeedbackLoop

logger = logging.getLogger(__name__)
router = APIRouter()

# Secret for verifying webhooks
CAPI_APP_SECRET = os.getenv('META_APP_SECRET', '')

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Meta webhook signature"""
    expected = hmac.new(
        CAPI_APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@router.get("/webhooks/capi")
async def verify_webhook(hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None):
    """Handle Meta webhook verification challenge"""
    verify_token = os.getenv('META_VERIFY_TOKEN', 'your_verify_token')

    if hub_mode == 'subscribe' and hub_verify_token == verify_token:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)

    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhooks/capi")
async def receive_capi_events(request: Request, background_tasks: BackgroundTasks):
    """
    Receive conversion events from Meta CAPI.

    These events tell us:
    - Who converted
    - What they bought
    - How much they spent

    This data feeds back into model training.
    """
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    body = await request.body()

    if CAPI_APP_SECRET and not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()

    # Process events in background
    events = data.get('entry', [])

    for entry in events:
        for event in entry.get('messaging', []) or entry.get('changes', []):
            background_tasks.add_task(process_capi_event, event)

    logger.info(f"Received {len(events)} CAPI events")

    return {"status": "received", "events": len(events)}

async def process_capi_event(event: Dict):
    """Process a single CAPI event"""
    try:
        # Get database session
        from shared.db.session import get_session
        async with get_session() as session:
            loop = CAPIFeedbackLoop(session)
            result = await loop.process_capi_event(event)
            logger.info(f"Processed event: {result}")
    except Exception as e:
        logger.error(f"Failed to process CAPI event: {e}")
