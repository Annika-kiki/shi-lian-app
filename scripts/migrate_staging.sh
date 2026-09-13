#!/usr/bin/env sh
set -eu

: "${APP_ENV:?Set APP_ENV=staging}"
: "${MYSQL_ADDRESS:?Set MYSQL_ADDRESS}"
: "${MYSQL_USERNAME:?Set MYSQL_USERNAME}"
: "${MYSQL_PASSWORD:?Set MYSQL_PASSWORD}"
: "${MYSQL_DATABASE:?Set MYSQL_DATABASE=shi_lian_staging}"

test "$APP_ENV" = "staging" || {
  echo "This migration entrypoint only permits APP_ENV=staging" >&2
  exit 2
}
test "$MYSQL_DATABASE" = "shi_lian_staging" || {
  echo "This migration entrypoint only permits MYSQL_DATABASE=shi_lian_staging" >&2
  exit 2
}
test "$MYSQL_USERNAME" = "shi_lian_migrator" || {
  echo "Use the dedicated shi_lian_migrator account" >&2
  exit 2
}

python -m alembic upgrade head
python -m backend.database.seed
python -m alembic check

echo "Staging schema migration and reference-data seed completed."
