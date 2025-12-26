#!/bin/bash

# scripts/dev_backup.sh - Backup Temporal database (Postgres, MySQL, or Cassandra)

set -e

FORMAT=${1:-"sql"}
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

if [[ "$FORMAT" != "sql" && "$FORMAT" != "zip" ]]; then
    echo "Usage: ./scripts/dev_backup.sh [sql|zip]"
    exit 1
fi

# 1. Detect which database is running
if docker ps --format '{{.Names}}' | grep -q "temporal-postgresql"; then
    TYPE="pg"
    CONTAINER="temporal-postgresql"
    FILE="$BACKUP_DIR/temporal_pg_$TIMESTAMP.sql"
    echo "📦 Detected PostgreSQL. Starting backup..."
    docker exec $CONTAINER pg_dump -U temporal temporal > "$FILE"

elif docker ps --format '{{.Names}}' | grep -q "temporal-mysql"; then
    TYPE="mysql"
    CONTAINER="temporal-mysql"
    FILE="$BACKUP_DIR/temporal_mysql_$TIMESTAMP.sql"
    echo "📦 Detected MySQL. Starting backup..."
    docker exec $CONTAINER mysqldump -u temporal -ptemporal temporal > "$FILE"

elif docker ps --format '{{.Names}}' | grep -q "temporal-cassandra"; then
    TYPE="cass"
    CONTAINER="temporal-cassandra"
    FILE="$BACKUP_DIR/temporal_cass_$TIMESTAMP.tar.gz"
    echo "📦 Detected Cassandra. Starting backup (snapshot)..."
    docker exec $CONTAINER nodetool snapshot temporal
    echo "⚠️  Cassandra snapshot created inside container."
    exit 0
else
    echo "❌ No supported database container found running."
    exit 1
fi

# 2. Handle ZIP format if requested
if [ "$FORMAT" == "zip" ]; then
    echo "🤐 Compressing to ZIP..."
    zip -j "$FILE.zip" "$FILE" > /dev/null
    rm "$FILE"
    FILE="$FILE.zip"
fi

echo "✅ Backup completed: $FILE"
# Keep only last 5 backups per type
ls -t $BACKUP_DIR/temporal_${TYPE}_* | tail -n +6 | xargs rm -f -- 2>/dev/null || true
