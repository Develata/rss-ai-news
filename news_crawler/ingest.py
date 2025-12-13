from __future__ import annotations

import os
import sys
import time

from news_crawler.core.bootstrap import bootstrap
from news_crawler.core.database import SessionLocal
from news_crawler.services.ai_service import process_new_summaries
from news_crawler.services.crawler_service import run_crawler_job
from news_crawler.services.email_service import send_notification

try:
    from news_crawler.utils.logger import logger
except ImportError:
    class FakeLogger:
        def info(self, msg):
            print(f"[INFO] {msg}")

        def error(self, msg):
            print(f"[ERROR] {msg}")

    logger = FakeLogger()


def main() -> None:
    bootstrap()

    start_time = time.time()
    sys.stdout.reconfigure(line_buffering=True)

    if SessionLocal is None:
        raise RuntimeError(
            "Database is not configured. Please create a .env and set DB_URI (or DB_HOST/DB_USER/DB_PASS/DB_PORT)."
        )

    logger.info(f"--- 🚜 启动采集与处理任务 (Time: {os.popen('date').read().strip()}) ---")

    new_raw_count = 0
    try:
        with SessionLocal() as session:
            new_raw_count = run_crawler_job(session)

        logger.info(f"📊 [Phase 1 Done] 新增原始文章: {new_raw_count} 篇")
    except Exception as e:
        err_msg = f"抓取阶段异常: {e}"
        logger.error(f"❌ [Phase 1 Failed] {err_msg}")
        try:
            send_notification("❌ 新闻系统报错 (Ingest)", err_msg)
        except Exception:
            pass

    processed_count = 0
    try:
        with SessionLocal() as session:
            processed_count = process_new_summaries(session)

        logger.info(f"📊 [Phase 2 Done] AI 处理完成: {processed_count} 篇")
    except Exception as e:
        logger.error(f"❌ [Phase 2 Failed] AI 处理中断: {e}")

    duration = time.time() - start_time
    logger.info(f"--- 🚜 采集任务结束 (耗时: {duration:.2f}s) ---")


if __name__ == "__main__":
    main()
