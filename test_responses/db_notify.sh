#!/bin/bash
DB_NAME="threatintel"
DB_USER="ti_user"
CHANNEL="nist_update"

psql -U "$DB_USER" -d "$DB_NAME" -Atq -c "LISTEN $CHANNEL" | while read -r line; do
    echo "Database change! for ID: $line"
    ntfy publish threat_intel_change "CVE DATABASE CHANGED... $line"
done
