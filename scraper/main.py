"""Backward-compatible module entry point; use ``scraper.jobs`` directly."""

from scraper.jobs import main

if __name__ == "__main__":
    raise SystemExit(main())
