"""Core building blocks (settings, database, crawler, config, category strategies)."""

from news_crawler.core.category_strategies import (
    CategoryStrategy,
    CATEGORY_STRATEGIES,
    get_strategy,
)
from news_crawler.core.config import RSS_CATEGORIES, REPORT_CONFIGS
from news_crawler.core.settings import get_settings

__all__ = [
    "CategoryStrategy",
    "CATEGORY_STRATEGIES",
    "get_strategy",
    "RSS_CATEGORIES",
    "REPORT_CONFIGS",
    "get_settings",
]
