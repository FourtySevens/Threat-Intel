import requests

URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

def fetch_kev():
    data = requests.get(URL, timeout=10).json()
    return data["vulnerabilities"]
