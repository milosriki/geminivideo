import os
from fastapi import HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

API_KEY_NAME = "X-Internal-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_internal_api_key():
    """Retrieves the internal API key from environment variables."""
    # SECURITY: No hardcoded fallback. If INTERNAL_API_KEY not set, verify_internal_api_key() returns 403
    return os.getenv("INTERNAL_API_KEY", "")

async def verify_internal_api_key(
    request: Request,
    api_key_header: str = Security(api_key_header)
):
    """
    Verifies the internal API key from the request header.
    Dependencies:
        - INTERNAL_API_KEY env var must be set (or default used)
    """
    if request.url.path == "/health":
        return None

    internal_key = get_internal_api_key()
    
    # If no key is set in env, we fail open or closed? Closed is safer.
    if not internal_key:
         raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Server misconfiguration: INTERNAL_API_KEY not set"
        )

    if api_key_header == internal_key:
        return api_key_header
    
    # Check if user is passing it via query param (fallback)
    # or if there's a specific logic for dev
    
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )
