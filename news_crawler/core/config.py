"""板块配置（动态加载）。

新结构：每个板块一个 TOML 文件，位于 news_crawler/categories/*.toml。
这样增删板块只需要增删一个配置文件，不需要改 Python 代码。

为减少现有改动，本模块仍暴露：
- RSS_CATEGORIES: dict[category_key, dict[source_name, url]]
- REPORT_CONFIGS: dict[category_key, dict]
"""

from __future__ import annotations

from functools import lru_cache

from news_crawler.core.category_config_loader import load_category_configs


@lru_cache(maxsize=1)
def get_category_configs():
    return load_category_configs()


def _resolve_rsshub(url: str, rsshub_base_url: str) -> str:
    if "{RSSHUB}" not in url:
        return url
    return url.format(RSSHUB=rsshub_base_url)


@lru_cache(maxsize=1)
def _rsshub_base_url() -> str:
    try:
        from news_crawler.core.settings import get_settings

        rsshub = get_settings().network.rsshub_base_url or "http://127.0.0.1:1200"
        return rsshub.rstrip("/")
    except Exception:
        return "http://127.0.0.1:1200"


def _build_rss_categories() -> dict[str, dict[str, str]]:
    rsshub = _rsshub_base_url()
    out: dict[str, dict[str, str]] = {}
    for cfg in get_category_configs():
        out[cfg.key] = {name: _resolve_rsshub(url, rsshub) for name, url in cfg.rss.items()}
    return out


def _build_report_configs() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for cfg in get_category_configs():
        out[cfg.key] = {
            "title_prefix": cfg.report.title_prefix,
            "folder": cfg.report.folder,
            "description": cfg.report.description,
            "max_items": cfg.report.max_items,
            "excerpt_max_titles": cfg.report.excerpt_max_titles,
            "excerpt_prompt": cfg.report.excerpt_prompt,
            "badge_enabled": cfg.report.badge_enabled,
        }
    return out


# 保持兼容：现有代码仍从这里 import 这两个变量
RSS_CATEGORIES = _build_rss_categories()
REPORT_CONFIGS = _build_report_configs()
