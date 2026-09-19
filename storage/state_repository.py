"""Persistent watermarks for incremental ingestion."""

from __future__ import annotations

from datetime import datetime


def get_last_successful_at(cur, job_name: str) -> datetime | None:
    cur.execute("SELECT last_successful_at FROM job_state WHERE job_name = %s", (job_name,))
    row = cur.fetchone()
    return row[0] if row else None


def set_last_successful_at(cur, job_name: str, value: datetime) -> None:
    cur.execute(
        """
        INSERT INTO job_state (job_name, last_successful_at, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (job_name) DO UPDATE SET
            last_successful_at = EXCLUDED.last_successful_at,
            updated_at = NOW()
        """,
        (job_name, value),
    )
