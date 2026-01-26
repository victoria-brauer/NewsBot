FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Установка poetry
RUN pip install --no-cache-dir "poetry==2.2.1"

# Копируем только файлы зависимостей
COPY pyproject.toml poetry.lock* /app/

# Ставим зависимости в системный Python, без venv внутри контейнера
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --only main --no-root

# Копируем код
COPY . /app

# папка под сессию Telethon
RUN mkdir -p /app/data/telegram

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]