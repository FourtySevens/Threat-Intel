"""RSS ingestion orchestration."""

from __future__ import annotations

import logging

from config.settings import Settings
from enrichment.enricher import enrich_article
from feeds.rss import fetch_feed
from storage.db import get_conn
from storage.repository import save_article
from storage.rss_repository import list_enabled_feeds, mark_feed_error, mark_feed_success

LOGGER = logging.getLogger(__name__)


def ingest_rss_feeds(settings: Settings) -> int:
    conn = get_conn()
    try:
        feeds = list_enabled_feeds(conn)
    finally:
        conn.close()
    stored = 0
    failures = []
    for feed in feeds:
        try:
            for article in fetch_feed(settings, feed):
                if save_article(enrich_article(article)) is not None:
                    stored += 1
            conn = get_conn()
            try:
                mark_feed_success(conn, feed["id"])
            finally:
                conn.close()
        except Exception as exc:
            LOGGER.exception("RSS feed failed: %s", feed["feed_url"])
            failures.append(feed["name"])
            conn = get_conn()
            try:
                mark_feed_error(conn, feed["id"], str(exc))
            finally:
                conn.close()
    if failures:
        raise RuntimeError(f"RSS ingestion failed for: {', '.join(failures)}")
    LOGGER.info("RSS ingestion completed: %s articles", stored)
    return stored
