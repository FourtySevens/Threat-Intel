"""NVD CVE API v2 client with explicit pagination."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Iterator

from config.settings import Settings
from feeds.http import build_session, timeout

NVD_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
LOGGER = logging.getLogger(__name__)


def _nvd_timestamp(value: datetime) -> str:
    """Render a UTC timestamp in the format accepted by the NVD API."""
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def fetch_modified_cves(
    settings: Settings, start: datetime, end: datetime
) -> Iterator[dict]:
    """Yield every CVE modified in [start, end], without retaining all pages."""
    if end <= start:
        raise ValueError("NVD end time must be later than start time")

    session = build_session(settings)
    if settings.nvd_api_key:
        session.headers["apiKey"] = settings.nvd_api_key

    start_index = 0
    total = None
    try:
        while total is None or start_index < total:
            params = {
                "lastModStartDate": _nvd_timestamp(start),
                "lastModEndDate": _nvd_timestamp(end),
                "startIndex": start_index,
                "resultsPerPage": 2000,
            }
            response = session.get(NVD_CVE_URL, params=params, timeout=timeout(settings))
            response.raise_for_status()
            payload = response.json()
            page = payload.get("vulnerabilities", [])
            total = int(payload.get("totalResults", 0))
            LOGGER.info(
                "NVD page received",
                extra={"start_index": start_index, "total_results": total, "record_count": len(page)},
            )
            if not page:
                break
            yield from page
            start_index += len(page)
            if start_index < total:
                time.sleep(settings.nvd_request_delay_seconds)
    finally:
        session.close()
