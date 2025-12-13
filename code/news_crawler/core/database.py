from __future__ import annotations

import sys
from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text, create_engine
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
    ai_tags = Column(String(255), nullable=True)
    is_ai_processed = Column(Boolean, default=False, index=True)
    category = Column(String(50), index=True, nullable=True)
    importance_score = Column(Integer, default=0, index=True)

    # 复合索引优化查询
    __table_args__ = (
        # AI处理查询：查找未处理的文章
        Index('ix_raw_news_ai_pending', 'is_ai_processed', postgresql_where=is_ai_processed == False),
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
    from news_crawler.core.bootstrap import bootstrap

    bootstrap()
    print("🔌 正在连接 Azure 数据库...")
    try:
        Base.metadata.create_all(get_engine())
        print("\n✅✅✅ 成功！数据库连接正常，表结构已同步！")
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        sys.exit(1)
