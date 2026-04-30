-- Phase 2: full-text and vector search indexes.

-- Postgres FTS index on transcript content. The to_tsvector expression in the
-- search query matches this functional index, so plans use it directly.
CREATE INDEX IF NOT EXISTS ix_transcript_segments_fts
  ON vaktram.transcript_segments
  USING GIN (to_tsvector('english', content));

-- Vector search via pgvector (optional — fail open if extension unavailable).
DO $$ BEGIN
  CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN insufficient_privilege THEN
  RAISE NOTICE 'pgvector not enabled; vector search will use JSONB fallback';
END $$;

-- Add a real vector column alongside the JSONB one. Old code keeps working;
-- new code can populate this column and benefit from a proper IVFFlat index.
DO $$ BEGIN
  ALTER TABLE vaktram.meeting_embeddings ADD COLUMN embedding_v vector(1536);
EXCEPTION WHEN duplicate_column THEN null;
WHEN undefined_object THEN
  RAISE NOTICE 'pgvector type unavailable; skipping embedding_v column';
END $$;

DO $$ BEGIN
  CREATE INDEX IF NOT EXISTS ix_meeting_embeddings_v
    ON vaktram.meeting_embeddings
    USING ivfflat (embedding_v vector_cosine_ops)
    WITH (lists = 100);
EXCEPTION WHEN undefined_table OR undefined_object THEN null; END $$;
