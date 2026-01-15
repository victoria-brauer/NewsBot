"""Вспомогательные утилиты.
    Здесь находятся:
    - генерация стабильных идентификаторов новостей,
    - нормализация даты и времени публикации.
"""
import hashlib
from datetime import datetime


def generate_news_id(source: str, url: str) -> str:
    """Сгенерировать стабильный идентификатор новости."""
    base = f"{source}:{url}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def normalize_published_at(raw_published_at: str | datetime | None) -> datetime | None:
    """Нормализовать дату и время публикации новости.
        Объект datetime при успешном парсинге,
        либо None, если значение отсутствует или формат неизвестен.
    """
    if isinstance(raw_published_at, datetime):
        return raw_published_at

    if not raw_published_at:
        return None

    if isinstance(raw_published_at, str):
        possible_formats = [
            "%Y-%m-%dT%H:%M:%S",       # 2025-01-01T12:30:45
            "%Y-%m-%dT%H:%M:%S%z",     # 2025-01-01T12:30:45+0300 / +03:00 (иногда)
            "%Y-%m-%dT%H:%M:%S.%f",    # 2025-01-01T12:30:45.123456
            "%Y-%m-%dT%H:%M:%S.%f%z",  # 2025-01-01T12:30:45.123456+0300
            "%d.%m.%Y, %H:%M:%S",      # 01.01.2025, 12:30:45
            "%d.%m.%Y, %H:%M",         # 01.01.2025, 12:30
        ]

        for fmt in possible_formats:
            try:
                return datetime.strptime(raw_published_at, fmt)
            except ValueError:
                continue

    return None


def prepare_keywords(raw_keywords: list[str]) -> list[str]:
    """Нормализовать список ключевых слов: lower, trim, unique."""
    seen: set[str] = set()
    for word in raw_keywords:
        normalized = str(word).strip().lower()
        if normalized:
            seen.add(normalized)
    return list(seen)


def build_search_text(title: str, summary: str | None) -> str:
    """Собрать текст (title + summary) для поиска ключевых слов."""
    safe_summary = summary or ""
    text = f"{title}\n{safe_summary}"
    return text.lower()


def find_matched_keywords(text: str, keywords: list[str]) -> list[str]:
    """Вернуть список ключевых слов, которые встречаются в тексте."""
    matched: list[str] = []
    seen: set[str] = set()

    for keyword in keywords:
        if keyword in seen:
            continue

        if keyword in text:
            seen.add(keyword)
            matched.append(keyword)
    return matched


def match_keywords(title: str, summary: str | None, keywords: list[str]) -> list[str]:
    """Найти ключевые слова по title/summary."""
    text = build_search_text(title, summary)



# def prepare_keywords(raw_keywords: list[str]) -> list[str]:
#     prepared: list[str] = []
#     seen = set[str] = set()
#
#     for word in raw_keywords:
#         normalized = str(word).strip().lower()
#
#         if not normalized:
#             continue
#         if normalized in seen:
#             continue
#
#         seen.add(normalized)
#     prepared = list(seen)
#     return prepared

