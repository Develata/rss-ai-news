"""Infrastructure connectivity tests.

This module tests:
- Proxy connectivity
- Email (SMTP) configuration and sending
- External service dependencies
"""

import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText

import pytest
import requests


@pytest.mark.live
def test_proxy_connectivity():
    """Test proxy connectivity to external sites.
    
    Run with: pytest -m live
    Skipped if AZURE_PROXY is not configured.
    """
    proxy_url = os.getenv('AZURE_PROXY')
    if not proxy_url:
        pytest.skip("AZURE_PROXY not configured, skipping")

    proxies = {"http": proxy_url, "https": proxy_url}
    print(f"\n🔍 Testing Proxy: {proxy_url}")

    try:
        resp = requests.get(
            "https://www.google.com",
            proxies=proxies,
            timeout=15
        )
        assert resp.status_code == 200
    except requests.RequestException as e:
        pytest.fail(f"Proxy connection failed: {e}")

@pytest.mark.live
def test_email_sending_real():
    """Test real email sending functionality.
    
    Run with: pytest -m live
    Skipped if using mock credentials or missing configuration.
    
    Note: Uses real system environment variables, not mocked ones.
    """
    mail_host = os.environ.get('MAIL_HOST')
    
    if not mail_host or "mock" in mail_host:
        pytest.skip("Mock environment or missing config, skipping real email test")

    mail_user = os.environ.get('MAIL_USER')
    mail_pass = os.environ.get('MAIL_PASS')
    mail_to = os.environ.get('MAIL_TO')

    msg = MIMEText('Pytest connectivity test', 'plain', 'utf-8')
    msg['From'] = Header('Tester', 'utf-8')
    msg['To'] = Header('Admin', 'utf-8')
    msg['Subject'] = Header('Test Email', 'utf-8')

    try:
        server = smtplib.SMTP_SSL(mail_host, 465, timeout=10)
        server.login(mail_user, mail_pass)
        server.sendmail(mail_user, [mail_to], msg.as_string())
        server.quit()
    except smtplib.SMTPException as e:
        pytest.fail(f"Email sending failed: {e}")