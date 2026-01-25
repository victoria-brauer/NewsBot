"""Redis-клиент проекта.
Создание подключения к Redis, базовая проверку доступности Redis.
Настройки подключения берутся из конфигурации приложения.
"""

from redis import Redis
from redis.exceptions import RedisError

from app.config import settings


def get_redis_client() -> Redis:
    """Создать и вернуть клиент Redis.
    Параметр decode_responses=True используется для
    декодирования ответов в строки (str), а не bytes.
    """
    client = Redis.from_url(settings.redis_url, decode_responses=True)

    return client


def ping_redis() -> bool:
    """Проверить доступность Redis"""
    try:
        client = get_redis_client()
        result = client.ping()
        return bool(result)
    except RedisError:
        return False