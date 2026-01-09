"""Точка входа для запуска Celery-worker"""
from app.tasks import celery_app

#  celery -A celery_worker.celery_app worker -l INFO -P solo (Команда для запуска)