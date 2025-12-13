import os
import time
from datetime import datetime, timezone

import feedparser
import requests

from news_crawler.core.crawler import SpiderCore
from news_crawler.core.settings import get_settings
from news_crawler.dtos.dto import ParsedItem, PseudoEntry
from news_crawler.utils.common import compute_hash

try:
    from news_crawler.utils.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def fetch_and_parse_feed(category, source_name, url, cutoff_date):
    settings = get_settings()
    proxy = settings.network.azure_proxy

    spider = SpiderCore()
    results = []
    feed_entries = []

    try:
        # 1. 下载逻辑
        if url.startswith("JSON|"):
            real_url = url.split("|")[1]
            try:
                proxies = {"http": proxy, "https": proxy} if proxy else None
                resp = requests.get(real_url, proxies=proxies, timeout=20)
                json_data = resp.json()
                for item in json_data.get("data", [])[:30]:
                    hot_val = item.get("hot", "N/A")
                    feed_entries.append(
                        PseudoEntry(
                            title=item.get("title"),
                            link=item.get("url") or item.get("mobileUrl"),
                            summary=f"热度: {hot_val}",
                        )
                    )
            except Exception as e:
                logger.error(f"  ❌ [Thread] JSON Error ({source_name}): {e}")
                return []
        else:
            try:
                rss_content = spider.fetch(url)
                if not rss_content:
                    return []
                feed = feedparser.parse(rss_content)
                feed_entries = feed.entries or []
            except Exception as e:
                logger.error(f"  ❌ [Thread] RSS Error ({source_name}): {e}")
                return []

        # 2. 清洗逻辑
        for entry in feed_entries:
            link = getattr(entry, "link", None)
            if not link:
                continue

            if not url.startswith("JSON|"):
                published_time = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_time = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed), timezone.utc
                    )
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published_time = datetime.fromtimestamp(
                        time.mktime(entry.updated_parsed), timezone.utc
                    )

                if published_time and published_time < cutoff_date:
                    continue

            final_content = ""
            content_hash = ""

            if category == "HotNews_CN":
                summary = getattr(entry, "summary", "")
                final_content = f"【标题】{entry.title}\n【信息】{summary}"
                content_hash = compute_hash(final_content)
            else:
                try:
                    html = spider.fetch(link)
                    data = spider.clean(html)
                    if not data:
                        continue
                    final_content = data["full_text"]
                    content_hash = compute_hash(final_content)
                except Exception:
                    continue

            results.append(
                ParsedItem(
                    title=entry.title,
                    link=link,
                    summary=getattr(entry, "summary", ""),
                    content_text=final_content,
                    content_hash=content_hash,
                    source_name=source_name,
                    category=category,
                    created_at=datetime.now(timezone.utc),
                )
            )

    except Exception as e:
        logger.error(f"  ❌ [Thread] Critical Error ({source_name}): {e}")
        return []

    return results
