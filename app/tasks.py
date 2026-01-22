"""Задачи Celery"""
import time
import json
import logging

from celery import Celery

from app.config import settings
from app.news_parser import collect_from_all_sources
from app.redis_client import get_redis_client
from app.utils import prepare_keywords, match_keywords


NEWS_LATEST_KEY = "new:latest"
NEWS_URL_SEEN_KEY = "new:urls_seen"
NEWS_LATEST_IDS_KEY = "new:latest_ids"
NEWS_LATEST_LIMIT = 100

logger = logging.getLogger(__name__)

"""Создаём экземпляр Celery-приложения"""
celery_app = Celery(
    settings.project_name, # имя приложения (используется в логах и конфигурации)
    broker=settings.redis_url,# брокер сообщений (Redis), через который задачи попадают в очередь
    backend=settings.redis_url,# хранилище результатов выполнения задач (тоже Redis)
)

"""Основная конфигурация Celery"""
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"], # Принимаем только JSON-сообщения
    result_serializer="json",
    broker_connect_retry_on_startup=True, # Повторные попытки подключения к брокеру при старте
    result_expires=3600, # Время хранения результатов задач (в секундах)
    task_default_queue="newsbot", # Очередь по умолчанию
)

"""Расписание Celery Beat"""
celery_app.conf.beat_schedule = {
    "publish-news-every-30-min": {
        "task": "app.tasks.publish_news",
        "schedule": 30 * 60, # каждые 30 минут
        "args": (5,), # по пять новостей
    }
}


@celery_app.task(name="app.tasks.ping")
def ping() -> str:
    """Health-check задача."""
    return "pong"


@celery_app.task(name="app.tasks.collect_news")
def collect_news() -> list[dict]:
    """Собрать новости из всех источников и применить фильтрацию по ключевым словам."""
    keywords = prepare_keywords(settings.keywords_list)
    logger.info(f"collect news: keywords {keywords}")

    # Если keywords пустой
    if not keywords and settings.strict_filtering:
        logger.info("collect_news: строгий режим включён, ключевые слова отсутствуют — возврат пустого списка")
        return []

    start_ts = time.time()
    items = collect_from_all_sources()
    logger.info("collect_news: collected=%s", len(items))

    result: list[dict] = []
    for item in items:
        matched = match_keywords(item.title, item.summary, keywords) if keywords else []

        # Если совпадений нет
        if not matched and settings.strict_filtering:
            continue

        payload = item.model_dump(mode="json")
        payload["keywords"] = matched
        result.append(payload)

    elapsed = time.time() - start_ts
    logger.info("collect_news: done in %.2fs, returned=%s", elapsed, len(result))
    return result


def load_latest_from_redis() -> list[dict]:
    """Загрузить последние новости из Redis (JSON list)."""
    client = get_redis_client()
    raw_value = client.get(NEWS_LATEST_KEY)
    if not raw_value:
        return []

    try:
        data = json.loads(raw_value)
    except json.JSONDecodeError:
        logger.warning("load_latest_from_redis: invalid JSON")
        return []

    if not isinstance(data,list):
        logger.warning("load_latest_from_redis: expected list, got %s", type(data).__name__)
        return []

    return [item for item in data if isinstance(item, dict)]


def save_latest_to_redis(items: list[dict]):
    """Сохранить последние новости в Redis (JSON list)."""
    client = get_redis_client()
    payload = json.dumps(items, ensure_ascii=False)
    client.set(NEWS_LATEST_KEY, payload)


def mark_urls_as_seen(urls: list[str]):
    """Добавить URL в Redis."""
    if not urls:
        return

    client = get_redis_client()
    client.sadd(NEWS_URL_SEEN_KEY, *urls)


def filter_new_items_by_urls_seen(items: list[dict]) -> list[dict]:
    """Оставить только новости, URL которых еще не встречался"""
    client = get_redis_client()
    news_items: list[dict] = []

    for item in items:
        url = item.get("url")
        if not url:
            continue

        if client.sismember(NEWS_URL_SEEN_KEY, url):
            continue

        news_items.append(item)

    return news_items


def merge_and_trim_latest(new_items: list[dict], existing_items: list[dict]) -> list[dict]:
    """Склеить новые+старые, убрать дубли по URL и обрезать до лимита."""
    merged: list[dict] =[]
    seen_urls: set[str] = set()

    for item in new_items + existing_items:
        url = item.get("url")
        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)
        merged.append(item)

        if len(merged) >= NEWS_LATEST_LIMIT:
            break

    return merged


def save_latest_ids_to_redis(items: list[dict]) -> None:
    """Сохранить id новостей в Redis list."""
    client = get_redis_client()
    ids: list[str] = []

    for item in items:
        news_id = item.get("id")
        if news_id:
            ids.append(str(news_id))

    if not ids:
        return

    client.rpush(NEWS_LATEST_IDS_KEY, *ids)


@celery_app.task(name="app.tasks.publish_news")
def publish_news(limit: int = 5) -> int:
    """Собрать свежие новости и опубликовать их в Telegram канал."""
    # Asyncio внутри celery-таски
    import asyncio
    from app.telegram.publisher import publish_latest_news

    return asyncio.run(publish_latest_news(limit=limit))