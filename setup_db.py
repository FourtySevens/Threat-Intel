#!/usr/bin/env python3
"""Compatibility wrapper for the idempotent schema initializer."""

from scraper.jobs import main

if __name__ == "__main__":
    raise SystemExit(main(["init-db"]))
