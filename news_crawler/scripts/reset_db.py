import logging

from news_crawler.core.bootstrap import bootstrap
from news_crawler.core.database import NewsArticle, get_engine

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

bootstrap()


if __name__ == "__main__":
    logger.warning("Dropping raw_news table...")
    try:
        NewsArticle.__table__.drop(get_engine())
        logger.info("✓ Table dropped successfully! Old data cleared.")
    except Exception as e:
        logger.error(f"Failed to drop table (may not exist): {e}")
