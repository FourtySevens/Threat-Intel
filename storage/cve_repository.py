"""CVE persistence. All write functions are idempotent."""

from __future__ import annotations

from collections.abc import Iterable

from psycopg2.extensions import connection


def get_or_create_cve_stub(cur, cve_id: str) -> int:
    """Create a minimal KEV CVE without overwriting NVD-enriched fields."""
    cur.execute(
        """
        INSERT INTO cve (cve_id, description, severity, source)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (cve_id) DO UPDATE SET updated_at = NOW()
        RETURNING id
        """,
        (cve_id, "KEV-listed CVE (details pending)", "UNKNOWN", "cisa"),
    )
    return cur.fetchone()[0]


def upsert_nvd_records(conn: connection, records: Iterable[dict]) -> int:
    """Upsert NVD records within the caller's transaction."""
    count = 0
    with conn.cursor() as cur:
        for record in records:
            cur.execute(
                """
                INSERT INTO cve (
                    cve_id, description, cvss_score, severity, source,
                    source_identifier, published_at, last_modified_at,
                    attack_vector, cvss_vector, exploitability_score, updated_at
                ) VALUES (
                    %(cve_id)s, %(description)s, %(cvss_score)s, %(severity)s,
                    %(source)s, %(source_identifier)s, %(published_at)s,
                    %(last_modified_at)s, %(attack_vector)s, %(cvss_vector)s,
                    %(exploitability_score)s, NOW()
                )
                ON CONFLICT (cve_id) DO UPDATE SET
                    description = COALESCE(EXCLUDED.description, cve.description),
                    cvss_score = COALESCE(EXCLUDED.cvss_score, cve.cvss_score),
                    severity = COALESCE(EXCLUDED.severity, cve.severity),
                    source = EXCLUDED.source,
                    source_identifier = COALESCE(EXCLUDED.source_identifier, cve.source_identifier),
                    published_at = COALESCE(EXCLUDED.published_at, cve.published_at),
                    last_modified_at = COALESCE(EXCLUDED.last_modified_at, cve.last_modified_at),
                    attack_vector = COALESCE(EXCLUDED.attack_vector, cve.attack_vector),
                    cvss_vector = COALESCE(EXCLUDED.cvss_vector, cve.cvss_vector),
                    exploitability_score = COALESCE(EXCLUDED.exploitability_score, cve.exploitability_score),
                    updated_at = NOW()
                """,
                record,
            )
            count += 1
    return count
