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
    import logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)


def main() -> None:
    bootstrap()

    start_time = time.time()
    sys.stdout.reconfigure(line_buffering=True)

    if SessionLocal is None:
        logger.error("❌ 数据库未配置")
        logger.error("   请在 .env 文件中配置以下任一项:")
        logger.error("   - DB_URI (PostgreSQL 完整连接串)")
        logger.error("   - 或设置 DB_BACKEND=sqlite 使用 SQLite")
        logger.error("   💡 示例: DB_URI=postgresql://user:pass@localhost:5432/dbname")
        sys.exit(1)

    logger.info(f"--- 🚜 启动采集与处理任务 (Time: {os.popen('date').read().strip()}) ---")

    # 错误统计
    has_critical_error = False
    new_raw_count = 0

    try:
        with SessionLocal() as session:
            new_raw_count = run_crawler_job(session)

        logger.info(f"📊 [Phase 1 Done] 新增原始文章: {new_raw_count} 篇")
    except Exception as e:
        err_msg = f"抓取阶段异常: {e}"
        logger.error(f"❌ [Phase 1 Failed] {err_msg}")
        has_critical_error = True
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
        has_critical_error = True

    duration = time.time() - start_time
    logger.info(f"--- 🚜 采集任务结束 (耗时: {duration:.2f}s) ---")

    # 返回错误码：确保 Docker/Cron 能检测到失败
    if has_critical_error:
        logger.error("❌ 任务执行过程中发生严重错误，返回退出码 1")
        sys.exit(1)


if __name__ == "__main__":
    main()
