"""Persistence for user-managed RSS sources."""

from __future__ import annotations


def list_enabled_feeds(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, feed_url, source_type, reliability, default_priority FROM rss_feeds WHERE enabled IS TRUE ORDER BY default_priority, id")
        return [{"id": row[0], "name": row[1], "feed_url": row[2], "source_type": row[3], "reliability": row[4], "default_priority": row[5]} for row in cur.fetchall()]


def list_feeds(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT f.id, f.name, f.feed_url, f.source_type, f.reliability, f.default_priority,
                      f.enabled, f.last_fetched_at, f.last_success_at, f.last_failure_at, f.failure_count, f.last_error,
                      COUNT(a.id) AS article_count
               FROM rss_feeds f LEFT JOIN articles a ON a.rss_feed_id = f.id
               GROUP BY f.id ORDER BY f.created_at DESC"""
        )
        columns = [item.name for item in cur.description]
        return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def add_feed(conn, *, name: str, feed_url: str, source_type: str = "research", reliability: str = "medium", default_priority: int = 3) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO rss_feeds (name, feed_url, source_type, reliability, default_priority) VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (feed_url) DO UPDATE SET name = EXCLUDED.name, source_type = EXCLUDED.source_type,
                 reliability = EXCLUDED.reliability, default_priority = EXCLUDED.default_priority,
                 enabled = TRUE, updated_at = NOW()""",
            (name, feed_url, source_type, reliability, default_priority),
        )
    conn.commit()


def mark_feed_success(conn, feed_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE rss_feeds SET last_fetched_at = NOW(), last_success_at = NOW(), failure_count = 0, last_error = NULL, updated_at = NOW() WHERE id = %s", (feed_id,))
    conn.commit()


def mark_feed_error(conn, feed_id: int, error: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE rss_feeds SET last_failure_at = NOW(), failure_count = failure_count + 1, last_error = %s, updated_at = NOW() WHERE id = %s", (error[:2000], feed_id))
    conn.commit()
