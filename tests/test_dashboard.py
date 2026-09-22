import unittest
from unittest.mock import MagicMock, patch

from dashboard.app import create_app


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    @patch("dashboard.app.get_readonly_conn")
    @patch("dashboard.app.search_articles", return_value=[])
    @patch("dashboard.app.search_cves", return_value=([], 0))
    @patch("dashboard.app.get_filter_values", return_value={"severities": ["HIGH"], "sources": ["nvd"]})
    @patch("dashboard.app.get_metrics", return_value={"cve_count": 1, "kev_count": 1, "article_count": 0, "high_critical_count": 1})
    def test_index_renders_search_and_filters(self, _metrics, _filter_values, _cves, _articles, get_conn):
        get_conn.return_value = MagicMock()
        response = self.client.get("/?q=openssl&severity=HIGH&kev=yes")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Search vulnerabilities and reporting", response.data)
        self.assertIn(b"openssl", response.data)

    @patch("dashboard.app.get_readonly_conn")
    def test_healthcheck_returns_ok(self, get_conn):
        conn = MagicMock()
        get_conn.return_value = conn
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})
        conn.cursor.return_value.__enter__.return_value.execute.assert_called_once_with("SELECT 1")

    @patch("dashboard.app.list_feeds", return_value=[])
    @patch("dashboard.app.search_articles", return_value=[])
    @patch("dashboard.app.get_readonly_conn")
    def test_articles_page_renders_rss_controls(self, get_conn, _articles, _feeds):
        get_conn.return_value = MagicMock()
        response = self.client.get("/articles")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add RSS feed", response.data)
        self.assertIn(b"Managed feeds", response.data)

    @patch("dashboard.app.add_rss_feed")
    @patch("dashboard.app.get_conn")
    def test_articles_page_adds_valid_feed(self, get_conn, add_feed):
        get_conn.return_value = MagicMock()
        response = self.client.post("/articles", data={"name": "Example", "feed_url": "https://example.org/feed.xml"})
        self.assertEqual(response.status_code, 302)
        add_feed.assert_called_once()
