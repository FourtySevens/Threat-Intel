from bs4 import BeautifulSoup
from config.settings import Settings
from feeds.http import build_session, timeout
from enrichment.categorizer import categorize
from enrichment.cve_extractor import extract_cves
from storage.repository import save_article
from enrichment.enricher import enrich_article


BASE_URL = "https://krebsonsecurity.com/"

def parse_article_list(soup: BeautifulSoup) -> list[dict]:
    articles = []

    for post in soup.select("article"):
        title_el = post.find("h2")
        link_el = title_el.find("a") if title_el else None
        content_el = post.find("div", class_="entry-content")

        if not link_el or not content_el or not link_el.get("href"):
            continue

        article = {
            "title": link_el.get_text(strip=True),
            "url": link_el["href"],
            "source": "krebsonsecurity",
            "published_at": None,  # optional, can add later
            "content": content_el.get_text("\n", strip=True),
            "tags": [],
        }

        articles.append(article)

    return articles


def run(settings: Settings) -> int:
    session = build_session(settings)
    try:
        response = session.get(BASE_URL, timeout=timeout(settings))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    finally:
        session.close()

    articles = parse_article_list(soup)

    stored = 0
    for article in articles:
        enriched = enrich_article(article)
        if save_article(enriched) is not None:
            stored += 1
    return stored
