"""
AI service module for article summarization and processing.

Provides functionality for:
- OpenAI API integration with retry logic
- Category-based article summarization with scoring
- Concurrent batch processing with memory optimization
- Rate limit handling and error recovery
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from openai import APIConnectionError, APIError, OpenAI, RateLimitError
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from news_crawler.core.category_strategies import get_strategy
from news_crawler.core.database import NewsArticle
from news_crawler.core.settings import get_settings
from news_crawler.utils.common import truncate_text

try:
    from news_crawler.utils.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


def _get_client() -> OpenAI | None:
    """
    Get configured OpenAI client.

    Returns:
        OpenAI client instance if API key is configured, None otherwise
    """
    settings = get_settings()
    if not settings.ai.api_key:
        return None
    return OpenAI(api_key=settings.ai.api_key, base_url=settings.ai.base_url)


def get_ai_summary(text: str, category: str = "通用") -> str:
    """
    Get AI-generated summary using category-specific strategy.

    Selects appropriate prompt template and input length based on category.
    Implements exponential backoff for rate limit errors.

    Args:
        text: Raw article content to summarize
        category: Article category for strategy selection

    Returns:
        AI-generated summary or error message
    """
    client = _get_client()
    if not client:
        return f"⚠️ API Key missing: {text[:200]}..."

    settings = get_settings()
    model_name = settings.ai.model
    base_delay = settings.ai.base_delay
    max_retries = settings.ai.max_retries

    # Get category strategy
    strategy = get_strategy(category)
    system_prompt = strategy.prompt
    max_input_chars = strategy.max_input_chars

    # Smart truncation of input text
    truncated_text = truncate_text(text, max_input_chars)

    last_err: Exception | None = None

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

        except RateLimitError as e:
            last_err = e
            backoff = base_delay * attempt
            logger.warning(
                f"API rate limit hit, retrying after {backoff:.1f}s "
                f"(attempt {attempt}/{max_retries})"
            )
            time.sleep(backoff)
            continue

        except APIConnectionError as e:
            last_err = e
            logger.error(f"API connection error: {e} | 💡 请检查网络连接或代理配置")
            return f"❌ 网络连接失败: {e.__class__.__name__}"

        except APIError as e:
            last_err = e
            err_msg = str(e)
            error_detail = f"❌ AI 请求失败: {e.__class__.__name__}: {err_msg}"
            if "api key" in err_msg.lower():
                error_detail += " | 💡 请检查 AI_API_KEY 配置"
            logger.error(error_detail)
            return error_detail

        except Exception as e:
            last_err = e
            logger.error(f"Unexpected error in AI request: {e}")
            return f"❌ 未知错误: {e.__class__.__name__}: {e}"

    return f"❌ AI Error after {max_retries} retries: {last_err.__class__.__name__}"


def get_custom_ai_response(user_text: str, system_prompt: str) -> str:
    """
    Get custom AI response with user-defined system prompt.

    Args:
        user_text: User input text (truncated to 4000 chars)
        system_prompt: Custom system prompt for AI behavior

    Returns:
        AI-generated response or error message
    """
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
    except (APIError, APIConnectionError) as e:
        logger.error(f"AI generation failed: {e}")
        return f"AI 生成失败: {e.__class__.__name__}"
    except Exception as e:
        logger.error(f"Unexpected error in custom AI response: {e}")
        return f"AI 生成失败: {e}"


def _extract_score_from_output(raw_output: str) -> int:
    """
    Extract importance score from AI output.

    Args:
        raw_output: Raw AI response text

    Returns:
        Score between 0-100, defaults to 50 if not found
    """
    score_match = re.search(r"(?:SCORE|分数)[^\d]*(\d+)", raw_output, re.IGNORECASE)
    if score_match:
        raw_score = int(score_match.group(1))
        return min(100, max(0, raw_score))
    return 50


def _extract_tags_from_output(raw_output: str) -> str:
    """
    Extract tags from AI output.

    Args:
        raw_output: Raw AI response text

    Returns:
        Comma-separated tags string, empty if not found
    """
    tags_match = re.search(r"(?:TAGS|标签)[\|\s:：]*([^\n\|]+)", raw_output, re.IGNORECASE)
    return tags_match.group(1).strip() if tags_match else ""


def _clean_summary_text(raw_output: str) -> str:
    """
    Clean and extract summary from AI output.

    Args:
        raw_output: Raw AI response text

    Returns:
        Cleaned summary text without tags/score markers
    """
    clean_summary = re.split(r"\|TAGS\||\|SCORE\|", raw_output)[0].strip()
    return clean_summary.strip('"').strip("'")


def _process_single_article_logic(
    art_id: int, content_text: str, category: str, title: str
) -> dict[str, Any]:
    """
    Process single article with AI summarization and scoring.

    Uses category-specific strategy for evaluation. Parses AI output
    to extract summary, tags, and importance score.

    Args:
        art_id: Article database ID
        content_text: Raw article content
        category: Article category name
        title: Article title

    Returns:
        Dict with processing status and extracted fields
    """
    try:
        raw_output = get_ai_summary(content_text, category)

        # Guard clause: Early exit for filtered articles
        if "PASS" in raw_output and len(raw_output) < 20:
            return {
                "id": art_id,
                "status": "filtered",
                "summary": "AI过滤：低价值",
                "tags": "",
                "score": 0,
                "raw": raw_output,
            }

        # Extract structured data from AI output
        score = _extract_score_from_output(raw_output)
        tags = _extract_tags_from_output(raw_output)
        clean_summary = _clean_summary_text(raw_output)

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
        logger.error(f"Error processing article {art_id}: {e}")
        return {"id": art_id, "status": "error", "error_msg": str(e)}


def _commit_with_error_handling(session: Session) -> None:
    """
    Commit session with specific error handling.

    Args:
        session: SQLAlchemy database session
    """
    try:
        session.commit()
    except IntegrityError as e:
        logger.error(f"Commit failed (IntegrityError): {e}")
        session.rollback()
    except OperationalError as e:
        logger.error(f"Commit failed (OperationalError): {e}")
        session.rollback()


def _update_article_from_result(article: NewsArticle, result: dict[str, Any]) -> bool:
    """
    Update article object based on AI processing result.

    Args:
        article: NewsArticle database object
        result: Processing result dictionary

    Returns:
        True if article was successfully updated, False on error
    """
    status = result["status"]

    if status == "success":
        article.summary = result["summary"]
        article.ai_tags = result["tags"]
        article.importance_score = result["score"]
        article.is_ai_processed = True
        category_hint = result.get("category", "")[:8]
        logger.debug(f"[{category_hint}] Score: {result['score']} | {result['title_preview']}...")
        return True

    if status == "filtered":
        article.summary = result["summary"]
        article.ai_tags = ""
        article.importance_score = 0
        article.is_ai_processed = True
        logger.debug(f"Filtered: {article.title[:15]}...")
        return True

    if status == "error":
        logger.error(f"Error processing article ID {result['id']}: {result.get('error_msg')}")
        return False

    return False


def process_new_summaries(session: Session, batch_size: int = 50, commit_every: int = 10) -> int:
    """
    Process unprocessed articles with AI using generator pattern.

    Batches articles by category and applies category-specific strategies.
    Uses concurrent processing for improved throughput.

    Args:
        session: SQLAlchemy database session
        batch_size: Number of articles to process per batch
        commit_every: Commit after this many successful updates

    Returns:
        Total number of successfully processed articles
    """
    total_success = 0
    total_errors = 0
    settings = get_settings()

    while True:
        # Query only IDs to minimize memory footprint
        article_ids = (
            session.query(NewsArticle.id)
            .filter(NewsArticle.is_ai_processed == False)  # noqa: E712
            .limit(batch_size)
            .all()
        )

        # Guard clause: No more articles to process
        if not article_ids:
            if total_success == 0:
                logger.info("No new articles to process")
            break

        # Load article details in batch
        ids = [aid[0] for aid in article_ids]
        articles = session.query(NewsArticle).filter(NewsArticle.id.in_(ids)).all()
        art_map = {art.id: art for art in articles}

        logger.info(
            f"Processing {len(articles)} articles with AI "
            f"(concurrency: {settings.ai.max_workers})"
        )

        success_count_this_round = 0
        with ThreadPoolExecutor(max_workers=settings.ai.max_workers) as executor:
            futures = []
            for art in articles:
                cat_name = art.category or "NetTech_Hardcore"
                strategy = get_strategy(cat_name)
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
                result = future.result()
                article = art_map[result["id"]]

                # Update article based on result
                if _update_article_from_result(article, result):
                    total_success += 1
                    success_count_this_round += 1
                else:
                    total_errors += 1

                # Periodic commit to avoid long transactions
                if success_count_this_round >= commit_every:
                    _commit_with_error_handling(session)
                    success_count_this_round = 0

        # Final commit for remaining articles
        _commit_with_error_handling(session)

    # Report processing statistics
    total_processed = total_success + total_errors
    if total_processed > 0:
        failure_rate = (total_errors / total_processed) * 100
        if failure_rate > 50:
            logger.warning(
                f"High AI failure rate: {failure_rate:.1f}% " f"({total_errors}/{total_processed})"
            )
        elif total_errors > 0:
            logger.info(
                f"AI processing completed with {total_errors} errors "
                f"({failure_rate:.1f}% failure rate)"
            )

    return total_success
