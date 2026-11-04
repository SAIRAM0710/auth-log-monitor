# auth-log-monitor

A small Bash + Python tool that watches `/var/log/auth.log` for failed password
attempts and sends an alert to a Discord channel when too many new ones appear.

## Why

Repeated failed logins (often over SSH) are usually the first sign of someone
guessing passwords on your machine. Linux already records every attempt in
`/var/log/auth.log`, but nobody reads that file by hand. This tool checks it on a
schedule and pings you on Discord when the number of new failures crosses a
threshold.

## How it works

1. **`check_failed_logins.sh` (the counter).** Counts lines in
   `/var/log/auth.log` that contain `Failed password`, skipping lines that contain
   `sudo:`. This is `CURRENT_COUNT`.
2. **`last_count.txt` (the state file).** Stores the count from the previous run,
   so the script can work out how many failures are *new*:
   `NEW_COUNT = CURRENT_COUNT - LAST_COUNT`. If the log has been rotated (the count
   went down), every failure in the fresh log is treated as new. The file is
   created automatically next to the script and is git-ignored.
3. **`check_and_alert.py` (the decision).** Runs the Bash script, reads the
   `New failed logins since last check:` line, and compares it to `THRESHOLD`
   (currently `2`).
4. **Discord post.** If `NEW_COUNT >= THRESHOLD`, it posts a message to the Discord
   webhook stored in `.env` as `DISCORD_WEBHOOK_URL`. Otherwise it prints `OK`.

## Setup

On Debian/Ubuntu, Python's `venv` module is a separate package. Install it first,
or `python3 -m venv` below fails with `ensurepip is not available`:

```bash
sudo apt install python3-venv
```

Then:

```bash
git clone https://github.com/SAIRAM0710/auth-log-monitor.git
cd auth-log-monitor
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and replace `your-webhook-url-here` with your real Discord webhook URL
(Discord: Server Settings → Integrations → Webhooks → New Webhook → Copy URL).

Run it once by hand:

```bash
.venv/bin/python check_and_alert.py
```

### Run it on a schedule (cron)

First make sure your user can read the log (see [Permissions](#permissions)).
Then add the job to **your own** crontab (`crontab -e`, no `sudo`). Use full
paths, because cron does not start in your repo folder or know about your
virtual environment. Replace the path with wherever you cloned the repo:

```cron
*/5 * * * * cd /home/YOUR_USER/Desktop/auth-log-monitor && .venv/bin/python check_and_alert.py >> monitor.log 2>&1
```

This runs every 5 minutes and appends output to `monitor.log` (git-ignored).

## Sample output

Output of `check_failed_logins.sh` on a test log with 4 failed SSH passwords and
1 failed `sudo` password (the `sudo` one is excluded):

```
Total failed logins in log: 4
New failed logins since last check: 4
```

And `monitor.log` from a real cron run (one line every 5 minutes), where three
failed SSH logins were made on purpose and the next run caught them and alerted:

```
OK: 0 new failed logins, below threshold
OK: 0 new failed logins, below threshold
OK: 0 new failed logins, below threshold
OK: 0 new failed logins, below threshold
Alert sent: 🚨 ALERT: 3 new failed SSH login attempts detected on ubuntu-2!
OK: 0 new failed logins, below threshold
```

The same output is saved in [`sample_output.log`](sample_output.log).

## Permissions

`/var/log/auth.log` is readable only by `root` and the `adm` group on
Debian/Ubuntu. The script reads it without `sudo`, so the user that runs it must
be in the `adm` group. Check with `groups`; if `adm` is missing, add it and then
log out and back in:

```bash
sudo usermod -aG adm "$USER"
```

This is deliberately less power than running as root: `adm` can read system logs
but cannot change the system. If the log isn't readable, the script stops with
`ERROR: cannot read /var/log/auth.log` and leaves `last_count.txt` untouched,
instead of silently counting 0.

## Known limitations

- **Excludes sudo failures.** Lines containing `sudo:` are skipped, so failed
  `sudo` passwords are not counted.
- **Fixed threshold.** `THRESHOLD = 2` is hardcoded in `check_and_alert.py`;
  change it there.
- **Hostname is hardcoded.** The alert text says `ubuntu-2`.
- **Depends on the log format.** It matches the literal text `Failed password` in
  `/var/log/auth.log` (Debian/Ubuntu). It will miss failures on systems that log
  elsewhere (e.g. `/var/log/secure` on RHEL/Fedora, or journald-only systems), and
  it does not count other failure types such as `Invalid user` or key-only
  rejections.
- **Rotation is approximate.** After a log rotation, failures that happened between
  the last check and the rotation are lost.

## Security note

- **Never commit `.env`.** It is listed in `.gitignore`; keep it that way.
- **The webhook URL is a credential.** Anyone who has it can post messages to your
  Discord channel. Don't paste it into issues, screenshots, logs, or chat.
- **If it leaks, rotate it.** In Discord, delete the webhook and create a new one,
  then update `.env`. Deleting the URL from a file or a git commit is not enough,
  because copies remain in git history and anywhere it was already seen.
