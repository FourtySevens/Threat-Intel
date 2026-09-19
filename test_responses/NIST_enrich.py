from .NIST_request import run_nist
from enrichment.nvd_normalizer import normalize_nvd

def enrich_nist_list():
    """Legacy convenience wrapper using the production normalizer."""
    return [normalize_nvd(vulnerability) for vulnerability in run_nist()]




if __name__ == "__main__":
    records = enrich_nist_list()
    print(f"Total records: {len(records)}")    
    for i, record in enumerate(records, 1):
        print(f"\nRecord {i}:")
        print(record)
