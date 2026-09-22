import unittest
from unittest.mock import MagicMock, patch

from config.settings import Settings
from feeds.rss import fetch_feed
from scraper.utils.hashing import canonical_url


class RssFeedTests(unittest.TestCase):
    def test_normalizes_valid_feed_entries(self):
        settings = Settings(
            database_url="postgresql://user:password@127.0.0.1:5432/threatintel",
            dashboard_database_url="postgresql://user:password@127.0.0.1:5432/threatintel",
            nvd_api_key=None, nvd_initial_lookback_days=7, nvd_overlap_minutes=15,
            nvd_request_delay_seconds=6.5, http_connect_timeout_seconds=10,
            http_read_timeout_seconds=60, log_level="INFO", log_format="json",
            dashboard_host="127.0.0.1", dashboard_port=8080,
        )
        response = MagicMock(content=b"<rss><channel><item><title>Example</title><link>https://example.org/a</link><description>Text</description></item></channel></rss>")
        session = MagicMock()
        session.get.return_value = response
        with patch("feeds.rss.build_session", return_value=session):
            records = fetch_feed(settings, {"id": 3, "name": "Example feed", "feed_url": "https://example.org/rss"})
        self.assertEqual(records[0]["rss_feed_id"], 3)
        self.assertEqual(records[0]["url"], "https://example.org/a")
        self.assertEqual(records[0]["content"], "Text")

    def test_canonical_url_removes_tracking_parameters_and_fragments(self):
        self.assertEqual(
            canonical_url("HTTPS://Example.org/post?utm_source=rss&id=7#section"),
            "https://example.org/post?id=7",
        )
