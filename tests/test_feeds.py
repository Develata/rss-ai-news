# 文件路径：/app/tests/test_feeds.py
import pytest
import requests
import os

from news_crawler.core.config import RSS_CATEGORIES


def test_rss_categories_are_configured():
    assert isinstance(RSS_CATEGORIES, dict)
    assert len(RSS_CATEGORIES) >= 5
from news_crawler.core.crawler import SpiderCore

# 扁平化配置，生成参数列表 [(category, name, url), ...]
def get_feed_params():
    params = []
    for cat, sources in RSS_CATEGORIES.items():
        for name, url in sources.items():
            params.append((cat, name, url))
    return params

@pytest.mark.live
@pytest.mark.parametrize("category, name, url", get_feed_params())
def test_rss_feed_connectivity(category, name, url):
    """
    [真实测试] 批量测试所有 RSS 源是否可达
    """
    spider = SpiderCore()
    
    # ✅ 现在这里不会报错了
    if not os.getenv('AZURE_PROXY'):
        print("⚠️ Warning: No Proxy configured, some feeds might fail.")

    print(f"Testing {name}...")
    
    if url.startswith("JSON|"):
        real_url = url.split("|")[1]
        try:
            resp = requests.get(real_url, timeout=10)
            assert resp.status_code == 200, f"JSON API {name} 返回状态码 {resp.status_code}"
        except Exception as e:
            pytest.fail(f"JSON API {name} 连接失败: {e}")
    else:
        try:
            content = spider.fetch(url)
            assert content is not None, f"RSS {name} 抓取内容为空"
            assert len(content) > 50, f"RSS {name} 内容过短"
        except Exception as e:
            pytest.fail(f"RSS {name} 连接异常: {e}")