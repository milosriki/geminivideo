# Winner Flow Integration Tests

Comprehensive integration tests for the Winner Detection and Replication System (Agent 09).

## Test Files

- **`test_winner_flow.ts`** - TypeScript/Jest integration tests
- **`test_winner_flow.py`** - Python/pytest integration tests

## Test Coverage

### 1. Winner Detection Tests
- ✅ Detect winners with ROAS > 2x threshold
- ✅ Exclude low-performing ads
- ✅ List all detected winners with pagination
- ✅ Get winner details by ID
- ✅ Filter by multiple criteria (ROAS, CTR, spend, revenue)
- ✅ Respect lookback window parameters

### 2. Winner Replication Tests
- ✅ Replicate winners with variations
- ✅ Create audience variations (lookalike, interest expansion, age range)
- ✅ Create hook variations (question, urgency, benefit)
- ✅ Create budget variations (multipliers)
- ✅ Limit replica count

### 3. Budget Optimization Tests
- ✅ Calculate budget changes for account
- ✅ Apply safety limits (min/max budget, max change %)
- ✅ Prioritize winners for budget increases
- ✅ Reduce budget for losers
- ✅ Respect total budget cap
- ✅ Provide reasoning for changes

### 4. Full Workflow Tests
- ✅ Run complete winner workflow (detect → replicate → optimize)
- ✅ Execute sequential steps
- ✅ Support dry-run mode
- ✅ Track execution time

### 5. Insights Extraction Tests
- ✅ Extract insights from winners
- ✅ Identify top-performing hook patterns
- ✅ Provide actionable recommendations
- ✅ Analyze creative elements

### 6. Scheduled Jobs Tests
- ✅ Trigger winner detection job manually
- ✅ Check job status
- ✅ List scheduled jobs
- ✅ Get job execution history

### 7. Agent Trigger Tests
- ✅ Trigger auto-promotion agent
- ✅ Trigger budget optimization agent
- ✅ Trigger winner replication agent
- ✅ Check agent health status

### 8. Edge Cases & Error Handling
- ✅ Handle no winners found gracefully
- ✅ Validate winner ID format
- ✅ Handle concurrent requests
- ✅ Rate limiting
- ✅ Database connection failures

## Running Tests

### TypeScript Tests (Jest)

```bash
# Run all winner flow tests
npm test -- test_winner_flow.ts

# Run with coverage
npm test -- --coverage test_winner_flow.ts

# Run specific test suite
npm test -- test_winner_flow.ts -t "Winner Detection"

# Run in watch mode
npm test -- --watch test_winner_flow.ts
```

### Python Tests (pytest)

```bash
# Run all winner flow tests
pytest tests/integration/test_winner_flow.py -v

# Run with coverage
pytest tests/integration/test_winner_flow.py --cov=services --cov-report=html

# Run specific test class
pytest tests/integration/test_winner_flow.py::TestWinnerDetection -v

# Run specific test
pytest tests/integration/test_winner_flow.py::TestWinnerDetection::test_detect_winners_with_roas_threshold -v

# Run in parallel
pytest tests/integration/test_winner_flow.py -n auto
```

### Run All Integration Tests

```bash
# TypeScript
npm test tests/integration/

# Python
pytest tests/integration/ -v
```

## Environment Variables

Configure these environment variables for testing:

```bash
# API URLs
export TEST_API_URL="http://localhost:8000"
export TEST_ML_SERVICE_URL="http://localhost:8004"

# Database
export TEST_DATABASE_URL="postgresql://test:test@localhost:5432/test_db"
export TEST_REDIS_URL="redis://localhost:6379"

# Test data
export TEST_AD_ACCOUNT_ID="test_account_123"
export TEST_API_KEY="test_api_key_12345"
```

## Test Data Setup

The tests automatically create and clean up test data:

1. **Test Ads** - 5 ads with varying performance metrics:
   - `test_ad_winner_1` - ROAS: 3.5, CTR: 0.045
   - `test_ad_winner_2` - ROAS: 4.2, CTR: 0.052
   - `test_ad_loser_1` - ROAS: 1.2, CTR: 0.015
   - `test_ad_loser_2` - ROAS: 0.8, CTR: 0.008
   - `test_ad_marginal_1` - ROAS: 1.8, CTR: 0.025

2. **Cleanup** - All test data is automatically cleaned up after tests complete

## CI/CD Integration

### GitHub Actions

```yaml
name: Winner Flow Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          npm install
          pip install -r requirements.txt

      - name: Run TypeScript tests
        run: npm test -- test_winner_flow.ts
        env:
          TEST_API_URL: http://localhost:8000
          TEST_DATABASE_URL: postgresql://test:test@localhost:5432/test_db

      - name: Run Python tests
        run: pytest tests/integration/test_winner_flow.py -v
        env:
          TEST_API_URL: http://localhost:8000
          TEST_DATABASE_URL: postgresql://test:test@localhost:5432/test_db
```

## Expected Test Results

### Success Criteria

- ✅ All winner detection tests pass
- ✅ All replication tests create valid replicas
- ✅ Budget optimization respects safety limits
- ✅ Full workflow completes in < 60 seconds
- ✅ Agent triggers respond successfully
- ✅ Edge cases handled gracefully
- ✅ No memory leaks or connection issues

### Performance Benchmarks

- Winner detection: < 10 seconds
- Winner replication: < 5 seconds per winner
- Budget optimization: < 15 seconds
- Full workflow: < 60 seconds
- Insights extraction: < 3 seconds (cached)

## Troubleshooting

### Common Issues

**Issue: Services not available**
```bash
# Check services are running
curl http://localhost:8000/health
curl http://localhost:8004/health

# Start services if needed
docker-compose up -d
```

**Issue: Database connection failed**
```bash
# Verify database is accessible
psql postgresql://test:test@localhost:5432/test_db

# Check migrations are applied
npm run migrate
```

**Issue: Redis connection failed**
```bash
# Check Redis is running
redis-cli ping

# Start Redis if needed
docker run -d -p 6379:6379 redis:7
```

**Issue: Tests timeout**
```bash
# Increase timeout in jest.config.js or pytest.ini
# Jest: testTimeout: 60000
# Pytest: timeout = 60
```

## Contributing

When adding new winner flow features:

1. Add corresponding tests to both TypeScript and Python versions
2. Update this README with new test coverage
3. Ensure all tests pass before submitting PR
4. Add integration test for the complete flow

## Related Documentation

- [Auto Promotion System](/services/ml-service/src/auto_promoter.py)
- [Budget Optimization](/tests/stress/test_budget_optimization_flow.py)
- [Winner Index](/tests/integration/test_winner_index.py)
- [API Documentation](/API_ENDPOINTS_REFERENCE.md)
