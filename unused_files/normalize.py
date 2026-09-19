def normalize_kev(v):
    return {
        "title": f"CVE-{v['cveID']} actively exploited",
        "description": v['shortDescription'],
        "source" : "CISA KEV",
        "published": v["dateAdded"],
        "intel_type": "vulnerability",
        "confidence": 0.95,
        "referances": v.get('notes', []),
        "iocs": {},
        "raw": v
    }
