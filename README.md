# 📰 NewsBot — Telegram News Publisher

**NewsBot** — сервис для автоматического сбора, фильтрации и публикации новостей в Telegram-канал.  
Проект построен на **FastAPI + Celery + Redis + Telethon** и полностью запускается через **Docker Compose**.

---

## 🚀 Возможности

- 🔎 Сбор новостей из разных источников
- 🧠 Фильтрация по ключевым словам
- 🚫 Дедупликация (повторные новости не публикуются)
- 🤖 Публикация в Telegram-канал через бота
- ⏱ Автопубликация по расписанию (Celery Beat)
- 🔁 Ручной запуск публикации через API
- 📦 Хранение состояния в Redis

---

## 🧱 Архитектура
```text
NewsBot/
├── app/
│   ├── news_parser/
│   │   ├── habr.py
│   │   └── rbc.py
│   ├── telegram/
│   │   ├── bot.py
│   │   └── publisher.py
│   ├── api.py
│   ├── config.py
│   ├── redis_client.py
│   ├── schemas.py
│   ├── tasks.py
│   └── utils.py
├── docker-compose.yml
├── Dockerfile
├── main.py
├── celery_worker.py
├── pyproject.toml
├── poetry.lock
├── requirements.txt
├── README.md
├── .gitignore
├── .dockerignore
├── .env.example
└── .env
```
---
## 📦 Технологии

- Python 3.13
- FastAPI
- Celery + Celery Beat
- Redis
- Telethon
- Poetry
- Docker / Docker Compose

---

## ⚙️ Переменные окружения

Создай файл `.env` (или используй `.env.example`):

```env
# Redis
REDIS_URL=redis://redis:6379/0

# Telegram
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel

# App
DEBUG=false
STRICT_FILTERING=true
NEWS_KEYWORDS=python,fastapi,django,ai

```

## 🐳 Запуск через Docker
docker compose up --build
```
После запуска будут доступны:

API: http://localhost:8000

Swagger: http://localhost:8000/docs

```
## 📡 API эндпоинты
```
🔍 Health check
GET /health

📰 Получить опубликованные посты
GET /posts

🔁 Ручной запуск публикации
POST /publish

🧲 Сбор новостей без публикации
GET /news/scrape

```
## ⏱ Автопубликация
```
Публикация запускается автоматически каждые 30 минут через Celery Beat:

celery_app.conf.beat_schedule = {
    "publish-news-every-30-min": {
        "task": "app.tasks.publish_news",
        "schedule": 30 * 60,
    }
}

```
## 🛡 Дедупликация
```
Проверка по URL

Повторные новости не отправляются

Состояние сохраняется между рестартами

```
## 🧪 Локальный запуск без Docker
```
poetry install
uvicorn main:app --reload

Celery:

celery -A app.tasks.celery_app worker -l INFO
celery -A app.tasks.celery_app beat -l INFO