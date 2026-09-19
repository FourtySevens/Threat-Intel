#!/bin/bash

DB_NAME="threatintel"
CHANNEL="updates"
DB_USER="ti_user"

echo "Listening for notifications on channel '$CHANNEL' in database '$DB_NAME'..."

psql -h localhost -U "$DB_USER" -d "$DB_NAME" <<EOF
LISTEN $CHANNEL;
SELECT pg_sleep(1000000);
EOF
