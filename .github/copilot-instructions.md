# Copilot Instructions for geminivideo

## Project Overview

This repository is for a video processing project that leverages Google's Gemini AI capabilities. The project aims to provide tools and utilities for working with video content using Gemini's multimodal AI features.

**Target Audience:** Developers building video analysis and processing applications with AI integration.

## Tech Stack

- **Language:** (To be determined based on project development)
- **AI Platform:** Google Gemini AI
- **Focus Area:** Video processing and analysis

## Coding Guidelines

### General Principles
- Write clean, readable, and maintainable code
- Follow language-specific best practices and conventions
- Include meaningful comments for complex logic
- Use descriptive variable and function names
- Implement proper error handling and logging

### Code Style
- Use consistent indentation (spaces preferred)
- Follow the existing code style in the repository
- Keep functions focused and modular
- Write self-documenting code where possible

### Testing
- Write unit tests for new functionality
- Ensure tests are isolated and repeatable
- Test edge cases and error conditions
- Maintain high test coverage for critical paths

### Documentation
- Update README.md with new features and usage instructions
- Document API endpoints and function signatures
- Include examples for complex functionality
- Keep documentation in sync with code changes

## Project Structure

```
geminivideo/
├── .github/                    # GitHub configuration and workflows
│   └── copilot-instructions.md # Copilot custom instructions
└── README.md                   # Project documentation
```

**Note:** As the project grows, maintain a clear and logical directory structure:
- Separate source code, tests, and documentation
- Group related functionality together
- Use meaningful directory names
- Keep configuration files at the root level

## Development Workflow

### Getting Started
1. Clone the repository
2. Review the README.md for setup instructions
3. Install required dependencies (to be added as project develops)

### Making Changes
1. Create a feature branch from main
2. Implement changes with appropriate tests
3. Run linters and tests locally
4. Submit a pull request with a clear description

### Code Review
- All changes should be reviewed before merging
- Address review comments promptly
- Ensure CI checks pass before merging

## Resources and References

### Key Documentation
- [Google Gemini AI Documentation](https://ai.google.dev/)
- [Gemini API Reference](https://ai.google.dev/api)
- [GitHub Copilot Best Practices](https://docs.github.com/en/copilot/best-practices)

### Contributing
- Follow the contribution guidelines (to be added)
- Ensure all commits are signed and have meaningful messages
- Keep pull requests focused on a single concern

## AI Agent Guidelines

When working on this repository:

1. **Understand Context:** Review related files and existing patterns before making changes
2. **Minimal Changes:** Make the smallest possible changes to achieve the goal
3. **Test Coverage:** Ensure changes are properly tested
4. **Security:** Never commit secrets or API keys; use environment variables
5. **Dependencies:** Check for security vulnerabilities before adding new dependencies
6. **Documentation:** Update relevant documentation with code changes
7. **Validation:** Test changes locally before committing

## Specific Instructions

### Video Processing
- Handle video files efficiently with proper memory management
- Support common video formats (MP4, AVI, MOV, etc.)
- Implement proper error handling for corrupted or unsupported files

### Gemini AI Integration
- Use official Gemini SDK/API when available
- Implement rate limiting and retry logic for API calls
- Cache responses where appropriate to minimize API usage
- Handle API errors gracefully with user-friendly messages

### Security Considerations
- Never hardcode API keys or credentials
- Validate and sanitize all user inputs
- Implement proper authentication and authorization
- Follow OWASP security best practices

## Notes for Copilot

- This is an early-stage project; structure and patterns will evolve
- Prioritize code clarity over premature optimization
- Ask clarifying questions when requirements are ambiguous
- Suggest best practices and modern approaches when appropriate
- Consider scalability and maintainability in design decisions
