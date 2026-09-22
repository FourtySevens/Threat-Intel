"""RSS/Atom feed retrieval and normalization."""

from __future__ import annotations

from datetime import datetime, timezone
from calendar import timegm

import feedparser
from bs4 import BeautifulSoup

from config.settings import Settings
from feeds.http import build_session, timeout


def _published(entry) -> datetime | None:
    value = entry.get("published_parsed") or entry.get("updated_parsed")
    return datetime.fromtimestamp(timegm(value), timezone.utc) if value else None


def _excerpt(value: str, limit: int = 2000) -> str:
    text = " ".join(BeautifulSoup(value, "html.parser").get_text(" ", strip=True).split())
    return text[:limit].rstrip()


def fetch_feed(settings: Settings, feed: dict) -> list[dict]:
    session = build_session(settings)
    try:
        response = session.get(feed["feed_url"], timeout=timeout(settings))
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
    finally:
        session.close()
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"invalid RSS/Atom document: {parsed.bozo_exception}")
    records = []
    for entry in parsed.entries:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue
        records.append({
            "title": title,
            "url": url,
            "source": feed["name"],
            "published_at": _published(entry),
            # Store an excerpt and URL, not a publisher's full article body.
            "content": _excerpt(entry.get("summary") or entry.get("description") or title),
            "tags": [],
            "rss_feed_id": feed["id"],
        })
    return records
