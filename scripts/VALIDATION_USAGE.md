# Final Validation Script - Usage Guide

## Quick Start

```bash
# Run validation from project root
python3 scripts/final_validation.py

# Run with output saved to file
python3 scripts/final_validation.py > validation_results.txt 2>&1

# Run and check exit code
python3 scripts/final_validation.py
echo $?  # 0 = success, 1 = failure
```

## What It Validates

### 1. Python Syntax (197 files)
Validates all `.py` files in:
- services/ml-service/src/
- services/video-agent/pro/
- services/titan-core/
- services/drive-intel/services/

### 2. Critical Components (8 components)
Checks that all mission-critical classes exist:
- MotionMomentSDK
- FaceWeightedAnalyzer
- HookOptimizer
- CTAOptimizer
- VariationGenerator
- BudgetOptimizer
- LoserKillSwitch
- CrossCampaignLearner

### 3. Configuration Files
Verifies presence of:
- docker-compose.yml
- .dockerignore
- .env.example
- Required environment variables

### 4. Database Migrations
Checks all SQL migration files:
- 001_creative_assets.sql
- 002_schema_consolidation.sql
- 003_performance_indexes.sql
- 004_schema_validation.sql

### 5. Test Coverage
Validates test files in:
- tests/integration/
- tests/e2e/
- tests/unit/

### 6. Docker Configurations
Checks Dockerfiles for all services:
- gateway-api
- ml-service
- video-agent
- titan-core

### 7. API Routes
Validates TypeScript route files:
- campaigns.ts
- analytics.ts
- ab-tests.ts
- creatives.ts

## Output Format

```
============================================================
GEMINIVIDEO PRODUCTION VALIDATION
============================================================

=== PYTHON SYNTAX VALIDATION ===
  ✓ file1.py
  ✓ file2.py
  ✗ file3.py: Syntax error on line 42

=== CRITICAL COMPONENT VALIDATION ===
  ✓ Motion Moment SDK (MotionMomentSDK)
  ⚠ Hook Optimizer: Module file not found

... (continues for all sections)

============================================================
VALIDATION SUMMARY
============================================================

  Passed:   245
  Failed:   2
  Warnings: 5
  Success:  99.2%

✅ VALIDATION PASSED - System is production-ready
```

## Exit Codes

- **0**: Success rate >= 80%, production ready
- **1**: Success rate < 80%, issues must be resolved

## Success Criteria

| Status | Condition | Action Required |
|--------|-----------|----------------|
| VALIDATION PASSED | 0 failures | System is production-ready |
| VALIDATION WARNING | 1-4 failures | Review needed before deploy |
| VALIDATION FAILED | 5+ failures | Critical issues must be fixed |

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Production Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run validation
        run: python3 scripts/final_validation.py
```

### Pre-deployment Check

```bash
#!/bin/bash
# Add to deployment pipeline

echo "Running pre-deployment validation..."
python3 scripts/final_validation.py

if [ $? -ne 0 ]; then
    echo "VALIDATION FAILED - Deployment aborted"
    exit 1
fi

echo "VALIDATION PASSED - Proceeding with deployment"
# ... continue deployment
```

## Customization

Edit `/home/user/geminivideo/scripts/final_validation.py` to:

1. **Add new directories to validate**:
```python
python_dirs = [
    ROOT / "services" / "new-service" / "src",  # Add here
]
```

2. **Add new critical components**:
```python
components = [
    ("New Component", "path.to.module", "ClassName"),  # Add here
]
```

3. **Adjust success threshold**:
```python
if summary['success_rate'] < 80:  # Change threshold here
    sys.exit(1)
```

## Troubleshooting

### Common Issues

1. **Module not found warnings**
   - Check file path is correct
   - Ensure file exists in expected location

2. **Syntax errors**
   - Review the specific file mentioned
   - Run `python -m py_compile <file>` for details

3. **Missing configuration files**
   - Verify files exist in root directory
   - Check .dockerignore patterns

## Best Practices

1. **Run before every commit**:
   ```bash
   git add .
   python3 scripts/final_validation.py && git commit -m "message"
   ```

2. **Add to pre-commit hook**:
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash
   python3 scripts/final_validation.py || exit 1
   ```

3. **Include in code reviews**:
   - Attach validation report to PRs
   - Require 100% pass rate for merges

4. **Monitor in production**:
   - Run validation after deployments
   - Schedule periodic health checks

## Related Files

- **Validation Script**: `/home/user/geminivideo/scripts/final_validation.py`
- **Latest Report**: `/home/user/geminivideo/VALIDATION_REPORT.txt`
- **Summary Document**: `/home/user/geminivideo/AGENTS_122-127_VALIDATION_COMPLETE.md`

---

**Last Updated**: 2025-12-06
**Version**: 1.0
**Agents**: 122-127 (Final Validation Suite)
