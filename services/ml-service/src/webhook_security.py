"""
Webhook Security - Signature Verification
Prevents unauthorized webhook calls
"""

import hmac
import hashlib
import os
from typing import Optional
from fastapi import Request, HTTPException, Header
import logging

logger = logging.getLogger(__name__)

# Get webhook secrets from environment
HUBSPOT_SECRET = os.getenv('HUBSPOT_WEBHOOK_SECRET', '')
META_SECRET = os.getenv('META_WEBHOOK_SECRET', '')
CAPI_SECRET = os.getenv('CAPI_WEBHOOK_SECRET', '')


def verify_hubspot_signature(request: Request, signature: Optional[str] = None) -> bool:
    """
    Verify HubSpot webhook signature
    
    HubSpot uses X-HubSpot-Signature-v3 header
    """
    if not HUBSPOT_SECRET:
        logger.warning("HUBSPOT_WEBHOOK_SECRET not set - webhook verification disabled")
        return True  # Allow if secret not configured (dev mode)
    
    if not signature:
        signature = request.headers.get('X-HubSpot-Signature-v3', '')
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    # Get request body
    body = request.body()
    if isinstance(body, bytes):
        body_str = body.decode('utf-8')
    else:
        body_str = str(body)
    
    # Compute expected signature
    expected = hmac.new(
        HUBSPOT_SECRET.encode('utf-8'),
        body_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(signature, expected)


async def verify_meta_signature(request: Request, signature: Optional[str] = None) -> bool:
    """
    Verify Meta/Facebook webhook signature
    
    Meta uses X-Hub-Signature-256 header (SHA256)
    """
    if not META_SECRET:
        logger.warning("META_WEBHOOK_SECRET not set - webhook verification disabled")
        return True
    
    if not signature:
        signature = request.headers.get('X-Hub-Signature-256', '')
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    # Get request body
    body = await request.body()
    if isinstance(body, bytes):
        body_str = body.decode('utf-8')
    else:
        body_str = str(body)
    
    # Compute expected signature
    expected = hmac.new(
        META_SECRET.encode('utf-8'),
        body_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(signature, expected)


async def verify_capi_signature(request: Request, signature: Optional[str] = None) -> bool:
    """
    Verify CAPI (Conversions API) webhook signature
    """
    if not CAPI_SECRET:
        logger.warning("CAPI_WEBHOOK_SECRET not set - webhook verification disabled")
        return True
    
    if not signature:
        signature = request.headers.get('X-CAPI-Signature', '')
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    # Get request body
    body = await request.body()
    if isinstance(body, bytes):
        body_str = body.decode('utf-8')
    else:
        body_str = str(body)
    
    # Compute expected signature
    expected = hmac.new(
        CAPI_SECRET.encode('utf-8'),
        body_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(signature, expected)


async def verify_webhook_middleware(request: Request, webhook_type: str = 'hubspot'):
    """
    Middleware to verify webhook signatures
    """
    try:
        if webhook_type == 'hubspot':
            if not await verify_hubspot_signature(request):
                raise HTTPException(status_code=401, detail="Invalid HubSpot webhook signature")
        elif webhook_type == 'meta':
            if not await verify_meta_signature(request):
                raise HTTPException(status_code=401, detail="Invalid Meta webhook signature")
        elif webhook_type == 'capi':
            if not await verify_capi_signature(request):
                raise HTTPException(status_code=401, detail="Invalid CAPI webhook signature")
        else:
            logger.warning(f"Unknown webhook type: {webhook_type}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        raise HTTPException(status_code=500, detail="Webhook verification failed")

