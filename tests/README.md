# Comprehensive Test Suite

**Agent 29 of 30** - Production-grade testing infrastructure with 80%+ coverage target.

## Overview

This test suite provides comprehensive coverage across all layers of the GeminiVideo application:

- **Unit Tests**: Individual component testing (TypeScript & Python)
- **Integration Tests**: API endpoint and service integration testing
- **E2E Tests**: Full user journey testing with Playwright
- **Load Tests**: Performance and scalability testing with Locust

## Test Structure

```
tests/
├── unit/                          # Unit tests
│   ├── test_meta_integration.ts   # Meta Marketing API (500+ lines)
│   └── test_ml_models.py          # ML models & ROAS predictor (500+ lines)
├── integration/                   # Integration tests
│   └── test_api_endpoints.ts      # Gateway API endpoints (400+ lines)
├── e2e/                          # End-to-end tests
│   └── test_campaign_flow.spec.ts # Campaign creation flow (300+ lines)
├── load/                         # Load & performance tests
│   └── test_performance.py        # API & ML performance (200+ lines)
├── fixtures/                     # Test data & mocks
│   ├── meta-mock-data.ts
│   └── ml-mock-data.py
├── mocks/                        # Mock implementations
│   └── facebook-sdk.mock.ts
└── helpers/                      # Test utilities
    ├── test-helpers.ts
    └── test-helpers.py
```

## Running Tests

### All Tests

```bash
# Run all tests
npm test

# With coverage report
npm run test:coverage
```

### Unit Tests

```bash
# TypeScript unit tests
npm test -- tests/unit/test_meta_integration.ts

# Python unit tests
pytest tests/unit/test_ml_models.py -v
```

### Integration Tests

```bash
# Requires running services (API, database, Redis)
npm test -- tests/integration/test_api_endpoints.ts
```

### E2E Tests

```bash
# Run with Playwright
npx playwright test

# Run specific browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug
```

### Load Tests

```bash
# Performance benchmarks
pytest tests/load/test_performance.py -v -s

# Run Locust for interactive load testing
locust -f tests/load/test_performance.py --host http://localhost:8000
```

## Test Configuration

### Jest (TypeScript)
- **Config**: `jest.config.js`
- **Coverage threshold**: 80%
- **Timeout**: 30 seconds

### Pytest (Python)
- **Config**: `pytest.ini`
- **Coverage threshold**: 80%
- **Markers**: unit, integration, e2e, load, slow, ml, meta

### Playwright (E2E)
- **Config**: `playwright.config.ts`
- **Browsers**: Chromium, Firefox, WebKit
- **Timeout**: 60 seconds

## Coverage Requirements

The test suite targets **80%+ coverage** across:

✅ **Meta Marketing API** (test_meta_integration.ts)
- Campaign creation & management
- AdSet configuration & targeting
- Video upload & ad creative
- Insights & analytics
- CAPI events & Pixel tracking

✅ **ML Models** (test_ml_models.py)
- ROAS predictor training/inference
- Feature engineering
- Model persistence & loading
- SHAP explainability
- Confidence intervals
- Self-learning & drift detection

✅ **API Endpoints** (test_api_endpoints.ts)
- Authentication & authorization
- Rate limiting
- Input validation & sanitization
- Error handling
- CORS & security headers
- Database operations

✅ **Campaign Flow** (test_campaign_flow.spec.ts)
- User authentication
- Campaign creation wizard
- Creative studio operations
- Ad publishing workflow
- Analytics dashboard
- Settings & integrations

✅ **Performance** (test_performance.py)
- API endpoint latency (< 100ms P95)
- ML inference speed (< 100ms)
- Concurrent request handling
- Database query performance
- Sustained load testing

## CI/CD Integration

Tests run automatically via GitHub Actions (`.github/workflows/tests.yml`):

- ✅ On every push to main/develop
- ✅ On every pull request
- ✅ Daily scheduled runs
- ✅ Parallel execution for speed
- ✅ Coverage reports to Codecov

### Workflow Jobs

1. **unit-tests-ts**: TypeScript unit tests
2. **unit-tests-python**: Python unit tests
3. **integration-tests**: API integration tests
4. **e2e-tests**: Playwright E2E tests
5. **load-tests**: Performance & load tests
6. **code-quality**: Linting & type checking
7. **coverage-report**: Combined coverage reporting

## Environment Variables

### Test Environment

```bash
# TypeScript Tests
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/test_db
TEST_REDIS_URL=redis://localhost:6379
TEST_API_URL=http://localhost:8000
TEST_API_KEY=test_api_key_12345

# Python Tests
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/test_db

# E2E Tests
E2E_BASE_URL=http://localhost:3000
E2E_API_URL=http://localhost:8000
```

## Development

### Adding New Tests

1. **Unit tests**: Add to `tests/unit/`
2. **Integration tests**: Add to `tests/integration/`
3. **E2E tests**: Add to `tests/e2e/`
4. **Load tests**: Add to `tests/load/`

### Test Utilities

Use helpers from:
- `tests/helpers/test-helpers.ts` (TypeScript)
- `tests/helpers/test-helpers.py` (Python)

### Mock Data

Use fixtures from:
- `tests/fixtures/meta-mock-data.ts`
- `tests/fixtures/ml-mock-data.py`
- `tests/mocks/facebook-sdk.mock.ts`

## Best Practices

1. **Isolation**: Each test should be independent
2. **Setup/Teardown**: Use beforeEach/afterEach for cleanup
3. **Mocking**: Mock external services (Meta API, etc.)
4. **Assertions**: Clear, descriptive assertions
5. **Performance**: Keep tests fast (< 30s per test)
6. **Coverage**: Aim for 80%+ line coverage
7. **Documentation**: Comment complex test logic

## Troubleshooting

### Tests Failing Locally

1. Ensure services are running:
   ```bash
   # Start database
   docker-compose up postgres redis

   # Start API
   cd services/gateway-api && npm start
   ```

2. Check environment variables are set

3. Clear test cache:
   ```bash
   jest --clearCache
   pytest --cache-clear
   ```

### Slow Tests

1. Run specific test file instead of all
2. Use `--maxWorkers=1` for debugging
3. Check for network timeouts
4. Profile with `--durations=10` (pytest)

### Coverage Not Meeting Threshold

1. Check which files lack coverage:
   ```bash
   npm run test:coverage
   open coverage/index.html
   ```

2. Add tests for uncovered code paths
3. Review `coverageThresholds` in jest.config.js

## Resources

- [Jest Documentation](https://jestjs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Locust Documentation](https://docs.locust.io/)

## License

Part of GeminiVideo - Agent 29 of 30
