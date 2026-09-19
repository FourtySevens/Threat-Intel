"""Shared HTTP client policy for scheduled ingestion jobs."""

from __future__ import annotations

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import Settings

LOGGER = logging.getLogger(__name__)


def build_session(settings: Settings) -> requests.Session:
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "threat-intel-ingestor/1.0 (+local scheduled ingestion)",
            "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
        }
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def timeout(settings: Settings) -> tuple[float, float]:
    return (settings.http_connect_timeout_seconds, settings.http_read_timeout_seconds)
