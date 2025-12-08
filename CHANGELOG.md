# Changelog

All notable changes to Gemini Video will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Root-level LICENSE file (MIT License)
- CONTRIBUTING.md with contribution guidelines
- CHANGELOG.md for version tracking

### Changed
- Improved documentation structure and organization

## [1.0.0] - 2024-12-07

### Added

#### Core Features
- **Scene Enrichment & Feature Extraction** - Automated shot detection, object recognition, OCR, motion analysis
- **Predictive Scoring Engine** - Psychology-based content analysis with CTR prediction
- **Multi-Format Rendering** - Automated video remix with overlays, subtitles, and compliance checks
- **Meta Integration** - Direct publishing to Instagram/Facebook with insights ingestion
- **Analytics Dashboards** - Comprehensive analysis, diversification tracking, and reliability monitoring
- **Self-Learning Loop** - Automated weight calibration based on actual performance data

#### Services
- **drive-intel** (Python/FastAPI) - Scene detection, feature extraction, semantic search
- **video-agent** (Python/FastAPI) - Video rendering, overlays, compliance checks
- **gateway-api** (Node/Express) - Unified API, scoring engine, reliability logging
- **meta-publisher** (Node/Express) - Meta Marketing API integration
- **frontend** (React/Vite) - Analytics dashboards and controls

#### ML & AI Features
- Champion-challenger evaluation for advanced ML features
- ML endpoints integration
- AI video generation capabilities
- Voice generation system
- Real-time streaming support

#### Video Processing
- Auto-caption system with Whisper Large V3 Turbo support
- Smart crop functionality
- Beat sync implementation
- Transitions library
- Asset library management
- Audio mixer capabilities
- Image generation integration

#### Infrastructure
- Docker Compose setup for local development
- Google Cloud Platform (GCP) Cloud Run deployment
- Edge deployment support
- CI/CD pipelines with GitHub Actions
- Monitoring and logging infrastructure
- Redis caching system
- Vector database integration

#### Documentation
- Comprehensive README with quick start guide
- API endpoints reference
- Deployment guides
- GitHub Projects guide for idea management
- Security documentation
- Architecture documentation
- Service-specific documentation

#### Developer Experience
- One-command start script (`./scripts/start-all.sh`)
- Connection testing scripts
- Health check endpoints
- Development setup guides
- Testing infrastructure

### Changed
- Refactored URL handling to use relative URLs
- Improved documentation structure
- Enhanced code organization and modularity
- Updated frontend dependencies and build configuration

### Fixed
- Frontend missing lib/utils module
- JSX file extension issues
- Markdown formatting in documentation
- Service connection and networking issues

### Security
- Security implementation documentation
- Security alerts and guidelines
- Firebase authentication integration
- API security best practices

## [0.9.0] - 2024-11-XX

### Added
- Initial project structure
- Core service implementations
- Basic video processing capabilities
- Integration with Meta Marketing API

### Changed
- Project organization and architecture refinements

## Notes

- For service-specific changelogs, see:
  - `services/video-agent/pro/CHANGELOG_AUTO_CAPTIONS.md` - Auto-caption system changelog
  - Service-specific documentation in respective service directories

- Major features and implementations are documented in:
  - Various `AGENT_*_IMPLEMENTATION.md` files
  - `IMPLEMENTATION_SUMMARY.md` files
  - Service-specific README files

---

## Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

