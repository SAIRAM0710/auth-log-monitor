#!/usr/bin/env python3
from dotenv import load_dotenv
import os

load_dotenv()

import subprocess
import requests

THRESHOLD = 2
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

result = subprocess.run(
    ["bash", "/home/sairam/Desktop/check_failed_logins.sh"],
    capture_output=True, text=True
)
output = result.stdout

new_count = 0
for line in output.splitlines():
    if "New failed logins" in line:
        new_count = int(line.split(":")[1].strip())

if new_count >= THRESHOLD:
    message = f"🚨 ALERT: {new_count} new failed SSH login attempts detected on ubuntu-2!"
    requests.post(WEBHOOK_URL, json={"content": message})
    print("Alert sent:", message)
else:
    print(f"OK: {new_count} new failed logins, below threshold")
