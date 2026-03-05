-- Optional pgvector migration
-- timestamp: 2026-03-04_20-05-00

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS memory_vectors (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  task_id TEXT,
  content TEXT NOT NULL,
  embedding vector(1536) NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_memory_user_task ON memory_vectors(user_id, task_id);
CREATE INDEX IF NOT EXISTS idx_memory_embedding_ivfflat
  ON memory_vectors USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
