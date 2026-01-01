import logging
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

from news_crawler.core.settings import get_settings

logger = logging.getLogger(__name__)


def send_notification(title, content):
    """
    Send email notification via SMTP.

    Args:
        title: Email subject
        content: Email body content
    """
    settings = get_settings()

    mail_host = settings.mail.host
    mail_port = settings.mail.port
    mail_user = settings.mail.user
    mail_pass = settings.mail.password
    mail_to = settings.mail.to

    if not mail_host or not mail_user or not mail_pass:
        logger.warning("Mail configuration missing, skipping notification")
        return

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_content = f"【情报系统通知】\n时间: {current_time}\n\n{content}"

    message = MIMEText(full_content, "plain", "utf-8")

    message["From"] = formataddr((Header(settings.mail.from_name, "utf-8").encode(), mail_user))
    message["To"] = formataddr((Header(settings.mail.to_name, "utf-8").encode(), mail_to))
    message["Subject"] = Header(title, "utf-8")

    try:
        server = smtplib.SMTP_SSL(mail_host, mail_port)
        server.login(mail_user, mail_pass)
        server.sendmail(mail_user, [mail_to], message.as_string())
        server.quit()
        logger.info(f"Email notification sent to {mail_to}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Email authentication failed: {e}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
    except OSError as e:
        logger.error(f"Network error sending email: {e}")
