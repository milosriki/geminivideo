# Copilot Coding Agent Instructions

## Project Overview

This repository is for the **geminivideo** project, which appears to be focused on video processing or video-related functionality, potentially leveraging Google's Gemini AI capabilities.

The project is in its early stages, and these instructions will guide development as the codebase grows.

## Coding Standards

### General Principles
- Write clean, readable, and maintainable code
- Follow the DRY (Don't Repeat Yourself) principle
- Use meaningful variable and function names
- Add comments only when necessary to explain "why", not "what"
- Keep functions small and focused on a single responsibility

### Language-Specific Guidelines

#### Python (if applicable)
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Prefer Python 3.10+ features
- Use `async/await` for I/O-bound operations
- Format code with `black` and lint with `pylint` or `ruff`

#### JavaScript/TypeScript (if applicable)
- Use ES6+ syntax
- Prefer `const` over `let`, avoid `var`
- Use TypeScript with strict mode enabled
- Follow Airbnb JavaScript style guide
- Use `async/await` over promises chains
- Format code with Prettier

#### Other Languages
- Follow the official style guide for the language
- Use modern language features and idioms
- Ensure code is well-documented

## Project Structure

As the project grows, maintain a clear directory structure:
```
/
├── .github/              # GitHub configuration and workflows
├── src/                  # Source code
├── tests/                # Test files
├── docs/                 # Documentation
├── config/               # Configuration files
└── README.md             # Project documentation
```

## Build & Test

### Testing Requirements
- All new features must include unit tests
- Aim for at least 80% code coverage
- Tests should be clear, isolated, and deterministic
- Place tests in a `tests/` directory or alongside source files with `_test` or `.test` suffix

### Test Commands (to be established)
- Run tests with appropriate command for the chosen framework
- Examples: `pytest`, `npm test`, `go test`, `cargo test`

### Build Process
- Document build steps in the README
- Use standard build tools for the language/framework
- Ensure builds are reproducible

## Validation Steps

Before submitting a pull request:
1. Run all tests and ensure they pass
2. Run linters and fix any issues
3. Verify code formatting is consistent
4. Update documentation if necessary
5. Test the changes manually if applicable
6. Check for security vulnerabilities

## Security Guidelines

- Never commit secrets, API keys, or credentials
- Use environment variables for sensitive configuration
- Validate and sanitize all user inputs
- Keep dependencies up to date
- Review dependency security advisories
- Follow OWASP security best practices

## Documentation Requirements

- Update README.md when adding new features
- Document all public APIs and functions
- Include usage examples where appropriate
- Keep documentation in sync with code changes
- Document any setup or configuration requirements

## Git Workflow

### Commits
- Write clear, descriptive commit messages
- Use conventional commit format: `type(scope): description`
  - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
  - Example: `feat(video): add video processing pipeline`

### Pull Requests
- Keep PRs focused and small
- Reference related issues in PR description
- Ensure all CI checks pass
- Request reviews from appropriate team members

## Dependency Management

- Prefer well-maintained, popular libraries
- Check licenses before adding dependencies
- Keep dependencies minimal
- Regular update dependencies for security patches
- Document why each major dependency is needed

## Performance Considerations

- Profile code before optimizing
- Consider memory usage for large video files
- Use streaming for large data processing
- Implement caching where appropriate
- Document any performance trade-offs

## Accessibility & User Experience

- Design with accessibility in mind
- Provide clear error messages
- Handle edge cases gracefully
- Consider internationalization if applicable

## Video-Specific Guidelines

Given the nature of this project:
- Support common video formats (MP4, AVI, MOV, etc.)
- Handle video metadata properly
- Consider streaming vs. full-file processing
- Implement proper error handling for corrupted files
- Document any video quality or format limitations
- Consider memory constraints when processing large videos

## AI/ML Guidelines (if using Gemini)

- Document AI model versions and parameters
- Handle API rate limits gracefully
- Implement retry logic with exponential backoff
- Cache API responses when appropriate
- Document API costs and usage limits
- Provide fallback behavior if API is unavailable

## Issue Assignment Best Practices

When creating issues for Copilot to work on:
- Provide clear acceptance criteria
- Specify which files should be modified
- Include examples of expected input/output
- Break large tasks into smaller, focused issues
- Tag issues appropriately (bug, feature, documentation, etc.)

## Custom Agents

Custom agents can be defined in `.github/agents/` for specialized tasks such as:
- Documentation updates
- Test generation
- Code refactoring
- Framework-specific patterns

## Notes for Copilot

- Start with the simplest solution that works
- Ask for clarification if requirements are ambiguous
- Consider backwards compatibility
- Highlight any breaking changes
- Suggest improvements to existing code when relevant
- Flag potential security or performance issues
