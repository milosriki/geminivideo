---
description: How to verify TypeScript code compiles and passes type-checking in this project
---

# TypeScript Verification Workflow

## Environment Setup

Node.js is installed at `/usr/local/bin/node` (v24.12.0) but is NOT in the default shell PATH.
Always use absolute paths for `node` and `npx`.

```
NODE=/usr/local/bin/node
NPX=/usr/local/bin/npx
```

## TypeScript Services in This Project

| Service | Directory | Has tsconfig.json | Build Script |
|---------|-----------|-------------------|--------------|
| `gateway-api` | `services/gateway-api` | ✅ | `npm run build` (runs `tsc`) |
| `meta-publisher` | `services/meta-publisher` | ✅ | Check `package.json` |

## Step 1: Install Dependencies (if needed)

If `node_modules/` is missing or stale:

// turbo
```bash
cd services/gateway-api && /usr/local/bin/npx --yes npm install
```

## Step 2: Type-Check Without Emitting

This is the core verification step. It runs the TypeScript compiler in check-only mode.

// turbo
```bash
cd services/gateway-api && PATH="/usr/local/bin:$PATH" npx tsc --noEmit 2>&1 | head -50
```

**Expected output for a clean build:**
```
(no output, exit code 0)
```

**If errors exist**, count them:
// turbo
```bash
cd services/gateway-api && PATH="/usr/local/bin:$PATH" npx tsc --noEmit 2>&1 | grep -c 'error TS'
```

## Step 3: Fix Common Issues

### Missing `@types/node`
```
Cannot find name 'process'. Do you need to install type definitions for node?
```
**Fix:**
```bash
cd services/gateway-api && PATH="/usr/local/bin:$PATH" npm install --save-dev @types/node
```

### Missing module type declarations
```
Cannot find module 'express' or its corresponding type declarations.
```
**Fix:**
```bash
cd services/gateway-api && PATH="/usr/local/bin:$PATH" npm install --save-dev @types/express @types/cors
```

### tsconfig.json must include `"types": ["node"]`
Verify with:
// turbo
```bash
cat services/gateway-api/tsconfig.json | grep -A2 '"types"'
```

## Step 4: Full Build Verification

Only after type-check passes:
```bash
cd services/gateway-api && PATH="/usr/local/bin:$PATH" npm run build
```

## Step 5: Docker Build (Integration)

For full integration verification:
```bash
docker build -t gateway-api-test services/gateway-api/
```

## Known Issues

- **`gateway-api/src/index.ts`**: Has ~30+ lint errors for missing type declarations (`express`, `cors`, `fs`, `path`, `js-yaml`, `redis`, `pg`, `uuid`). These are pre-existing and require `npm install` + `@types/*` packages.
- The `tsconfig.json` already has `"types": ["node"]` and `"skipLibCheck": true`, but `node_modules` may need a fresh install.
