#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SQL_FILE="$SCRIPT_DIR/create-tables.sql"
ENV_FILE="$ROOT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env file not found at $ENV_FILE"
  exit 1
fi

SUPABASE_URL=$(grep -E "^NEXT_PUBLIC_SUPABASE_URL=" "$ENV_FILE" | sed 's/^NEXT_PUBLIC_SUPABASE_URL=//')
SERVICE_KEY=$(grep -E "^SUPABASE_SERVICE_ROLE_KEY=" "$ENV_FILE" | sed 's/^SUPABASE_SERVICE_ROLE_KEY=//')
DB_PASSWORD=$(grep -E "^DATABASE_URL=" "$ENV_FILE" | sed 's/^DATABASE_URL=//' | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')
PROJECT_REF=$(echo "$SUPABASE_URL" | sed -E 's|https://([^.]+)\.supabase\.co|\1|')

if [ -z "$SUPABASE_URL" ] || [ -z "$SERVICE_KEY" ]; then
  echo "ERROR: Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env"
  exit 1
fi

SQL=$(cat "$SQL_FILE")

echo "==> Project: $PROJECT_REF"
echo "==> Creating all 12 tables via Supabase Management API..."

# Use Supabase Management API to run SQL
# Endpoint: POST https://api.supabase.com/v1/projects/{ref}/database/query
# Auth: Bearer <access_token> OR we use the direct pg pooler

# Method: Use supabase CLI linked project
cd "$ROOT_DIR"

# Initialize supabase if not already
if [ ! -f "supabase/config.toml" ]; then
  supabase init 2>/dev/null || true
fi

# Link to remote project
echo "==> Linking to Supabase project..."
echo "$DB_PASSWORD" | supabase link --project-ref "$PROJECT_REF" --password stdin 2>&1 || true

# Create migration file
MIGRATION_NAME="initial_schema"
MIGRATIONS_DIR="supabase/migrations"
mkdir -p "$MIGRATIONS_DIR"

# Find existing or create new
MIGRATION_FILE=$(ls "$MIGRATIONS_DIR"/*_${MIGRATION_NAME}.sql 2>/dev/null | head -1 || true)
if [ -z "$MIGRATION_FILE" ]; then
  TIMESTAMP=$(date +%Y%m%d%H%M%S)
  MIGRATION_FILE="${MIGRATIONS_DIR}/${TIMESTAMP}_${MIGRATION_NAME}.sql"
  cp "$SQL_FILE" "$MIGRATION_FILE"
  echo "==> Created migration: $MIGRATION_FILE"
else
  echo "==> Migration already exists: $MIGRATION_FILE"
fi

# Push migration to remote
echo "==> Pushing migration to Supabase..."
echo "$DB_PASSWORD" | supabase db push --password stdin 2>&1

echo ""
echo "==> Done! All tables created successfully."
