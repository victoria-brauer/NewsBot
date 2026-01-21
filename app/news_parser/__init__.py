from __future__ import annotations

import logging
from typing import Any

from app.schemas import NewsItem
from app.news_parser import habr, rbc
from app.utils import generate_news_id, normalize_published_at

logger = logging.getLogger(__name__)

NEWS_SOURCES = ["habr", "rbc"]


def normalize_raw_news(source_name: str, raw_item: dict[str, Any]) -> NewsItem:
    """Привести сырую новость к формату NewsItem"""
    raw_title = raw_item.get("title", "")
    title = str(raw_title).strip()

    raw_url = raw_item.get("url") or raw_item.get("link")
    if not raw_url:
        raise ValueError(f"Неверный URL в новости: {title!r}")

    url = str(raw_url).strip()

    raw_summary = raw_item.get("summary") or raw_item.get("description") or None
    summary = str(raw_summary).strip() if raw_summary is not None else None

    raw_source = raw_item.get("source") or source_name
    source = str(raw_source).strip()

    raw_published_at = raw_item.get("published_at") or raw_item.get("date")
    published_at = normalize_published_at(raw_published_at)

    news_id = generate_news_id(source=source, url=url)

    return NewsItem(
        id=news_id,
        title=title,
        url=url,
        summary=summary,
        source=source,
        published_at=published_at,
        keywords=[],
    )


def collect_from_all_sources() -> list[NewsItem]:
    """Собрать и нормализовать новости из всех источников"""
    collected_news: list[NewsItem] = []

    sources: list[tuple[str, Any]] = [
        ("habr", habr.fetch_habr_news_raw),
        ("rbc", rbc.fetch_rbc_news_raw),
    ]

    for source_name, fetch_func in sources:
        try:
            raw_items = fetch_func()
        except Exception:
            logger.exception("Ошибка при парсинге новостей из источника=%s", source_name)
            continue

        for raw_item in raw_items:
            try:
                news_item = normalize_raw_news(source_name=source_name, raw_item=raw_item)
            except Exception:
                logger.exception(
                    "Не получилось нормализовать новость (source=%s) raw_item=%r",
                    source_name,
                    raw_item,
                )
                continue

            collected_news.append(news_item)

    return collected_news