# Contributing to Gemini Video

Thank you for your interest in contributing to Gemini Video! This document provides guidelines and instructions for contributing to the project.

## 🤝 How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. **Check existing issues** - Search [GitHub Issues](https://github.com/milosriki/geminivideo/issues) to see if your issue has already been reported
2. **Create a new issue** - Use the appropriate issue template:
   - Bug reports
   - Feature requests
   - Documentation improvements
3. **Provide details** - Include:
   - Clear description of the issue or feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)

### Submitting Ideas

We love hearing your ideas! Check out our **[GitHub Projects Guide](GITHUB_PROJECTS_GUIDE.md)** to learn how to:
- Submit and track ideas using GitHub Projects
- Organize features and enhancements
- Participate in project planning
- Follow ideas from concept to completion

[**Submit a new idea →**](https://github.com/milosriki/geminivideo/issues/new?template=idea.yml)

### Pull Requests

1. **Fork the repository** and create a new branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards:
   - Follow existing code style and patterns
   - Add tests for new features
   - Update documentation as needed
   - Keep commits focused and descriptive

3. **Test your changes**:
   ```bash
   # Start all services
   ./scripts/start-all.sh
   
   # Run tests
   # Python services
   cd services/drive-intel && pytest
   cd services/video-agent && pytest
   
   # Node services
   cd services/gateway-api && npm test
   ```

4. **Update documentation** if your changes affect:
   - API endpoints
   - Configuration options
   - Setup instructions
   - Architecture

5. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "feat: Add new feature description"
   git commit -m "fix: Resolve issue with X"
   git commit -m "docs: Update API documentation"
   ```

6. **Push to your fork** and open a Pull Request:
   - Provide a clear description of your changes
   - Reference any related issues
   - Include screenshots or examples if applicable

## 📋 Development Setup

### Prerequisites

- Docker & Docker Compose
- At least 8GB RAM and 10GB disk space
- Git

### Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/milosriki/geminivideo.git
   cd geminivideo
   ```

2. **Start all services**:
   ```bash
   ./scripts/start-all.sh
   ```

3. **Verify services are running**:
   - Frontend: http://localhost:3000
   - Gateway API: http://localhost:8000
   - Drive Intel: http://localhost:8001
   - Video Agent: http://localhost:8002
   - Meta Publisher: http://localhost:8003

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## 🏗️ Project Structure

### Services

- **drive-intel** (Python/FastAPI) - Scene detection, feature extraction, semantic search
- **video-agent** (Python/FastAPI) - Video rendering, overlays, compliance checks
- **gateway-api** (Node/Express) - Unified API, scoring engine, reliability logging
- **meta-publisher** (Node/Express) - Meta Marketing API integration
- **frontend** (React/Vite) - Analytics dashboards and controls

### Key Directories

- `services/` - Individual microservices
- `shared/` - Shared configuration and utilities
- `frontend/` - React frontend application
- `tests/` - Test suites
- `docs/` - Documentation
- `.github/` - GitHub workflows and templates

## 📝 Coding Standards

### Python Services

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and single-purpose

### Node/TypeScript Services

- Follow ESLint configuration
- Use TypeScript for type safety
- Write JSDoc comments for public APIs
- Use async/await for asynchronous operations

### General Guidelines

- Write clear, descriptive commit messages
- Keep PRs focused on a single feature or fix
- Add tests for new functionality
- Update relevant documentation
- Follow existing code patterns and architecture

## 🧪 Testing

### Running Tests

```bash
# Python services
cd services/drive-intel && pytest
cd services/video-agent && pytest

# Node services
cd services/gateway-api && npm test
cd services/meta-publisher && npm test

# Frontend
cd frontend && npm test
```

### Writing Tests

- Write unit tests for new functions
- Add integration tests for API endpoints
- Include edge cases and error handling
- Aim for good test coverage

## 📚 Documentation

### Code Documentation

- Document public APIs and functions
- Include examples in docstrings
- Update README files when adding features
- Keep architecture diagrams current

### API Documentation

- Document new endpoints in `API_ENDPOINTS_REFERENCE.md`
- Include request/response examples
- Document authentication requirements
- Note any breaking changes

## 🔍 Code Review Process

1. All PRs require review before merging
2. Address review comments promptly
3. Keep discussions constructive and respectful
4. Be open to feedback and suggestions

## 🐛 Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Docker version, service versions
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable

## ✨ Feature Requests

When requesting features:

- **Use Case**: Describe the problem you're trying to solve
- **Proposed Solution**: Your idea for how to solve it
- **Alternatives**: Other solutions you've considered
- **Additional Context**: Any other relevant information

## 📄 License

By contributing to Gemini Video, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!

For questions or support, please open a GitHub issue or contact the maintainers.

