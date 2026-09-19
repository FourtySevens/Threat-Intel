"""PostgreSQL connection helpers."""

from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection

from config.settings import get_settings


def get_conn() -> connection:
    """Return a connection configured for a bounded, identifiable job run."""
    settings = get_settings()
    conn = psycopg2.connect(
        settings.database_url,
        connect_timeout=10,
        application_name="threat-intel-ingestor",
    )
    # Public threat feeds regularly contain non-ASCII vendor names and smart
    # punctuation. Do not inherit an ASCII client encoding from a legacy DB.
    conn.set_client_encoding("UTF8")
    return conn
