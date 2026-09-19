import requests
import time
from datetime import datetime, timedelta
import json

def fetch_new_cves(last_checked):
    """
    Fetch CVEs modified since last_checked using NIST API's lastModStartDate parameter
    """
    all_vulnerabilities = []
    start_index = 0
    results_per_page = 2000
    
    # Format timestamp for NIST API - without milliseconds
    last_checked_iso = last_checked.replace(microsecond=0).isoformat() + "Z"
    now_iso = datetime.now().replace(microsecond=0).isoformat() + "Z"
    print(f"Fetching CVEs modified since: {last_checked_iso}")
    
    while True:
        nist_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        # Filter by lastModStartDate for only recent changes
        # Note: Both lastModStartDate and lastModEndDate are required
        params = {
            "lastModStartDate": last_checked_iso,
            "lastModEndDate": now_iso,
            "startIndex": start_index,
            "resultsPerPage": results_per_page
        }
        
        print(f"Fetching from {nist_url} with params: {params}")
        
        res = requests.get(nist_url, params=params, timeout=120)
        print(f"Status code: {res.status_code}")
        print(f"Full URL: {res.url}")
        res.raise_for_status()
        
        data = res.json()
        vulnerabilities = data.get("vulnerabilities", [])
        
        if not vulnerabilities:
            break
        
        all_vulnerabilities.extend(vulnerabilities)
        total = data.get("totalResults", 0)
        
        print(f"Fetched {len(all_vulnerabilities)} of {total} new vulnerabilities...")
        
        if start_index + len(vulnerabilities) >= total:
            break
        
        start_index += results_per_page
        time.sleep(10)  # Rate limit
    
    return all_vulnerabilities

def cve_exists_in_db(cve_id, db_connection):
    """Check if CVE already exists in database"""
    cursor = db_connection.cursor()
    cursor.execute("SELECT id FROM cves WHERE cve_id = %s", (cve_id,))
    return cursor.fetchone() is not None

def extract_cvss_data(metrics):
    """Extract CVSS score, vector, and severity from metrics"""
    cvss_score = None
    access_vector = None
    severity = None
    exploitability = None
    
    if metrics:
        # Try to get CVSS v3.1 first, then fall back to v3.0
        cvss_v3 = metrics.get('cvssMetricV31', []) or metrics.get('cvssMetricV30', [])
        if cvss_v3:
            cvss_data = cvss_v3[0].get('cvssData', {})
            cvss_score = cvss_data.get('baseScore')
            access_vector = cvss_data.get('attackVector')
            severity = cvss_data.get('baseSeverity')
            exploitability = cvss_data.get('attackComplexity')
    
    return cvss_score, access_vector, severity, exploitability

def insert_cves(vulnerabilities, db_connection):
    """Insert new CVEs into database"""
    cursor = db_connection.cursor()
    inserted_count = 0
    
    for vuln in vulnerabilities:
        cve_id = vuln['cve']['id']
        
        # Skip if already in DB
        if cve_exists_in_db(cve_id, db_connection):
            continue
        
        # Extract relevant data
        cve_data = vuln['cve']
        description = cve_data.get('descriptions', [{}])[0].get('value', '')
        published = cve_data.get('published', None)
        last_modified = cve_data.get('lastModified', None)
        
        # Extract CVSS data
        metrics = cve_data.get('metrics', {})
        cvss_score, access_vector, severity, exploitability = extract_cvss_data(metrics)
        
        source = "NIST"
        
        # Insert into your table
        cursor.execute("""
            INSERT INTO cves (cve_id, source, published, last_modified, 
                             cvss_score, access_vector, severity, exploitability, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (cve_id, source, published, last_modified, cvss_score, 
              access_vector, severity, exploitability, description))
        
        inserted_count += 1
    
    db_connection.commit()
    print(f"Inserted {inserted_count} new CVEs")

def update_cves_periodic():
    """Run this on a schedule (every hour, every 6 hours, etc.)"""
    import psycopg2
    
    # Get last_checked from your config/database
    last_checked = datetime.now() - timedelta(hours=1)  # Check last hour
    
    try:
        new_cves = fetch_new_cves(last_checked)
        if new_cves:
            conn = psycopg2.connect("host=localhost dbname=threatintel user=ti_user")
            insert_cves(new_cves, conn)
            conn.close()
            print("CVE update complete!")
        else:
            print("No new CVEs found")
    except Exception as e:
        print(f"Error fetching CVEs: {e}")

if __name__ == "__main__":
    update_cves_periodic()