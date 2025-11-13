# Copilot Instructions for geminivideo

This document provides context and guidelines for GitHub Copilot when working on this repository.

## Project Overview

**geminivideo** is an AI Ad Intelligence & Creation Suite - a complete end-to-end platform for AI-powered video ad creation, optimization, and publishing. The system uses:
- **Video Intelligence**: Scene detection, feature extraction, FAISS indexing for similarity search
- **AI Scoring**: Psychology-based scoring (curiosity, urgency, social proof), hook strength analysis, novelty detection
- **Video Creation**: Storyboard builder, automated rendering with ffmpeg, compliance checking
- **Publishing & Analytics**: Meta (Facebook/Instagram) ad publishing, performance tracking, prediction logging
- **Continuous Learning**: Nightly calibration, pattern mining from successful ads

## Architecture

This is a **microservices architecture** deployed on Google Cloud Platform (GCP):

### Services
1. **gateway-api** (Node.js/Express + TypeScript) - Port 8080
   - API gateway and knowledge router
   - Coordinates between all services
   - Manages shared configuration and knowledge base

2. **drive-intel** (Python/FastAPI) - Port 8081
   - Video intelligence service
   - Ingests from local folders or Google Drive
   - Scene detection, feature extraction, FAISS indexing

3. **video-agent** (Python/FastAPI) - Port 8082
   - Video rendering service
   - Background job queue for ffmpeg rendering
   - Compliance checking

4. **meta-publisher** (Node.js/Express) - Port 8083
   - Meta Marketing API integration
   - Publishes ads to Facebook/Instagram
   - Tracks performance metrics and insights

5. **frontend** (React/Vite) - Port 5173
   - User interface for the platform
   - Storyboard builder and video creation tools

### Shared Resources
- `shared/config/` - YAML configuration files for hooks, drivers, personas, weights, scene ranking
- `knowledge/` - Knowledge base for AI scoring and recommendations
- `scripts/` - Automation scripts for nightly learning and pattern mining
- `tests/` - Integration and unit tests

## Technology Stack

### Backend Services
- **Node.js Services**: Express, TypeScript, Google Cloud Storage SDK
  - Build: `npm run build` (TypeScript compilation)
  - Dev: `npm run dev` (ts-node)
  - Test: `npm test` (Jest)

- **Python Services**: FastAPI, Uvicorn, PyTorch/CV libraries
  - Dev: `python -m uvicorn src.main:app --reload --port <PORT>`
  - Test: `pytest` (from tests/ directory)
  - Dependencies: opencv, scenedetect, faiss, pytesseract, pyyaml

### Frontend
- React + Vite
- Dev: `npm run dev`
- Build: `npm run build`

### Infrastructure
- **Docker Compose**: Available for local development (`docker-compose up --build`)
- **GCP Deployment**: Cloud Run, Artifact Registry, Cloud Storage, Secret Manager
- **CI/CD**: GitHub Actions (`.github/workflows/deploy-cloud-run.yml`, `codeql.yml`)

## Development Guidelines

### Code Style

#### TypeScript/JavaScript
- Use TypeScript for type safety
- Follow Express.js patterns for route handlers
- Use async/await for asynchronous operations
- Export types and interfaces for shared models
- Prefer functional programming patterns

#### Python
- Follow PEP 8 style guidelines
- Use FastAPI for async API endpoints with proper type hints
- Use Pydantic models for request/response validation
- Organize code: separate routes, models, services, and utilities
- Use async/await for I/O operations

#### General
- Keep functions small and focused
- Add docstrings/JSDoc for public APIs
- Use meaningful variable names
- Avoid hardcoding values - use configuration files

### Testing

#### Unit Tests
- Python services: Use `pytest` with fixtures
- Node.js services: Use `jest` with mocks
- Test individual functions and components
- Mock external dependencies (GCS, Meta API)

