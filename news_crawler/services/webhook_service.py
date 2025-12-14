import requests
from news_crawler.core.settings import get_settings

def send_webhook(text: str):
    url = get_settings().mail.webhook_url # 假设你在 settings 里加了这个字段
    if not url:
        return
    
    # 以飞书/钉钉/Discord 为例，通常就是一个 POST 请求
    try:
        # 这是一个通用的 JSON payload，具体看你用什么 IM
        payload = {"msg_type": "text", "content": {"text": text}}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Webhook send failed: {e}")