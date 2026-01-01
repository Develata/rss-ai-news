import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


def generate_excerpt(articles, config):
    if not articles:
        return "本期无内容。"

    max_titles = int(config.get("excerpt_max_titles") or 15)
    titles_list = "\n".join([f"- {art.title}" for art in articles[:max_titles]])

    system_prompt = (config.get("excerpt_prompt") or "").strip()
    if not system_prompt:
        system_prompt = (
            f"你是一个科技新闻主编。请根据以下【{config['title_prefix']}】板块的新闻标题列表，"
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

    excerpt_text = generate_excerpt(articles, config)
    if not excerpt_text:
        excerpt_text = "暂无摘要"

    raw_title = f"{config['title_prefix']} {date_str}"

    safe_title = raw_title.replace('"', '\\"').strip()
    safe_excerpt = excerpt_text.replace('"', '\\"').replace("\n", " ").strip()

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

    badge_enabled = bool(config.get("badge_enabled", True))

    for art in articles:
        title = art.title.replace("|", "-").replace("[", "(").replace("]", ")").strip()

        tags = "".join([f"`{t.strip()}` " for t in (art.ai_tags or "").split(",") if t.strip()])

        if badge_enabled:
            md.append(f'## {title} <Badge type="tip" text="{art.importance_score}" />\n')
        else:
            md.append(f"## {title}\n")
        if tags:
            md.append(f"- **Tags:** {tags}\n")

        md.append(f"- **Source:** `{art.source}` | [阅读原文]({art.link})\n")

        summary_text = art.summary if art.summary else "暂无摘要"
        md.append(f"> {summary_text}\n\n")
        md.append("---\n")

    return "\n".join(md)


def run_publishing_job(session):
    publisher = GitHubPublisher()
    local_root = (os.getenv("REPORT_LOCAL_DIR") or "./data/news").strip() or "./data/news"
    local_root_path = Path(local_root)

    # 1. 准备环境
    tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(tz)
    current_year = str(now.year)
    current_date_file = now.strftime("%Y%m%d")
    time_window = datetime.now(timezone.utc) - timedelta(hours=25)

    # 2. 查询数据
    all_articles = (
        session.query(NewsArticle)
        .filter(
            NewsArticle.created_at >= time_window,
            NewsArticle.is_ai_processed.is_(True),
            NewsArticle.category.in_(list(REPORT_CONFIGS.keys())),
        )
        .order_by(
            NewsArticle.category,
            NewsArticle.importance_score.desc(),
            NewsArticle.created_at.desc(),
        )
        .all()
    )

    # 3. 数据分组
    articles_by_category = {}
    for art in all_articles:
        if art.category not in articles_by_category:
            articles_by_category[art.category] = []
        articles_by_category[art.category].append(art)

    # 4. 生成内容并暂存
    pending_updates = []  # [{"path": "...", "content": "..."}]
    generated_titles = []

    for category_key, cfg in REPORT_CONFIGS.items():
        try:
            max_items = int(cfg.get("max_items") or 10)
            articles = articles_by_category.get(category_key, [])[:max_items]
            if articles:
                logger.info(
                    f"    🛠️ Generating MD for {cfg['title_prefix']} ({len(articles)} items)..."
                )

                content = generate_md_content(articles, cfg)
                folder_name = cfg.get("folder", "Other")
                file_path = f"{folder_name}/{current_year}/{current_date_file}.md"

                pending_updates.append({"path": file_path, "content": content})
                generated_titles.append(cfg["title_prefix"])
            else:
                logger.info(f"    😴 Skipped {cfg['title_prefix']}")

        except Exception as e:
            logger.error(f"    ❌ 生成日报失败 [{category_key}]")
            logger.error(f"       错误类型: {type(e).__name__}")
            logger.error(f"       错误信息: {e}")
            logger.error("       💡 该分类将被跳过，不影响其他分类")
            continue

    # 5. 本地落盘（与上传后的相同相对路径结构），不影响后续推送
    if pending_updates:
        try:
            for item in pending_updates:
                rel_path = (item.get("path") or "").lstrip("/\\")
                out_path = (local_root_path / rel_path).resolve()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(item.get("content") or "", encoding="utf-8")
            logger.info(f"💾 本地已保存 {len(pending_updates)} 个 Markdown 到 {local_root_path}")
        except Exception as e:
            logger.warning(f"⚠️ 本地保存 Markdown 失败（不影响推送）：{e}")

    # 6. 一次性推送 (One Commit)
    published_count = len(pending_updates)
    if published_count > 0:
        try:
            # 构造 Commit Message
            commit_msg = (
                f"🤖 Bot Update: {current_date_file} Report ({', '.join(generated_titles)})"
            )

            # 调用批量推送
            publisher.publish_changes(pending_updates, commit_msg)

        except ValueError as e:
            # GitHub 配置或认证错误
            logger.error("❌ GitHub 配置错误")
            logger.error(f"   {e}")
            return 0
        except RuntimeError as e:
            # GitHub API 操作错误
            logger.error("❌ GitHub 推送失败")
            logger.error(f"   {e}")
            return 0
        except Exception as e:
            # 其他未预期的错误
            logger.error(f"❌ 发布失败: {type(e).__name__}")
            logger.error(f"   错误详情: {e}")
            logger.error("   💡 请检查网络连接和 GitHub 配置")
            return 0

    return published_count
