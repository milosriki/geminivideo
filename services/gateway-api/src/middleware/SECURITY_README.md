# Security Middleware Documentation

**Agent 5 - Comprehensive Security Implementation**
Following OWASP Top 10 Best Practices

## Overview

This security middleware provides comprehensive protection for the Gateway API, implementing industry-standard security practices including:

- ✅ Rate Limiting (Distributed & In-Memory)
- ✅ Security Headers (Helmet)
- ✅ Input Validation & Sanitization
- ✅ SQL Injection Prevention
- ✅ XSS Protection
- ✅ CORS Configuration
- ✅ API Key Validation
- ✅ Audit Logging
- ✅ Brute Force Protection

## Security Layers

### 1. Security Headers (Helmet)

Comprehensive HTTP security headers following OWASP recommendations:

```typescript
- Content-Security-Policy: Prevents XSS attacks
- Strict-Transport-Security: Enforces HTTPS (1 year)
- X-Frame-Options: Prevents clickjacking (DENY)
- X-Content-Type-Options: Prevents MIME sniffing
- Referrer-Policy: Controls referrer information
- X-DNS-Prefetch-Control: Controls DNS prefetching
```

### 2. Rate Limiting

Multi-tier rate limiting strategy:

**Global Rate Limiter:**
- 100 requests per 15 minutes per user/IP
- Returns `429 Too Many Requests` when exceeded
- Standard rate limit headers included

**Auth Rate Limiter:**
- 5 requests per 15 minutes
- Protects authentication endpoints
- Skips successful requests from count

**API Rate Limiter:**
- 60 requests per minute
- Applied to API endpoints

**Upload Rate Limiter:**
- 10 requests per hour
- Protects resource-intensive operations

**Key Generation Priority:**
1. User ID (if authenticated)
2. API Key (if provided)
3. IP Address (fallback)

### 3. Input Validation

Type-safe validation with sanitization:

```typescript
validateInput({
  body: {
    email: { type: 'email', required: true },
    name: { type: 'string', min: 1, max: 100, sanitize: true },
    age: { type: 'number', min: 18, max: 120 },
    role: { type: 'string', enum: ['user', 'admin'] }
  }
})
```

**Supported Types:**
- `string`, `number`, `boolean`
- `email`, `uuid`, `url`
- `object`, `array`

**Validation Rules:**
- `required`: Field must be present
- `min/max`: Length/value constraints
- `pattern`: Regex validation
- `enum`: Allowed values
- `sanitize`: HTML sanitization

### 4. SQL Injection Prevention

Automatic SQL injection detection and prevention:

- Removes SQL comments (`--`, `/* */`)
- Detects dangerous patterns:
  - `UNION SELECT`
  - `DROP TABLE`
  - `DELETE FROM`
  - `INSERT INTO`
  - `UPDATE SET`
  - `EXEC/EXECUTE`
- Throws error on suspicious input
- Recursively sanitizes objects

### 5. XSS Protection

HTML sanitization to prevent cross-site scripting:

- Encodes: `& < > " ' /`
- Applied to all string inputs
- Recursive object sanitization
- Preserves data integrity

### 6. CORS Configuration

Secure cross-origin resource sharing:

```typescript
Allowed Origins: Process.env.ALLOWED_ORIGINS
Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Headers: Content-Type, Authorization, X-API-Key, X-Request-ID
Credentials: Enabled
Max Age: 24 hours
```

### 7. API Key Validation

Secure API key authentication:

- Format validation: Alphanumeric, 32+ characters
- SHA-256 hashing for secure storage
- Environment variable based validation
- Attached to request object for downstream use

### 8. Audit Logging

Comprehensive request logging:

```json
{
  "timestamp": "2025-12-01T10:30:00Z",
  "method": "POST",
  "url": "/api/analyze",
  "ip": "192.168.1.1",
  "userAgent": "Mozilla/5.0...",
  "statusCode": 200,
  "duration": 145,
  "userId": "user-123",
  "apiKey": "***"
}
```

- All requests logged
- Error requests highlighted (4xx, 5xx)
- Duration tracking
- User/API key tracking (sanitized)

### 9. Brute Force Protection

Exponential backoff for failed attempts:

