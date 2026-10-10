#!/bin/sh
set -eu
umask 077
cd "$(dirname "$0")/.."
backup_dir=${BACKUP_DIR:-backups}
mkdir -p "$backup_dir"
temporary=$(mktemp "$backup_dir/.yatra-XXXXXXXX.dump.partial")
trap 'rm -f "$temporary"' EXIT HUP INT TERM
docker compose -f docker-compose.prod.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$temporary"
test -s "$temporary"
backup_file="$backup_dir/yatra-$(date -u +%Y%m%dT%H%M%SZ)-$(basename "$temporary" .dump.partial).dump"
mv "$temporary" "$backup_file"
printf '%s\n' "$backup_file"
