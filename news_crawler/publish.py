from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import sessionmaker

from news_crawler.core.bootstrap import bootstrap
from news_crawler.core.database import NewsArticle, get_engine
from news_crawler.services.email_service import send_notification
from news_crawler.services.report_service import run_publishing_job

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
    logger.info(f"--- 📰 启动日报发布任务 (Time: {os.popen('date').read().strip()}) ---")

    published_count = 0

    try:
        Session = sessionmaker(bind=get_engine())
        with Session() as session:
            published_count = run_publishing_job(session)
        logger.info(f"✅ [Phase 3 Done] 报告推送完成: {published_count} 份")

    except Exception as e:
        err_msg = f"发布阶段失败: {e}"
        logger.error(f"❌ [Phase 3 Failed] {err_msg}")
        try:
            send_notification("❌ 爬虫发布失败", err_msg)
        except Exception:
            pass
        sys.exit(1)

    if published_count > 0:
        try:
            Session = sessionmaker(bind=get_engine())
            with Session() as session:
                time_window = datetime.now(timezone.utc) - timedelta(hours=24)

                new_raw_count = (
                    session.query(NewsArticle)
                    .filter(NewsArticle.created_at >= time_window)
                    .count()
                )

                ai_processed_count = (
                    session.query(NewsArticle)
                    .filter(
                        NewsArticle.is_ai_processed == True,
                        NewsArticle.created_at >= time_window,
                    )
                    .count()
                )

                send_notification(
                    f"✅ 日报发布成功 ({published_count}份)",
                    "过去24小时数据统计：\n"
                    f"新增文章: {new_raw_count} 篇\n"
                    f"AI处理: {ai_processed_count} 篇\n\n"
                    "详情请查看 GitHub Pages。",
                )
        except Exception as e:
            logger.error(f"❌ 邮件统计查询失败: {e}")
            send_notification(f"✅ 日报发布成功 ({published_count}份)", "统计数据查询异常，但文件已推送。")
    else:
        logger.info("😴 [Phase 3 Skipped] 今日无内容发布，不发送邮件。")

    duration = time.time() - start_time
    logger.info(f"--- 📰 发布任务结束 (耗时: {duration:.2f}s) ---")


if __name__ == "__main__":
    main()
