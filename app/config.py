"""Конфигурация проекта. Модуль содержит настройки приложения, загружаемые из переменного окружения
(и файла .env)"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
    )

    debug: bool = False            #Включает расширенное логирование, отладочный режим

    redis_url: str = 'redis://localhost:6379/0'
    project_name: str = 'newsbot'

    telegram_api_id: int = 0        #Telegram API ID для Telethon
    telegram_api_hash: str = ""     #Telegram API hash для Telethon
    telegram_bot_token: str = ""    #Bot API token (если используешь бота)
    telegram_channel_id: str = ""   #ID/username канала для публикаций

    # Фильтры ключевых слов по умолчанию (можно переопределить через .env)
    news_keywords: str = 'python,fastapi,django,ai,aiogram,нейросети'

    @property
    def keywords_list(self) -> list[str]:
        """Список ключевых слов для фильтрации новостей.
        Слова разделяются запятыми, пробелы обрезаются, пустые элементы игнорируются.
        """
        raw_value = self.news_keywords
        parts = [part.strip() for part in raw_value.split(",") if part.strip()]
        return parts


settings = Settings()