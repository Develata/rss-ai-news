import pytest
import os

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """
    自动为所有测试设置虚假环境变量。
    如果是真实联网测试 (live)，测试函数内部会覆盖或者读取真实系统变量。
    """
    # 设置默认 Mock 值，防止代码因找不到 Key 报错
    monkeypatch.setenv("AI_API_KEY", "sk-mock-key")
    monkeypatch.setenv("AI_URL", "https://api.mock.com")
    monkeypatch.setenv("AI_MODEL", "gpt-mock")
    monkeypatch.setenv("MAIL_HOST", "smtp.mock.com")
    monkeypatch.setenv("MAIL_USER", "mock@test.com")
    monkeypatch.setenv("MAIL_PASS", "mockpass")
    monkeypatch.setenv("MAIL_TO", "admin@test.com")