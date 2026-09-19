import re

def extract_cves(text):
    """Return stable, normalized CVE identifiers mentioned in text."""
    matches = re.findall(r"\bCVE-\d{4}-\d{4,7}\b", text, flags=re.IGNORECASE)
    return sorted({match.upper() for match in matches})
