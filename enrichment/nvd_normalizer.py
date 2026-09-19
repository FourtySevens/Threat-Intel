"""Convert NVD API records into the storage contract."""

from __future__ import annotations


def _description(descriptions: list[dict]) -> str | None:
    for item in descriptions:
        if item.get("lang") == "en" and item.get("value"):
            return item["value"]
    for item in descriptions:
        if item.get("value"):
            return item["value"]
    return None


def _metric(metrics: dict) -> dict:
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        values = metrics.get(key) or []
        if values:
            primary = next((item for item in values if item.get("type") == "Primary"), values[0])
            return primary
    return {}


def normalize_nvd(entry: dict) -> dict:
    cve = entry.get("cve", entry)
    cve_id = cve.get("id")
    if not cve_id:
        raise ValueError("NVD record is missing cve.id")

    metric = _metric(cve.get("metrics") or {})
    cvss = metric.get("cvssData") or {}
    return {
        "cve_id": cve_id,
        "description": _description(cve.get("descriptions") or []),
        "cvss_score": cvss.get("baseScore"),
        "severity": cvss.get("baseSeverity") or metric.get("baseSeverity"),
        "source": "nvd",
        "source_identifier": cve.get("sourceIdentifier"),
        "published_at": cve.get("published"),
        "last_modified_at": cve.get("lastModified"),
        "attack_vector": cvss.get("attackVector") or cvss.get("accessVector"),
        "cvss_vector": cvss.get("vectorString"),
        "exploitability_score": metric.get("exploitabilityScore"),
    }
