"""RSS feed connectivity and configuration tests.

This module tests:
- RSS category configuration
- Feed connectivity and availability
- Support for different feed formats (RSS, Atom, JSON)
"""

import pytest
import requests

from news_crawler.core.config import RSS_CATEGORIES
from news_crawler.core.crawler import SpiderCore


def test_rss_categories_are_configured():
    """Verify RSS categories are properly configured."""
    assert isinstance(RSS_CATEGORIES, dict)
    assert len(RSS_CATEGORIES) >= 5


def get_feed_params():
    """Generate test parameters for all configured feeds.

    Returns:
        List of tuples: [(category, name, url), ...]
    """
    params = []
    for cat, sources in RSS_CATEGORIES.items():
        for name, url in sources.items():
            params.append((cat, name, url))
    return params


@pytest.mark.live
@pytest.mark.parametrize("category, name, url", get_feed_params())
def test_rss_feed_connectivity(category, name, url):
    """Test connectivity for all configured RSS feeds.

    Run with: pytest -m live
    Tests both standard RSS/Atom feeds and JSON API endpoints.
    """
    spider = SpiderCore()

    # Note: Tests may fail without proxy configuration (set AZURE_PROXY)
    # pytest will show test name automatically, no need for print statements

    if url.startswith("JSON|"):
        # JSON API endpoint
        real_url = url.split("|")[1]
        try:
            resp = requests.get(real_url, timeout=10)
            assert resp.status_code == 200, f"JSON API {name} returned status {resp.status_code}"
        except requests.RequestException as e:
            pytest.fail(f"JSON API {name} connection failed: {e}")
    else:
        # Standard RSS/Atom feed
        try:
            content = spider.fetch(url)
            assert content is not None, f"RSS {name} returned empty content"
            assert len(content) > 50, f"RSS {name} content too short"
        except Exception as e:
            pytest.fail(f"RSS {name} connection failed: {e}")
