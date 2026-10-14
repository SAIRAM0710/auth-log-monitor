#!/bin/bash

STATE_FILE="/home/sairam/Desktop/last_count.txt"

CURRENT_COUNT=$(sudo grep "Failed password" /var/log/auth.log | grep -v "sudo:" | wc -l)

if [ -f "$STATE_FILE" ]; then
    LAST_COUNT=$(cat "$STATE_FILE")
else
    LAST_COUNT=0
fi

NEW_COUNT=$((CURRENT_COUNT - LAST_COUNT))

echo "Total failed logins in log: $CURRENT_COUNT"
echo "New failed logins since last check: $NEW_COUNT"

echo "$CURRENT_COUNT" > "$STATE_FILE"
