from __future__ import annotations

import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from news_crawler.core.settings import get_settings

Base = declarative_base()


class NewsArticle(Base):
    __tablename__ = "raw_news"

    id = Column(Integer, primary_key=True)
    title = Column(String(512), nullable=False)
    link = Column(String(1024), unique=True, nullable=False)
    content_hash = Column(String(64), index=True)
    content_text = Column(Text)
    source = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    summary = Column(Text, nullable=True)
    # 🔥 使用 Text 类型防止 AI 生成的标签过多导致 Data too long 错误
    ai_tags = Column(Text, nullable=True)
    is_ai_processed = Column(Boolean, default=False, index=True)
    category = Column(String(50), index=True, nullable=True)
    importance_score = Column(Integer, default=0, index=True)

    # 复合索引优化查询
    __table_args__ = (
        # AI处理查询：查找未处理的文章
        Index('ix_raw_news_ai_pending', 'is_ai_processed', postgresql_where=is_ai_processed.is_(False)),
        # 报表查询：按分类+时间+分数查询
        Index('ix_raw_news_report', 'category', 'created_at', 'importance_score'),
    )


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    db_uri = settings.db.build_uri()
    if not db_uri:
        raise RuntimeError(
            "Database is not configured. Please set DB_URI or (DB_HOST/DB_USER/DB_PASS/DB_PORT)."
        )

    parsed = urlparse(db_uri)
    is_sqlite = parsed.scheme.startswith("sqlite")

    if is_sqlite:
        # 尝试创建 SQLite 文件目录（:memory: 不处理）
        if parsed.path and parsed.path not in ("/", "/:memory:") and ":memory:" not in db_uri:
            # sqlite 绝对路径通常形如 sqlite:////abs/path.db 或 sqlite+pysqlite:////abs/path.db
            # urlparse 会把路径放在 .path，去掉前导 '/' 后再当作文件路径处理
            candidate = parsed.path
            # 对于 sqlite:////abs/path.db，parsed.path 为 '//abs/path.db'
            while candidate.startswith("/"):
                candidate = candidate[1:]
            if candidate:
                path = Path("/" + candidate)
                path.parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(
            db_uri,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )

        # 🔥 SQLite 性能优化核心逻辑
        # 开启 WAL (Write-Ahead Logging) 模式，大幅提升并发写入性能
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            # NORMAL 模式在 WAL 下是安全的，且比 FULL 快很多
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

        # SQLite 模式下自动建表，实现“开箱即用”
        Base.metadata.create_all(engine)
        return engine

    # PostgreSQL / 其他数据库
    return create_engine(
        db_uri,
        pool_size=5,
        pool_recycle=1800,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )


def _try_create_sessionmaker():
    try:
        engine = get_engine()
    except Exception:
        return None
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


SessionLocal = _try_create_sessionmaker()

try:
    engine = get_engine()
except Exception:
    engine = None


if __name__ == "__main__":
    import logging

    from news_crawler.core.bootstrap import bootstrap

    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)

    bootstrap()
    logger.info("Testing database connection...")
    try:
        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("✓ Database connection successful, tables synced!")

        # 简单检查 WAL 是否生效 (仅针对 SQLite)
        if str(engine.url).startswith("sqlite"):
            with engine.connect() as conn:
                mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
                logger.info(f"SQLite Journal Mode: {mode} (Expected: wal)")

    except Exception as e:
        logger.error(f"Connection failed: {e}")
        sys.exit(1)
