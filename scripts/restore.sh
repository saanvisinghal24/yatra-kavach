#!/bin/sh
# Restore only into a newly created, disposable database. Never drop an existing database.
set -eu
cd "$(dirname "$0")/.."
if [ "$#" -ne 2 ]; then
  echo 'Usage: sh scripts/restore.sh backups/file.dump new_restore_database' >&2
  exit 2
fi
backup_file=$1
target_db=$2
case "$target_db" in ''|*[!a-zA-Z0-9_]*) echo 'Database name must contain only letters, digits and underscores.' >&2; exit 2;; esac
test -s "$backup_file"
# createdb fails if the database exists, preventing accidental overwrite.
docker compose -f docker-compose.prod.yml exec -T db sh -c 'createdb -U "$POSTGRES_USER" "$1"' sh "$target_db"
docker compose -f docker-compose.prod.yml exec -T db sh -c 'pg_restore --exit-on-error --no-owner -U "$POSTGRES_USER" -d "$1"' sh "$target_db" < "$backup_file"
printf 'Restored into %s. Review it before changing application database URLs.\n' "$target_db"
