-- Enable pgvector for IVFFlat similarity search on meeting_embeddings.
-- Idempotent — safe to re-run.

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE vaktram.meeting_embeddings
  ADD COLUMN IF NOT EXISTS embedding_v vector(1536);

CREATE INDEX IF NOT EXISTS ix_embeddings_v
  ON vaktram.meeting_embeddings
  USING ivfflat (embedding_v vector_cosine_ops)
  WITH (lists = 100);
