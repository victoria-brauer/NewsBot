"""Публикация новостей в Telegram.
Этот модуль можно запускать как скрипт:
    python -m app.telegram.publisher
"""

from __future__ import annotations

import asyncio
import html
import logging
import json
from datetime import datetime

from app.config import settings
from app.news_parser import collect_from_all_sources
from app.redis_client import get_redis_client
from app.schemas import NewsItem
from app.telegram.bot import get_telegram_client
from app.tasks import PUBLISHED_POSTS_KEY
from app.utils import prepare_keywords, match_keywords

logger = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 200
SUMMARY_MAX_LENGTH = 700

# Сколько новостей отправлять за один запуск
PUBLISH_LIMIT = 5

# Redis key, множество URL уже опубликованных новостей
PUBLISHED_URLS_KEY = "news:published_urls"


def normalize_text(value: str | None) -> str:
    """Нормализовать строку: None -> '', если строка, то убрать пробелы по краям"""
    if value is None:
        return ""
    return str(value).strip()


def truncate_text(text: str, max_len: int) -> str:
    """Обрезать текст до max_len символов, добавив '...' при необходимости."""
    if max_len <= 3:
        return text[:max_len]
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def format_news_message(item: NewsItem) -> str:
    """Сформировать HTML-сообщение для Telegram."""
    title = truncate_text(normalize_text(item.title), TITLE_MAX_LENGTH)

    source = normalize_text(item.source)
    source_map = {"habr": "Habr", "rbc": "РБК"}
    source = source_map.get(source.lower(), source)

    summary = normalize_text(item.summary)
    if summary:
        summary = truncate_text(summary, SUMMARY_MAX_LENGTH)

    url = str(item.url) if item.url else ""

    title_html = html.escape(title)
    source_html = html.escape(source)
    summary_html = html.escape(summary) if summary else ""
    url_html = html.escape(url)

    parts: list[str] = [f"<b>{title_html}</b>"]

    if source_html:
        parts.append(f"<i>Источник: {source_html}</i>")

    if summary_html:
        parts.append(summary_html)

    # Показываем совпавшие keywords
    if getattr(item, "keywords", None):
        tags = ", ".join(item.keywords[:5])
        if tags:
            parts.append(f"🏷️ {html.escape(tags)}")

    if url_html:
        parts.append(f'🔗 <a href="{url_html}">Читать полностью</a>')

    return "\n\n".join(parts)


def filter_not_published(items: list[NewsItem]) -> list[NewsItem]:
    """Оставить только новости, которые еще не публиковались (по URL)."""
    client = get_redis_client()
    result: list[NewsItem] = []

    skipped = 0
    for item in items:
        url = str(item.url) if item.url else ""
        if not url:
            continue

        if client.sismember(PUBLISHED_URLS_KEY, url):
            skipped += 1
            continue

        result.append(item)

    logger.info("Дедупликация: пропущено уже опубликованных=%s", skipped)
    return result


def mark_published(urls: list[str]) -> None:
    """Пометить URL как опубликованные (добавить в Redis SET)."""
    if not urls:
        return
    client = get_redis_client()
    client.sadd(PUBLISHED_URLS_KEY, *urls)


async def publish_latest_news(limit: int = PUBLISH_LIMIT) -> int:
    """Собрать и опубликовать свежие новости в Telegram.
        Сколько сообщений отправлено.
    """
    items = collect_from_all_sources()
    logger.info("Собрано новостей: %s", len(items))
    if not items:
        return 0

    keywords = prepare_keywords(settings.keywords_list)

    filtered: list[NewsItem] = []
    for item in items:
        matched = match_keywords(item.title, item.summary, keywords) if keywords else []

        # Строгая фильтрация: если ключевых слов нет в новости, то пропускаем
        if settings.strict_filtering and keywords and not matched:
            continue

        item.keywords = matched
        filtered.append(item)

    logger.info("После фильтрации по ключевым словам: %s", len(filtered))
    if not filtered:
        return 0

    #Дедупликация по URL (Redis)
    filtered = filter_not_published(filtered)
    if not filtered:
        logger.info("Новых (не опубликованных) новостей нет")
        return 0

    to_send = filtered[:limit]

    client = await get_telegram_client()
    redis_client = get_redis_client()
    sent_urls: list[str] = []
    try:
        sent = 0
        for item in to_send:
            message = format_news_message(item)
            await client.send_message(
                settings.telegram_channel_id,
                message,
                parse_mode="html",
            )
            # История публикаций (для /api/posts)
            published_post = {
                "news_id": item.id,
                "published_at": datetime.utcnow().isoformat(),
                "channel_id": settings.telegram_channel_id,
                "title": item.title,
                "url": str(item.url),
                "source": item.source,
                "keywords": item.keywords,
            }

            redis_client.rpush(
                PUBLISHED_POSTS_KEY,
                json.dumps(published_post, ensure_ascii=False),
            )

            sent += 1

            url = str(item.url) if item.url else ""
            if url:
                sent_urls.append(url)

        #Помечаем как опубликованные только то, что реально отправили
        mark_published(sent_urls)

        logger.info("Отправлено сообщений: %s", sent)
        return sent
    finally:
        await client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = asyncio.run(publish_latest_news())
    print(f"Готово: отправлено сообщений: {count}")