- Free retries: 5 (configurable)
- Min wait: 1 second
- Max wait: 60 seconds
- Lifetime: 1 hour
- Exponential backoff: 2^(attempts - freeRetries)

**Response Example:**
```json
{
  "error": "Too Many Attempts",
  "message": "Please wait 8 seconds before trying again",
  "retryAfter": 8
}
```

## Environment Variables

Required configuration:

```bash
# Redis for distributed rate limiting
REDIS_URL=redis://localhost:6379

# CORS allowed origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,https://geminivideo.app

# API Keys (comma-separated, hashed recommended)
API_KEYS=key1_hashed,key2_hashed
```

## Usage Examples

### Endpoint-Specific Protection

```typescript
// High-security endpoint
app.post('/api/auth/login',
  authRateLimiter,           // Strict rate limit
  bruteForceProtection(),     // Exponential backoff
  validateInput({             // Input validation
    body: {
      email: { type: 'email', required: true },
      password: { type: 'string', required: true, min: 8 }
    }
  }),
  async (req, res) => {
    // Handler logic
  }
);

// Resource-intensive endpoint
app.post('/api/upload',
  uploadRateLimiter,          // Upload-specific limit
  validateApiKey,              // Require API key
  validateInput({
    body: {
      file: { type: 'string', required: true }
    }
  }),
  async (req, res) => {
    // Handler logic
  }
);
```

### Custom Rate Limiter

```typescript
const customLimiter = createRateLimiter({
  windowMs: 60000,           // 1 minute
  maxRequests: 10,            // 10 requests
  keyGenerator: (req) => {
    return `custom:${req.userId}`;
  },
  skipSuccessfulRequests: true
});

app.post('/api/special', customLimiter, handler);
```

## Security Event Logging

All security events are logged with type classification:

- `RATE_LIMIT_EXCEEDED`
- `VALIDATION_FAILED`
- `SQL_INJECTION_ATTEMPT`
- `XSS_PROTECTION_ERROR`
- `CORS_BLOCKED`
- `MISSING_API_KEY`
- `INVALID_API_KEY`
- `BRUTE_FORCE_DETECTED`

Events include timestamp, IP, URL, user agent, and details.

## Production Recommendations

### 1. Redis Backend
Deploy Redis for distributed rate limiting across multiple instances:
```typescript
await initializeSecurityRedis();
```

### 2. SIEM Integration
Replace console logging with SIEM:
```typescript
function logSecurityEvent(type, req, details) {
  sendToSIEM({ type, timestamp, ip, url, details });
}
```

### 3. Database API Keys
Store hashed API keys in database instead of env vars:
```typescript
const validKey = await pgPool.query(
  'SELECT * FROM api_keys WHERE key_hash = $1',
  [hashedKey]
);
```

### 4. SSL/TLS
Always use HTTPS in production for HSTS to work properly.

### 5. Monitoring
Set up alerts for:
- High rate of 429 responses
- SQL injection attempts
- Brute force attacks
- CORS violations

## Testing

```bash
# Install dependencies
npm install

# Run tests
npm test

# Test rate limiting
for i in {1..101}; do
  curl http://localhost:8000/api/analyze -X POST
done

# Test validation
curl http://localhost:8000/api/analyze \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Test SQL injection protection
curl http://localhost:8000/api/search/clips \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "test; DROP TABLE users--"}'
```

## OWASP Top 10 Coverage

- ✅ A01:2021 - Broken Access Control (API Keys, Rate Limiting)
- ✅ A02:2021 - Cryptographic Failures (HTTPS, Hashing)
- ✅ A03:2021 - Injection (SQL Injection Prevention, Input Validation)
- ✅ A04:2021 - Insecure Design (Defense in Depth)
- ✅ A05:2021 - Security Misconfiguration (Helmet Headers)
- ✅ A06:2021 - Vulnerable Components (Updated Dependencies)
- ✅ A07:2021 - Authentication Failures (Brute Force Protection)
- ✅ A08:2021 - Software and Data Integrity (Input Validation)
- ✅ A09:2021 - Security Logging Failures (Audit Logging)
- ✅ A10:2021 - Server-Side Request Forgery (URL Validation)

## Support

For security issues, contact: security@geminivideo.app
For general questions, see main documentation.

---

**Agent 5 Implementation Complete** ✅
Production-grade security following OWASP best practices.
