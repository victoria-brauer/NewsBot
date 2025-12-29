import logging
import requests
from bs4 import BeautifulSoup

""" Парсер с сайта rbc.ru """

RBC_BASE_URL = "https://www.rbc.ru"
# Можно поменять на другую рубрику
RBC_NEWS_URL = f"{RBC_BASE_URL}/gorod/"

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
}

logger = logging.getLogger(__name__)


def parse_rbc_list_html(html: str, limit: int) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    news_items: list[dict[str, str]] = []

    link_tags = soup.find_all("a", class_="item__link")

    for a in link_tags:
        title = a.get_text(strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        if href.startswith("/"):
            url = f"{RBC_BASE_URL}{href}"
        else:
            url = href.strip()

        news_items.append(
            {
                "source": "rbc",
                "title": title,
                "url": url,
            }
        )

        if len(news_items) >= limit:
            break

    return news_items


def fetch_rbc_news_raw(limit: int = 20) -> list[dict[str, str]]:
    try:
        response = requests.get(RBC_NEWS_URL, headers=DEFAULT_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Ошибка при парсинге новостей с RBC")
        return []

    return parse_rbc_list_html(response.text, limit=limit)
