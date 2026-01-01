"""
Crawler service module for fetching and processing RSS feeds.

This module provides functionality for:
- Concurrent RSS feed fetching with rate limiting
- Memory-efficient article deduplication
- Batch database insertion with error handling
"""

import random
import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from news_crawler.core.config import RSS_CATEGORIES
from news_crawler.core.database import NewsArticle
from news_crawler.utils.common import chunker
from news_crawler.workers.crawler_worker import fetch_and_parse_feed

try:
    from news_crawler.utils.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def fetch_with_delay(category: str, source_name: str, url: str, cutoff_date: datetime) -> list:
    """
    Fetch RSS feed with random delay for rate limiting.

    Args:
        category: Category name for the feed
        source_name: Source identifier
        url: RSS feed URL
        cutoff_date: Cutoff date for filtering articles

    Returns:
        List of parsed feed items, empty list on error
    """
    sleep_time = random.uniform(1.5, 4.0)
    logger.info(f"🕸️ Start fetch: {category}/{source_name} (sleep {sleep_time:.2f}s)")
    time.sleep(sleep_time)

    try:
        items = fetch_and_parse_feed(category, source_name, url, cutoff_date)
        logger.info(
            f"✅ Done fetch: {category}/{source_name}, got {len(items) if items else 0} items"
        )
        return items
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"❌ 抓取失败 [{category}/{source_name}]")
        logger.error(f"   错误类型: {error_type}")
        logger.error(f"   错误信息: {e}")
        logger.error(f"   源地址: {url}")
        return []


def _items_to_articles_generator(
    items: list, existing_links: set[str], existing_hashes: set[str]
) -> Generator[NewsArticle, None, None]:
    """
    Convert feed items to NewsArticle objects using generator pattern.

    Avoids creating all objects at once to reduce memory footprint.
    Filters out duplicates based on existing links and content hashes.

    Args:
        items: List of parsed feed items
        existing_links: Set of existing article links in database
        existing_hashes: Set of existing content hashes in database

    Yields:
        NewsArticle objects for new, non-duplicate items
    """
    seen_links: set[str] = set()
    for item in items:
        # Skip duplicate links
        if item.link in existing_links or item.link in seen_links:
            continue
        # Skip duplicate content hashes
        if item.content_hash in existing_hashes:
            continue

        seen_links.add(item.link)
        yield NewsArticle(
            title=item.title,
            link=item.link,
            source=item.source_name,
            content_text=item.content_text,
            content_hash=item.content_hash,
            created_at=item.created_at,
            category=item.category,
            is_ai_processed=False,
        )


def _fetch_existing_values(
    session: Session, values: list[str], column, chunk_size: int = 500
) -> set[str]:
    """
    Fetch existing values from database in batches to optimize memory.

    Args:
        session: SQLAlchemy database session
        values: List of values to check (links or hashes)
        column: Database column to query (NewsArticle.link or NewsArticle.content_hash)
        chunk_size: Batch size for chunked queries

    Returns:
        Set of existing values found in database
    """
    existing_set: set[str] = set()
    for chunk in chunker(values, chunk_size):
        if not chunk:
            continue
        results = session.query(column).filter(column.in_(chunk)).all()
        existing_set.update(r[0] for r in results)
    return existing_set


def _commit_articles_in_batches(session: Session, batch_buffer: list[NewsArticle]) -> int:
    """
    Commit a batch of articles to database with error handling.

    Args:
        session: SQLAlchemy database session
        batch_buffer: List of NewsArticle objects to commit

    Returns:
        Number of successfully committed articles, 0 on error
    """
    if not batch_buffer:
        return 0

    try:
        session.add_all(batch_buffer)
        session.commit()
        logger.info(f"📝 Committed batch of {len(batch_buffer)} articles")
        return len(batch_buffer)
    except IntegrityError as e:
        logger.error(f"❌ Batch Insert Failed (Integrity): {e}")
        session.rollback()
        return 0
    except OperationalError as e:
        logger.error(f"❌ Batch Insert Failed (Operational): {e}")
        session.rollback()
        return 0


def run_crawler_job(session: Session, batch_size: int = 100, wait_timeout: int = 300) -> int:
    """
    Execute RSS feed crawling job with memory-optimized processing.

    Fetches articles from all configured RSS sources concurrently,
    deduplicates against existing database records, and saves new
    articles in batches.

    Args:
        session: SQLAlchemy database session
        batch_size: Number of articles per batch commit (default: 100)
        wait_timeout: Maximum seconds to wait for all tasks (default: 300)

    Returns:
        Number of new articles successfully saved to database
    """
    start_time = time.time()
    logger.info("🚀 Starting Concurrent Crawler (Memory Optimized)...")

    cutoff_date = datetime.now(timezone.utc) - timedelta(hours=48)
    tasks = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        for category, sources in RSS_CATEGORIES.items():
            for source_name, url in sources.items():
                tasks.append(
                    executor.submit(
                        fetch_with_delay,
                        category,
                        source_name,
                        url,
                        cutoff_date,
                    )
                )

        all_items = []
        logger.info(f"⏳ Waiting for {len(tasks)} tasks... (timeout={wait_timeout}s)")

        try:
            for future in as_completed(tasks, timeout=wait_timeout):
                try:
                    res = future.result()
                    if res:
                        all_items.extend(res)
                except Exception as e:
                    logger.warning(f"⚠️ A task failed: {e}")
        except TimeoutError:
            logger.error(
                f"⏰ Crawler tasks did not finish within {wait_timeout} seconds, skip remaining tasks."
            )

    if not all_items:
        logger.warning("😴 No items found from any source.")
        # Check if all tasks failed
        failed_tasks = sum(1 for t in tasks if t.done() and t.exception())
        if failed_tasks == len(tasks) and len(tasks) > 0:
            logger.error(
                f"❌ All {len(tasks)} crawler tasks failed. This may indicate a critical issue."
            )
        return 0

    logger.info(f"📥 Downloaded {len(all_items)} items. DB Deduplicating...")

    # Batch query existing links and hashes for memory optimization
    incoming_links = [item.link for item in all_items]
    incoming_hashes = [item.content_hash for item in all_items]

    existing_link_set = _fetch_existing_values(session, incoming_links, NewsArticle.link)
    existing_hash_set = _fetch_existing_values(session, incoming_hashes, NewsArticle.content_hash)

    # Use generator pattern for batch saving
    new_count = 0
    batch_buffer: list[NewsArticle] = []

    for article in _items_to_articles_generator(all_items, existing_link_set, existing_hash_set):
        batch_buffer.append(article)

        if len(batch_buffer) >= batch_size:
            new_count += _commit_articles_in_batches(session, batch_buffer)
            batch_buffer = []

    # Commit remaining articles
    new_count += _commit_articles_in_batches(session, batch_buffer)

    logger.info(
        f"⚡ Crawl finished in {time.time() - start_time:.2f}s. "
        f"Staged {new_count} new articles."
    )
    return new_count
