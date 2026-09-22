"""Parameterized read models for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass

PAGE_SIZE = 50


@dataclass(frozen=True)
class SearchFilters:
    query: str = ""
    severity: str = ""
    source: str = ""
    kev: str = ""
    page: int = 1


def _rows(cursor):
    columns = [column.name for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def get_metrics(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM cve) AS cve_count,
                (SELECT COUNT(*) FROM cve_kev WHERE exploited) AS kev_count,
                (SELECT COUNT(*) FROM articles) AS article_count,
                (SELECT COUNT(*) FROM cve WHERE severity IN ('HIGH', 'CRITICAL')) AS high_critical_count
            """
        )
        row = cur.fetchone()
    return {
        "cve_count": row[0],
        "kev_count": row[1],
        "article_count": row[2],
        "high_critical_count": row[3],
    }


def get_filter_values(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT severity FROM cve WHERE severity IS NOT NULL ORDER BY severity")
        severities = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT DISTINCT source FROM cve WHERE source IS NOT NULL ORDER BY source")
        sources = [row[0] for row in cur.fetchall()]
    return {"severities": severities, "sources": sources}


def search_cves(conn, filters: SearchFilters) -> tuple[list[dict], int]:
    clauses: list[str] = []
    params: list[object] = []
    if filters.query:
        clauses.append("(c.cve_id ILIKE %s OR c.description ILIKE %s)")
        value = f"%{filters.query}%"
        params.extend((value, value))
    if filters.severity:
        clauses.append("c.severity = %s")
        params.append(filters.severity)
    if filters.source:
        clauses.append("c.source = %s")
        params.append(filters.source)
    if filters.kev == "yes":
        clauses.append("k.exploited IS TRUE")
    elif filters.kev == "no":
        clauses.append("COALESCE(k.exploited, FALSE) IS FALSE")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    offset = (filters.page - 1) * PAGE_SIZE
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT c.id, c.cve_id, c.description, c.cvss_score, c.severity,
                   c.source, c.published_at, c.last_modified_at,
                   COALESCE(k.exploited, FALSE) AS is_kev, k.due_date
            FROM cve c
            LEFT JOIN cve_kev k ON k.cve_id = c.id
            {where}
            ORDER BY COALESCE(k.exploited, FALSE) DESC,
                     c.last_modified_at DESC NULLS LAST,
                     c.cve_id ASC
            LIMIT %s OFFSET %s
            """,
            [*params, PAGE_SIZE, offset],
        )
        results = _rows(cur)
        cur.execute(
            f"SELECT COUNT(*) FROM cve c LEFT JOIN cve_kev k ON k.cve_id = c.id {where}",
            params,
        )
        total = cur.fetchone()[0]
    return results, total


def search_articles(conn, query: str) -> list[dict]:
    value = f"%{query}%"
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, url, source, published_at, content
            FROM articles
            WHERE (%s = '' OR title ILIKE %s OR content ILIKE %s)
            ORDER BY published_at DESC NULLS LAST, id DESC
            LIMIT 10
            """,
            (query, value, value),
        )
        return _rows(cur)


def add_rss_feed(conn, name: str, feed_url: str, source_type: str, reliability: str, default_priority: int) -> None:
    from storage.rss_repository import add_feed

    add_feed(conn, name=name, feed_url=feed_url, source_type=source_type, reliability=reliability, default_priority=default_priority)


def get_cve(conn, cve_id: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.cve_id, c.description, c.cvss_score, c.severity,
                   c.source, c.source_identifier, c.published_at, c.last_modified_at,
                   c.attack_vector, c.cvss_vector, c.exploitability_score,
                   COALESCE(k.exploited, FALSE) AS is_kev, k.date_added,
                   k.due_date, k.required_action
            FROM cve c
            LEFT JOIN cve_kev k ON k.cve_id = c.id
            WHERE c.cve_id = %s
            """,
            (cve_id,),
        )
        rows = _rows(cur)
    return rows[0] if rows else None


def get_article(conn, article_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.id, a.title, a.url, a.source, a.published_at, a.content,
                   COALESCE(array_agg(t.name ORDER BY t.name) FILTER (WHERE t.name IS NOT NULL), '{}') AS tags
            FROM articles a
            LEFT JOIN article_tags at ON at.article_id = a.id
            LEFT JOIN tags t ON t.id = at.tag_id
            WHERE a.id = %s
            GROUP BY a.id
            """,
            (article_id,),
        )
        rows = _rows(cur)
    return rows[0] if rows else None
