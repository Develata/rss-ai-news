import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from sqlalchemy.exc import SQLAlchemyError

from news_crawler.core.category_strategies import get_strategy
from news_crawler.core.database import NewsArticle
from news_crawler.core.settings import get_settings
from news_crawler.utils.common import truncate_text


def _get_client():
    settings = get_settings()
    if not settings.ai.api_key:
        return None
    return OpenAI(api_key=settings.ai.api_key, base_url=settings.ai.base_url)


def get_ai_summary(text: str, category: str = "通用") -> str:
    """
    使用分类策略获取AI摘要。
    根据category选择对应的prompt模板和最大输入字符数。
    """
    client = _get_client()
    if not client:
        return f"⚠️ API Key missing: {text[:200]}..."

    settings = get_settings()
    model_name = settings.ai.model
    base_delay = settings.ai.base_delay
    max_retries = settings.ai.max_retries

    # 获取分类策略
    strategy = get_strategy(category)
    system_prompt = strategy.prompt
    max_input_chars = strategy.max_input_chars

    # 智能截断输入文本
    truncated_text = truncate_text(text, max_input_chars)

    last_err = None

    for attempt in range(1, max_retries + 1):
        try:
            start_ts = time.time()
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": truncated_text},
                ],
                temperature=0.3,
            )
            elapsed = time.time() - start_ts
            if base_delay > 0 and elapsed < base_delay:
                time.sleep(base_delay - elapsed)

            return response.choices[0].message.content.strip()

        except Exception as e:
            err_msg = str(e)
            last_err = e

            if (
                "rate limit" in err_msg.lower()
                or "429" in err_msg
                or "quota" in err_msg.lower()
            ):
                backoff = base_delay * attempt
                time.sleep(backoff)
                continue
            else:
                return f"❌ AI Error: {e.__class__.__name__}: {err_msg}"

    return f"❌ AI Error: {last_err.__class__.__name__}: {last_err}"


def get_custom_ai_response(user_text: str, system_prompt: str) -> str:
    client = _get_client()
    if not client:
        return "AI配置缺失。"
    try:
        settings = get_settings()
        response = client.chat.completions.create(
            model=settings.ai.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text[:4000]},
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI 生成失败: {e}"


def _process_single_article_logic(art_id, content_text, category, title):
    """处理单篇文章的AI摘要逻辑，使用分类策略进行评分。"""
    strategy = get_strategy(category)
    try:
        raw_output = get_ai_summary(content_text, category)

        if "PASS" in raw_output and len(raw_output) < 20:
            return {
                "id": art_id,
                "status": "filtered",
                "summary": "AI过滤：低价值",
                "tags": "",
                "score": 0,
                "raw": raw_output,
            }

        tags = ""
        score = 50

        score_match = re.search(r"(?:SCORE|分数)[^\d]*(\d+)", raw_output, re.IGNORECASE)
        if score_match:
            raw_score = int(score_match.group(1))
            # 应用分类权重进行加权计算（如有多维度评分）
            score = min(100, max(0, raw_score))

        tags_match = re.search(
            r"(?:TAGS|标签)[\|\s:：]*([^\n\|]+)", raw_output, re.IGNORECASE
        )
        if tags_match:
            tags = tags_match.group(1).strip()

        clean_summary = re.split(r"\|TAGS\||\|SCORE\|", raw_output)[0].strip()
        clean_summary = clean_summary.strip('"').strip("'")

        return {
            "id": art_id,
            "status": "success",
            "summary": clean_summary,
            "tags": tags,
            "score": score,
            "title_preview": title[:15],
            "category": category,
        }

    except Exception as e:
        return {"id": art_id, "status": "error", "error_msg": str(e)}


def process_new_summaries(session, batch_size: int = 50, commit_every: int = 10) -> int:
    """
    处理未AI处理的文章，使用生成器模式减少内存占用。
    按分类分批处理，每个分类使用对应的策略。
    """
    total_success = 0

    while True:
        # 使用生成器模式：只查询ID，避免一次性加载所有文章到内存
        article_ids = (
            session.query(NewsArticle.id)
            .filter(NewsArticle.is_ai_processed == False)
            .limit(batch_size)
            .all()
        )

        if not article_ids:
            if total_success == 0:
                print(" 💤 No new articles to process.")
            break

        # 分批加载文章详情
        ids = [aid[0] for aid in article_ids]
        articles = session.query(NewsArticle).filter(NewsArticle.id.in_(ids)).all()

        art_map = {art.id: art for art in articles}
        settings = get_settings()
        print(
            f" 🚀 Processing {len(articles)} articles with AI (Concurrency: {settings.ai.max_workers})..."
        )

        success_count_this_round = 0
        with ThreadPoolExecutor(max_workers=settings.ai.max_workers) as executor:
            futures = []
            for art in articles:
                cat_name = art.category if art.category else "NetTech_Hardcore"
                strategy = get_strategy(cat_name)
                # 使用策略的max_input_chars进行预截断
                truncated_content = truncate_text(art.content_text, strategy.max_input_chars)
                futures.append(
                    executor.submit(
                        _process_single_article_logic,
                        art.id,
                        truncated_content,
                        cat_name,
                        art.title,
                    )
                )

            for future in as_completed(futures):
                res = future.result()
                art = art_map[res["id"]]

                if res["status"] == "success":
                    art.summary = res["summary"]
                    art.ai_tags = res["tags"]
                    art.importance_score = res["score"]
                    art.is_ai_processed = True
                    category_hint = res.get("category", "")[:8]
                    print(f" ✅ [{category_hint}] Score: {res['score']} | {res['title_preview']}...")
                    total_success += 1
                    success_count_this_round += 1

                elif res["status"] == "filtered":
                    art.summary = res["summary"]
                    art.ai_tags = ""
                    art.importance_score = 0
                    art.is_ai_processed = True
                    print(f" 🗑️ [Filtered] {art.title[:15]}...")
                    total_success += 1
                    success_count_this_round += 1

                elif res["status"] == "error":
                    print(
                        f" ❌ Error processing ID {res['id']}: {res.get('error_msg')}"
                    )

                if success_count_this_round >= commit_every:
                    try:
                        session.commit()
                    except SQLAlchemyError as e:
                        print(f" ❌ Commit failed during AI processing: {e}")
                        session.rollback()
                    success_count_this_round = 0

        try:
            session.commit()
        except SQLAlchemyError as e:
            print(f" ❌ Commit failed at end of batch: {e}")
            session.rollback()

    return total_success
