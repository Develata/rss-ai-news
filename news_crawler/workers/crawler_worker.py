"""
Crawler worker module for RSS feed fetching and parsing.

Provides functionality for:
- RSS/JSON feed downloading with proxy support
- Feed entry parsing and filtering by date
- Full-text extraction from article URLs
- Content hashing for deduplication
"""

import os
import time
from datetime import datetime, timezone
from typing import Any

import feedparser
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from news_crawler.core.crawler import SpiderCore
from news_crawler.core.settings import get_settings
from news_crawler.dtos.dto import ParsedItem, PseudoEntry
from news_crawler.utils.common import compute_hash

try:
    from news_crawler.utils.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Constants
JSON_PREFIX = "JSON|"
JSON_DATA_KEY = "data"
JSON_MAX_ITEMS = 30
REQUEST_TIMEOUT = 20
HOTNEWS_CATEGORY = "HotNews_CN"


def _fetch_json_feed(
    url: str, source_name: str, proxy: str | None
) -> list[PseudoEntry]:
    """
    Fetch and parse JSON-formatted feed.

    Args:
        url: Feed URL with JSON| prefix
        source_name: Source identifier for logging
        proxy: Optional proxy URL

    Returns:
        List of PseudoEntry objects, empty list on error
    """
    real_url = url.split("|")[1]
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        resp = requests.get(real_url, proxies=proxies, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        json_data = resp.json()

        entries = []
        for item in json_data.get(JSON_DATA_KEY, [])[:JSON_MAX_ITEMS]:
            hot_val = item.get("hot", "N/A")
            entries.append(
                PseudoEntry(
                    title=item.get("title"),
                    link=item.get("url") or item.get("mobileUrl"),
                    summary=f"热度: {hot_val}",
                )
            )
        return entries

    except (RequestException, Timeout, ConnectionError) as e:
        logger.error(f"  ❌ [Thread] JSON Error ({source_name}): {e}")
        return []
    except ValueError as e:
        logger.error(f"  ❌ [Thread] JSON Parse Error ({source_name}): {e}")
        return []


def _fetch_rss_feed(
    url: str, source_name: str, spider: SpiderCore
) -> list[Any]:
    """
    Fetch and parse RSS feed.

    Args:
        url: RSS feed URL
        source_name: Source identifier for logging
        spider: SpiderCore instance for fetching

    Returns:
        List of feed entries, empty list on error
    """
    try:
        rss_content = spider.fetch(url)
        if not rss_content:
            logger.warning(f"Empty RSS content from {source_name}")
            return []

        feed = feedparser.parse(rss_content)
        return feed.entries or []

    except Exception as e:
        logger.error(f"  ❌ [Thread] RSS Error ({source_name}): {e}")
        return []


def _get_published_time(entry: Any) -> datetime | None:
    """
    Extract published time from feed entry.

    Args:
        entry: Feed entry object

    Returns:
        Datetime object in UTC, None if not available
    """
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime.fromtimestamp(
            time.mktime(entry.published_parsed), timezone.utc
        )
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime.fromtimestamp(
            time.mktime(entry.updated_parsed), timezone.utc
        )
    return None


def _extract_hotnews_content(entry: Any) -> tuple[str, str]:
    """
    Extract content for HotNews category (summary only).

    Args:
        entry: Feed entry object

    Returns:
        Tuple of (content_text, content_hash)
    """
    summary = getattr(entry, "summary", "")
    content = f"【标题】{entry.title}\n【信息】{summary}"
    return content, compute_hash(content)


def _extract_full_article_content(
    link: str, spider: SpiderCore
) -> tuple[str, str] | None:
    """
    Extract full article content from URL.

    Args:
        link: Article URL
        spider: SpiderCore instance for fetching and cleaning

    Returns:
        Tuple of (content_text, content_hash) or None on error
    """
    try:
        html = spider.fetch(link)
        data = spider.clean(html)
        if not data:
            return None

        content = data["full_text"]
        return content, compute_hash(content)

    except Exception as e:
        logger.debug(f"Failed to extract content from {link}: {e}")
        return None


def fetch_and_parse_feed(
    category: str, source_name: str, url: str, cutoff_date: datetime
) -> list[ParsedItem]:
    """
    Fetch and parse RSS/JSON feed into ParsedItem objects.

    Handles both RSS and JSON feed formats. Filters entries by cutoff date
    and extracts full article content where applicable.

    Args:
        category: Article category name
        source_name: Source identifier
        url: Feed URL (prefix with JSON| for JSON format)
        cutoff_date: Filter out entries older than this date

    Returns:
        List of ParsedItem objects
    """
    settings = get_settings()
    proxy = settings.network.azure_proxy

    spider = SpiderCore()
    results: list[ParsedItem] = []

    # Step 1: Download feed
    if url.startswith(JSON_PREFIX):
        feed_entries = _fetch_json_feed(url, source_name, proxy)
    else:
        feed_entries = _fetch_rss_feed(url, source_name, spider)

    # Guard clause: No entries found
    if not feed_entries:
        return []

    # Step 2: Process each entry
    for entry in feed_entries:
        # Guard clause: Skip entries without links
        link = getattr(entry, "link", None)
        if not link:
            continue

        # Check published date for RSS feeds
        if not url.startswith(JSON_PREFIX):
            published_time = _get_published_time(entry)
            if published_time and published_time < cutoff_date:
                continue

        # Extract content based on category
        if category == HOTNEWS_CATEGORY:
            final_content, content_hash = _extract_hotnews_content(entry)
        else:
            content_result = _extract_full_article_content(link, spider)
            # Guard clause: Skip if content extraction failed
            if not content_result:
                continue
            final_content, content_hash = content_result

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

    return results
