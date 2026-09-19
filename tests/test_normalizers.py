import unittest
from unittest.mock import MagicMock, patch

from config.settings import Settings
from enrichment.kev_normalizer import normalize_kev
from enrichment.nvd_normalizer import normalize_nvd
from enrichment.cve_extractor import extract_cves
from storage.db import get_conn


class KevNormalizerTests(unittest.TestCase):
    def test_normalizes_optional_and_required_kev_fields(self):
        record = normalize_kev(
            {
                "cveID": "CVE-2026-12345",
                "dateAdded": "2026-01-02",
                "dueDate": "2026-02-03",
                "requiredAction": "Apply updates.",
            }
        )
        self.assertEqual(record["cve_id"], "CVE-2026-12345")
        self.assertTrue(record["exploited"])
        self.assertEqual(record["due_date"], "2026-02-03")


class NvdNormalizerTests(unittest.TestCase):
    def test_prefers_primary_cvss_31_and_english_description(self):
        record = normalize_nvd(
            {
                "cve": {
                    "id": "CVE-2026-12345",
                    "sourceIdentifier": "example@example.com",
                    "published": "2026-01-01T00:00:00.000",
                    "lastModified": "2026-01-02T00:00:00.000",
                    "descriptions": [
                        {"lang": "fr", "value": "French"},
                        {"lang": "en", "value": "English"},
                    ],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "type": "Secondary",
                                "cvssData": {"baseScore": 4.0},
                            },
                            {
                                "type": "Primary",
                                "exploitabilityScore": 3.9,
                                "cvssData": {
                                    "baseScore": 9.8,
                                    "baseSeverity": "CRITICAL",
                                    "attackVector": "NETWORK",
                                    "vectorString": "CVSS:3.1/AV:N",
                                },
                            },
                        ]
                    },
                }
            }
        )
        self.assertEqual(record["description"], "English")
        self.assertEqual(record["cvss_score"], 9.8)
        self.assertEqual(record["severity"], "CRITICAL")
        self.assertEqual(record["attack_vector"], "NETWORK")

    def test_requires_cve_id(self):
        with self.assertRaises(ValueError):
            normalize_nvd({"cve": {}})


class CveExtractorTests(unittest.TestCase):
    def test_extracts_case_insensitive_cves_without_duplicates(self):
        self.assertEqual(
            extract_cves("cve-2026-1234 and CVE-2026-1234567 and CVE-2026-1234"),
            ["CVE-2026-1234", "CVE-2026-1234567"],
        )


class DatabaseConnectionTests(unittest.TestCase):
    def test_requests_utf8_client_encoding(self):
        settings = Settings(
            database_url="postgresql://user:password@127.0.0.1:5432/threatintel",
            dashboard_database_url="postgresql://user:password@127.0.0.1:5432/threatintel",
            nvd_api_key=None,
            nvd_initial_lookback_days=7,
            nvd_overlap_minutes=15,
            nvd_request_delay_seconds=6.5,
            http_connect_timeout_seconds=10,
            http_read_timeout_seconds=60,
            log_level="INFO",
            log_format="json",
            dashboard_host="127.0.0.1",
            dashboard_port=8080,
        )
        connection = MagicMock()
        with patch("storage.db.get_settings", return_value=settings), patch(
            "storage.db.psycopg2.connect", return_value=connection
        ) as connect:
            self.assertIs(get_conn(), connection)

        connect.assert_called_once_with(
            settings.database_url,
            connect_timeout=10,
            application_name="threat-intel-ingestor",
        )
        connection.set_client_encoding.assert_called_once_with("UTF8")


if __name__ == "__main__":
    unittest.main()
