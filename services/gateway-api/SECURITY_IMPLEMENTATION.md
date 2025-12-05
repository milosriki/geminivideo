# Security Implementation Guide - Agent 98

## Overview

This document outlines the comprehensive security measures implemented in the Gateway API to protect against common vulnerabilities and ensure production-grade security.

## Table of Contents

1. [Security Layers](#security-layers)
2. [Input Validation](#input-validation)
3. [Authentication & Authorization](#authentication--authorization)
4. [Rate Limiting](#rate-limiting)
5. [Security Headers](#security-headers)
6. [CORS Configuration](#cors-configuration)
7. [SQL Injection Prevention](#sql-injection-prevention)
8. [XSS Prevention](#xss-prevention)
9. [Password Security](#password-security)
10. [API Key Management](#api-key-management)
11. [Audit Logging](#audit-logging)
12. [Environment Variables](#environment-variables)
13. [Security Checklist](#security-checklist)

---

## Security Layers

The Gateway API implements multiple layers of security (defense in depth):

```
┌─────────────────────────────────────────┐
│  1. Security Headers (Helmet)           │
├─────────────────────────────────────────┤
│  2. CORS Validation                     │
├─────────────────────────────────────────┤
│  3. Rate Limiting                       │
├─────────────────────────────────────────┤
│  4. SQL Injection Protection            │
├─────────────────────────────────────────┤
│  5. XSS Protection                      │
├─────────────────────────────────────────┤
│  6. Input Validation (Zod)              │
├─────────────────────────────────────────┤
│  7. Authentication (Firebase JWT)       │
├─────────────────────────────────────────┤
│  8. Authorization (RBAC)                │
├─────────────────────────────────────────┤
│  9. Audit Logging                       │
└─────────────────────────────────────────┘
```

---

## Input Validation

### Zod Schema Validation

All endpoints use Zod for type-safe input validation:

```typescript
import { validateBody, createCampaignSchema } from './middleware/validation-schemas';

router.post('/campaigns',
  validateBody(createCampaignSchema),
  async (req, res) => {
    // req.body is now validated and type-safe
  }
);
```

### Available Validation Schemas

- **Campaign**: `createCampaignSchema`, `updateCampaignSchema`, `queryCampaignsSchema`
- **Ads**: `createAdSchema`, `approveAdSchema`
- **A/B Tests**: `createABTestSchema`, `updateABTestSchema`
- **Publishing**: `publishMetaSchema`, `publishMultiPlatformSchema`
- **Google Ads**: `createGoogleCampaignSchema`, `createGoogleVideoAdSchema`
- **Images**: `generateImageSchema`
- **Analytics**: `analyticsQuerySchema`
- **Auth**: `registerUserSchema`, `loginUserSchema`, `updatePasswordSchema`

### Legacy Validation (Being Phased Out)

The custom validation middleware is still available:

```typescript
import { validateInput } from './middleware/security';

router.post('/example',
  validateInput({
    body: {
      name: { type: 'string', required: true, min: 1, max: 255, sanitize: true },
      age: { type: 'number', required: true, min: 0, max: 150 }
    }
  }),
  handler
);
```

---

## Authentication & Authorization

### Firebase Authentication

JWT-based authentication using Firebase Admin SDK:

```typescript
import { authenticateUser, requireRole, UserRole } from './middleware/auth';

// Require authentication
router.get('/protected',
  authenticateUser,
  handler
);

// Require specific role
router.post('/admin-only',
  authenticateUser,
  requireRole(UserRole.ADMIN),
  handler
);

// Multiple roles
router.post('/editors-and-admins',
  authenticateUser,
  requireRole(UserRole.ADMIN, UserRole.EDITOR),
  handler
);

// Optional authentication
router.get('/public-or-private',
  optionalAuth,
  handler
);
```

### Role-Based Access Control (RBAC)

Three user roles:
- **ADMIN**: Full access to all resources
- **EDITOR**: Can create and edit content
- **VIEWER**: Read-only access

### Password Security

Using bcrypt for password hashing:

```typescript
import { hashPassword, verifyPassword, validatePasswordStrength } from './utils/password';

// Hash password
const hashedPassword = await hashPassword('userPassword123');

// Verify password
const isValid = await verifyPassword('userPassword123', hashedPassword);

// Validate strength
const validation = validatePasswordStrength('userPassword123');
if (!validation.valid) {
  console.error(validation.error);
}
```

**Password Requirements:**
- Minimum 8 characters
- Maximum 128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Optional: special characters

**Bcrypt Configuration:**
- Salt rounds: 12 (configurable via `BCRYPT_SALT_ROUNDS`)
- Automatic rehashing when salt rounds increase
- Timing-safe comparison

---

## Rate Limiting

### Global Rate Limiting

Applied to all endpoints:

```typescript
app.use(globalRateLimiter); // 100 requests per 15 minutes
```

### Endpoint-Specific Rate Limiters

```typescript
import {
  authRateLimiter,     // 5 requests per 15 minutes
  apiRateLimiter,      // 60 requests per minute
  uploadRateLimiter    // 10 requests per hour
} from './middleware/security';

// Auth endpoints (strict)
router.post('/login', authRateLimiter, handler);

// Standard API endpoints
router.get('/campaigns', apiRateLimiter, handler);

// Upload/heavy operations
router.post('/upload', uploadRateLimiter, handler);
```

### Custom Rate Limiters

```typescript
import { createRateLimiter } from './middleware/security';

const customLimiter = createRateLimiter({
  windowMs: 60 * 1000,        // 1 minute
  maxRequests: 30,             // 30 requests
  skipSuccessfulRequests: false,
  skipFailedRequests: false
});

router.post('/custom', customLimiter, handler);
```

### Distributed Rate Limiting

Uses Redis for distributed systems (automatic fallback to in-memory if Redis unavailable).

---

## Security Headers

### Helmet Configuration

Comprehensive security headers via Helmet:

```typescript
import { securityHeaders } from './middleware/security';

app.use(securityHeaders);
```

**Headers Applied:**
- **Content-Security-Policy**: Prevents XSS attacks
- **Strict-Transport-Security**: Enforces HTTPS (HSTS)
- **X-Frame-Options**: Prevents clickjacking
- **X-Content-Type-Options**: Prevents MIME sniffing
- **X-DNS-Prefetch-Control**: Controls DNS prefetching
- **Referrer-Policy**: Controls referrer information
- **X-Permitted-Cross-Domain-Policies**: Restricts cross-domain policies

### Custom Headers

Environment variables for customization:

```bash
HSTS_MAX_AGE=31536000
CSP_DEFAULT_SRC='self'
CSP_SCRIPT_SRC='self','unsafe-inline'
CSP_STYLE_SRC='self','unsafe-inline'
```

---

## CORS Configuration

### Secure CORS Setup

```typescript
import { corsConfig } from './middleware/security';
import cors from 'cors';

app.use(cors(corsConfig));
```

### Configuration

```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com,https://app.yourdomain.com
```

**Features:**
- Whitelist-based origin validation
- Credentials support
- Preflight caching (24 hours)
- Security event logging for blocked origins

---

## SQL Injection Prevention

### Parameterized Queries

**Always use parameterized queries:**

```typescript
// ✅ CORRECT - Parameterized query
const result = await pgPool.query(
  'SELECT * FROM users WHERE email = $1',
  [email]
);

// ❌ WRONG - String concatenation (vulnerable!)
const result = await pgPool.query(
  `SELECT * FROM users WHERE email = '${email}'`
);
```

### Automatic SQL Injection Detection

Middleware scans all inputs:

```typescript
import { sqlInjectionProtection } from './middleware/security';

app.use(sqlInjectionProtection);
```

**Detects:**
- UNION SELECT attacks
- DROP TABLE commands
- DELETE FROM statements
- Malicious SQL comments
- Stacked queries

---

## XSS Prevention

### Automatic HTML Sanitization

```typescript
import { xssProtection, sanitizeHTML } from './middleware/security';

// Applied globally
app.use(xssProtection);

// Manual sanitization
const safe = sanitizeHTML(userInput);
```

**Escapes:**
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&#x27;`
- `/` → `&#x2F;`
- `&` → `&amp;`

### Content Security Policy

CSP headers prevent inline script execution and restrict resource loading.

---

## API Key Management

### API Key Validation

```typescript
import { validateApiKey } from './middleware/security';

// Require valid API key
router.post('/internal-api',
  validateApiKey,
  handler
);
```

### Configuration

```bash
# .env
API_KEYS=hashed-key-1,hashed-key-2,hashed-key-3
```

**Features:**
- SHA-256 hashing
- Format validation (alphanumeric, 32+ chars)
- Secure key generation
- Request attribution

### Generating API Keys

```bash
# Generate secure API key
openssl rand -hex 32
```

---

## Audit Logging

### Automatic Request Logging

```typescript
import { auditLog } from './middleware/security';

app.use(auditLog);
```

**Logged Information:**
- Timestamp
- HTTP method and URL
- IP address
- User agent
- Response status code
- Request duration
- User ID (if authenticated)
- API key (masked)

### Security Event Logging

Automatic logging for:
- Failed login attempts
- Invalid API keys
- Rate limit violations
- SQL injection attempts
- XSS attempts
- CORS violations
- Unauthorized access attempts

**Example:**

```
🛡️ Security Event: {
  "type": "RATE_LIMIT_EXCEEDED",
  "timestamp": "2025-12-05T10:30:00Z",
  "ip": "192.168.1.100",
  "url": "/api/campaigns",
  "userAgent": "Mozilla/5.0...",
  "details": { "attempts": 101, "limit": 100 }
}
```

---

## Environment Variables

### Critical Security Variables

**Must be changed in production:**

```bash
# JWT & Sessions
JWT_SECRET=CHANGE_ME_your-super-secret-jwt-key-minimum-32-characters-long
SESSION_SECRET=CHANGE_ME_your-session-secret-minimum-32-characters-long

# API Keys
API_KEYS=CHANGE_ME_your-api-key-here
GEMINI_API_KEY=CHANGE_ME_your-gemini-api-key

# Platform Secrets
META_APP_SECRET=CHANGE_ME_your-meta-app-secret
META_ACCESS_TOKEN=CHANGE_ME_your-meta-access-token
GOOGLE_ADS_CLIENT_SECRET=CHANGE_ME_your-client-secret
TIKTOK_APP_SECRET=CHANGE_ME_your-tiktok-app-secret

# Webhook Secrets
META_WEBHOOK_SECRET=CHANGE_ME_your-meta-webhook-secret
GOOGLE_WEBHOOK_SECRET=CHANGE_ME_your-google-webhook-secret

# Encryption
ENCRYPTION_KEY=CHANGE_ME_your-encryption-key-32-bytes-base64-encoded
```

### Generating Secure Secrets

```bash
# JWT Secret (64 bytes, base64)
openssl rand -base64 64

# API Key (32 bytes, hex)
openssl rand -hex 32

# Encryption Key (32 bytes, base64)
openssl rand -base64 32
```

### .gitignore Verification

Ensure all `.env` files are in `.gitignore`:

```gitignore
# Environment files
.env
.env.local
.env.production
.env.development
.env.staging
*.env
```

**Never commit:**
- `.env` files
- Service account JSON files
- Private keys
- API credentials

---

## Security Checklist

### Pre-Production Checklist

- [ ] All `CHANGE_ME_` values replaced in `.env`
- [ ] `JWT_SECRET` is 32+ characters and randomly generated
- [ ] `BCRYPT_SALT_ROUNDS` is set to 12
- [ ] `ALLOWED_ORIGINS` only includes production domains
- [ ] Database uses strong password and SSL
- [ ] Redis uses authentication
- [ ] All API keys are from production accounts
- [ ] Webhook secrets are configured
- [ ] `NODE_ENV=production`
- [ ] Rate limiting is properly configured
- [ ] HTTPS is enforced (HSTS)
- [ ] Error messages don't leak sensitive info
- [ ] Logging is configured (Sentry, CloudWatch, etc.)
- [ ] Security headers are enabled
- [ ] CORS is properly restricted
- [ ] SQL parameterized queries everywhere
- [ ] File upload limits are set
- [ ] No hardcoded secrets in code

### Monitoring Checklist

- [ ] Security event logging enabled
- [ ] Rate limit alerts configured
- [ ] Failed auth attempt monitoring
- [ ] SQL injection attempt alerts
- [ ] Unusual traffic pattern detection
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring
- [ ] Performance monitoring

### Code Review Checklist

- [ ] All endpoints use rate limiting
- [ ] All endpoints use input validation
- [ ] Authentication required where appropriate
- [ ] Authorization checks for protected resources
- [ ] No string concatenation in SQL queries
- [ ] User input is sanitized
- [ ] Errors don't expose stack traces
- [ ] Secrets not in code
- [ ] Dependencies are up to date
- [ ] No vulnerable dependencies (npm audit)

---

## Testing Security

### Manual Security Tests

```bash
# Test rate limiting
for i in {1..150}; do curl http://localhost:8000/api/campaigns; done

# Test SQL injection
curl -X POST http://localhost:8000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "Test'; DROP TABLE campaigns;--"}'

# Test XSS
curl -X POST http://localhost:8000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "<script>alert('XSS')</script>"}'

# Test CORS
curl -H "Origin: http://malicious-site.com" \
  http://localhost:8000/api/campaigns

# Test invalid authentication
curl -H "Authorization: Bearer invalid-token" \
  http://localhost:8000/api/protected
```

### Automated Security Scanning

```bash
# NPM audit
npm audit

# Fix vulnerabilities
npm audit fix

# Dependency check
npm outdated

# Security scanning with Snyk
npx snyk test
```

---

## Common Vulnerabilities Prevented

| Vulnerability | Prevention Method | Status |
|--------------|-------------------|--------|
| SQL Injection | Parameterized queries + Detection middleware | ✅ Protected |
| XSS | HTML sanitization + CSP headers | ✅ Protected |
| CSRF | SameSite cookies + CORS | ✅ Protected |
| Clickjacking | X-Frame-Options header | ✅ Protected |
| MIME Sniffing | X-Content-Type-Options | ✅ Protected |
| Man-in-the-Middle | HSTS + HTTPS enforcement | ✅ Protected |
| Brute Force | Rate limiting + Exponential backoff | ✅ Protected |
| Session Hijacking | Secure cookies + Token rotation | ✅ Protected |
| Weak Passwords | bcrypt + Password validation | ✅ Protected |
| Insecure Direct Object References | Authorization checks | ✅ Protected |
| Security Misconfiguration | Helmet + Environment validation | ✅ Protected |
| Sensitive Data Exposure | Encryption + Audit logging | ✅ Protected |

---

## Support & Resources

### Internal Documentation

- [Security Middleware README](./src/middleware/SECURITY_README.md)
- [Validation Schemas](./src/middleware/validation-schemas.ts)
- [Password Utilities](./src/utils/password.ts)
- [Firebase Auth Service](./src/services/firebase-auth.ts)

### External Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [Firebase Security Rules](https://firebase.google.com/docs/rules)
- [bcrypt Documentation](https://github.com/kelektiv/node.bcrypt.js)
- [Zod Documentation](https://zod.dev/)
- [Helmet Documentation](https://helmetjs.github.io/)

---

## Version History

- **v1.0.0** (2025-12-05) - Initial comprehensive security implementation by Agent 98
  - Zod validation schemas
  - bcrypt password hashing
  - Enhanced CORS configuration
  - Comprehensive .env.example
  - Security documentation

---

**Agent 98: SECURITY + VALIDATION FIX EXECUTOR**
*Production-grade security for investor-ready infrastructure*
