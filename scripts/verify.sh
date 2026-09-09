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
PYTHONPATH=ai/demo python3 -m unittest discover -s ai/demo/tests -v

find frontend -name '*.json' -type f -exec python3 -m json.tool '{}' /dev/null ';'
find frontend -name '*.js' -type f -exec node --check '{}' ';'
node --check scripts/upload-miniprogram.js
bash -n scripts/backup_mysql.sh scripts/restore_mysql_staging.sh
node scripts/test_upload_guards.js
node scripts/test_frontend_auth.js
python3 scripts/check_frontend_contracts.py
python3 scripts/check_package_size.py

echo "All repository checks passed."
