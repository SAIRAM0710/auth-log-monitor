#!/usr/bin/env python3
from dotenv import load_dotenv
import os

load_dotenv()

import subprocess
import sys
import requests

THRESHOLD = 2
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

result = subprocess.run(
    ["bash", os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_failed_logins.sh")],
    capture_output=True, text=True
)
if result.returncode != 0:
    print("ERROR: check_failed_logins.sh failed:", result.stderr.strip())
    sys.exit(1)
output = result.stdout

new_count = 0
for line in output.splitlines():
    if "New failed logins" in line:
        new_count = int(line.split(":")[1].strip())

if new_count >= THRESHOLD:
    message = f"🚨 ALERT: {new_count} new failed SSH login attempts detected on ubuntu-2!"
    if not WEBHOOK_URL:
        print("ERROR: DISCORD_WEBHOOK_URL is not set in .env; alert not sent.")
        sys.exit(1)
    # requests puts the full URL in many of its error messages, and the webhook
    # URL is a secret. Catch every error and print only safe details, so the URL
    # never ends up in the terminal, monitor.log, or cron mail.
    try:
        response = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    except requests.exceptions.RequestException as error:
        print(f"ERROR: could not reach Discord ({type(error).__name__}); alert not sent.")
        sys.exit(1)
    if not response.ok:
        print(f"ERROR: Discord returned HTTP {response.status_code}; alert not sent.")
        sys.exit(1)
    print("Alert sent:", message)
else:
    print(f"OK: {new_count} new failed logins, below threshold")
