"""Environment-backed settings.  No credentials belong in source control."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def _float(name: str, default: float) -> float:
    value = os.getenv(name, str(default))
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc


@dataclass(frozen=True)
class Settings:
    database_url: str
    dashboard_database_url: str
    nvd_api_key: str | None
    nvd_initial_lookback_days: int
    nvd_overlap_minutes: int
    nvd_request_delay_seconds: float
    http_connect_timeout_seconds: float
    http_read_timeout_seconds: float
    log_level: str
    log_format: str
    dashboard_host: str
    dashboard_port: int


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required (for example, "
            "postgresql://user:password@127.0.0.1:5432/threatintel)."
        )

    initial_lookback = _int("NVD_INITIAL_LOOKBACK_DAYS", 7)
    overlap = _int("NVD_OVERLAP_MINUTES", 15)
    if initial_lookback < 1 or initial_lookback > 120:
        raise ValueError("NVD_INITIAL_LOOKBACK_DAYS must be between 1 and 120")
    if overlap < 0:
        raise ValueError("NVD_OVERLAP_MINUTES cannot be negative")

    dashboard_port = _int("DASHBOARD_PORT", 8080)
    if not 1 <= dashboard_port <= 65535:
        raise ValueError("DASHBOARD_PORT must be between 1 and 65535")

    return Settings(
        database_url=database_url,
        dashboard_database_url=os.getenv("DASHBOARD_DATABASE_URL") or database_url,
        nvd_api_key=os.getenv("NVD_API_KEY") or None,
        nvd_initial_lookback_days=initial_lookback,
        nvd_overlap_minutes=overlap,
        nvd_request_delay_seconds=_float("NVD_REQUEST_DELAY_SECONDS", 6.5),
        http_connect_timeout_seconds=_float("HTTP_CONNECT_TIMEOUT_SECONDS", 10),
        http_read_timeout_seconds=_float("HTTP_READ_TIMEOUT_SECONDS", 60),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_format=os.getenv("LOG_FORMAT", "json").lower(),
        dashboard_host=os.getenv("DASHBOARD_HOST", "127.0.0.1"),
        dashboard_port=dashboard_port,
    )
