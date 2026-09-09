#!/usr/bin/env bash
set -euo pipefail

umask 077

: "${BACKUP_ENV:?Set BACKUP_ENV to staging or production}"
: "${MYSQL_DEFAULTS_FILE:?Set MYSQL_DEFAULTS_FILE to a chmod 600 MySQL client config}"
: "${BACKUP_ENCRYPTION_KEY_FILE:?Set BACKUP_ENCRYPTION_KEY_FILE to a chmod 600 passphrase file}"
: "${BACKUP_OUTPUT_DIR:?Set BACKUP_OUTPUT_DIR}"

case "$BACKUP_ENV" in
  staging|production) ;;
  *) echo "BACKUP_ENV must be staging or production" >&2; exit 2 ;;
esac

for secret_file in "$MYSQL_DEFAULTS_FILE" "$BACKUP_ENCRYPTION_KEY_FILE"; do
  test -f "$secret_file" || { echo "Required file not found: $secret_file" >&2; exit 2; }
  mode=$(stat -f '%Lp' "$secret_file" 2>/dev/null || stat -c '%a' "$secret_file")
  test "$mode" = "600" || { echo "Secret files must use chmod 600" >&2; exit 2; }
done

mkdir -p "$BACKUP_OUTPUT_DIR"
timestamp=$(date -u '+%Y%m%dT%H%M%SZ')
backup_file="$BACKUP_OUTPUT_DIR/shi-lian-${BACKUP_ENV}-${timestamp}.sql.gz.enc"

mysqldump \
  --defaults-extra-file="$MYSQL_DEFAULTS_FILE" \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --hex-blob \
  --set-gtid-purged=OFF \
  | gzip -9 \
  | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
      -pass "file:$BACKUP_ENCRYPTION_KEY_FILE" \
      -out "$backup_file"

if command -v shasum >/dev/null 2>&1; then
  checksum=$(shasum -a 256 "$backup_file" | awk '{print $1}')
else
  checksum=$(sha256sum "$backup_file" | awk '{print $1}')
fi
printf '%s  %s\n' "$checksum" "$(basename "$backup_file")" > "$backup_file.sha256"

echo "Encrypted backup created: $backup_file"
