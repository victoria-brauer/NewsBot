"""Вспомогательные утилиты"""
import hashlib
from datetime import datetime


def generate_news_id(source: str, url: str) -> str:
    base = f"{source}:{url}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def normalize_published_at(raw_published_at: str | datetime | None) -> datetime | None:
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
