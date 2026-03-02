#!/usr/bin/env bash
# ==========================================================================
# Seed the Supabase database with schema and dev data
# ==========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Load environment
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
fi

# Database connection (default to local Supabase)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-54322}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

SCHEMA_FILE="$ROOT_DIR/packages/db/schema.sql"
SEED_FILE="$ROOT_DIR/packages/db/seed.sql"

PSQL_CMD="psql postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo ""
echo "=========================================="
echo "  Vaktram Database Seeding"
echo "=========================================="
echo ""

# --------------------------------------------------------------------------
# Apply schema
# --------------------------------------------------------------------------

if [ -f "$SCHEMA_FILE" ]; then
    log_info "Applying database schema..."
    $PSQL_CMD -f "$SCHEMA_FILE" 2>&1 | while IFS= read -r line; do
        case "$line" in
            *ERROR*) log_error "$line" ;;
            *NOTICE*) log_warn "$line" ;;
            *) ;;
        esac
    done
    log_ok "Schema applied successfully"
else
    log_error "Schema file not found: $SCHEMA_FILE"
    exit 1
fi

echo ""

# --------------------------------------------------------------------------
# Apply seed data
# --------------------------------------------------------------------------

if [ -f "$SEED_FILE" ]; then
    log_info "Seeding development data..."
    $PSQL_CMD -f "$SEED_FILE" 2>&1 | while IFS= read -r line; do
        case "$line" in
            *ERROR*) log_error "$line" ;;
            *NOTICE*) log_warn "$line" ;;
            *) ;;
        esac
    done
    log_ok "Seed data applied successfully"
else
    log_warn "Seed file not found: $SEED_FILE (skipping)"
fi

echo ""

# --------------------------------------------------------------------------
# Verify tables
# --------------------------------------------------------------------------

log_info "Verifying tables..."
TABLE_COUNT=$($PSQL_CMD -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
log_ok "$TABLE_COUNT tables found in public schema"

echo ""
echo "=========================================="
echo -e "  ${GREEN}Database seeded successfully!${NC}"
echo "=========================================="
echo ""
