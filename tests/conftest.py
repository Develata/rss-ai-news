"""Pytest configuration and fixtures.

Provides shared test fixtures and configuration:
- Mock environment variables for unit tests
- Prevents accidental use of real credentials in tests
"""

import os

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Automatically set mock environment variables for all tests.
    
    For 'live' tests, test functions should explicitly read from
    os.environ or override these mocked values.
    
    This prevents accidental API calls or credential leaks during
    unit testing.
    """
    monkeypatch.setenv("AI_API_KEY", "sk-mock-key")
    monkeypatch.setenv("AI_URL", "https://api.mock.com")
    monkeypatch.setenv("AI_MODEL", "gpt-mock")
    monkeypatch.setenv("MAIL_HOST", "smtp.mock.com")
    monkeypatch.setenv("MAIL_USER", "mock@test.com")
    monkeypatch.setenv("MAIL_PASS", "mockpass")
    monkeypatch.setenv("MAIL_TO", "admin@test.com")