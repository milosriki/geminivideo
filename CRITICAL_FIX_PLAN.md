# CRITICAL FIX PLAN - 157 Issues, 20 Agents, Systematic Approach

**Generated:** 2025-12-09  
**Total Issues:** 157 (Current) + 200 (Previous) = ~357 issues  
**Agents:** 20 Claude Opus 4.5 parallel  
**Approach:** Dependency-aware, systematic, test-driven

---

## EXECUTIVE SUMMARY

### Current State: ❌ NOT PRODUCTION READY (3.5/10)

**Blocking Issues:** 45 CRITICAL must be fixed before ANY deployment

**Right Way:** Fix in dependency order, not by severity alone

---

## PART 1: DEPENDENCY ANALYSIS

### Critical Path (Must Fix First)

```
┌─────────────────────────────────────────────────────────┐
│              BLOCKING ISSUES (Fix First)                 │
└─────────────────────────────────────────────────────────┘

1. Build Blockers (Service won't start)
   ├── Missing lib/api.ts → Frontend crashes
   ├── Broken imports → Services won't start
   └── asyncio.run() in Celery → Memory leaks, crashes
   
2. Security Blockers (Can't deploy)
   ├── Path traversal → Arbitrary file access
   ├── SQL injection → Data breach
   ├── No webhook signatures → Fake data
   └── Hardcoded credentials → Account compromise
   
3. Stability Blockers (Will crash)
   ├── DB connections not closed → Connection exhaustion
   ├── Missing timeouts → Indefinite hangs
   └── RAG dimension mismatch → Query failures
```

### Non-Blocking (Can Fix Later)

- API versioning (nice to have)
- Documentation (can add later)
- Error format standardization (refactor)
- Circuit breakers (optimization)

---

## PART 2: SYSTEMATIC FIX ORDER

### PHASE 0: FOUNDATION (1 Hour) - 4 Agents

**Why First:** Everything else depends on services starting

**Agents 1-4: Build Fixes**

#### Agent 1: Frontend Build Fix
```typescript
// File: frontend/src/lib/api.ts
// CREATE MISSING FILE

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle auth error
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

#### Agent 2: Fix Broken Imports
```python
# File: services/ml-service/src/batch_api.py
# FIX IMPORTS (lines 21-28)

# BEFORE (broken):
# from src.enhanced_ctr_model import enhanced_ctr_predictor
# from src.ctr_model import ctr_predictor

# AFTER (fixed):
try:
    from src.enhanced_ctr_model import enhanced_ctr_predictor
except ImportError:
    enhanced_ctr_predictor = None

try:
    from src.ctr_model import ctr_predictor
except ImportError:
    ctr_predictor = None

# Add graceful degradation
if not enhanced_ctr_predictor and not ctr_predictor:
    logger.warning("No CTR predictors available")
```

#### Agent 3: Fix asyncio.run() in Celery
```python
# File: services/ml-service/src/celery_tasks.py
# FIX LINES 103, 170, 216

# BEFORE (broken):
# result = asyncio.run(async_function())

# AFTER (fixed):
import asyncio
from celery import current_task

