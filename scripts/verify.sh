#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_root"

python3 -m compileall -q backend ai/demo
python3 -m pytest
temp_db=$(mktemp "${TMPDIR:-/tmp}/shi-lian-migration.XXXXXX.db")
trap 'rm -f "$temp_db"' EXIT
DATABASE_URL="sqlite:///$temp_db" alembic upgrade head
DATABASE_URL="sqlite:///$temp_db" alembic check
APP_ENV=development DATABASE_URL="mysql+pymysql://dummy:dummy@127.0.0.1:3306/shi_lian_staging?charset=utf8mb4" \
  python3 -m alembic upgrade head --sql >/dev/null
PYTHONPATH=ai/demo python3 -m unittest discover -s ai/demo/tests -v

find frontend -name '*.json' -type f -exec python3 -m json.tool '{}' /dev/null ';'
find frontend -name '*.js' -type f -exec node --check '{}' ';'
node --check scripts/upload-miniprogram.js
bash -n scripts/backup_mysql.sh scripts/restore_mysql_staging.sh scripts/migrate_staging.sh
if APP_ENV=production MYSQL_ADDRESS=db:3306 MYSQL_USERNAME=sl_migrator MYSQL_PASSWORD=test MYSQL_DATABASE=shi_lian_staging sh scripts/migrate_staging.sh >/dev/null 2>&1; then
  echo "Staging migration guard accepted a production environment" >&2
  exit 1
fi
if APP_ENV=staging MYSQL_ADDRESS=db:3306 MYSQL_USERNAME=root MYSQL_PASSWORD=test MYSQL_DATABASE=shi_lian_staging sh scripts/migrate_staging.sh >/dev/null 2>&1; then
  echo "Staging migration guard accepted the root account" >&2
  exit 1
fi
if APP_ENV=staging MYSQL_ADDRESS=db:3306 MYSQL_USERNAME=shi_lian_migrator MYSQL_PASSWORD=test MYSQL_DATABASE=shi_lian_staging sh scripts/migrate_staging.sh >/dev/null 2>&1; then
  echo "Staging migration guard accepted an unapproved account name" >&2
  exit 1
fi
node scripts/test_upload_guards.js
node scripts/test_frontend_auth.js
python3 scripts/check_frontend_contracts.py
python3 scripts/check_package_size.py

echo "All repository checks passed."
