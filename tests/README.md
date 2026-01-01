# Tests

English | [简体中文](README_zh-CN.md)

This directory contains the test suite for the RSS AI News Crawler project.

## Test Structure

```
tests/
├── conftest.py         # Shared fixtures and configuration
├── test_ai.py          # AI service and strategy tests
├── test_feeds.py       # RSS feed connectivity tests
├── test_infra.py       # Infrastructure (proxy, email) tests
└── README.md           # This file
```

## Running Tests

### Quick Start

```bash
# Run all unit tests (default, skips live tests)
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_ai.py

# Run specific test
pytest tests/test_ai.py::test_process_logic_parsing
```

### Live Tests (Network Required)

Live tests require real credentials and network connectivity:

```bash
# Run ALL tests including live network tests
pytest -m live

# Run only live tests
pytest -m "live"

# Run all tests (unit + live)
pytest -m ""
```

**Warning**: Live tests will:
- Make real API calls (consumes quota/credits)
- Test proxy connectivity
- Attempt to send emails
- Access external RSS feeds

Ensure your `.env` file is properly configured before running live tests.

## Test Categories

### Unit Tests (Default)
- **Fast**: Run in milliseconds
- **Isolated**: Use mocks, no external dependencies
- **Safe**: No API calls, no credentials needed

Examples:
- `test_process_logic_parsing()` - Tests AI response parsing
- `test_strategy_has_required_fields()` - Tests configuration validation

### Live Tests (`@pytest.mark.live`)
- **Slow**: Depend on network latency
- **External**: Require real services (AI API, SMTP, RSS feeds)
- **Credentials**: Need valid API keys/tokens

Examples:
- `test_ai_connectivity_real()` - Tests real AI API
- `test_rss_feed_connectivity()` - Tests RSS feed availability
- `test_email_sending_real()` - Tests SMTP email sending

## Configuration

### Mock Credentials

By default, tests use mock credentials defined in `conftest.py`:
- `AI_API_KEY=sk-mock-key`
- `MAIL_HOST=smtp.mock.com`
- etc.

This prevents accidental API calls during unit testing.

### Real Credentials

For live tests, ensure your `.env` file contains valid credentials:

```env
AI_API_KEY=sk-real-key-here
AI_URL=https://api.openai.com/v1
MAIL_HOST=smtp.gmail.com
MAIL_USER=your@email.com
MAIL_PASS=your-password
```

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:
1. Unit tests only (fast, no credentials needed)
2. On multiple Python versions (3.10-3.13)
3. With linting checks (ruff)

Live tests are **not** run in CI by default to avoid:
- Consuming API quotas
- Exposing credentials
- Slow build times

## Coverage

To generate test coverage report:

```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage
pytest --cov=news_crawler --cov-report=html

# View report
open htmlcov/index.html
```

## Writing New Tests

### Unit Test Template

```python
def test_my_function():
    """Brief description of what is being tested."""
    # Arrange
    input_data = "test"
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == expected_value
```

### Live Test Template

```python
@pytest.mark.live
def test_external_service():
    """Test real external service."""
    if os.getenv("SERVICE_KEY", "").startswith("mock"):
        pytest.skip("Using mock credentials")
    
    result = call_external_service()
    assert result is not None
```

## Troubleshooting

### Tests Fail with "Connection Error"
- Check if live tests are running when they shouldn't: `pytest -m "not live"`
- Verify proxy settings: `echo $AZURE_PROXY`

### Tests Fail with "API Key Invalid"
- Live tests require real credentials in `.env`
- Unit tests should not reach external APIs (check if mock is working)

### Import Errors
```bash
# Install in editable mode
pip install -e .

# Or ensure PYTHONPATH is set
export PYTHONPATH=/path/to/rss-ai-news
```

## Best Practices

1. **Write unit tests first** - Fast, reliable, no dependencies
2. **Use live tests sparingly** - Only for critical integrations
3. **Mock external services** - Avoid API calls in unit tests
4. **Test edge cases** - Empty inputs, errors, boundary conditions
5. **Keep tests independent** - No shared state between tests
6. **Use descriptive names** - `test_parse_valid_rss_feed` not `test_1`

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