#### Integration Tests
- Located in `tests/` directory
- Test cross-service interactions
- Run with: `cd tests && pytest test_integration.py`
- Ensure all services are running before integration tests

#### Test Patterns
- Always test happy paths and error cases
- Use meaningful test names: `test_<function>_<scenario>_<expected_result>`
- Clean up test data after tests complete
- Mock time-dependent operations for consistency

### Build and Validation

#### Before Committing
1. **TypeScript services**: Run `npm run build` to check for compilation errors
2. **Python services**: Check with `python -m py_compile <file>` or run the service locally
3. **All changes**: Run existing tests: `npm test` or `pytest`
4. **Integration**: If modifying APIs, test with integration tests

#### Local Development
- Use `docker-compose up --build` for full stack testing
- Individual services can run standalone for faster iteration
- Check logs for errors: `docker-compose logs <service>`

#### CI/CD
- All PRs trigger GitHub Actions workflows
- CodeQL security scanning runs automatically
- Cloud Run deployment happens on merge to `main`

### Documentation

#### When to Update Documentation
- **README.md**: Feature additions, setup changes, new services
- **Service READMEs**: API changes, new endpoints, configuration updates
- **DEPLOYMENT.md**: Infrastructure changes, new GCP resources
- **This file**: Development process changes, new patterns

#### Documentation Style
- Use clear, concise language
- Include code examples for complex features
- Update quickstart guides if setup changes
- Document environment variables and their purpose

## Working with This Repository

### Project Structure
```
geminivideo/
├── .github/
│   ├── workflows/          # CI/CD pipelines
│   └── copilot-instructions.md  # This file
├── services/
│   ├── gateway-api/        # TypeScript API gateway
│   ├── drive-intel/        # Python video intelligence
│   ├── video-agent/        # Python rendering service
│   ├── meta-publisher/     # Node.js Meta API integration
│   └── frontend/           # React UI
├── shared/config/          # YAML configurations
├── knowledge/              # Knowledge base
├── scripts/                # Automation scripts
├── tests/                  # Integration tests
└── DEPLOYMENT.md           # GCP deployment guide
```

### Configuration Management
- **YAML files** in `shared/config/` control AI behavior:
  - `weights.yaml` - Scoring weights for different metrics
  - `scene_ranking.yaml` - Scene ranking parameters
  - `hooks/`, `drivers/`, `personas/` - AI personalities and strategies

- **Environment Variables**:
  - `PROJECT_ID` - GCP project ID
  - `GCS_BUCKET` - Cloud Storage bucket name
  - `GCS_MOCK_MODE` - Enable mock mode for local dev (true/false)
  - `GATEWAY_URL` - Gateway API URL for service communication
  - `META_ACCESS_TOKEN` - Meta Marketing API token (use Secret Manager)
  - `PORT` - Service port (defaults per service)

### Common Development Tasks

#### Adding a New API Endpoint
1. Add route in appropriate service (`gateway-api`, `drive-intel`, etc.)
2. Define request/response models (TypeScript interface or Pydantic model)
3. Implement handler with proper error handling
4. Add unit tests for the endpoint
5. Update service README with endpoint documentation
6. Test integration with other services if applicable

#### Modifying AI Scoring
1. Update YAML configuration in `shared/config/`
2. If changing scoring logic, modify in `gateway-api` knowledge router
3. Add tests to verify new scoring behavior
4. Update `knowledge/README.md` with changes
5. Run integration tests to ensure end-to-end flow works

#### Adding a New Service
1. Create directory under `services/<service-name>`
2. Add appropriate `package.json` or `requirements.txt`
3. Create `README.md` explaining service purpose and API
4. Add service to `docker-compose.yml` (if exists)
5. Update gateway routing to include new service
6. Add deployment configuration in `.github/workflows/`
7. Update main README.md architecture diagram

