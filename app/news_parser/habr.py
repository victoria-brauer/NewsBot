""" Парсер с сайта habr.com """
import logging

import requests
from bs4 import BeautifulSoup

HABR_BASE_URL = "https://habr.com"
HABR_NEWS_URL = f"{HABR_BASE_URL}/news/"
HABR_ARTICLE_URL = f"{HABR_BASE_URL}/article/"

HABR_CARD_SELECTOR = "article"
HABR_TITLE_SELECTOR = "a"
HABR_TITLE_LINK_SELECTOR = "tm-title__link"

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
}

logger = logging.getLogger(__name__)


def parser_habr_list_html(html: str, limit: int) -> list[dict]:
    """Распарсить HTML страницы новостей Habr.
        Извлекает заголовки и ссылки на новости.
    """
    soup = BeautifulSoup(html, "html.parser")
    news_items: list[dict] = []

    article_tags = soup.select(HABR_CARD_SELECTOR)

    for article_tag in article_tags:
        title_link = article_tag.find(HABR_TITLE_SELECTOR, class_=HABR_TITLE_LINK_SELECTOR)
        if title_link is None:
            continue

        title_text = title_link.get_text(strip=True)
        relative_url = title_link.get('href', '')
        if relative_url is None:
            continue

        if relative_url.startswith("http"):
            full_url = relative_url
        else:
            full_url = f'https://habr.com{relative_url}'

        news_item = {
            'source': 'habr',
            'title': title_text,
            'url': full_url,
        }
        news_items.append(news_item)

    return news_items


def fetch_habr_news_raw(limit: int = 20) -> list[dict[str, str]]:
    """Загрузить и распарсить список новостей с Habr.
        Список "сырых" новостей в виде словарей.
        В случае ошибки возвращается пустой список.
    """
    raw_items: list[dict[str, str]] = []

    try:
        response = requests.get(HABR_NEWS_URL, headers=DEFAULT_HEADERS, timeout=10)
    except requests.RequestException as e:
        logger.warning(f'Ошибка при парсинге новостей с HABR {e}')
        return raw_items

    if response.status_code != 200:
        logger.warning(f'При парсинге новостей с HABR - статус код: {response.status_code}')
        return raw_items

    raw_items = parser_habr_list_html(response.text, limit=limit)

    return raw_items