"""Legacy compatibility wrapper. Production uses ``scraper.jobs nvd``."""

from datetime import datetime, timedelta, timezone

from config.settings import get_settings
from feeds.nvd import fetch_modified_cves


def run_nist():
    """Return the initial NVD lookback window without writing a checkpoint."""
    settings = get_settings()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=settings.nvd_initial_lookback_days)
    return list(fetch_modified_cves(settings, start, end))

