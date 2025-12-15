"""Pydantic-схемы"""
from pydantic import BaseModel, Field, AnyHttpUrl
from datetime import datetime
from uuid import UUID


class NewsItem(BaseModel):
    id: str = Field(
        ...,
        description="uuid новости",
        examples=["fhygiy7dxcb4557ffxdhjlkj9097t543"]
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Заголовок новости",
        examples=["Intel подписала предварительное соглашение о приобретении стартапа SambaNova Systems, который разрабатывает чипы для вычислений искусственного интеллекта"]
    )
    url: AnyHttpUrl = Field(
        ...,
        description="Оригинальный url новости",
        examples=["https://habr.com/ru/news/976862/"]
    )
    summary: str | None = Field(
        default=None,
        description="Короткое описание новости",
        examples=["Intel приобретёт стартап SambaNova по производству чипов для ИИ"]
    )
    source: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя источника",
        examples=["Habr"]
    )
    published_at: datetime = Field(
        ...,
        description="Время публикации на новостном источнике",
        examples=["2025-01-01T00:00:00Z"]
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Список ключевых слов",
        examples=[["Python", "FastAPI"]]
    )


class PublishedNews(BaseModel):
    news_id: str = Field(
        ...,
        description="uuid новости",
        examples=["fhygiy7dxcb4557ffxdhjlkj9097t543"]
    )
    published_at: datetime = Field(
        ...,
        description="Время публикации новости в телеграм канале",
        examples=["2025-01-01T00:00:00Z"]
    )
    channel_id: str = Field(
        ...,
        description="id телеграм канала",
        examples=["@my_telegram_channel", "-1000173864598"]
    )


class Keywords(BaseModel):
    id: int = Field(
        ...,
        description="id ключевого слова",
        examples=[1, 2]
    )
    word: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Ключевое слово новости",
        examples=["python", "fastapi"]
    )
















