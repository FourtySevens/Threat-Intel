"""Read-only PostgreSQL connections for the dashboard."""

from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection

from config.settings import get_settings


def get_readonly_conn() -> connection:
    settings = get_settings()
    conn = psycopg2.connect(
        settings.dashboard_database_url,
        connect_timeout=5,
        options="-c statement_timeout=5000",
        application_name="threat-intel-dashboard",
    )
    conn.set_client_encoding("UTF8")
    conn.set_session(readonly=True, autocommit=True)
    return conn
