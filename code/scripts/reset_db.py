from news_crawler.core.bootstrap import bootstrap
from news_crawler.core.database import NewsArticle, get_engine

bootstrap()


if __name__ == "__main__":
    print("⚠️ 正在删除 raw_news 表...")
    try:
        NewsArticle.__table__.drop(get_engine())
        print("✅ 删除成功！旧数据已清空。")
    except Exception as e:
        print(f"❌ 删除失败 (可能是表不存在): {e}")