"""Verify all Vaktram tables exist via Supabase REST API (no direct DB needed)."""

import json
import os
import sys
import urllib.request
import urllib.error

# Load .env
ROOT_DIR = os.path.join(os.path.dirname(__file__), "../..")
env_path = os.path.join(ROOT_DIR, ".env")

env = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            env[key.strip()] = val.strip()

SUPABASE_URL = env.get("NEXT_PUBLIC_SUPABASE_URL", "")
SERVICE_KEY = env.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SERVICE_KEY:
    print("ERROR: Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

SCHEMA = "vaktram"

EXPECTED_TABLES = [
    "organizations",
    "user_profiles",
    "meetings",
    "meeting_participants",
    "transcript_segments",
    "meeting_summaries",
    "user_ai_configs",
    "calendar_connections",
    "meeting_embeddings",
    "api_keys",
    "audit_logs",
    "notifications",
]

EXPECTED_ENUMS = ["meeting_status", "meeting_platform"]


def run_sql(sql: str) -> list[dict]:
    """Execute SQL via Supabase PostgREST RPC or pg-meta."""
    # Use the Supabase pg-meta API (available on all projects)
    url = f"{SUPABASE_URL}/rest/v1/rpc/vaktram_verify_query"

    # First try: create a helper function, then call it
    # Simpler approach: use PostgREST's built-in query on information_schema
    # But PostgREST only exposes the public schema by default.
    # Best approach: use the raw SQL endpoint via management API

    # Use Supabase's postgres-meta endpoint
    # POST /pg/query with {"query": sql}
    # This is available at the project URL under /pg
    # Actually, let's just query the tables directly via PostgREST

    # The simplest reliable method: hit the REST API for each table
    # If the table exists, we get 200. If not, we get 404.
    return []


def check_table_via_rest(table_name: str) -> tuple[bool, int]:
    """Check if a table exists by hitting its REST endpoint. Returns (exists, count)."""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?select=*&limit=0"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "count=exact",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            count_header = resp.headers.get("content-range", "")
            # Format: "0-0/5" or "*/0"
            if "/" in count_header:
                count = int(count_header.split("/")[1])
            else:
                count = 0
            return True, count
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, 0
        # 400 might mean table exists but schema not exposed
        return False, -1
    except Exception:
        return False, -1


def check_schema_via_rest() -> dict:
    """Query information_schema via PostgREST to check vaktram schema tables."""
    # PostgREST can't query information_schema directly.
    # Instead, we'll create a temporary RPC function to inspect the schema.

    # Step 1: Create a verification function
    create_fn_sql = """
    CREATE OR REPLACE FUNCTION public.vaktram_verify()
    RETURNS json
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    DECLARE
      result json;
    BEGIN
      SELECT json_build_object(
        'schema_exists', EXISTS(
          SELECT 1 FROM information_schema.schemata WHERE schema_name = 'vaktram'
        ),
        'tables', (
          SELECT json_agg(json_build_object('name', table_name))
          FROM information_schema.tables
          WHERE table_schema = 'vaktram'
        ),
        'enums', (
          SELECT json_agg(json_build_object(
            'name', t.typname,
            'values', (
              SELECT json_agg(e.enumlabel ORDER BY e.enumsortorder)
              FROM pg_enum e WHERE e.enumtypid = t.oid
            )
          ))
          FROM pg_type t
          JOIN pg_namespace n ON t.typnamespace = n.oid
          WHERE n.nspname = 'vaktram' AND t.typtype = 'e'
        ),
        'triggers', (
          SELECT json_agg(json_build_object(
            'name', trigger_name,
            'table', event_object_table
          ))
          FROM information_schema.triggers
          WHERE trigger_schema = 'vaktram'
        ),
        'indexes', (
          SELECT json_agg(json_build_object(
            'name', indexname,
            'table', tablename
          ))
          FROM pg_indexes
          WHERE schemaname = 'vaktram' AND indexname LIKE 'idx_%'
        )
      ) INTO result;
      RETURN result;
    END;
    $$;
    """

    # Create the function via SQL
    url = f"{SUPABASE_URL}/rest/v1/rpc/vaktram_verify"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }

    # First, try calling the function (may already exist)
    req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError:
        pass

    # Function doesn't exist, create it first via the SQL endpoint
    # We need to use a different approach - create it via PostgREST raw SQL
    # Use the pg endpoint
    print("  [INFO] Creating verification function...")

    # Try creating via raw query endpoint
    sql_url = f"{SUPABASE_URL}/rest/v1/rpc/exec"
    sql_req = urllib.request.Request(
        sql_url,
        data=json.dumps({"query": create_fn_sql}).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(sql_req) as resp:
            pass
    except urllib.error.HTTPError:
        # exec doesn't exist either, print instructions
        print("\n  The verification function doesn't exist yet.")
        print("  Please run this SQL in Supabase SQL Editor first:\n")
        print(create_fn_sql)
        print("\n  Then re-run this script.")
        return None

    # Now call the function
    req = urllib.request.Request(url, data=b"{}", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    print(f"{'='*55}")
    print(f"  Vaktram DB Verification (schema: {SCHEMA})")
    print(f"{'='*55}\n")
    print(f"  Supabase: {SUPABASE_URL}\n")

    result = check_schema_via_rest()

    if result is None:
        # Fallback: check tables via REST API directly
        print("\n  Falling back to REST API table checks...\n")
        print(f"--- Tables (expected: {len(EXPECTED_TABLES)}) ---")

        # PostgREST only exposes public schema by default
        # If tables are in 'vaktram' schema, they won't be accessible via REST
        # unless db_schemas is configured
        print("  [INFO] Tables in 'vaktram' schema are not accessible via REST API")
        print("         by default. To verify, run this SQL in Supabase SQL Editor:\n")
        print_verification_sql()
        return

    # Parse results
    schema_exists = result.get("schema_exists", False)
    tables = result.get("tables") or []
    enums = result.get("enums") or []
    triggers = result.get("triggers") or []
    indexes = result.get("indexes") or []

    if schema_exists:
        print(f"[OK] Schema '{SCHEMA}' exists")
    else:
        print(f"[FAIL] Schema '{SCHEMA}' does NOT exist")
        print("\n  -> Run create-tables.sql in Supabase SQL Editor first.")
        return

    # Tables
    existing_tables = {t["name"] for t in tables}
    print(f"\n--- Tables (expected: {len(EXPECTED_TABLES)}) ---")
    all_ok = True
    for table in EXPECTED_TABLES:
        if table in existing_tables:
            print(f"  [OK]   {SCHEMA}.{table}")
        else:
            print(f"  [FAIL] {SCHEMA}.{table:<25} MISSING")
            all_ok = False

    extra = existing_tables - set(EXPECTED_TABLES)
    if extra:
        print(f"\n  [INFO] Extra tables: {', '.join(extra)}")

    # Enums
    existing_enums = {e["name"] for e in enums}
    print(f"\n--- Enums (expected: {len(EXPECTED_ENUMS)}) ---")
    for enum_name in EXPECTED_ENUMS:
        matching = [e for e in enums if e["name"] == enum_name]
        if matching:
            vals = matching[0].get("values", [])
            print(f"  [OK]   {enum_name:<25} values: {', '.join(vals)}")
        else:
            print(f"  [FAIL] {enum_name:<25} MISSING")
            all_ok = False

    # Triggers
    print(f"\n--- Triggers ---")
    if triggers:
        for trig in triggers:
            print(f"  [OK]   {trig['name']:<40} on {trig['table']}")
    else:
        print("  [WARN] No triggers found")

    # Indexes
    print(f"\n--- Custom Indexes ---")
    if indexes:
        for idx in indexes:
            print(f"  [OK]   {idx['name']:<45} on {idx['table']}")
    else:
        print("  [WARN] No custom indexes found")

    # Summary
    print(f"\n{'='*55}")
    if all_ok:
        print("  ALL CHECKS PASSED - Database is ready!")
    else:
        print("  SOME CHECKS FAILED - See above for details")
    print(f"{'='*55}")


def print_verification_sql():
    """Print SQL that can be run in Supabase SQL Editor to verify."""
    sql = f"""
-- Run this in Supabase SQL Editor to verify tables:

-- 1. Check schema
SELECT schema_name FROM information_schema.schemata
WHERE schema_name = '{SCHEMA}';

-- 2. Check all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = '{SCHEMA}'
ORDER BY table_name;

-- 3. Check enums
SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder)
FROM pg_type t
JOIN pg_namespace n ON t.typnamespace = n.oid
JOIN pg_enum e ON e.enumtypid = t.oid
WHERE n.nspname = '{SCHEMA}' AND t.typtype = 'e'
GROUP BY t.typname;

-- 4. Check triggers
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_schema = '{SCHEMA}';

-- 5. Check indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = '{SCHEMA}' AND indexname LIKE 'idx_%';
"""
    print(sql)


if __name__ == "__main__":
    main()
