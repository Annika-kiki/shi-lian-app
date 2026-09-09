#!/usr/bin/env bash
set -euo pipefail

: "${CONFIRM_RESTORE:?Set CONFIRM_RESTORE=staging-only}"
: "${RESTORE_ENV:?Set RESTORE_ENV=staging}"
: "${MYSQL_DEFAULTS_FILE:?Set MYSQL_DEFAULTS_FILE to a chmod 600 staging MySQL client config}"
: "${BACKUP_ENCRYPTION_KEY_FILE:?Set BACKUP_ENCRYPTION_KEY_FILE to a chmod 600 passphrase file}"
: "${BACKUP_FILE:?Set BACKUP_FILE to an encrypted backup}"

test "$CONFIRM_RESTORE" = "staging-only" || { echo "Restore confirmation missing" >&2; exit 2; }
test "$RESTORE_ENV" = "staging" || { echo "This script refuses non-staging restores" >&2; exit 2; }
test -f "$BACKUP_FILE" || { echo "Backup file not found" >&2; exit 2; }

for secret_file in "$MYSQL_DEFAULTS_FILE" "$BACKUP_ENCRYPTION_KEY_FILE"; do
  test -f "$secret_file" || { echo "Required file not found: $secret_file" >&2; exit 2; }
  mode=$(stat -f '%Lp' "$secret_file" 2>/dev/null || stat -c '%a' "$secret_file")
  test "$mode" = "600" || { echo "Secret files must use chmod 600" >&2; exit 2; }
done

checksum_file="$BACKUP_FILE.sha256"
test -f "$checksum_file" || { echo "Backup checksum file not found" >&2; exit 2; }
backup_dir=$(CDPATH= cd -- "$(dirname -- "$BACKUP_FILE")" && pwd)
if command -v shasum >/dev/null 2>&1; then
  (cd "$backup_dir" && shasum -a 256 -c "$(basename "$checksum_file")")
else
  (cd "$backup_dir" && sha256sum -c "$(basename "$checksum_file")")
fi

openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -pass "file:$BACKUP_ENCRYPTION_KEY_FILE" \
  -in "$BACKUP_FILE" \
  | gzip -dc \
  | mysql --defaults-extra-file="$MYSQL_DEFAULTS_FILE"

echo "Staging restore completed; run migrations and core API checks before accepting it."
