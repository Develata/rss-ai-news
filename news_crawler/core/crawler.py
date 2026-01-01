import urllib3

import requests
import trafilatura
from requests.adapters import HTTPAdapter
from tenacity import retry, stop_after_attempt, wait_fixed
from urllib3.util.retry import Retry

from news_crawler.core.settings import get_settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _create_session(proxy_url: str = None) -> requests.Session:
    """创建带连接池的 requests Session，复用 TCP 连接"""
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=retry_strategy,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    if proxy_url:
        session.proxies = {"http": proxy_url, "https": proxy_url}
    
    return session


class SpiderCore:
    # 类级别的 Session 缓存（按代理URL区分）
    _sessions: dict = {}
    
    def __init__(self):
        settings = get_settings()
        self.proxy_url = settings.network.azure_proxy
        self.timeout = getattr(settings.network, 'request_timeout', 20)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    
    def _get_session(self, use_proxy: bool) -> requests.Session:
        """获取或创建复用的 Session"""
        cache_key = self.proxy_url if use_proxy else "no_proxy"
        if cache_key not in SpiderCore._sessions:
            proxy = self.proxy_url if use_proxy else None
            SpiderCore._sessions[cache_key] = _create_session(proxy)
        return SpiderCore._sessions[cache_key]

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def fetch(self, url):
        # 本地地址不走代理
        use_proxy = not ("127.0.0.1" in url or "localhost" in url) and bool(self.proxy_url)
        session = self._get_session(use_proxy)

        with session.get(
            url,
            headers=self.headers,
            timeout=self.timeout,
            verify=False,
            stream=True,
        ) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "").lower()
            if any(
                x in content_type
                for x in [
                    "image/",
                    "video/",
                    "audio/",
                    "application/pdf",
                    "application/zip",
                ]
            ):
                return None
            content_length = resp.headers.get("Content-Length")
            if content_length and int(content_length) > 10 * 1024 * 1024:
                return None
            if resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = "utf-8"
            return resp.text

    def clean(self, html):
        if not html:
            return None

        text = trafilatura.extract(html, include_images=False, include_links=False)

        if not text or len(text) < 50:
            return None

        return {"full_text": text}
