import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from datetime import datetime, timedelta, timezone
from typing import Generator, List

from sqlalchemy.exc import SQLAlchemyError

from news_crawler.core.config import RSS_CATEGORIES
from news_crawler.core.database import NewsArticle
from news_crawler.utils.common import chunker
from news_crawler.workers.crawler_worker import fetch_and_parse_feed

try:
    from news_crawler.utils.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def fetch_with_delay(category, source_name, url, cutoff_date):
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
        logger.error(f"❌ fetch_and_parse_feed error [{category}/{source_name}]: {e}")
        return []


def _items_to_articles_generator(items: List, existing_links: set, existing_hashes: set) -> Generator[NewsArticle, None, None]:
    """
    生成器模式：将抓取到的items逐个转换为NewsArticle对象。
    避免一次性创建所有对象占用大量内存。
    """
    seen_links = set()
    for item in items:
        # 跳过重复链接
        if item.link in existing_links or item.link in seen_links:
            continue
        # 跳过重复内容哈希
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


def run_crawler_job(session, batch_size: int = 100, wait_timeout: int = 300) -> int:
    """
    执行RSS抓取任务，使用生成器模式优化内存占用。
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
        logger.info("😴 No items found.")
        return 0

    logger.info(f"📥 Downloaded {len(all_items)} items. DB Deduplicating...")

    # 批量查询已存在的链接和哈希（内存优化：分批查询）
    incoming_links = [item.link for item in all_items]
    incoming_hashes = [item.content_hash for item in all_items]

    existing_link_set = set()
    existing_hash_set = set()

    for chunk in chunker(incoming_links, 500):
        if not chunk:
            continue
        res = session.query(NewsArticle.link).filter(NewsArticle.link.in_(chunk)).all()
        existing_link_set.update(r[0] for r in res)

    for chunk in chunker(incoming_hashes, 500):
        if not chunk:
            continue
        res = (
            session.query(NewsArticle.content_hash)
            .filter(NewsArticle.content_hash.in_(chunk))
            .all()
        )
        existing_hash_set.update(r[0] for r in res)

    # 使用生成器模式批量保存
    new_count = 0
    batch_buffer = []

    for article in _items_to_articles_generator(all_items, existing_link_set, existing_hash_set):
        batch_buffer.append(article)
        
        if len(batch_buffer) >= batch_size:
            try:
                session.add_all(batch_buffer)
                session.commit()
                new_count += len(batch_buffer)
                logger.info(f"📝 Committed batch of {len(batch_buffer)} articles")
            except SQLAlchemyError as e:
                logger.error(f"❌ Batch Insert Failed: {e}")
                session.rollback()
            batch_buffer = []

    # 处理剩余的文章
    if batch_buffer:
        try:
            session.add_all(batch_buffer)
            session.commit()
            new_count += len(batch_buffer)
        except SQLAlchemyError as e:
            logger.error(f"❌ Final Batch Insert Failed: {e}")
            session.rollback()

    logger.info(
        f"⚡ Crawl finished in {time.time() - start_time:.2f}s. "
        f"Staged {new_count} new articles."
    )
    return new_count
