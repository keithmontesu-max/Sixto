#!/usr/bin/env bash
# SIXTO ROOT X — nightly encrypted backup (run via cron/systemd timer)
set -euo pipefail
DB_URL="${1:?Usage: backup.sh <POSTGRES_DSN> [dest]}"
DEST="${2:-/backups/sixto-$(date +%F)}"
mkdir -p "$DEST"
pg_dump "$DB_URL" | gzip > "$DEST/db.sql.gz"
# Encrypt with age (install age, key in secret manager — never in repo)
# age -r "$AGE_RECIPIENT" -o "$DEST/db.sql.gz.age" "$DEST/db.sql.gz"
echo "Backup written to $DEST (encrypt before offsite copy)"
# Monitor: alert if $DEST missing or older than 26h (see docs/runbook.md)
