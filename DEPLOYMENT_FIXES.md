# Deployment Fixes Summary

## Date: November 13, 2025

This document summarizes the critical deployment issues that were identified and fixed in this PR.

## Issues Identified

### 1. Docker BuildKit npm Compatibility Issue
**Problem:** Docker BuildKit has a known bug with npm that causes "Exit handler never called" errors during `npm install`, preventing successful package installation in Docker builds.

**Impact:** All Node.js services (gateway-api, meta-publisher) failed to build in CI/CD pipelines.

**Solution:** 
- Added `DOCKER_BUILDKIT=0` environment variable to all GitHub Actions workflows
- Updated local deployment scripts to use legacy Docker builder
- Updated documentation to reflect this requirement

**References:**
- GitHub Issue: https://github.com/npm/cli/issues/4028
- Affects: Node.js services in Docker

### 2. Inconsistent Docker Build Contexts
**Problem:** Dockerfiles were inconsistently configured - some expected to be built from repository root with paths like `COPY services/gateway-api/...`, while others expected to be built from their service directory.

**Impact:** Docker builds would fail or build with wrong context depending on where they were invoked.

**Solution:**
- Standardized all Dockerfiles to build from their service directory
- Updated all `COPY` commands to use relative paths from service root
- Updated GitHub Actions workflows to consistently use `./services/<service-name>` as build context
- Updated docker-compose.yml to use service directories as build context

**Affected Services:**
- gateway-api
- drive-intel
- video-agent
- meta-publisher

### 3. Duplicate Frontend Directories
**Problem:** Two frontend directories existed: `/frontend` and `/services/frontend`, causing confusion and inconsistency in deployment workflows.

**Impact:** Deployment workflows had conditional logic to detect which frontend to use, making deployments unpredictable.

**Solution:**
- Removed `/services/frontend` directory completely
- Kept `/frontend` as the canonical frontend location
- Updated all references in workflows and docker-compose.yml

### 4. Outdated Node.js Base Images
**Problem:** Node.js services were using `node:18-slim` which has compatibility issues with Docker and npm.

**Solution:**
- Updated all Node.js Dockerfiles to use `node:20-alpine`
- Alpine images are smaller and more stable
- Node 20 is LTS with better Docker compatibility

**Affected Services:**
- gateway-api
- meta-publisher

### 5. Missing TypeScript Type Declarations
**Problem:** The `facebook-nodejs-business-sdk` package doesn't include TypeScript type definitions, causing build failures in meta-publisher service.

**Impact:** TypeScript compilation failed with errors about missing type declarations.

**Solution:**
- Created custom type declaration file: `facebook-nodejs-business-sdk.d.ts`
- Used loose typing with index signatures to allow flexible method calls
- Maintained type safety while accommodating SDK's dynamic API

### 6. Docker Compose Command Inconsistencies
**Problem:** Mix of `docker-compose` (v1) and `docker compose` (v2) commands in documentation and scripts.

**Solution:**
- Updated all scripts to use `docker compose` (v2 command)
- v2 is the current standard and comes bundled with Docker

## Files Modified

### Dockerfiles
- `services/gateway-api/Dockerfile` - Fixed build context, updated Node version
- `services/drive-intel/Dockerfile` - Fixed build context
- `services/video-agent/Dockerfile` - Fixed build context  
- `services/meta-publisher/Dockerfile` - Fixed build context, updated Node version
- `services/ml-service/Dockerfile` - Already correct, no changes needed
- `frontend/Dockerfile` - Already correct, no changes needed

### GitHub Actions Workflows
- `.github/workflows/deploy.yml` - Added DOCKER_BUILDKIT=0, fixed build contexts
- `.github/workflows/deploy-cloud-run.yml` - Added DOCKER_BUILDKIT=0, fixed build contexts

### Scripts and Documentation
- `deploy-local.sh` - Added DOCKER_BUILDKIT=0, updated docker-compose commands
- `README.md` - Added DOCKER_BUILDKIT=0 to manual deployment instructions
- `DEPLOYMENT.md` - Added DOCKER_BUILDKIT=0 to manual build instructions

### New Files
- `services/meta-publisher/src/facebook/facebook-nodejs-business-sdk.d.ts` - TypeScript type declarations

### Removed
- `services/frontend/*` - Entire duplicate frontend directory removed

## Testing Results

All services now build successfully:

✅ **gateway-api** - Node.js/TypeScript service  
✅ **drive-intel** - Python/FastAPI service  
✅ **video-agent** - Python/FastAPI service  
✅ **ml-service** - Python/FastAPI service  
✅ **meta-publisher** - Node.js/TypeScript service  
✅ **frontend** - React/Vite application  
✅ **drive-worker** - Python worker service  
✅ **video-worker** - Python worker service  

## Security Scan Results

CodeQL security scan completed with **0 alerts** - no security vulnerabilities introduced.

## Local Testing

Full Docker Compose build tested and verified:
```bash
DOCKER_BUILDKIT=0 docker compose build
```

All 8 services built successfully without errors.

## Deployment Impact

### Local Development
Developers must now use `DOCKER_BUILDKIT=0` when building locally:
```bash
DOCKER_BUILDKIT=0 docker compose up -d --build
```

### CI/CD Pipelines
GitHub Actions workflows now automatically use legacy builder - no manual intervention needed.

### Cloud Deployment
No changes to Cloud Run configuration needed. Services will continue to run as before.

## Known Limitations

1. **Docker BuildKit Disabled**: The project cannot use Docker BuildKit features until the npm compatibility issue is resolved upstream.
   
2. **Type Safety**: meta-publisher uses loose typing for facebook SDK. This trades type safety for build compatibility.

3. **Build Speed**: Legacy Docker builder is slightly slower than BuildKit but provides reliable builds.

## Future Improvements

1. Monitor for resolution of npm/BuildKit issue and re-enable BuildKit when fixed
2. Consider contributing proper TypeScript types for facebook-nodejs-business-sdk upstream
3. Evaluate multi-stage builds to reduce final image sizes

## Verification Checklist

- [x] All Dockerfiles standardized to build from service directories
- [x] Duplicate frontend directory removed
- [x] DOCKER_BUILDKIT=0 added to all workflows
- [x] All Node.js services use node:20-alpine
- [x] TypeScript type declarations added for facebook SDK
- [x] All 8 services build successfully
- [x] Security scan passes with 0 alerts
- [x] Documentation updated with new requirements
- [x] Local docker-compose build tested and verified

## Rollback Plan

If issues arise, revert commits in reverse order:
1. Revert type declaration addition
2. Revert documentation updates
3. Revert DOCKER_BUILDKIT changes
4. Revert Dockerfile standardization
5. Restore services/frontend directory if needed

However, rolling back is NOT recommended as these fixes address critical deployment blockers.

---

**Status**: ✅ All deployment issues resolved and tested
**Branch**: copilot/fix-deployment-issues
**Ready for**: Merge to main
