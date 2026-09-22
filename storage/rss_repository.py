"""Persistence for user-managed RSS sources."""

from __future__ import annotations


def list_enabled_feeds(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, feed_url FROM rss_feeds WHERE enabled IS TRUE ORDER BY id")
        return [{"id": row[0], "name": row[1], "feed_url": row[2]} for row in cur.fetchall()]


def list_feeds(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT f.id, f.name, f.feed_url, f.enabled, f.last_fetched_at, f.last_error,
                      COUNT(a.id) AS article_count
               FROM rss_feeds f LEFT JOIN articles a ON a.rss_feed_id = f.id
               GROUP BY f.id ORDER BY f.created_at DESC"""
        )
        columns = [item.name for item in cur.description]
        return [dict(zip(columns, row, strict=True)) for row in cur.fetchall()]


def add_feed(conn, *, name: str, feed_url: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO rss_feeds (name, feed_url) VALUES (%s, %s)
               ON CONFLICT (feed_url) DO UPDATE SET name = EXCLUDED.name, enabled = TRUE, updated_at = NOW()""",
            (name, feed_url),
        )
    conn.commit()


def mark_feed_success(conn, feed_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE rss_feeds SET last_fetched_at = NOW(), last_error = NULL, updated_at = NOW() WHERE id = %s", (feed_id,))
    conn.commit()


def mark_feed_error(conn, feed_id: int, error: str) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE rss_feeds SET last_error = %s, updated_at = NOW() WHERE id = %s", (error[:2000], feed_id))
    conn.commit()
