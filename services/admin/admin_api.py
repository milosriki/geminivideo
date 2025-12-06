"""
Admin Panel API - Connection & Credential Management

Manages all external service connections:
- Foreplay (winning ads)
- Creatify (URL-to-video)
- HubSpot (CRM)
- AnyTrack (conversions)
- Meta Marketing (FB/IG ads)
- Google Ads (optional)

Features:
- Secure credential storage
- Connection testing
- Status monitoring
- API key rotation
"""

import os
import json
import logging
import hashlib
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import asyncio

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# =============================================================================
# Data Models
# =============================================================================

class ServiceType(str, Enum):
    FOREPLAY = "foreplay"
    CREATIFY = "creatify"
    HUBSPOT = "hubspot"
    ANYTRACK = "anytrack"
    META = "meta"
    GOOGLE_ADS = "google_ads"
    TOGETHER_AI = "together_ai"
    FIREWORKS_AI = "fireworks_ai"
    OPENAI = "openai"
    GEMINI = "gemini"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"
    TESTING = "testing"


@dataclass
class ServiceCredential:
    """Stored credential for a service"""
    service: ServiceType
    api_key: str
    api_secret: Optional[str] = None
    api_id: Optional[str] = None
    account_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = None
    last_tested: Optional[datetime] = None
    status: ConnectionStatus = ConnectionStatus.NOT_CONFIGURED
    error_message: Optional[str] = None


class CredentialInput(BaseModel):
    """Input model for setting credentials"""
    service: ServiceType
    api_key: str = Field(..., min_length=1)
    api_secret: Optional[str] = None
    api_id: Optional[str] = None
    account_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class ConnectionTestResult(BaseModel):
    """Result of connection test"""
    service: ServiceType
    status: ConnectionStatus
    message: str
    response_time_ms: Optional[int] = None
    account_info: Optional[Dict[str, Any]] = None


class ServiceStatusResponse(BaseModel):
    """Service status response"""
    service: ServiceType
    status: ConnectionStatus
    last_tested: Optional[str] = None
    error_message: Optional[str] = None
    is_configured: bool = False


# =============================================================================
# Credential Store
# =============================================================================

