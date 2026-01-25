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
    """Подготовить ключевые слова: нижний регистр + убрать пробелы + убрать дубликаты."""
    seen: set[str] = set()
    result: list[str] = []
    for word in raw_keywords:
        normalized = str(word).strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def match_keywords(title: str, summary: str | None, keywords: list[str]) -> list[str]:
    """Найти ключевые слова, которые встретились в title/summary."""
    if not keywords:
        return []
    text = (title + "\n" + (summary or "")).lower()

    matched: list[str] = []
    for kw in keywords:
        if kw and kw in text:
            matched.append(kw)
    # Убираем дубли, сохранив порядок
    return list(dict.fromkeys(matched))