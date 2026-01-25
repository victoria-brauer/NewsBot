""" Маршруты для FastAPI """
import json
from fastapi import APIRouter, HTTPException, status
from app.schemas import NewsItem, PublishedNews, Keywords, Source
from app.news_parser import collect_from_all_sources
from app.redis_client import ping_redis, get_redis_client
from app.tasks import NEWS_LATEST_KEY, PUBLISHED_POSTS_KEY


api_router = APIRouter()


@api_router.get("/health")
async def health():
    """Проверка состояния сервиса."""
    redis_ok = ping_redis()
    return {
        "status": "ok",
        "redis": redis_ok,
    }


@api_router.get("/news", response_model=list[NewsItem])
async def news_list() -> list[NewsItem]:
    fake_news = [
        NewsItem(
            id="test1",
            title="FASTAPI 2.0.1 is released",
            url="https://fastapi.com/",
            summary="Краткое описание новости o FastAPI",
            source="FastAPI blog",
            published_at="2025-01-01T00:00:00Z",
            keywords=["python", "fastapi"]
        ),
        NewsItem(
            id="test2",
            title="Python 3.15.1 is released",
            url="https://python.org/",
            summary="Краткое описание новости o Python",
            source="Python blog",
            published_at="2025-01-02T00:00:00Z",
            keywords=["python"]
        )
    ]
    return fake_news


@api_router.get("/posts", response_model=list[PublishedNews])
async def get_posts():
    client = get_redis_client()
    raw_items = client.lrange(PUBLISHED_POSTS_KEY, 0, -1)[::-1]

    posts: list[PublishedNews] = []
    for raw in raw_items:
        try:
            data = json.loads(raw)
            posts.append(PublishedNews(**data))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

    return posts


@api_router.get("/news/scrape", response_model=list[NewsItem])
async def scrape_news() -> list[NewsItem]:
    """Ручной запуск парсинга(без публикации)"""
    return collect_from_all_sources()


@api_router.post("/publish")
async def publish_now():
    """Ручной запуск задачи публикации новостей в Telegram"""
    from app.tasks import publish_news

    publish_news.delay()
    return {"status": "publish task started"}