@celery_app.task
def sync_wrapper_async_task():
    """Wrapper to run async function in Celery"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_function())
    finally:
        loop.close()

# OR use celery's async support:
from celery import Task

class AsyncTask(Task):
    async def run(self, *args, **kwargs):
        return await async_function()
```

#### Agent 4: Fix RAG Dimension Mismatch
```python
# File: services/rag/winner_index.py
# STANDARDIZE EMBEDDING DIMENSION

# BEFORE (inconsistent):
# dimension = 384  # Some places
# dimension = 768  # Other places
# dimension = 3072 # Other places

# AFTER (standardized):
EMBEDDING_DIMENSION = 768  # Use consistent dimension

# Update all places:
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')  # 768 dimensions
# OR
model = SentenceTransformer('all-MiniLM-L6-v2')   # 384 dimensions (faster)

# Choose ONE and use everywhere:
EMBEDDING_DIMENSION = model.get_sentence_embedding_dimension()
```

**Time:** 1 hour  
**Impact:** Services can start, builds succeed

---

### PHASE 1: SECURITY FIXES (2.5 Hours) - 12 Agents

**Why Second:** Can't deploy with security vulnerabilities

#### Agents 5-8: Path Traversal & SQL Injection

**Agent 5: Fix Path Traversal (competitor_tracker.py:288)**
```python
# File: services/market-intel/competitor_tracker.py
# FIX LINE 288

import os
from pathlib import Path

def safe_save_file(filename: str, content: bytes, base_dir: str = "/tmp") -> str:
    """
    Safely save file with path traversal protection
    """
    # Sanitize filename
    filename = os.path.basename(filename)  # Remove any path components
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")  # Allow only safe chars
    
    # Validate extension
    allowed_extensions = {'.csv', '.json', '.txt'}
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise ValueError(f"Invalid file extension: {ext}")
    
    # Create safe path
    safe_path = Path(base_dir) / filename
    
    # Ensure within base directory (prevent ../ attacks)
    safe_path = safe_path.resolve()
    base_path = Path(base_dir).resolve()
    
    if not str(safe_path).startswith(str(base_path)):
        raise ValueError("Path traversal detected")
    
    # Save file
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.write_bytes(content)
    
    # Set secure permissions (owner read/write only)
    os.chmod(safe_path, 0o600)
    
    return str(safe_path)
```

**Agent 6: Fix Path Traversal (knowledge.ts:44)**
```typescript
// File: services/gateway-api/src/knowledge.ts
// FIX LINE 44

import * as path from 'path';
import * as crypto from 'crypto';

function sanitizeGcsPath(userPath: string): string {
    // Remove any path traversal attempts
    const normalized = path.normalize(userPath);
    
    // Remove any .. or . components
    const parts = normalized.split(path.sep).filter(part => 
        part !== '..' && part !== '.' && part !== ''
    );
    
    // Generate safe filename
    const safeFilename = parts[parts.length - 1];
    const sanitized = safeFilename.replace(/[^a-zA-Z0-9._-]/g, '_');
    
    // Add hash to prevent collisions
    const hash = crypto.createHash('sha256')
        .update(userPath + Date.now().toString())
        .digest('hex')
        .substring(0, 8);
    
    return `knowledge/${sanitized}_${hash}`;
}
```

**Agent 7: Fix Local File Inclusion (main.py:2047)**
```python
# File: services/ml-service/src/main.py
# FIX LINE 2047

import os
from pathlib import Path

@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """
    Get report file - WITH PATH TRAVERSAL PROTECTION
    """
    # Validate report_id format (UUID or alphanumeric)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', report_id):
        raise HTTPException(status_code=400, detail="Invalid report_id")
    
    # Define safe report directory
    REPORT_DIR = Path("/app/reports")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Construct safe path
    safe_path = REPORT_DIR / f"{report_id}.pdf"
    
    # Resolve to absolute path
    safe_path = safe_path.resolve()
    report_dir_abs = REPORT_DIR.resolve()
    
    # Verify path is within report directory
    if not str(safe_path).startswith(str(report_dir_abs)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check file exists
    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Return file
    return FileResponse(str(safe_path))
```

**Agent 8: Fix SQL Injection (analytics.ts:57)**
```typescript
// File: services/gateway-api/src/routes/analytics.ts
// FIX LINE 57

import { Pool } from 'pg';

// BEFORE (vulnerable):
// const query = `SELECT * FROM campaigns WHERE name = '${req.query.name}'`;

// AFTER (parameterized):
app.get('/api/analytics/campaigns', async (req: Request, res: Response) => {
    const { name, status, start_date, end_date } = req.query;
    
    // Build parameterized query
    const conditions: string[] = [];
    const params: any[] = [];
    let paramIndex = 1;
    
    if (name) {
        conditions.push(`name = $${paramIndex}`);
        params.push(name);
        paramIndex++;
    }
    
    if (status) {
        // Validate status against allowed values
        const allowedStatuses = ['active', 'paused', 'archived'];
        if (!allowedStatuses.includes(status as string)) {
            return res.status(400).json({ error: 'Invalid status' });
        }
        conditions.push(`status = $${paramIndex}`);
        params.push(status);
        paramIndex++;
    }
    
    if (start_date) {
        conditions.push(`created_at >= $${paramIndex}`);
        params.push(start_date);
        paramIndex++;
    }
    
    if (end_date) {
        conditions.push(`created_at <= $${paramIndex}`);
        params.push(end_date);
        paramIndex++;
    }
    
    const whereClause = conditions.length > 0 
        ? `WHERE ${conditions.join(' AND ')}`
        : '';
    
    const query = `SELECT * FROM campaigns ${whereClause} LIMIT 100`;
    
    try {
        const result = await pgPool.query(query, params);
        res.json(result.rows);
    } catch (error) {
        res.status(500).json({ error: 'Database error' });
    }
});
```

#### Agents 9-12: Webhook Signature Verification

**Agent 9: HubSpot Webhook Signature**
```python
# File: services/ml-service/src/main.py
# FIX LINES 1054-1068

import hmac
import hashlib
from fastapi import Request, HTTPException

@app.post("/api/webhook/hubspot")
async def hubspot_webhook(request: Request):
    """
    HubSpot webhook with signature verification
    """
    # Get signature from header
    signature = request.headers.get('X-HubSpot-Signature-v3')
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # Get webhook secret from environment
    webhook_secret = os.getenv('HUBSPOT_WEBHOOK_SECRET')
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    # Get request body
    body = await request.body()
    
    # Get timestamp from header
    timestamp = request.headers.get('X-HubSpot-Request-Timestamp')
    if not timestamp:
        raise HTTPException(status_code=401, detail="Missing timestamp")
    
    # Verify timestamp (prevent replay attacks)
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > 300:  # 5 minutes
        raise HTTPException(status_code=401, detail="Request too old")
    
    # Compute expected signature
    source_string = f"{webhook_secret}{timestamp}{body.decode('utf-8')}"
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        source_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison (prevent timing attacks)
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    data = await request.json()
    # ... rest of webhook processing ...
```

**Agent 10: Meta CAPI Webhook Signature**
```python
# File: services/ml-service/src/main.py
# FIX LINES 1030-1051

import hmac
import hashlib
import json

@app.post("/api/webhook/meta/capi")
async def meta_capi_webhook(request: Request):
    """
    Meta Conversions API webhook with signature verification
    """
    # Get signature from header
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # Get app secret from environment
    app_secret = os.getenv('META_APP_SECRET')
    if not app_secret:
        raise HTTPException(status_code=500, detail="App secret not configured")
    
    # Get request body
    body = await request.body()
    
    # Compute expected signature
    expected_signature = hmac.new(
        app_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Meta sends signature as "sha256=<hash>"
    received_hash = signature.replace('sha256=', '')
    
    # Constant-time comparison
    if not hmac.compare_digest(expected_signature, received_hash):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    data = json.loads(body)
    # ... rest of webhook processing ...
```

**Agent 11-12: WebSocket Authentication**
```typescript
// File: services/gateway-api/src/realtime/websocket-manager.ts
// FIX ALL 4 ENDPOINTS

import { Server as HTTPServer } from 'http';
import { Server as SocketServer } from 'socket.io';
import jwt from 'jsonwebtoken';

// Add authentication middleware
io.use(async (socket, next) => {
    try {
        // Get token from handshake
        const token = socket.handshake.auth.token || socket.handshake.query.token;
        
        if (!token) {
            return next(new Error('Authentication required'));
        }
        
        // Verify JWT token
        const secret = process.env.JWT_SECRET || process.env.AUTH_SECRET;
        if (!secret) {
            return next(new Error('JWT secret not configured'));
        }
        
        const decoded = jwt.verify(token as string, secret);
        
        // Attach user info to socket
        socket.data.user = decoded;
        socket.data.userId = decoded.userId || decoded.sub;
        
        next();
    } catch (error) {
        next(new Error('Invalid token'));
    }
});

// Add rate limiting per user
const userConnections = new Map<string, number>();
const MAX_CONNECTIONS_PER_USER = 5;

io.use((socket, next) => {
    const userId = socket.data.userId;
    const currentConnections = userConnections.get(userId) || 0;
    
    if (currentConnections >= MAX_CONNECTIONS_PER_USER) {
        return next(new Error('Too many connections'));
    }
    
    userConnections.set(userId, currentConnections + 1);
    
    socket.on('disconnect', () => {
        const count = userConnections.get(userId) || 0;
        userConnections.set(userId, Math.max(0, count - 1));
    });
    
    next();
});
```

#### Agents 13-16: Credential Removal

**Agent 13-14: Remove Hardcoded DB Passwords**
```yaml
# File: docker-compose.yml
# FIX ALL 11 OCCURRENCES

# BEFORE (hardcoded):
# POSTGRES_PASSWORD: geminivideo

# AFTER (from env):
postgres:
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-geminivideo}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # REQUIRED, no default
    POSTGRES_DB: ${POSTGRES_DB:-geminivideo}

# Add to .env.example:
# POSTGRES_PASSWORD=your-secure-password-here
# POSTGRES_USER=geminivideo
# POSTGRES_DB=geminivideo
```

**Agent 15-16: Move API Keys to Backend**
```typescript
// File: frontend/src/services/geminiService.ts
// FIX LINE 161 - Remove API key from URL

// BEFORE (exposed):
// const url = `https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=${API_KEY}`;

// AFTER (proxy through backend):
import api from '@/lib/api';

export async function generateContent(prompt: string) {
    // Call backend endpoint instead
    const response = await api.post('/api/gemini/generate', {
        prompt,
        model: 'gemini-pro'
    });
    return response.data;
}

// Backend endpoint (services/gateway-api/src/index.ts):
app.post('/api/gemini/generate',
  apiRateLimiter,
  async (req: Request, res: Response) => {
    const { prompt, model } = req.body;
    
    // Get API key from environment (server-side only)
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
        return res.status(500).json({ error: 'Gemini API key not configured' });
    }
    
    // Call Gemini API from backend
    const response = await axios.post(
        `https://generativelanguage.googleapis.com/v1/models/${model}:generateContent`,
        { contents: [{ parts: [{ text: prompt }] }] },
        { 
            params: { key: apiKey },
            headers: { 'Content-Type': 'application/json' }
        }
    );
    
    res.json(response.data);
  }
);
```

**Time:** 2.5 hours  
**Impact:** Security vulnerabilities fixed, can deploy safely

---

### PHASE 2: STABILITY FIXES (2 Hours) - 8 Agents

#### Agents 17-20: DB Connection Management

**Agent 17-18: Add Connection Pool Config**
```python
# File: services/ml-service/src/main.py
# ADD CONNECTION POOL CONFIG

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# BEFORE (no pool config):
# engine = create_engine(DATABASE_URL)

# AFTER (with pool):
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,              # Max 10 connections
    max_overflow=20,           # Allow 20 extra connections
    pool_pre_ping=True,        # Verify connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False
)
```

**Agent 19-20: Add try-finally to DB Connections**
```python
# File: services/ml-service/src/hubspot_attribution.py
# FIX LINES 139-184

# BEFORE (leaks):
# session = get_db_session()
# result = session.query(...)
# # No close!

# AFTER (fixed):
def get_attribution_data(deal_id: str) -> Dict:
    session = None
    try:
        session = get_db_session()
        result = session.query(...).filter(...).first()
        return result.to_dict() if result else {}
    finally:
        if session:
            session.close()  # Always close

# OR use context manager:
from contextlib import contextmanager

@contextmanager
def db_session():
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Usage:
with db_session() as session:
    result = session.query(...).first()
```

#### Agents 1-4 (Round 2): HTTP Timeouts & Retry Logic

**Agent 1-2: Add Timeouts to All HTTP Calls**
```python
# File: services/ml-service/src/main.py
# ADD TIMEOUTS TO ALL AXIOS/REQUESTS CALLS

import httpx  # Use httpx instead of requests (better async support)

# Create client with default timeout
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,    # 10s to connect
        read=30.0,      # 30s to read
        write=10.0,     # 10s to write
        pool=5.0        # 5s to get connection from pool
    ),
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)

# Use in all calls:
response = await http_client.post(
    f"{META_PUBLISHER_URL}/publish",
    json=data,
    timeout=30.0  # Explicit timeout
)
```

**Agent 3-4: Add Retry Logic**
```python
# File: services/ml-service/src/utils/retry.py
# CREATE RETRY DECORATOR

import asyncio
from functools import wraps
from typing import Type, Tuple

def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Retry decorator for async functions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
            
            raise last_exception
        return wrapper
    return decorator

# Usage:
@async_retry(max_attempts=3, delay=1.0, backoff=2.0)
async def call_meta_api(data):
    response = await http_client.post(META_URL, json=data)
    return response.json()
```

**Time:** 2 hours  
**Impact:** Services stable, won't crash from connection leaks

---

### PHASE 3: DATA INTEGRITY (1.5 Hours) - 6 Agents

#### Agents 5-10: Bounded Caches

**Agent 5-6: Fix Unbounded Cache (ensemble.py:72)**
```python
# File: services/ml-service/src/ensemble.py
# FIX LINE 72

from functools import lru_cache
from collections import OrderedDict

class LRUCache:
    """Bounded LRU cache with size limit"""
    def __init__(self, maxsize: int = 100):
        self.cache = OrderedDict()
        self.maxsize = maxsize
    
    def get(self, key: str):
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: any):
        if key in self.cache:
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.maxsize:
            # Remove least recently used
            self.cache.popitem(last=False)
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()

# Replace unbounded dict:
# _cache = {}  # ❌ Unbounded

# With bounded cache:
_cache = LRUCache(maxsize=100)  # ✅ Bounded
```

**Agent 7-8: Fix Other Unbounded Caches**
```python
# Apply same pattern to:
# - manager.py:296
# - preview_generator.py:242
# - cross_learner.py:172
# - vertex_ai.py:130

# Use LRUCache or Python's @lru_cache decorator:
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(input_data):
    # Cached, max 100 entries
    pass
```

**Agent 9-10: Fix Race Conditions**
```python
# File: services/ml-service/src/websocket.py
# FIX LINES 40-59

import asyncio
from threading import Lock

# Add locks for shared state
_active_connections_lock = asyncio.Lock()
_active_connections = {}

async def add_connection(connection_id: str, socket):
    async with _active_connections_lock:
        _active_connections[connection_id] = socket

async def remove_connection(connection_id: str):
    async with _active_connections_lock:
        _active_connections.pop(connection_id, None)

async def broadcast(message: dict):
    async with _active_connections_lock:
        connections = list(_active_connections.values())
    
    # Send outside lock to avoid deadlock
    for socket in connections:
        try:
            await socket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send to {socket}: {e}")
```

**Time:** 1.5 hours  
**Impact:** No memory leaks, no race conditions

---

### PHASE 4: PRODUCTION POLISH (4 Hours) - 10 Agents

#### Agents 11-15: API Versioning

**Agent 11-12: Add API Versioning**
```typescript
// File: services/gateway-api/src/index.ts
// ADD VERSIONING TO ALL ENDPOINTS

// BEFORE:
// app.post('/api/score/storyboard', ...)

// AFTER:
const API_VERSION = process.env.API_VERSION || 'v1';

// Version middleware
app.use(`/api/${API_VERSION}`, (req, res, next) => {
    req.apiVersion = API_VERSION;
    next();
});

// All endpoints:
app.post(`/api/${API_VERSION}/score/storyboard`, ...)
app.post(`/api/${API_VERSION}/predict/ctr`, ...)
// etc.

// Legacy support (redirect to v1):
app.use('/api/score/storyboard', (req, res) => {
    res.redirect(`/api/v1/score/storyboard`);
});
```

**Agent 13-15: Standardize Error Responses**
```typescript
// File: services/gateway-api/src/utils/errors.ts
// CREATE STANDARD ERROR FORMAT

export interface ApiError {
    error: {
        code: string;
        message: string;
        details?: any;
        timestamp: string;
        request_id?: string;
    };
}

export function createErrorResponse(
    code: string,
    message: string,
    details?: any,
    statusCode: number = 400
): { status: number; body: ApiError } {
    return {
        status: statusCode,
        body: {
            error: {
                code,
                message,
                details,
                timestamp: new Date().toISOString(),
                request_id: crypto.randomUUID()
            }
        }
    };
}

// Use everywhere:
app.post('/api/v1/score/storyboard', async (req, res) => {
    try {
        // ... logic ...
    } catch (error) {
        const errorResponse = createErrorResponse(
            'VALIDATION_ERROR',
            'Invalid storyboard data',
            { field: 'scenes', issue: 'missing' },
            400
        );
        return res.status(errorResponse.status).json(errorResponse.body);
    }
});
```

#### Agents 16-20: Documentation & Circuit Breakers

**Agent 16-17: Document Endpoints**
```typescript
// File: services/gateway-api/src/index.ts
// ADD OPENAPI/SWAGGER DOCS

import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

const swaggerOptions = {
    definition: {
        openapi: '3.0.0',
        info: {
            title: 'GeminiVideo API',
            version: '1.0.0',
        },
        servers: [
            { url: 'http://localhost:8000', description: 'Development' },
            { url: 'https://api.geminivideo.com', description: 'Production' },
        ],
    },
    apis: ['./src/**/*.ts'],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Add JSDoc comments to endpoints:
/**
 * @swagger
 * /api/v1/score/storyboard:
 *   post:
 *     summary: Score a video storyboard
 *     tags: [Scoring]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               scenes:
 *                 type: array
 *     responses:
 *       200:
 *         description: Scoring results
 */
app.post('/api/v1/score/storyboard', ...)
```

**Agent 18-20: Add Circuit Breakers**
```python
# File: services/ml-service/src/utils/circuit_breaker.py
# CREATE CIRCUIT BREAKER

from enum import Enum
import time
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            # Success - reset if half-open
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            raise

# Usage:
meta_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60.0
)

try:
    result = meta_circuit_breaker.call(
        lambda: meta_api.publish_ad(ad_data)
    )
except Exception as e:
    logger.error(f"Circuit breaker opened: {e}")
    # Fallback logic
```

**Time:** 4 hours  
**Impact:** Production-ready API, resilient to failures

---

### PHASE 5: TESTING & VALIDATION (2 Hours) - 10 Agents

#### Agents 1-10: Integration Tests

**Create test files for each fix:**

```python
# File: tests/test_security.py
def test_path_traversal_protection():
    # Test competitor_tracker.py
    with pytest.raises(ValueError):
        safe_save_file("../../../etc/passwd", b"data")

def test_sql_injection_protection():
    # Test analytics endpoint
    response = client.get("/api/analytics/campaigns?name='; DROP TABLE--")
    assert response.status_code == 400

def test_webhook_signature():
    # Test HubSpot webhook
    signature = compute_signature(secret, timestamp, body)
    response = client.post(
        "/api/webhook/hubspot",
        json=body,
        headers={"X-HubSpot-Signature-v3": signature}
    )
    assert response.status_code == 200
```

**Time:** 2 hours  
**Impact:** All fixes verified, confidence in deployment

---

## PART 3: REALISTIC TIMELINE WITH 20 AGENTS

### Optimized Schedule (Dependency-Aware)

```
Hour 0-1:   PHASE 0 - Foundation (Build fixes)
            Agents 1-4: Build blockers
            ✅ Services can start

Hour 1-3.5: PHASE 1 - Security (Critical vulnerabilities)
            Agents 5-16: Security fixes
            ✅ Can deploy safely

Hour 3.5-5.5: PHASE 2 - Stability (Crash prevention)
            Agents 17-20, 1-4: Stability fixes
            ✅ Won't crash

Hour 5.5-7: PHASE 3 - Data Integrity (Memory leaks)
            Agents 5-10: Cache bounds, race conditions
            ✅ No memory leaks

Hour 7-11:  PHASE 4 - Production Polish
            Agents 11-20: Versioning, docs, circuit breakers
            ✅ Production-ready

Hour 11-13: PHASE 5 - Testing
            Agents 1-10: Integration tests
            ✅ Verified & validated

TOTAL: 13 hours (realistic with dependencies)
```

### Parallelization Strategy

**Can Run in Parallel:**
- Security fixes (Agents 5-16) - No dependencies
- Cache fixes (Agents 5-10) - Independent files
- Documentation (Agents 16-17) - No dependencies

**Must Run Sequentially:**
- Build fixes → Everything else
- DB connection fixes → Before other DB work
- API versioning → Before documentation

---

## PART 4: CONFIGURATION VS HARDCODING

### Right Approach for Each Issue

#### ✅ Use Configuration (YAML):
- Winner thresholds (CTR, ROAS)
- Learning cycle intervals
- Rate limits
- Timeout values
- Feature flags

#### ✅ Use Environment Variables:
- API keys
- Database passwords
- Service URLs
- Secrets

#### ✅ Use Constants (Code):
- Embedding dimensions (after standardization)
- HTTP status codes
- File size limits
- Connection pool sizes

#### ❌ Never Hardcode:
- Passwords
- API keys
- User-specific thresholds
- Business logic values

---

## PART 5: PRIORITY MATRIX

### Must Fix Before Deployment (45 Critical)

| Priority | Issue | Time | Agent | Blocks |
|----------|-------|------|-------|--------|
| P0 | Build failures | 1h | 1-4 | Everything |
| P0 | Path traversal | 0.5h | 5-7 | Security |
| P0 | SQL injection | 0.5h | 8 | Security |
| P0 | Webhook signatures | 1h | 9-10 | Data integrity |
| P0 | Hardcoded passwords | 0.5h | 13-14 | Security |
| P1 | WebSocket auth | 1h | 11-12 | Security |
| P1 | DB connection leaks | 1h | 17-20 | Stability |
| P1 | Missing timeouts | 1h | 1-4 | Stability |

### Can Fix After Deployment (112 Issues)

- API versioning
- Documentation
- Error format standardization
- Circuit breakers (nice to have)

---

## PART 6: FINAL RECOMMENDATION

### Right Way: 3-Phase Approach

**Phase 1: Blockers Only (6 hours)**
- Fix build failures
- Fix security vulnerabilities
- Fix stability crashes
- **Result:** Can deploy safely

**Phase 2: Critical Fixes (4 hours)**
- Fix memory leaks
- Fix data integrity
- Add monitoring
- **Result:** Production-stable

**Phase 3: Polish (3 hours)**
- API versioning
- Documentation
- Circuit breakers
- **Result:** Production-excellent

**Total: 13 hours with 20 agents**

### Alternative: Conservative (20 hours)

If you want to be extra safe:
- More testing time
- Staged rollouts
- Additional validation
- **Total: 20 hours**

---

## CONCLUSION

### Recommended Approach:

1. **Fix blockers first** (6 hours) → Deploy
2. **Fix critical issues** (4 hours) → Stabilize
3. **Polish** (3 hours) → Excel

### Configuration Strategy:

- ✅ **Use config files** for business logic thresholds
- ✅ **Use env vars** for secrets and URLs
- ✅ **Use constants** for technical limits
- ❌ **Never hardcode** passwords or API keys

**Total Time: 13-20 hours with 20 parallel agents**

---

**Document Generated:** 2025-12-09  
**Status:** Ready for execution  
**Priority:** Fix blockers first, then iterate

