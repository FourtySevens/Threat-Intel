def classify(text):
    if "CVE-" in text:
        return "vulnerability", 0.9
    if "ransomware" in text.lower():
        return "malware", 0.8
    if "phishing" in text.lower():
        return "phishing"
    return "other", 0.5
