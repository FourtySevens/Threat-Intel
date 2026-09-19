THREAT_KEYWORDS = {
    'malware': ['ransomware', 'trojan', 'botnet'],
    'vulnerability': ['cve-', 'zero-day', 'exploit'],
    'phishing': ['phishing', 'credential harvesting']
}

def categorize(text):
    hits = []
    lower = text.lower()

    for tag, words in THREAT_KEYWORDS.items():
        if any(w in lower for w in words):
            hits.append(tag)

    return hits
