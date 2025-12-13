# Testing Guide - Quick Reference

## Running Tests

### All Tests
```bash
npm test
```

### Specific Test File
```bash
npm test -- credits-endpoint.test.ts
```

### Watch Mode
```bash
npm test -- --watch
```

### Coverage Report
```bash
npm test -- --coverage
```

## Test Files

- credits-endpoint.test.ts (911 lines, ~65 tests)
- knowledge.test.ts (777 lines, ~55 tests)  
- index-initialization.test.ts (596 lines, ~50 tests)
- env-configuration.test.ts (458 lines, ~45 tests)

## Best Practices

1. Test Naming: Use descriptive "should" statements
2. Independence: Tests should not depend on each other
3. Cleanup: Always clean up in afterEach
4. Mocking: Mock external dependencies
5. Coverage: Aim for >90% coverage

## Resources

- Jest Docs: https://jestjs.io/docs/getting-started
- Project test examples in src/tests/