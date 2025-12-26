#!/bin/bash

# scripts/dev.sh - Manage local Temporal development environment

set -e

# Default mode
MODE=${2:-"postgres"}

case "$MODE" in
    postgres)
        COMPOSE_FILE="docker-compose-postgres.yml"
        ;;
    tls)
        COMPOSE_FILE="docker-compose-tls.yml"
        ;;
    all)
        COMPOSE_FILE="docker-compose.yml" # Standard with ES
        ;;
    *)
        echo "❌ Unknown mode: $MODE (Supported: postgres, tls, all)"
        exit 1
        ;;
esac

show_help() {
    echo "Usage: ./scripts/dev_control.sh [command] [mode]"
    echo ""
    echo "Commands:"
    echo "  start    Start the Temporal stack in detached mode"
    echo "  stop     Stop and remove containers"
    echo "  status   Show status of containers"
    echo "  logs     Follow logs for all services"
    echo ""
    echo "Modes (optional, default: postgres):"
    echo "  postgres  Lightweight (Postgres only)"
    echo "  tls       Secure (Postgres + TLS)"
    echo "  all       Standard (Postgres + Elasticsearch)"
}

case "$1" in
    start)
        echo "🚀 Starting Temporal ($MODE mode)..."
        docker-compose -f $COMPOSE_FILE up -d
        echo "✅ Stack is up. UI: http://localhost:8080"
        ;;
    stop)
        echo "🛑 Shutting down Temporal ($MODE mode)..."
        docker-compose -f $COMPOSE_FILE down
        ;;
    status)
        docker-compose -f $COMPOSE_FILE ps
        ;;
    logs)
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    *)
        show_help
        exit 1
        ;;
esac
