"""Legacy compatibility wrapper. Use ``python -m scraper.jobs nvd`` instead."""

import warnings

from config.settings import get_settings
from scraper.jobs import run_nvd

def upsert_nist_data(records=None):
    if records is not None:
        raise ValueError("records is no longer accepted; the NVD job fetches and checkpoints its own data")
    warnings.warn("Use `python -m scraper.jobs nvd` instead", DeprecationWarning, stacklevel=2)
    return run_nvd(get_settings())