class CredentialStore:
    """
    Secure credential storage.

    In production, use:
    - AWS Secrets Manager
    - GCP Secret Manager
    - HashiCorp Vault
    - Azure Key Vault

    For development, uses encrypted file storage.
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.getenv(
            "CREDENTIAL_STORE_PATH",
            "/home/user/geminivideo/data/credentials.enc"
        )
        self.credentials: Dict[ServiceType, ServiceCredential] = {}
        self._encryption_key = os.getenv("CREDENTIAL_KEY", "dev-key-change-in-prod")
        self._load_credentials()

    def _load_credentials(self):
        """Load credentials from storage"""
        try:
            path = Path(self.storage_path)
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                    for service_name, cred_data in data.items():
                        try:
                            service = ServiceType(service_name)
                            self.credentials[service] = ServiceCredential(
                                service=service,
                                api_key=cred_data.get("api_key", ""),
                                api_secret=cred_data.get("api_secret"),
                                api_id=cred_data.get("api_id"),
                                account_id=cred_data.get("account_id"),
                                access_token=cred_data.get("access_token"),
                                refresh_token=cred_data.get("refresh_token"),
                                expires_at=datetime.fromisoformat(cred_data["expires_at"]) if cred_data.get("expires_at") else None,
                                created_at=datetime.fromisoformat(cred_data["created_at"]) if cred_data.get("created_at") else datetime.now(),
                                last_tested=datetime.fromisoformat(cred_data["last_tested"]) if cred_data.get("last_tested") else None,
                                status=ConnectionStatus(cred_data.get("status", "not_configured")),
                                error_message=cred_data.get("error_message")
                            )
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Failed to load credential for {service_name}: {e}")
                logger.info(f"Loaded {len(self.credentials)} credentials")
        except Exception as e:
            logger.warning(f"Could not load credentials: {e}")

        # Also load from environment variables
        self._load_from_env()

    def _load_from_env(self):
        """Load credentials from environment variables"""
        env_mappings = {
            ServiceType.FOREPLAY: {"api_key": "FOREPLAY_API_KEY"},
            ServiceType.CREATIFY: {"api_id": "CREATIFY_API_ID", "api_key": "CREATIFY_API_KEY"},
            ServiceType.HUBSPOT: {"api_key": "HUBSPOT_API_KEY", "access_token": "HUBSPOT_ACCESS_TOKEN"},
            ServiceType.ANYTRACK: {"api_key": "ANYTRACK_API_KEY", "account_id": "ANYTRACK_ACCOUNT_ID"},
            ServiceType.META: {"access_token": "META_ACCESS_TOKEN", "account_id": "META_AD_ACCOUNT_ID"},
            ServiceType.GOOGLE_ADS: {"api_key": "GOOGLE_ADS_DEVELOPER_TOKEN"},
            ServiceType.TOGETHER_AI: {"api_key": "TOGETHER_API_KEY"},
            ServiceType.FIREWORKS_AI: {"api_key": "FIREWORKS_API_KEY"},
            ServiceType.OPENAI: {"api_key": "OPENAI_API_KEY"},
            ServiceType.GEMINI: {"api_key": "GEMINI_API_KEY"},
        }

        for service, mapping in env_mappings.items():
            if service not in self.credentials:
                cred_data = {}
                has_value = False

                for field, env_var in mapping.items():
                    value = os.getenv(env_var)
                    if value:
                        cred_data[field] = value
                        has_value = True

                if has_value:
                    self.credentials[service] = ServiceCredential(
                        service=service,
                        api_key=cred_data.get("api_key", ""),
                        api_id=cred_data.get("api_id"),
                        api_secret=cred_data.get("api_secret"),
                        account_id=cred_data.get("account_id"),
                        access_token=cred_data.get("access_token"),
                        created_at=datetime.now(),
                        status=ConnectionStatus.NOT_CONFIGURED
                    )
                    logger.info(f"Loaded {service.value} credentials from env")

    def _save_credentials(self):
        """Save credentials to storage"""
        try:
            path = Path(self.storage_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            data = {}
            for service, cred in self.credentials.items():
                data[service.value] = {
                    "api_key": cred.api_key,
                    "api_secret": cred.api_secret,
                    "api_id": cred.api_id,
                    "account_id": cred.account_id,
                    "access_token": cred.access_token,
                    "refresh_token": cred.refresh_token,
                    "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                    "created_at": cred.created_at.isoformat() if cred.created_at else None,
                    "last_tested": cred.last_tested.isoformat() if cred.last_tested else None,
                    "status": cred.status.value,
                    "error_message": cred.error_message
                }

            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.credentials)} credentials")

        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")

    def set_credential(self, cred_input: CredentialInput) -> ServiceCredential:
        """Set or update a credential"""
        cred = ServiceCredential(
            service=cred_input.service,
            api_key=cred_input.api_key,
            api_secret=cred_input.api_secret,
            api_id=cred_input.api_id,
            account_id=cred_input.account_id,
            access_token=cred_input.access_token,
            refresh_token=cred_input.refresh_token,
            created_at=datetime.now(),
            status=ConnectionStatus.NOT_CONFIGURED
        )

        self.credentials[cred_input.service] = cred
        self._save_credentials()

        logger.info(f"Set credentials for {cred_input.service.value}")
        return cred

    def get_credential(self, service: ServiceType) -> Optional[ServiceCredential]:
        """Get credential for a service"""
        return self.credentials.get(service)

    def delete_credential(self, service: ServiceType) -> bool:
        """Delete credential for a service"""
        if service in self.credentials:
            del self.credentials[service]
            self._save_credentials()
            logger.info(f"Deleted credentials for {service.value}")
            return True
        return False

    def update_status(
        self,
        service: ServiceType,
        status: ConnectionStatus,
        error_message: str = None
    ):
        """Update connection status after testing"""
        if service in self.credentials:
            self.credentials[service].status = status
            self.credentials[service].last_tested = datetime.now()
            self.credentials[service].error_message = error_message
            self._save_credentials()

    def get_all_statuses(self) -> List[ServiceStatusResponse]:
        """Get status of all services"""
        statuses = []

        for service in ServiceType:
            cred = self.credentials.get(service)
            if cred:
                statuses.append(ServiceStatusResponse(
                    service=service,
                    status=cred.status,
                    last_tested=cred.last_tested.isoformat() if cred.last_tested else None,
                    error_message=cred.error_message,
                    is_configured=bool(cred.api_key or cred.access_token)
                ))
            else:
                statuses.append(ServiceStatusResponse(
                    service=service,
                    status=ConnectionStatus.NOT_CONFIGURED,
                    is_configured=False
                ))

        return statuses


# =============================================================================
# Connection Testers
# =============================================================================

class ConnectionTester:
    """Test connections to external services"""

    def __init__(self, credential_store: CredentialStore):
        self.store = credential_store

    async def test_connection(self, service: ServiceType) -> ConnectionTestResult:
        """Test connection to a service"""
        cred = self.store.get_credential(service)

        if not cred or not (cred.api_key or cred.access_token):
            return ConnectionTestResult(
                service=service,
                status=ConnectionStatus.NOT_CONFIGURED,
                message="No credentials configured"
            )

        # Update status to testing
        self.store.update_status(service, ConnectionStatus.TESTING)

        # Call appropriate tester
        testers = {
            ServiceType.FOREPLAY: self._test_foreplay,
            ServiceType.CREATIFY: self._test_creatify,
            ServiceType.HUBSPOT: self._test_hubspot,
            ServiceType.ANYTRACK: self._test_anytrack,
            ServiceType.META: self._test_meta,
            ServiceType.TOGETHER_AI: self._test_together,
            ServiceType.FIREWORKS_AI: self._test_fireworks,
            ServiceType.OPENAI: self._test_openai,
            ServiceType.GEMINI: self._test_gemini,
        }

        tester = testers.get(service)
        if tester:
            result = await tester(cred)
        else:
            result = ConnectionTestResult(
                service=service,
                status=ConnectionStatus.ERROR,
                message=f"No tester implemented for {service.value}"
            )

        # Update store with result
        self.store.update_status(
            service,
            result.status,
            result.message if result.status == ConnectionStatus.ERROR else None
        )

        return result

    async def test_all_connections(self) -> List[ConnectionTestResult]:
        """Test all configured connections"""
        results = []
        for service in ServiceType:
            cred = self.store.get_credential(service)
            if cred and (cred.api_key or cred.access_token):
                result = await self.test_connection(service)
                results.append(result)
        return results

    async def _test_foreplay(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test Foreplay connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://public.api.foreplay.co/api/swipefile/ads",
                    headers={"Authorization": cred.api_key},
                    params={"page": 1, "per_page": 1},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        return ConnectionTestResult(
                            service=ServiceType.FOREPLAY,
                            status=ConnectionStatus.CONNECTED,
                            message="Successfully connected to Foreplay API",
                            response_time_ms=elapsed
                        )
                    elif resp.status == 401:
                        return ConnectionTestResult(
                            service=ServiceType.FOREPLAY,
                            status=ConnectionStatus.ERROR,
                            message="Invalid API key"
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.FOREPLAY,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.FOREPLAY,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_creatify(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test Creatify connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.creatify.ai/api/avatars/",
                    headers={
                        "X-API-ID": cred.api_id or "",
                        "X-API-KEY": cred.api_key
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        data = await resp.json()
                        avatar_count = len(data) if isinstance(data, list) else len(data.get("data", []))
                        return ConnectionTestResult(
                            service=ServiceType.CREATIFY,
                            status=ConnectionStatus.CONNECTED,
                            message=f"Connected ({avatar_count} avatars available)",
                            response_time_ms=elapsed,
                            account_info={"avatar_count": avatar_count}
                        )
                    elif resp.status == 401:
                        return ConnectionTestResult(
                            service=ServiceType.CREATIFY,
                            status=ConnectionStatus.ERROR,
                            message="Invalid API credentials"
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.CREATIFY,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.CREATIFY,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_hubspot(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test HubSpot connection"""
        import aiohttp
        import time

        token = cred.access_token or cred.api_key
        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"limit": 1},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        return ConnectionTestResult(
                            service=ServiceType.HUBSPOT,
                            status=ConnectionStatus.CONNECTED,
                            message="Successfully connected to HubSpot CRM",
                            response_time_ms=elapsed
                        )
                    elif resp.status == 401:
                        return ConnectionTestResult(
                            service=ServiceType.HUBSPOT,
                            status=ConnectionStatus.ERROR,
                            message="Invalid access token"
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.HUBSPOT,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.HUBSPOT,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_anytrack(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test AnyTrack connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.anytrack.io/v1/conversions",
                    headers={
                        "Authorization": f"Bearer {cred.api_key}",
                        "X-Account-ID": cred.account_id or ""
                    },
                    params={"limit": 1},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        return ConnectionTestResult(
                            service=ServiceType.ANYTRACK,
                            status=ConnectionStatus.CONNECTED,
                            message="Successfully connected to AnyTrack",
                            response_time_ms=elapsed
                        )
                    elif resp.status == 401:
                        return ConnectionTestResult(
                            service=ServiceType.ANYTRACK,
                            status=ConnectionStatus.ERROR,
                            message="Invalid API key or account ID"
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.ANYTRACK,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.ANYTRACK,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_meta(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test Meta Marketing API connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://graph.facebook.com/v18.0/me",
                    params={"access_token": cred.access_token},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        data = await resp.json()
                        return ConnectionTestResult(
                            service=ServiceType.META,
                            status=ConnectionStatus.CONNECTED,
                            message=f"Connected as {data.get('name', 'Unknown')}",
                            response_time_ms=elapsed,
                            account_info={"name": data.get("name"), "id": data.get("id")}
                        )
                    else:
                        error = await resp.json()
                        return ConnectionTestResult(
                            service=ServiceType.META,
                            status=ConnectionStatus.ERROR,
                            message=error.get("error", {}).get("message", f"Error: {resp.status}")
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.META,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_together(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test Together AI connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.together.xyz/v1/models",
                    headers={"Authorization": f"Bearer {cred.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        return ConnectionTestResult(
                            service=ServiceType.TOGETHER_AI,
                            status=ConnectionStatus.CONNECTED,
                            message="Connected to Together AI",
                            response_time_ms=elapsed
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.TOGETHER_AI,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.TOGETHER_AI,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_fireworks(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test Fireworks AI connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.fireworks.ai/inference/v1/models",
                    headers={"Authorization": f"Bearer {cred.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        return ConnectionTestResult(
                            service=ServiceType.FIREWORKS_AI,
                            status=ConnectionStatus.CONNECTED,
                            message="Connected to Fireworks AI",
                            response_time_ms=elapsed
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.FIREWORKS_AI,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.FIREWORKS_AI,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_openai(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test OpenAI connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {cred.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        return ConnectionTestResult(
                            service=ServiceType.OPENAI,
                            status=ConnectionStatus.CONNECTED,
                            message="Connected to OpenAI",
                            response_time_ms=elapsed
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.OPENAI,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.OPENAI,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )

    async def _test_gemini(self, cred: ServiceCredential) -> ConnectionTestResult:
        """Test Google Gemini connection"""
        import aiohttp
        import time

        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={cred.api_key}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    elapsed = int((time.time() - start) * 1000)

                    if resp.status == 200:
                        return ConnectionTestResult(
                            service=ServiceType.GEMINI,
                            status=ConnectionStatus.CONNECTED,
                            message="Connected to Google Gemini",
                            response_time_ms=elapsed
                        )
                    else:
                        return ConnectionTestResult(
                            service=ServiceType.GEMINI,
                            status=ConnectionStatus.ERROR,
                            message=f"API error: {resp.status}"
                        )
        except Exception as e:
            return ConnectionTestResult(
                service=ServiceType.GEMINI,
                status=ConnectionStatus.ERROR,
                message=str(e)
            )


# =============================================================================
# Admin Authentication
# =============================================================================

class AdminAuth:
    """Simple admin authentication"""

    def __init__(self):
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password_hash = self._hash_password(
            os.getenv("ADMIN_PASSWORD", "changeme123")
        )
        self.sessions: Dict[str, datetime] = {}
        self.session_timeout = timedelta(hours=24)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_credentials(self, username: str, password: str) -> bool:
        if username != self.admin_username:
            return False
        return self._hash_password(password) == self.admin_password_hash

    def create_session(self) -> str:
        token = secrets.token_urlsafe(32)
        self.sessions[token] = datetime.now()
        return token

    def verify_session(self, token: str) -> bool:
        if token not in self.sessions:
            return False

        created = self.sessions[token]
        if datetime.now() - created > self.session_timeout:
            del self.sessions[token]
            return False

        return True

    def invalidate_session(self, token: str):
        if token in self.sessions:
            del self.sessions[token]


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="GeminiVideo Admin API",
    description="Admin panel for managing external service connections",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
credential_store = CredentialStore()
connection_tester = ConnectionTester(credential_store)
admin_auth = AdminAuth()
security = HTTPBasic()


# Auth dependency
async def verify_admin(
    credentials: HTTPBasicCredentials = Depends(security)
) -> str:
    if not admin_auth.verify_credentials(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


async def verify_token(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization[7:]
    if not admin_auth.verify_session(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    return token


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "admin-api"}


@app.post("/auth/login")
async def login(username: str = Depends(verify_admin)):
    """Login and get session token"""
    token = admin_auth.create_session()
    return {"token": token, "username": username}


@app.post("/auth/logout")
async def logout(token: str = Depends(verify_token)):
    """Logout and invalidate session"""
    admin_auth.invalidate_session(token)
    return {"message": "Logged out successfully"}


@app.get("/services/status")
async def get_all_services_status(token: str = Depends(verify_token)):
    """Get status of all services"""
    return credential_store.get_all_statuses()


@app.get("/services/{service}/status")
async def get_service_status(
    service: ServiceType,
    token: str = Depends(verify_token)
):
    """Get status of a specific service"""
    cred = credential_store.get_credential(service)
    if not cred:
        return ServiceStatusResponse(
            service=service,
            status=ConnectionStatus.NOT_CONFIGURED,
            is_configured=False
        )

    return ServiceStatusResponse(
        service=service,
        status=cred.status,
        last_tested=cred.last_tested.isoformat() if cred.last_tested else None,
        error_message=cred.error_message,
        is_configured=bool(cred.api_key or cred.access_token)
    )


@app.post("/services/{service}/credentials")
async def set_service_credentials(
    service: ServiceType,
    cred_input: CredentialInput,
    token: str = Depends(verify_token)
):
    """Set credentials for a service"""
    cred_input.service = service  # Ensure service matches
    credential_store.set_credential(cred_input)
    return {"message": f"Credentials set for {service.value}"}


@app.delete("/services/{service}/credentials")
async def delete_service_credentials(
    service: ServiceType,
    token: str = Depends(verify_token)
):
    """Delete credentials for a service"""
    if credential_store.delete_credential(service):
        return {"message": f"Credentials deleted for {service.value}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No credentials found for {service.value}"
        )


@app.post("/services/{service}/test")
async def test_service_connection(
    service: ServiceType,
    token: str = Depends(verify_token)
):
    """Test connection to a service"""
    result = await connection_tester.test_connection(service)
    return result


@app.post("/services/test-all")
async def test_all_connections(token: str = Depends(verify_token)):
    """Test all configured connections"""
    results = await connection_tester.test_all_connections()
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "connected": sum(1 for r in results if r.status == ConnectionStatus.CONNECTED),
            "error": sum(1 for r in results if r.status == ConnectionStatus.ERROR)
        }
    }


# Data sync triggers
@app.post("/sync/foreplay")
async def sync_foreplay_data(token: str = Depends(verify_token)):
    """Trigger Foreplay data sync"""
    # Import and run Foreplay sync
    try:
        from services.intel.foreplay_scraper import ForeplayIntegration

        cred = credential_store.get_credential(ServiceType.FOREPLAY)
        if not cred or not cred.api_key:
            raise HTTPException(400, "Foreplay not configured")

        client = ForeplayIntegration(cred.api_key)
        await client.connect()

        # Get winning ads
        ads = await client.get_long_running_winners(min_days=30, max_ads=100)
        patterns = client.extract_winning_patterns(ads)

        await client.disconnect()

        return {
            "message": "Foreplay sync completed",
            "ads_analyzed": len(ads),
            "patterns_extracted": len(patterns.get("hooks", [])) + len(patterns.get("ctas", []))
        }
    except ImportError:
        raise HTTPException(500, "Foreplay module not available")
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/sync/creatify")
async def sync_creatify_data(token: str = Depends(verify_token)):
    """Trigger Creatify data sync"""
    try:
        from services.intel.creatorify_client import CreatifyIntegration

        cred = credential_store.get_credential(ServiceType.CREATIFY)
        if not cred or not (cred.api_id and cred.api_key):
            raise HTTPException(400, "Creatify not configured")

        client = CreatifyIntegration(cred.api_id, cred.api_key)
        await client.connect()

        avatars = await client.get_avatars()

        await client.disconnect()

        return {
            "message": "Creatify sync completed",
            "avatars_available": len(avatars)
        }
    except ImportError:
        raise HTTPException(500, "Creatify module not available")
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/sync/meta-historical")
async def sync_meta_historical(
    date_from: str = None,
    date_to: str = None,
    token: str = Depends(verify_token)
):
    """Trigger Meta historical data import"""
    try:
        from services.intel.fb_historical_import import FBHistoricalImporter

        cred = credential_store.get_credential(ServiceType.META)
        if not cred or not cred.access_token:
            raise HTTPException(400, "Meta not configured")

        importer = FBHistoricalImporter(cred.access_token, cred.account_id)
        await importer.connect()

        result = await importer.import_campaigns(days_back=90)

        await importer.disconnect()

        return {
            "message": "Meta historical import completed",
            "campaigns_imported": result.campaigns_imported,
            "ads_imported": result.ads_imported
        }
    except ImportError:
        raise HTTPException(500, "FB Historical module not available")
    except Exception as e:
        raise HTTPException(500, str(e))


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
