import logging

from config.settings import Settings
from feeds.http import build_session, timeout

CISA_KEV_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
)

LOGGER = logging.getLogger(__name__)


def run_kev(settings: Settings) -> list[dict]:
    session = build_session(settings)
    try:
        response = session.get(CISA_KEV_URL, timeout=timeout(settings))
        response.raise_for_status()
        data = response.json()
    finally:
        session.close()

    vulnerabilities = data.get("vulnerabilities", [])
    if not isinstance(vulnerabilities, list):
        raise ValueError("CISA KEV response has an invalid vulnerabilities field")
    LOGGER.info("CISA KEV feed received", extra={"record_count": len(vulnerabilities)})
    return vulnerabilities
