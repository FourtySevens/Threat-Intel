import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def canonical_url(url: str) -> str:
    """Remove fragments and common tracking parameters for stable URL deduplication."""
    parts = urlsplit(url.strip())
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", urlencode(query, doseq=True), ""))
