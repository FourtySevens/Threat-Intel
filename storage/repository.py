from storage.db import get_conn
from scraper.utils.hashing import content_hash

def save_article(article: dict) -> int | None:
    """
    Save a scraped article and its tags.

    Returns:
        article_id (int) if a new article was inserted
        None if the article already exists
    """

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # Compute hash for deduplication
                h = content_hash(article["content"])

                # Insert article (Postgres enforces uniqueness)
                cur.execute("""
                    INSERT INTO articles
                    (title, url, source, published_at, content, content_hash, rss_feed_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (content_hash) DO NOTHING
                    RETURNING id
                """, (
                    article["title"],
                    article["url"],
                    article["source"],
                    article.get("published_at"),
                    article["content"],
                    h,
                    article.get("rss_feed_id"),
                ))

                row = cur.fetchone()
                if row is None:
                    # Article already exists
                    return None

                article_id = row[0]

                # Attach tags
                _attach_tags(cur, article_id, article.get("tags", []))

                return article_id

    finally:
        conn.close()


def _attach_tags(cur, article_id: int, tags: list[str]) -> None:
    """
    Attach tags to an article using the article_tags table.
    Assumes tags already exist in the tags table.
    """

    for tag in tags:
        cur.execute(
            "INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
            (tag,),
        )
        # Get tag ID
        cur.execute(
            "SELECT id FROM tags WHERE name = %s",
            (tag,)
        )
        result = cur.fetchone()

        if not result:
            # Unknown tag — skip silently (by design)
            continue

        tag_id = result[0]

        # Create relationship (ignore duplicates)
        cur.execute("""
            INSERT INTO article_tags (article_id, tag_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (article_id, tag_id))
