"""Command-line entry points for independently scheduled ingestion jobs."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.settings import Settings, get_settings
from enrichment.kev_enricher import enrich_with_kev
from enrichment.nvd_normalizer import normalize_nvd
from feeds.nvd import fetch_modified_cves
from scraper.sources.krebsonsecurity import run as run_krebs
from storage.cve_repository import upsert_nvd_records
from storage.db import get_conn
from storage.state_repository import get_last_successful_at, set_last_successful_at

LOGGER = logging.getLogger(__name__)
NVD_JOB_NAME = "nvd"
NVD_MAX_WINDOW = timedelta(days=120)


class JsonFormatter(logging.Formatter):
    """Small dependency-free formatter suitable for one-line cron logs."""

    _BASE_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in self._BASE_RECORD_FIELDS and key not in {"message", "asctime"}:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, sort_keys=True)


def configure_logging(settings: Settings) -> None:
    handler = logging.StreamHandler()
    if settings.log_format == "json":
        handler.setFormatter(JsonFormatter())
    elif settings.log_format == "plain":
        handler.setFormatter(logging.Formatter("%(asctime)sZ %(levelname)s %(name)s %(message)s"))
    else:
        raise ValueError("LOG_FORMAT must be 'json' or 'plain'")
    logging.basicConfig(level=settings.log_level, handlers=[handler], force=True)


def init_database() -> None:
    schema = (Path(__file__).resolve().parents[1] / "storage" / "schema.sql").read_text()
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(schema)
    finally:
        conn.close()
    LOGGER.info("database schema is ready")


def _nvd_start(settings: Settings, now: datetime) -> datetime:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            checkpoint = get_last_successful_at(cur, NVD_JOB_NAME)
    finally:
        conn.close()
    if checkpoint is None:
        return now - timedelta(days=settings.nvd_initial_lookback_days)
    return checkpoint - timedelta(minutes=settings.nvd_overlap_minutes)


def run_nvd(settings: Settings) -> int:
    """Persist NVD deltas and advance a watermark only after each full window."""
    run_end = datetime.now(timezone.utc)
    window_start = _nvd_start(settings, run_end)
    total = 0

    while window_start < run_end:
        window_end = min(window_start + NVD_MAX_WINDOW, run_end)
        LOGGER.info("starting NVD window %s through %s", window_start.isoformat(), window_end.isoformat())
        conn = get_conn()
        try:
            with conn:
                records = (normalize_nvd(entry) for entry in fetch_modified_cves(settings, window_start, window_end))
                count = upsert_nvd_records(conn, records)
                with conn.cursor() as cur:
                    set_last_successful_at(cur, NVD_JOB_NAME, window_end)
        finally:
            conn.close()
        total += count
        LOGGER.info("NVD window persisted: %s CVEs", count)
        window_start = window_end

    LOGGER.info("NVD job completed: %s CVEs", total)
    return total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one threat-intel ingestion job")
    parser.add_argument("job", choices=("init-db", "cisa-kev", "nvd", "krebs"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = get_settings()
        configure_logging(settings)
        if args.job == "init-db":
            init_database()
        elif args.job == "cisa-kev":
            enrich_with_kev(settings)
        elif args.job == "nvd":
            run_nvd(settings)
        else:
            run_krebs(settings)
    except KeyboardInterrupt:
        LOGGER.warning("job interrupted")
        return 130
    except Exception:
        LOGGER.exception("job failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
