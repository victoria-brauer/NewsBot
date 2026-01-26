""" Маршруты для FastAPI """
import json
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas import NewsItem, PublishedNews, Keywords, Source
from app.news_parser import collect_from_all_sources
from app.redis_client import ping_redis, get_redis_client
from app.tasks import PUBLISHED_POSTS_KEY


api_router = APIRouter()

# Redis keys для CRUD
SOURCES_KEY = "sources:list"
KEYWORDS_KEY = "keywords:list"


"""Загрузить список объектов из Redis по ключу"""
def _load_list(key: str) -> list[dict[str, Any]]:
    client = get_redis_client()
    raw = client.get(key)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError:
        return []
    return []

"""Сохранить список объектов в Redis"""
def _save_list(key: str, items: list[dict[str, Any]]) -> None:
    client = get_redis_client()
    client.set(key, json.dumps(items, ensure_ascii=False))

"""Сгенерировать следующий id для новой записи"""
def _next_id(items: list[dict[str, Any]]) -> int:
    max_id = 0
    for it in items:
        try:
            max_id = max(max_id, int(it.get("id", 0)))
        except (TypeError, ValueError):
            continue
    return max_id + 1


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


@api_router.get("/posts", response_model=list[PublishedNews])
async def get_posts():
    """История публикаций (последние сверху)."""
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


"""CRUD: /api/sources/"""
@api_router.get("/api/sources/", response_model=list[Source])
async def list_sources() -> list[Source]:
    items = _load_list(SOURCES_KEY)
    return [Source(**x) for x in items]


@api_router.get("/api/sources/{source_id}", response_model=Source)
async def get_source(source_id: int) -> Source:
    items = _load_list(SOURCES_KEY)
    for x in items:
        if int(x.get("id", 0)) == source_id:
            return Source(**x)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")


@api_router.post("/api/sources/", response_model=Source, status_code=status.HTTP_201_CREATED)
async def create_source(payload: Source) -> Source:
    items = _load_list(SOURCES_KEY)

    # назначаем id автоматически
    new_id = _next_id(items)
    data = payload.model_dump()
    data["id"] = new_id

    items.append(data)
    _save_list(SOURCES_KEY, items)
    return Source(**data)


@api_router.put("/api/sources/{source_id}", response_model=Source)
async def update_source(source_id: int, payload: Source) -> Source:
    items = _load_list(SOURCES_KEY)

    for i, x in enumerate(items):
        if int(x.get("id", 0)) == source_id:
            data = payload.model_dump()
            data["id"] = source_id
            items[i] = data
            _save_list(SOURCES_KEY, items)
            return Source(**data)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")


@api_router.delete("/api/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: int):
    items = _load_list(SOURCES_KEY)
    new_items = [x for x in items if int(x.get("id", 0)) != source_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    _save_list(SOURCES_KEY, new_items)
    return None


"""CRUD: /api/keywords/"""
@api_router.get("/api/keywords/", response_model=list[Keywords])
async def list_keywords() -> list[Keywords]:
    items = _load_list(KEYWORDS_KEY)
    return [Keywords(**x) for x in items]


@api_router.get("/api/keywords/{keyword_id}", response_model=Keywords)
async def get_keyword(keyword_id: int) -> Keywords:
    items = _load_list(KEYWORDS_KEY)
    for x in items:
        if int(x.get("id", 0)) == keyword_id:
            return Keywords(**x)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")


@api_router.post("/api/keywords/", response_model=Keywords, status_code=status.HTTP_201_CREATED)
async def create_keyword(payload: Keywords) -> Keywords:
    items = _load_list(KEYWORDS_KEY)

    # защита от дублей по word
    word = (payload.word or "").strip()
    if not word:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="word is required")

    for x in items:
        if str(x.get("word", "")).strip().lower() == word.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Keyword already exists")

    new_id = _next_id(items)
    data = payload.model_dump()
    data["id"] = new_id
    data["word"] = word

    items.append(data)
    _save_list(KEYWORDS_KEY, items)
    return Keywords(**data)


@api_router.put("/api/keywords/{keyword_id}", response_model=Keywords)
async def update_keyword(keyword_id: int, payload: Keywords) -> Keywords:
    items = _load_list(KEYWORDS_KEY)

    word = (payload.word or "").strip()
    if not word:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="word is required")

    # проверка дубля по word для других записей
    for x in items:
        if int(x.get("id", 0)) != keyword_id and str(x.get("word", "")).strip().lower() == word.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Keyword already exists")

    for i, x in enumerate(items):
        if int(x.get("id", 0)) == keyword_id:
            data = payload.model_dump()
            data["id"] = keyword_id
            data["word"] = word
            items[i] = data
            _save_list(KEYWORDS_KEY, items)
            return Keywords(**data)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")


@api_router.delete("/api/keywords/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(keyword_id: int):
    items = _load_list(KEYWORDS_KEY)
    new_items = [x for x in items if int(x.get("id", 0)) != keyword_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")
    _save_list(KEYWORDS_KEY, new_items)
    return None