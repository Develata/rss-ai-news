"""Backward-compatible entrypoint.

Prefer running:
  - python -m news_crawler publish
  - news-crawler publish
"""

from news_crawler.publish import main

if __name__ == "__main__":
    main()