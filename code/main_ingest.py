# 文件路径：/app/code/ingest.py

"""Backward-compatible entrypoint.

Prefer running:
  - python -m news_crawler ingest
  - news-crawler ingest
"""

from news_crawler.ingest import main


if __name__ == "__main__":
    main()
