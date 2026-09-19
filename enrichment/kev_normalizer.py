
def normalize_kev(entry: dict) -> dict:
    return {
        "cve_id": entry["cveID"],
        "date_added": entry.get("dateAdded"),
        "due_date": entry.get("dueDate"),
        "required_action": entry.get("requiredAction"),
        "exploited": True
    }
    