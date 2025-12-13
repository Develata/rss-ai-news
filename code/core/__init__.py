"""Compatibility layer.

This project has been namespaced under news_crawler.*.
Keep these re-exports so existing imports keep working.
"""

from news_crawler.core.config import *  # noqa: F401,F403
from news_crawler.core.crawler import *  # noqa: F401,F403
from news_crawler.core.database import *  # noqa: F401,F403
from news_crawler.core.bootstrap import *  # noqa: F401,F403
from news_crawler.core.settings import *  # noqa: F401,F403
