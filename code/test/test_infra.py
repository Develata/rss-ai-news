# 文件路径：/app/code/test/test_infra.py
import pytest
import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header

@pytest.mark.live
def test_proxy_connectivity():
    """测试代理是否能连通 Google"""
    proxy_url = os.getenv('AZURE_PROXY')
    if not proxy_url:
        pytest.skip("未配置 AZURE_PROXY，跳过")

    proxies = {"http": proxy_url, "https": proxy_url}
    print(f"\n🔍 Testing Proxy: {proxy_url}")

    try:
        resp = requests.get("https://www.google.com", proxies=proxies, timeout=15)
        assert resp.status_code == 200
    except Exception as e:
        pytest.fail(f"代理连接失败: {e}")

@pytest.mark.live
def test_email_sending_real():
    """测试邮件发送功能"""
    # 注意：这里需要读取真实的系统环境变量，而不是 conftest 里的 mock
    # 如果系统没配环境变量，这些值为 None
    mail_host = os.environ.get('MAIL_HOST')
    
    if not mail_host or "mock" in mail_host:
        pytest.skip("检测到 Mock 环境或配置缺失，跳过真实邮件发送")

    mail_user = os.environ.get('MAIL_USER')
    mail_pass = os.environ.get('MAIL_PASS')
    mail_to = os.environ.get('MAIL_TO')

    msg = MIMEText("Pytest 连通性测试", 'plain', 'utf-8')
    msg['From'] = Header("Tester", 'utf-8')
    msg['To'] = Header("Admin", 'utf-8')
    msg['Subject'] = Header("Test Email", 'utf-8')

    try:
        server = smtplib.SMTP_SSL(mail_host, 465, timeout=10)
        server.login(mail_user, mail_pass)
        server.sendmail(mail_user, [mail_to], msg.as_string())
        server.quit()
    except Exception as e:
        pytest.fail(f"邮件发送失败: {e}")