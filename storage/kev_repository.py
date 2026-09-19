"""CISA KEV persistence."""

from __future__ import annotations


def upsert_kev_status(cur, *, cve_id: int, date_added, due_date, required_action, exploited: bool) -> None:
    cur.execute(
        """
        INSERT INTO cve_kev (
            cve_id, exploited, date_added, due_date, required_action, updated_at
        ) VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (cve_id) DO UPDATE SET
            exploited = EXCLUDED.exploited,
            date_added = EXCLUDED.date_added,
            due_date = EXCLUDED.due_date,
            required_action = EXCLUDED.required_action,
            updated_at = NOW()
        """,
        (cve_id, exploited, date_added, due_date, required_action),
    )
