# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-01

### 🎉 Initial Release

#### Added
- **Multi-source RSS aggregation**: Support for standard RSS/Atom feeds, RSSHub, and JSON APIs
- **AI-powered content analysis**: Intelligent scoring, summarization, and tagging using OpenAI-compatible APIs
- **Category-based strategies**: Specialized prompts for different domains (Math Research, Tech News, Global Politics)
- **Automatic report generation**: Daily Markdown reports with configurable content
- **GitHub Pages publishing**: One-commit workflow for automated content deployment
- **Dual database support**: PostgreSQL (production) and SQLite (development)
- **Docker deployment**: Complete containerization with Cron scheduling
- **External configuration**: Support for mounting config files via `CONFIG_DIR` environment variable
- **Notification system**: Email and webhook notifications for task status
- **Comprehensive error handling**: Detailed error messages with exit codes for CI/CD integration
- **Memory-optimized processing**: Batch operations and generator patterns for efficient resource usage

#### Technical Highlights
- Python 3.10+ with full type annotations
- Modular architecture: `core/`, `services/`, `workers/`, `utils/`
- Concurrent processing with ThreadPoolExecutor
- Structured logging with rotation support
- Multi-stage Docker build for minimal image size
- Flexible mirror configuration for China mainland users

#### Documentation
- Comprehensive README with quick start guide
- Detailed `.env.example` with bilingual comments
- MIT License
- GitHub Actions CI workflow

#### Developer Tools
- Unit tests with pytest
- Linting support (ruff compatible)
- `.dockerignore` for optimized builds
- Type hints throughout codebase

---

### Known Limitations
- No web UI (CLI and scheduled tasks only)
- Manual GitHub token renewal required
- Single-node deployment (no distributed mode)
- Chinese-language focused documentation (English translation in progress)

### Breaking Changes
None (initial release)

### Upgrade Path
Fresh installation - no migration needed for first-time users.

---

## [0.0.1] - 2025-12-xx

### Internal Alpha
- Initial prototype development
- Core functionality testing

---

[Unreleased]: https://github.com/Develata/rss-ai-news/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Develata/rss-ai-news/releases/tag/v0.1.0
