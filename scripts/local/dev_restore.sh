#!/bin/bash

# scripts/dev_restore.sh - Restore Temporal database from backup

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./scripts/dev_restore.sh [path_to_backup_file.sql|.zip]"
    echo "Available backups:"
    ls -1 backups/*.{sql,zip} 2>/dev/null || echo "  (none found)"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ File not found: $BACKUP_FILE"
    exit 1
fi

# 1. Handle ZIP extraction
CLEANUP_REQUIRED=false
if [[ "$BACKUP_FILE" == *.zip ]]; then
    echo "🤐 ZIP detected. Extracting..."
    unzip -o "$BACKUP_FILE" -d backups/ > /dev/null
    # Extract the base filename without .zip
    EXTRACTED_FILE="${BACKUP_FILE%.zip}"
    BACKUP_FILE="$EXTRACTED_FILE"
    CLEANUP_REQUIRED=true
fi

# Detect DB type from filename
if [[ "$BACKUP_FILE" == *"_pg_"* ]]; then
    TYPE="postgres"
    CONTAINER="temporal-postgresql"
    DB_USER="temporal"
    DB_NAME="temporal"
elif [[ "$BACKUP_FILE" == *"_mysql_"* ]]; then
    TYPE="mysql"
    CONTAINER="temporal-mysql"
    DB_USER="temporal"
    DB_NAME="temporal"
else
    echo "❌ Cannot determine database type from filename (expected '_pg_' or '_mysql_')."
    exit 1
fi

echo "⚠️  Restoring to $CONTAINER will overwrite current data. Continue? (y/n)"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "🔄 Restoring $BACKUP_FILE to $TYPE..."

if [ "$TYPE" == "postgres" ]; then
    docker exec $CONTAINER dropdb -U $DB_USER $DB_NAME --if-exists
    docker exec $CONTAINER createdb -U $DB_USER $DB_NAME
    cat "$BACKUP_FILE" | docker exec -i $CONTAINER psql -U $DB_USER $DB_NAME > /dev/null
elif [ "$TYPE" == "mysql" ]; then
    cat "$BACKUP_FILE" | docker exec -i $CONTAINER mysql -u $DB_USER -ptemporal $DB_NAME > /dev/null
fi

if [ "$CLEANUP_REQUIRED" = true ]; then
    rm "$BACKUP_FILE"
fi

echo "✅ Restore completed. You may need to restart the temporal server."
