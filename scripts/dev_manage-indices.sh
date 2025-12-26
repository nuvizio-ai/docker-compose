#!/bin/bash

# scripts/dev_manage-indices.sh - Manage Temporal Elasticsearch indices

set -e

ES_URL="http://localhost:9200"
INDEX_NAME="temporal-visibility-dev"

# Check if ES is reachable
if ! curl -s --connect-timeout 2 "$ES_URL" > /dev/null; then
    echo "❌ Elasticsearch is not reachable at $ES_URL."
    echo "This might be because you are running in 'postgres' mode (which is Elasticsearch-free)."
    exit 1
fi

show_help() {
    echo "Usage: ./scripts/dev_manage-indices.sh [command]"
    echo ""
    echo "Commands:"
    echo "  list      List all indices"
    echo "  delete    Delete the visibility index (DANGER!)"
    echo "  health    Check Elasticsearch cluster health"
}

case "$1" in
    list)
        curl -s "$ES_URL/_cat/indices?v"
        ;;
    delete)
        echo "⚠️  Deleting index '$INDEX_NAME' will remove Visibility metadata. Continue? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            curl -X DELETE "$ES_URL/$INDEX_NAME"
            echo -e "\n✅ Index deleted."
        else
            echo "Aborted."
        fi
        ;;
    health)
        curl -s "$ES_URL/_cluster/health" | python3 -m json.tool
        ;;
    *)
        show_help
        exit 1
        ;;
esac
