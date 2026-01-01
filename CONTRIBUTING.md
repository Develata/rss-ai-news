# Contributing to RSS AI News

Thank you for your interest in contributing! We welcome contributions from the community.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/rss-ai-news.git`
3. **Create a branch**: `git checkout -b feature/amazing-feature`
4. **Make changes** and commit: `git commit -m 'feat: add amazing feature'`
5. **Push** to your fork: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

## 📋 Development Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (recommended)
- Git

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Develata/rss-ai-news.git
cd rss-ai-news

# 2. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 3. Install dependencies (choose one method)

# Method A: Using Docker (recommended)
docker compose up -d

# Method B: Using virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[test]

# 4. Run tests
pytest
pytest -m live  # Run live tests (requires real credentials)
```

## 🧪 Testing Guidelines

- **Write tests** for new features
- **Run tests** before submitting PR: `pytest -v`
- **Maintain coverage**: Aim for >80% test coverage
- **Use markers**:
  - `@pytest.mark.live` for tests requiring network/credentials
  - Default tests should run without external dependencies

## 📝 Code Standards

### Python Style Guide

- Follow **PEP 8** conventions
- Use **type hints** for function signatures
- Maximum line length: **100 characters**
- Use **docstrings** for all public functions:

```python
def my_function(param: str) -> int:
    """Brief description of function.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    pass
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, no logic change)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add support for Atom feeds
fix: prevent database connection leak
docs: update README installation steps
```

### Code Review Checklist

Before submitting PR, ensure:

- [ ] Code follows project style guide
- [ ] Tests pass locally (`pytest`)
- [ ] New code has tests (unit + integration)
- [ ] Documentation updated (if adding features)
- [ ] No hardcoded credentials or sensitive data
- [ ] CHANGELOG.md updated (for significant changes)
- [ ] Commit messages follow conventions

## 🐛 Reporting Bugs

Use the [GitHub issue tracker](https://github.com/Develata/rss-ai-news/issues):

1. **Search existing issues** first
2. **Use issue templates** (if available)
3. **Provide details**:
   - Environment (OS, Python version, Docker version)
   - Steps to reproduce
   - Expected vs actual behavior
   - Error logs (use code blocks)
   - Screenshots (if applicable)

## 💡 Feature Requests

We love new ideas! Submit feature requests via issues:

- Explain the **use case**
- Describe the **expected behavior**
- Suggest an **implementation approach** (optional)
- Tag with `enhancement` label

## 📚 Documentation

Help improve documentation:

- **README.md**: Main project documentation
- **Docstrings**: Inline code documentation
- **tests/README.md**: Testing guide
- **CHANGELOG.md**: Version history

## 🎯 Areas for Contribution

Looking for ways to contribute? Check these areas:

- 🐛 **Bug fixes**: See [issues labeled 'bug'](https://github.com/Develata/rss-ai-news/labels/bug)
- 📝 **Documentation**: Improve clarity, fix typos, add examples
- 🧪 **Testing**: Increase test coverage, add edge case tests
- 🌐 **Localization**: Add support for more languages
- 🔌 **Integrations**: Add new RSS sources, AI providers, or notification channels
- ⚡ **Performance**: Optimize database queries, reduce memory usage

## 🚫 What NOT to Contribute

Please avoid:

- **Breaking changes** without discussion
- **Unrelated features** that expand scope significantly
- **Large refactors** without prior agreement
- **Proprietary/licensed code** you don't own
- **Generated AI code** without human review and testing

## 📜 License

By contributing, you agree that your contributions will be licensed under the **MIT License**.

## 💬 Communication

- **GitHub Issues**: Bug reports, feature requests
- **Discussions**: Q&A, ideas, general discussions
- **Pull Requests**: Code contributions

## 🙏 Recognition

Contributors will be:
- Mentioned in release notes
- Listed in GitHub contributors page
- Credited in CHANGELOG.md for significant contributions

Thank you for making RSS AI News better! 🎉
