import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from news_crawler.core.settings import get_settings


def setup_logger(name="news_crawler"):
    """配置并返回一个全局 logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    settings = get_settings()
    log_dir = settings.runtime.log_dir

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y-%m-%d"

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
