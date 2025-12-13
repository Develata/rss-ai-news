import smtplib
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

from news_crawler.core.settings import get_settings


def send_notification(title, content):
    settings = get_settings()

    mail_host = settings.mail.host
    mail_port = settings.mail.port
    mail_user = settings.mail.user
    mail_pass = settings.mail.password
    mail_to = settings.mail.to

    if not mail_host or not mail_user or not mail_pass:
        print("⚠️ 邮件配置缺失，跳过发送通知。")
        return

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_content = f"【情报系统通知】\n时间: {current_time}\n\n{content}"

    message = MIMEText(full_content, "plain", "utf-8")

    message["From"] = formataddr(
        (Header(settings.mail.from_name, "utf-8").encode(), mail_user)
    )
    message["To"] = formataddr(
        (Header(settings.mail.to_name, "utf-8").encode(), mail_to)
    )
    message["Subject"] = Header(title, "utf-8")

    try:
        server = smtplib.SMTP_SSL(mail_host, mail_port)
        server.login(mail_user, mail_pass)
        server.sendmail(mail_user, [mail_to], message.as_string())
        server.quit()
        print(f"📧 [通知] 邮件已发送至 {mail_to}")
    except Exception as e:
        print(f"❌ [通知] 邮件发送失败: {e}")