### Debugging Tips
- **Service Logs**: Check individual service output for errors
- **Gateway Logs**: Gateway coordinates services - check for routing issues
- **Network Issues**: Verify `GATEWAY_URL` and service ports
- **GCS Issues**: Enable `GCS_MOCK_MODE=true` for local development
- **Video Processing**: Check ffmpeg logs in video-agent service
- **Meta API**: Verify `META_ACCESS_TOKEN` and API permissions

## Security Considerations

### Critical Security Rules
- **Never commit secrets**: Use environment variables and GCP Secret Manager
- **API Tokens**: Store Meta access tokens, GCP credentials in Secret Manager
- **Input Validation**: Always validate user input in API endpoints
- **File Uploads**: Sanitize filenames, check file types, limit file sizes
- **Dependencies**: Regularly update dependencies for security patches
- **Secrets in Logs**: Never log sensitive data (tokens, passwords, PII)

### Best Practices
- Use `.env.example` files to document required environment variables
- Never include actual `.env` files in commits (use `.gitignore`)
- Review dependencies for known vulnerabilities before adding
- Use HTTPS for all external API calls
- Implement rate limiting on public endpoints
- Follow principle of least privilege for GCP IAM roles

## Best Practices for Copilot

### When Making Changes
1. **Understand context**: Read related code and documentation first
2. **Minimal changes**: Make smallest possible change to achieve goal
3. **Test incrementally**: Test after each change, not at the end
4. **Follow patterns**: Match existing code style and architecture
5. **Update docs**: Keep documentation in sync with code changes

### Task Scoping
- **Good tasks**: Bug fixes, new endpoints, test additions, documentation updates
- **Complex tasks**: Refactors, architectural changes, multi-service features - break into smaller tasks
- **Avoid**: Removing working code, changing unrelated code, adding unnecessary dependencies

### Service-Specific Guidelines

#### gateway-api (TypeScript)
- Use Express middleware for cross-cutting concerns (logging, auth)
- Keep routes simple - delegate to service functions
- Use async/await for Google Cloud Storage operations
- Type all request/response objects

#### drive-intel & video-agent (Python)
- Use FastAPI dependency injection for shared resources
- Define Pydantic models for all API contracts
- Use async functions for I/O operations
- Handle video processing errors gracefully (corrupted files, unsupported formats)

#### meta-publisher (Node.js)
- Handle Meta API rate limits with exponential backoff
- Validate ad creative requirements before publishing
- Log all API interactions for debugging
- Cache insights data to reduce API calls

#### frontend (React)
- Use React hooks for state management
- Keep components small and focused
- Use TypeScript for props and state
- Handle loading and error states in UI

### Common Pitfalls to Avoid
- Don't break existing API contracts without updating all consumers
- Don't add dependencies without checking existing solutions
- Don't remove error handling to simplify code
- Don't skip testing video processing edge cases
- Don't forget to update environment variable documentation
- Don't hardcode configuration that belongs in YAML files

## Deployment

### Local Development
- Use `docker-compose up` for full stack
- Or run services individually for faster iteration
- Mock external services (GCS, Meta API) for local testing

### Staging/Production
- Deployed to GCP Cloud Run via GitHub Actions
- Triggered automatically on push to `main` branch
- Manual deployment: `gcloud run deploy <service> --image=<image-url>`
- See `DEPLOYMENT.md` for complete instructions

### Environment-Specific Configuration
- Use different GCS buckets for dev/staging/prod
- Separate Meta API ad accounts per environment
- Use GCP Secret Manager for production credentials
- Set appropriate resource limits in Cloud Run

## Additional Resources
- [Main README](../README.md) - Project overview and quickstart
- [Deployment Guide](../DEPLOYMENT.md) - GCP deployment details
- [Knowledge Base](../knowledge/README.md) - AI knowledge system
- Service READMEs - Individual service documentation

## Getting Help
- Check existing issues for similar problems
- Review service logs for error details
- Consult service-specific README files
- Ask for clarification on unclear requirements
- Test changes thoroughly before requesting review
