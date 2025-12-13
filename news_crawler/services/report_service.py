from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from news_crawler.core.config import REPORT_CONFIGS
from news_crawler.core.database import NewsArticle
from news_crawler.services.ai_service import get_custom_ai_response
from news_crawler.services.publisher_service import GitHubPublisher

try:
    from news_crawler.utils.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def generate_excerpt(articles, title_prefix):
    if not articles:
        return "本期无内容。"

    titles_list = "\n".join([f"- {art.title}" for art in articles[:15]])

    system_prompt = (
        f"你是一个科技新闻主编。请根据以下【{title_prefix}】板块的新闻标题列表，"
        "写一段简短的日报导读（Excerpt）。要求语气专业客观，80字以内。"
    )

    try:
        excerpt = get_custom_ai_response(titles_list, system_prompt)
        if not excerpt:
            return "今日科技热点速览。"
        return excerpt.replace('"', "").replace("'", "")
    except Exception as e:
        logger.warning(f"⚠️ 生成导读失败: {e}")
        return "今日科技热点速览。"


def generate_md_content(articles, config):
    if not articles:
        return None

    tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(tz)
    date_str = f"{now.year}-{now.month}-{now.day}"

    excerpt_text = generate_excerpt(articles, config["title_prefix"])
    if not excerpt_text:
        excerpt_text = "暂无摘要"

    raw_title = f"{config['title_prefix']} {date_str}"

    safe_title = raw_title.replace('"', "\\\"").strip()
    safe_excerpt = excerpt_text.replace('"', "\\\"").replace("\n", " ").strip()

    md = [
        "---",
        f'title: "{safe_title}"',
        f"date: {date_str}",
        f'excerpt: "{safe_excerpt}"',
        "---",
        "",
        f"# {safe_title}\n",
        f"> {excerpt_text}\n",
    ]

    for art in articles:
        title = (
            art.title.replace("|", "-")
            .replace("[", "(")
            .replace("]", ")")
            .strip()
        )

        tags = "".join(
            [f"`{t.strip()}` " for t in (art.ai_tags or "").split(",") if t.strip()]
        )

        md.append(
            f"## {title} <Badge type=\"tip\" text=\"{art.importance_score}\" />\n"
        )
        if tags:
            md.append(f"- **Tags:** {tags}\n")

        md.append(f"- **Source:** `{art.source}` | [阅读原文]({art.link})\n")

        summary_text = art.summary if art.summary else "暂无摘要"
        md.append(f"> {summary_text}\n\n")
        md.append("---\n")

    return "\n".join(md)


def run_publishing_job(session):
    publisher = GitHubPublisher()
    published_count = 0

    tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(tz)
    current_year = str(now.year)
    current_date_file = now.strftime("%Y%m%d")

    time_window = datetime.now(timezone.utc) - timedelta(hours=25)
    
    # 优化：一次查询获取所有分类的文章，减少数据库往返
    all_articles = (
        session.query(NewsArticle)
        .filter(
            NewsArticle.created_at >= time_window,
            NewsArticle.is_ai_processed == True,
            NewsArticle.category.in_(list(REPORT_CONFIGS.keys())),
        )
        .order_by(
            NewsArticle.category,
            NewsArticle.importance_score.desc(),
            NewsArticle.created_at.desc(),
        )
        .all()
    )
    
    # 按分类分组
    articles_by_category = {}
    for art in all_articles:
        if art.category not in articles_by_category:
            articles_by_category[art.category] = []
        if len(articles_by_category[art.category]) < 10:  # 每个分类最多10条
            articles_by_category[art.category].append(art)

    for category_key, cfg in REPORT_CONFIGS.items():
        try:
            articles = articles_by_category.get(category_key, [])

            if articles:
                logger.info(
                    f"    ✅ Generating {cfg['title_prefix']} ({len(articles)} items)"
                )
                content = generate_md_content(articles, cfg)

                folder_name = cfg.get("folder", "Other")
                file_path = f"{folder_name}/{current_year}/{current_date_file}.md"

                publisher.push_markdown(file_path, content)
                published_count += 1
            else:
                logger.info(
                    f"    😴 Skipped {cfg['title_prefix']} (No content processed today)"
                )

        except Exception as e:
            logger.error(f"    ❌ Error generating report for [{category_key}]: {e}")
            continue

    return published_count
