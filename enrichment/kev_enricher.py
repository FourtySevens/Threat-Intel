import logging

from config.settings import Settings
from feeds.cisa_kev import run_kev
from enrichment.kev_normalizer import normalize_kev
from storage.cve_repository import get_or_create_cve_stub
from storage.db import get_conn
from storage.kev_repository import upsert_kev_status

LOGGER = logging.getLogger(__name__)


def enrich_with_kev(settings: Settings) -> int:
    """Fetch and atomically upsert the current CISA KEV catalogue."""
    entries = run_kev(settings)
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                for entry in entries:
                    kev = normalize_kev(entry)
                    cve_id = get_or_create_cve_stub(cur, kev["cve_id"])
                    upsert_kev_status(
                        cur,
                        cve_id=cve_id,
                        date_added=kev["date_added"],
                        due_date=kev["due_date"],
                        required_action=kev["required_action"],
                        exploited=True,
                    )
    finally:
        conn.close()

    LOGGER.info("CISA KEV records persisted", extra={"record_count": len(entries)})
    return len(entries)
