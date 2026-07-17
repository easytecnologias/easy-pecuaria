#!/bin/sh
# Backup diario do Postgres do sistema de pecuaria (rotacao 14 dias).
set -eu
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

BDIR=/home/central/pecuaria/backups
CONT=pecuaria-postgres
mkdir -p "$BDIR"
STAMP=$(date +%F_%H%M)
FILE="$BDIR/pecuaria_${STAMP}.sql.gz"

# dump direto do container (usa credenciais do proprio container), comprimido no host
docker exec "$CONT" sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' | gzip > "$FILE"

# valida que o dump nao ficou vazio/corrompido
if ! gzip -t "$FILE" 2>/dev/null || [ "$(stat -c%s "$FILE")" -lt 1000 ]; then
  echo "$(date '+%F %T') ERRO: backup invalido ($FILE)" >&2
  rm -f "$FILE"
  exit 1
fi

# rotacao: remove backups com mais de 14 dias
find "$BDIR" -name 'pecuaria_*.sql.gz' -mtime +14 -delete

echo "$(date '+%F %T') OK: $FILE ($(du -h "$FILE" | cut -f1))"
