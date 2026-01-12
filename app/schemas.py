"""Pydantic-схемы. Модели:
- NewsItem: новость (сырые данные после парсинга)
- PublishedNews: сгенерированный/опубликованный пост по новости
- Source: источник новостей
- Keywords: ключевое слово для фильтрации
"""
from datetime import datetime
from pydantic import BaseModel, Field, AnyHttpUrl
from typing import Literal


class NewsItem(BaseModel):
    id: str = Field(
        ...,
        description="Уникальный идентификатор новости (uuid или hash)",
        examples=["fhygiy7dxcb4557ffxdhjlkj9097t543"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Заголовок новости",
        examples=[
            "Intel подписала предварительное соглашение о приобретении стартапа SambaNova Systems, который разрабатывает чипы для вычислений искусственного интеллекта"
        ],
    )
    url: AnyHttpUrl = Field(
        ...,
        description="Оригинальный url новости",
        examples=["https://habr.com/ru/news/976862/"],
    )
    summary: str | None = Field(
        default=None,
        description="Короткое описание новости",
        examples=["Intel приобретёт стартап SambaNova по производству чипов для ИИ"],
    )
    source: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя источника",
        examples=["habr"],
    )
    published_at: datetime | None = Field(
        default=None,
        description="Время публикации на новостном источнике",
        examples=["2025-01-01T00:00:00Z"],
    )
    raw_text: str | None = Field(
        default=None,
        description="Сырой текст (актуально для Telegram-источников)",
        examples=["Сегодня вышел релиз FastAPI 1.0..."],
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Список ключевых слов, связанных с новостью",
        examples=[["python", "fastapi"]],
    )


class PublishedNews(BaseModel):
    news_id: str = Field(
        ...,
        description="Идентификатор новости (uuid или hash)",
        examples=["fhygiy7dxcb4557ffxdhjlkj9097t543"],
    )
    published_at: datetime = Field(
        ...,
        description="Время публикации новости в телеграм канале",
        examples=["2025-01-01T00:00:00Z"],
    )
    channel_id: str = Field(
        ...,
        description="id телеграм канала",
        examples=["@my_telegram_channel", "-1000173864598"],
    )


class Keywords(BaseModel):
    id: int = Field(
        ...,
        description="id ключевого слова",
        examples=[1, 2],
    )
    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Ключевое слово новости",
        examples=["python", "fastapi"],
    )


class Source(BaseModel):
    id: int = Field(
        ...,
        description="Идентификатор источника.",
        examples=[1],
    )
    type: Literal["site", "tg"] = Field(
        ...,
        description="Тип источника.",
        examples=["site"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Название источника.",
        examples=["Habr"],
    )
    url: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="URL сайта или username Telegram-канала.",
        examples=["https://habr.com/ru/news/", "@some_public_channel"],
    )
    enabled: bool = Field(
        default=True,
        description="Флаг активности источника.",
        examples=[True],
    )
















